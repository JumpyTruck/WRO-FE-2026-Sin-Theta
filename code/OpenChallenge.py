import cv2
import numpy as np
from picamera2 import Picamera2
import serial
import time
import RPi.GPIO as GPIO
from gpiozero import LED
from enum import Enum, auto

# --- GPIO pins ---
START_BUTTON_PIN = 26
STATUS_LED_PIN = 16

# --- camera capture size vs the cropped frame we actually process ---
CAMERA_PIC_WIDTH = 640
CAMERA_PIC_HEIGHT = 360
PIC_WIDTH = 640
PIC_HEIGHT = 280
CAMERA_WARMUP_FRAMES = 10  # throwaway captures so camera settle before we trust anything

# threshold used to split floor (white) from wall/shadow (black)
GRAY_THRESHOLD = 75

# LAB colour range for the blue line
BLUE_LOWER = np.array([22, 131, 75])
BLUE_UPPER = np.array([95, 158, 112])

# --- steering geometry ---
STEER_CENTER = 97
MAX_STEER_OFFSET = 43
STEER_MIN = STEER_CENTER - MAX_STEER_OFFSET
STEER_MAX = STEER_CENTER + MAX_STEER_OFFSET
STEER_SIGN = -1  

# --- run config ---
MOTOR_FORWARD = 1
MOTOR_REVERSE = 2
DRIVE_SPEED = 255
LAPS_TARGET = 3
TOTAL_QUARTER_TURNS = LAPS_TARGET * 4  # each corner = one quarter turn
FINISH_DRIVE_SECONDS = 1  # keep wall-following this long after the final turn, then stop

# --- corner marker detection for lap counting ---
TURN_MARKER_ENTER_AREA = 150
TURN_MARKER_EXIT_AREA = 60
TURN_ENTER_CONFIRM_FRAMES = 3
TURN_EXIT_CONFIRM_FRAMES = 2
TURN_MIN_TIME = 0.25
TURN_MAX_TIME = 2.0
TURN_COOLDOWN_TIME = 0.2

# --- wall follow config ---
ROI_LEFT_WALL = [0, 84, 128, 210]
ROI_RIGHT_WALL = [512, 84, 640, 210]
WALL_CENTER_OFFSET = 0
WALL_OPENING_AREA = 700
OPENING_BOOST_MULT = 2
OPENING_BOOST_ADD = 25000
AREA_WALL_KP = 0.003
AREA_WALL_KD = 0.0001
HARD_TURN_SIGN = -1  


class TurnState(Enum):
    IDLE = auto()
    TURNING = auto()


class RunState(Enum):
    WARM_UP_CAMERA = auto()
    WAIT_FOR_BUTTON = auto()
    DRIVE_LAPS = auto()
    FINISHED = auto()


ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
time.sleep(2)  # give the board time to boot before we send anything

GPIO.setmode(GPIO.BCM)
GPIO.setup(START_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

status_led = LED(STATUS_LED_PIN)


def wait_for_start_button():
    # lights the LED and blocks until the button (wired to GND) is pressed,
    # with a small debounce so a noisy edge can't fake a press
    status_led.on()
    print("[button] waiting for start button on GPIO26...")
    while GPIO.input(START_BUTTON_PIN) == GPIO.HIGH:
        time.sleep(0.02)

    time.sleep(0.05)
    if GPIO.input(START_BUTTON_PIN) == GPIO.HIGH:
        return wait_for_start_button()

    status_led.off()
    print("[button] start button pressed -- starting run")

    # wait for release so a held button doesn't do anything unexpected later
    while GPIO.input(START_BUTTON_PIN) == GPIO.LOW:
        time.sleep(0.02)


def to_servo_angle(logical_angle):
    # our angle convention increases clockwise, the servo expects the opposite
    if STEER_SIGN == -1:
        return int(round(2 * STEER_CENTER - logical_angle))
    return int(round(logical_angle))


def set_steering_angle(angle):
    angle = max(STEER_MIN, min(STEER_MAX, angle))
    servo_angle = to_servo_angle(angle)
    ser.write(f"SERVO,{servo_angle}\n".encode())
    ser.flush()
    return angle


def drive(motor_direction, speed, ticks=None):
    motor_direction = max(0, min(2, int(motor_direction)))
    speed = max(0, min(255, int(speed)))

    if ticks is not None:
        reset_tick_counter()
        return drive_ticks(motor_direction, speed, int(ticks))

    ser.write(f"MOTOR,{motor_direction},{speed}\n".encode())
    return None


def stop():
    ser.write(b"STOP\n")


def drive_ticks(motor_direction, speed, ticks, timeout=11.0):
    motor_direction = max(0, min(2, int(motor_direction)))
    speed = max(0, min(255, int(speed)))
    ticks = int(abs(ticks))

    ser.reset_input_buffer()
    ser.write(f"MOVE,{motor_direction},{speed},{ticks}\n".encode())

    # wait for the board to report it finished the move
    deadline = time.time() + timeout
    while time.time() < deadline:
        line = ser.readline().decode(errors="ignore").strip()
        if not line:
            continue
        if line.startswith("DONE"):
            parts = line.split(",")
            moved = int(parts[1]) if len(parts) > 1 else None
            return moved
    return None


def reset_tick_counter():
    ser.reset_input_buffer()
    ser.write(b"RESET\n")
    ser.readline()


def blue_mask_of(lab_img):
    return cv2.inRange(lab_img, BLUE_LOWER, BLUE_UPPER)


def crop_frame(image, x_start, x_end, y_start, y_end):
    return image[y_start:y_end, x_start:x_end]


def get_track_boundary(binary_image, fallback_image):
    # outer contours of the floor mask
    contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # keep only the blob the robot is actually standing on, so noise elsewhere
    # in the frame doesn't get mistaken for the track
    robot_point = (PIC_WIDTH / 2, PIC_HEIGHT - 10)
    contours = [cnt for cnt in contours if cv2.pointPolygonTest(cnt, robot_point, False) >= 0]

    if not contours:
        return fallback_image, None

    contour = max(contours, key=cv2.contourArea)

    epsilon = 0.001 * cv2.arcLength(contour, True)
    mat_roi = cv2.approxPolyDP(contour, epsilon, True)

    mask = np.zeros_like(binary_image)
    cv2.fillPoly(mask, [mat_roi], 255)
    result = cv2.bitwise_and(binary_image, mask)
    return result, mat_roi


def get_wall_rois():
    # wall follow ROIs
    return ROI_LEFT_WALL, ROI_RIGHT_WALL


def largest_wall_contour(track_image, roi, min_area=50):
    x1, y1, x2, y2 = roi
    region = track_image[y1:y2, x1:x2]
    if region.size == 0:
        return None, 0
    walls_as_white = cv2.bitwise_not(region)  # flip so walls (0) become the foreground (255)
    contours, _ = cv2.findContours(walls_as_white, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None, 0
    cnt = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(cnt)
    if area <= min_area:
        return None, 0
    return cnt, area


def largest_wall_area(track_image, roi, min_area=50):
    _, area = largest_wall_contour(track_image, roi, min_area)
    return area


def draw_wall_rois(frame, rois, color=(255, 204, 0)):
    for x1, y1, x2, y2 in rois:
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    return frame


_prev_area_wall_error = 0.0


def area_wall_follow_angle(track_image, blue_area=0):
    # main driving controller: compares how much wall is visible on each
    # side and steers toward the side with less wall (more open space)
    global _prev_area_wall_error

    roi_left, roi_right = get_wall_rois()
    area_left = largest_wall_area(track_image, roi_left)
    area_right = largest_wall_area(track_image, roi_right)

    # if one side has basically nothing, treat it as a big opening so we commit to the turn
    if area_left < WALL_OPENING_AREA and area_right > 100:
        area_right = area_right * OPENING_BOOST_MULT + OPENING_BOOST_ADD
    elif area_right < WALL_OPENING_AREA and area_left > 100:
        area_left = area_left * OPENING_BOOST_MULT + OPENING_BOOST_ADD

    wall_error = (area_left - area_right) - WALL_CENTER_OFFSET
    derivative = wall_error - _prev_area_wall_error
    control = (wall_error * AREA_WALL_KP) + (derivative * AREA_WALL_KD)
    _prev_area_wall_error = wall_error

    angle = STEER_CENTER - control

    # neither wall visible at all, deep in a corner -- hard turn using the blue
    # marker as a tiebreak
    if area_left == 0 and area_right == 0:
        if blue_area > TURN_MARKER_ENTER_AREA:
            angle = STEER_CENTER + HARD_TURN_SIGN * 35
        else:
            angle = STEER_CENTER + HARD_TURN_SIGN * 20

    return max(STEER_MIN, min(STEER_MAX, angle))


class LapCounter:
    # counts corners (quarter turns) by watching the blue line
    def __init__(self):
        self.state = TurnState.IDLE
        self.quarter_turns = 0
        self._enter_confirm_count = 0
        self._exit_confirm_count = 0
        self._turn_start_time = 0.0
        self._cooldown_until = 0.0

    def update(self, blue_mask, track_mask):
        now = time.time()
        marker_mask = cv2.bitwise_and(blue_mask, blue_mask, mask=track_mask)
        marker_area = cv2.countNonZero(marker_mask)

        if self.state == TurnState.IDLE:
            # cooldown stops us re-triggering on the same marker right after counting it
            if now >= self._cooldown_until:
                self._enter_confirm_count = (
                    self._enter_confirm_count + 1 if marker_area > TURN_MARKER_ENTER_AREA else 0
                )
                if self._enter_confirm_count >= TURN_ENTER_CONFIRM_FRAMES:
                    self.state = TurnState.TURNING
                    self._turn_start_time = now
                    self._exit_confirm_count = 0
                    self._enter_confirm_count = 0
        else:
            turn_elapsed = now - self._turn_start_time
            self._exit_confirm_count = (
                self._exit_confirm_count + 1 if marker_area < TURN_MARKER_EXIT_AREA else 0
            )
            should_exit = (
                (turn_elapsed >= TURN_MIN_TIME and self._exit_confirm_count >= TURN_EXIT_CONFIRM_FRAMES)
                or (turn_elapsed >= TURN_MAX_TIME)  # safety cutoff in case we never see it shrink
            )
            if should_exit:
                self.quarter_turns += 1
                self.state = TurnState.IDLE
                self._cooldown_until = now + TURN_COOLDOWN_TIME
                self._enter_confirm_count = 0
                self._exit_confirm_count = 0


class RobotController:
    # state machine script
    def __init__(self):
        self.state = RunState.WARM_UP_CAMERA
        self.picam2 = None

        self.lap_counter = LapCounter()
        self.lap_count = 0
        self.quarter_lap_count = 0

        self.motor_started = False
        self.race_finished = False
        self.finishing = False
        self.finish_start_time = None
        self.run_start_time = None

        self.prevang = None
        self.first_frame_done = False

        self._handlers = {
            RunState.WARM_UP_CAMERA: self._state_warm_up_camera,
            RunState.WAIT_FOR_BUTTON: self._state_wait_for_button,
            RunState.DRIVE_LAPS: self._state_drive_laps,
        }

    def run(self):
        while self.state != RunState.FINISHED:
            handler = self._handlers[self.state]
            handler()
        self._cleanup()

    def _cleanup(self):
        if not self.race_finished:
            stop()
        if self.picam2 is not None:
            self.picam2.stop()
        ser.close()
        status_led.off()
        GPIO.cleanup()

    def _state_warm_up_camera(self):
        self.picam2 = Picamera2()
        sensor_mode = self.picam2.sensor_modes[1]
        sensor_width, sensor_height = sensor_mode["size"]

        config = self.picam2.create_video_configuration(
            raw={"size": (sensor_width, sensor_height)},
            main={"format": "RGB888", "size": (CAMERA_PIC_WIDTH, CAMERA_PIC_HEIGHT)},
            controls={"FrameRate": 30},
        )
        self.picam2.configure(config)
        self.picam2.start()

        # let auto exposure/white balance settle before we start reading frames for real
        for _ in range(CAMERA_WARMUP_FRAMES):
            self.picam2.capture_array()

        self.state = RunState.WAIT_FOR_BUTTON

    def _state_wait_for_button(self):
        # don't move (or even start reading frames for real) until the button is pressed
        wait_for_start_button()
        self.run_start_time = time.time()
        self.state = RunState.DRIVE_LAPS

    def _state_drive_laps(self):
        # covers the whole race in one loop
        while True:
            raw_frame = self.picam2.capture_array()

            frame = crop_frame(
                raw_frame,
                0, CAMERA_PIC_WIDTH,
                CAMERA_PIC_HEIGHT - PIC_HEIGHT, CAMERA_PIC_HEIGHT
            )

            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blurred = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)
            _, binary = cv2.threshold(blurred, GRAY_THRESHOLD, 255, cv2.THRESH_BINARY)

            # force the blue line to read as FLOOR (white) before cleanup
            blue_mask = blue_mask_of(lab)
            line_mask = blue_mask
            binary[line_mask > 0] = 255

            clean = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))

            track_image, mat_roi = get_track_boundary(clean, clean)

            track_mask = np.zeros_like(clean)
            if mat_roi is not None:
                cv2.fillPoly(track_mask, [mat_roi], 255)

            # camera pipeline confirmed working on the first processed frame --
            # only now is it safe to let the motor spin
            if not self.first_frame_done:
                self.first_frame_done = True
                if not self.motor_started:
                    drive(MOTOR_FORWARD, DRIVE_SPEED)
                    self.motor_started = True

            # only count marker/wall pixels inside the drivable area
            blue_area = cv2.countNonZero(cv2.bitwise_and(blue_mask, blue_mask, mask=track_mask))

            prev_quarter_turns = self.lap_counter.quarter_turns
            self.lap_counter.update(blue_mask, track_mask)
            self.quarter_lap_count = self.lap_counter.quarter_turns

            if self.quarter_lap_count > prev_quarter_turns:
                if self.quarter_lap_count % 4 == 0:
                    self.lap_count = self.quarter_lap_count // 4
                    print(f"[laps] lap {self.lap_count} complete")

                if self.quarter_lap_count >= TOTAL_QUARTER_TURNS and not self.finishing:
                    self.finishing = True
                    self.finish_start_time = time.time()
                    print("[laps] final turn complete -- wall-following for a bit before stopping")

            roi_left, roi_right = get_wall_rois()
            draw_wall_rois(frame, [roi_left, roi_right])

            angle = area_wall_follow_angle(track_image, blue_area=blue_area)

            angle = round(angle)
            if self.prevang is None or self.prevang != angle:
                set_steering_angle(angle)
                self.prevang = angle

            print(
                f"blue_area:{blue_area}, "
                f"angle:{angle}, "
                f"quarterlaps:{self.quarter_lap_count}, "
                f"laps:{self.lap_count}, "
                f"finishing:{self.finishing}"
            )

            # keep wall-following normally for FINISH_DRIVE_SECONDS after the
            # final turn, then just stop -- no separate fixed-distance move
            if self.finishing and (time.time() - self.finish_start_time >= FINISH_DRIVE_SECONDS):
                print(f"[race] {LAPS_TARGET} laps complete -- stopping")
                stop()
                set_steering_angle(STEER_CENTER)
                self.race_finished = True

                total_run_time = time.time() - self.run_start_time
                print(f"[timer] total run time: {total_run_time:.2f} seconds")
                break

        self.state = RunState.FINISHED


if __name__ == "__main__":
    RobotController().run()
