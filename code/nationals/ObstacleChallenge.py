import time
import math
from enum import Enum, auto

import cv2
import numpy as np
import serial
from picamera2 import Picamera2
import RPi.GPIO as GPIO
from gpiozero import LED

# --- serial link to the motor/servo board ---
SERIAL_PORT = "/dev/ttyUSB0"
BAUD_RATE = 115200
SERIAL_TIMEOUT = 1
SERIAL_WARMUP_TIME = 2.0

# --- GPIO pins ---
START_BUTTON_PIN = 26
STATUS_LED_PIN = 16

# --- camera capture size vs the cropped frame we actually process ---
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 360
FRAME_WIDTH = 640
FRAME_HEIGHT = 280
CAMERA_WARMUP_TIME = 1.5

# threshold used to split floor (white) from wall/shadow (black)
GRAY_THRESHOLD = 130

# LAB colour ranges for the corner markers and pillars, tuned by hand on the mat
BLUE_LOWER = np.array([22, 131, 75])
BLUE_UPPER = np.array([95, 158, 112])

ORANGE_LOWER = np.array([78, 146, 159])
ORANGE_UPPER = np.array([139, 167, 194])

GREEN_LOWER = np.array([61, 79, 129])
GREEN_UPPER = np.array([151, 122, 168])

RED_LOWER = np.array([53, 164, 147])
RED_UPPER = np.array([119, 187, 169])

PINK_LOWER = np.array([39, 156, 115])
PINK_UPPER = np.array([94, 185, 141])

CLEAN_KERNEL = np.ones((5, 5), np.uint8)

# --- steering geometry ---
STEER_CENTER = 97
MAX_STEER_OFFSET = 43
PARK_MAX_STEER_OFFSET = 60  # parking manoeuvres need a bit more lock than normal driving

STEER_MIN = STEER_CENTER - MAX_STEER_OFFSET
STEER_MAX = STEER_CENTER + MAX_STEER_OFFSET
PARK_STEER_MIN = STEER_CENTER - PARK_MAX_STEER_OFFSET
PARK_STEER_MAX = STEER_CENTER + PARK_MAX_STEER_OFFSET

STEER_SIGN = -1  # servo turns the opposite way to our angle convention

# --- run config ---
LAPS_TARGET = 3
TOTAL_QUARTER_TURNS = LAPS_TARGET * 4  # each corner = one quarter turn

DRIVE_SPEED = 200
PARK_SPEED = 85

MOTOR_FORWARD = 1
MOTOR_REVERSE = 2

# --- corner marker detection for lap counting ---
TURN_MARKER_ENTER_AREA = 150
TURN_MARKER_EXIT_AREA = 60

TURN_ENTER_CONFIRM_FRAMES = 3
TURN_EXIT_CONFIRM_FRAMES_LEFT = 6
TURN_EXIT_CONFIRM_FRAMES_RIGHT = 6
TURN_MIN_TIME_LEFT = 1.0
TURN_MIN_TIME_RIGHT = 0.0
TURN_MAX_TIME = 2.0
TURN_COOLDOWN_TIME = 1.8

# --- side wall ROIs, mirrored depending on which way we're going ---
LEFT_WALL_ROI = [0, 80, 128, 200]
RIGHT_WALL_ROI = [504, 60, 638, 198]

WALL_CENTER_OFFSET = 0
WALL_OPENING_AREA = 700
OPENING_BOOST_MULT = 2
OPENING_BOOST_ADD = 25000

AREA_WALL_KP = 0.075
AREA_WALL_KD = 0.0003
AREA_WALL_KP_DAMPED = 0.0023  # softer gains used near the inner wall so we don't overcorrect into it
AREA_WALL_KD_DAMPED = 0.0

# --- point-based wall following used when approaching / parking ---
APPROACH_WALL_TARGET_X_LEFT = 0
APPROACH_WALL_TARGET_X_RIGHT = FRAME_WIDTH
APPROACH_WALL_TARGET_Y = FRAME_HEIGHT - 1
APPROACH_WALL_KP = 0.37
APPROACH_WALL_KD = 0.005

INNER_WALL_KP = 0.15
INNER_WALL_KD = 0.0

PARK_ENTRY_TARGET_X_LEFT = 0
PARK_ENTRY_TARGET_X_RIGHT = FRAME_WIDTH
PARK_ENTRY_TARGET_Y = FRAME_HEIGHT - 1
PARK_ENTRY_WALL_KP = 1.5
PARK_ENTRY_WALL_KD = 0.2
PARK_ENTRY_FORWARD_TIME = 3

FORCED_ALIGN_TIME = 0.5
RIGHT_FORCED_ALIGN_POINT_X = 60
LEFT_FORCED_ALIGN_POINT_X = FRAME_WIDTH - 60
FORCED_ALIGN_POINT_Y = 280

# --- pillar (obstacle) avoidance ---
RED_PILLAR_TARGET_X = 15
GREEN_PILLAR_TARGET_X = FRAME_WIDTH - RED_PILLAR_TARGET_X

PILLAR_STEER_OFFSET_DEG = 45
GREEN_PILLAR_KP = 1.45
RED_PILLAR_KP = 1.45

PILLAR_TRACK_START_Y = FRAME_HEIGHT - 60
PILLAR_TOO_CLOSE_Y = FRAME_HEIGHT - 15

MIN_PILLAR_AREA = 200

INNER_WALL_SAMPLE_POINTS = 15

PARK_APPROACH_TARGET_Y = FRAME_HEIGHT - 75
PARK_APPROACH_X_TOLERANCE = 80

PARK_WALL_STEER_OFFSET_DEG = 45
PARK_WALL_KP = 3.0

MIN_PARK_WALL_AREA = 10
PARK_WALL_SEEN_AREA = 50

PARK_WALL_TOO_FAR_Y = FRAME_HEIGHT - 200
PARK_WALL_TOO_CLOSE_Y = FRAME_HEIGHT - 10


class Direction(Enum):
    LEFT = -1
    RIGHT = 1


class TurnState(Enum):
    IDLE = auto()
    TURNING = auto()


class WallState(Enum):
    NONE = 0
    INNER = 1
    OUTER = 2


class RunState(Enum):
    WAIT_FOR_BUTTON = auto()
    WARM_UP_CAMERA = auto()
    DETECT_START_DIRECTION = auto()
    EXIT_START_PARK = auto()
    DRIVE_LAPS = auto()
    APPROACH_PARKING_SPOT = auto()
    FINISHED = auto()


serial_port = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=SERIAL_TIMEOUT)
time.sleep(SERIAL_WARMUP_TIME)  # give the board time to boot before we send anything

GPIO.setmode(GPIO.BCM)
GPIO.setup(START_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def to_servo_angle(angle):
    # our angle convention increases clockwise, the servo expects the opposite
    if STEER_SIGN == -1:
        return int(round(2 * STEER_CENTER - angle))
    return int(round(angle))


def set_steering_angle(angle, duration=0.0, resend_interval=0.03, min_angle=None, max_angle=None):
    low = STEER_MIN if min_angle is None else min_angle
    high = STEER_MAX if max_angle is None else max_angle
    angle = max(low, min(high, angle))
    servo_angle = to_servo_angle(angle)

    if duration <= 0:
        serial_port.write(f"SERVO,{servo_angle}\n".encode())
        return

    # keep resending for a bit, in case a single packet gets dropped
    end_time = time.time() + duration
    while time.time() < end_time:
        serial_port.write(f"SERVO,{servo_angle}\n".encode())
        time.sleep(resend_interval)


def drive(motor_direction, speed, ticks=None):
    motor_direction = max(0, min(2, int(motor_direction)))
    speed = max(0, min(255, int(speed)))

    if ticks is not None:
        # tick-based moves reset the encoder count first so distance is relative to now
        reset_tick_counter()
        return drive_ticks(motor_direction, speed, int(ticks))

    serial_port.write(f"MOTOR,{motor_direction},{speed}\n".encode())
    return None


def stop():
    serial_port.write(b"STOP\n")


def drive_ticks(motor_direction, speed, ticks, timeout=11.0):
    motor_direction = max(0, min(2, int(motor_direction)))
    speed = max(0, min(255, int(speed)))
    ticks = int(abs(ticks))

    serial_port.reset_input_buffer()
    serial_port.write(f"MOVE,{motor_direction},{speed},{ticks}\n".encode())

    # wait for the board to report it finished the move
    deadline = time.time() + timeout
    while time.time() < deadline:
        line = serial_port.readline().decode(errors="ignore").strip()
        if not line:
            continue
        if line.startswith("DONE"):
            parts = line.split(",")
            moved = int(parts[1]) if len(parts) > 1 else None
            return moved
    return None


def reset_tick_counter():
    serial_port.reset_input_buffer()
    serial_port.write(b"RESET\n")
    serial_port.readline()


def get_color_mask(lab_image, color):
    thresholds = {
        "blue": (BLUE_LOWER, BLUE_UPPER),
        "orange": (ORANGE_LOWER, ORANGE_UPPER),
        "green": (GREEN_LOWER, GREEN_UPPER),
        "red": (RED_LOWER, RED_UPPER),
        "pink": (PINK_LOWER, PINK_UPPER),
    }
    lower, upper = thresholds.get(color, (None, None))
    if lower is None:
        mask = np.zeros(lab_image.shape[:2], dtype=np.uint8)
    else:
        mask = cv2.inRange(lab_image, lower, upper)

    # open then close to drop speckle noise and fill small gaps in the blob
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, CLEAN_KERNEL)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, CLEAN_KERNEL)
    return mask


def crop_frame(image, x_start, x_end, y_start, y_end):
    return image[y_start:y_end, x_start:x_end]


def capture_cropped_frame(picam2):
    # just grabs a frame and chops it down to the FRAME_HEIGHT band we actually care about
    raw_frame = picam2.capture_array()
    return crop_frame(raw_frame, 0, CAMERA_WIDTH, CAMERA_HEIGHT - FRAME_HEIGHT, CAMERA_HEIGHT)


def get_track_boundary(binary_image, fallback_image):
    # outer contours of the floor mask
    contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # keep only the blob the robot is actually standing on, so noise elsewhere
    # in the frame doesn't get mistaken for the track
    robot_point = (FRAME_WIDTH / 2, FRAME_HEIGHT - 10)
    contours = [cnt for cnt in contours if cv2.pointPolygonTest(cnt, robot_point, False) >= 0]

    if not contours:
        return fallback_image, None

    contour = max(contours, key=cv2.contourArea)

    # simplify into a polygon, works fine for curved or irregular track edges
    epsilon = 0.001 * cv2.arcLength(contour, True)
    mat_roi = cv2.approxPolyDP(contour, epsilon, True)

    mask = np.zeros_like(binary_image)
    cv2.fillPoly(mask, [mat_roi], 255)
    result = cv2.bitwise_and(binary_image, mask)
    return result, mat_roi


def process_frame(raw_frame, extra_masks=()):
    # main image pipeline: crop -> hide the coloured markers so they don't
    # get read as wall -> threshold into black/white -> isolate the blob
    # of floor the robot is actually on
    frame = crop_frame(raw_frame, 0, CAMERA_WIDTH, CAMERA_HEIGHT - FRAME_HEIGHT, CAMERA_HEIGHT)
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)

    blue_mask = get_color_mask(lab, "blue")
    orange_mask = get_color_mask(lab, "orange")
    green_mask = get_color_mask(lab, "green")
    red_mask = get_color_mask(lab, "red")

    # paint the markers white first so they don't get read as a wall
    floor_image = frame.copy()
    marker_mask = cv2.bitwise_or(cv2.bitwise_or(blue_mask, orange_mask),
                                  cv2.bitwise_or(green_mask, red_mask))
    for mask in extra_masks:
        marker_mask = cv2.bitwise_or(marker_mask, mask)
    floor_image[marker_mask > 0] = (255, 255, 255)

    grayscale_image = cv2.cvtColor(floor_image, cv2.COLOR_BGR2GRAY)
    blurred_image = cv2.bilateralFilter(grayscale_image, 9, 75, 75)  # smooths noise but keeps edges sharp
    _, binary_image = cv2.threshold(blurred_image, GRAY_THRESHOLD, 255, cv2.THRESH_BINARY)
    clean_image = cv2.morphologyEx(binary_image, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))

    track_image, mat_roi = get_track_boundary(clean_image, clean_image)

    track_mask = np.zeros_like(clean_image)
    if mat_roi is not None:
        cv2.fillPoly(track_mask, [mat_roi], 255)

    return {
        "frame": frame,
        "blue_mask": blue_mask,
        "orange_mask": orange_mask,
        "green_mask": green_mask,
        "red_mask": red_mask,
        "track_image": track_image,
        "track_mask": track_mask,
        "mat_roi": mat_roi,
    }


class LapCounter:
    # counts corners (quarter turns) by watching how big the corner marker
    # gets as we drive past it, then confirming once it shrinks back down
    def __init__(self):
        self.state = TurnState.IDLE
        self.quarter_turns = 0
        self._enter_confirm_count = 0
        self._exit_confirm_count = 0
        self._turn_start_time = 0.0
        self._cooldown_until = 0.0

    def update(self, blue_mask, orange_mask, direction, track_mask):
        now = time.time()
        marker_mask = blue_mask if direction == Direction.LEFT else orange_mask
        marker_mask = cv2.bitwise_and(marker_mask, marker_mask, mask=track_mask)
        marker_area = cv2.countNonZero(marker_mask)

        exit_confirm_frames = (TURN_EXIT_CONFIRM_FRAMES_LEFT if direction == Direction.LEFT
                                else TURN_EXIT_CONFIRM_FRAMES_RIGHT)
        turn_min_time = TURN_MIN_TIME_LEFT if direction == Direction.LEFT else TURN_MIN_TIME_RIGHT

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
                (turn_elapsed >= turn_min_time and self._exit_confirm_count >= exit_confirm_frames)
                or (turn_elapsed >= TURN_MAX_TIME)  # safety cutoff in case we never see it shrink
            )
            if should_exit:
                self.quarter_turns += 1
                self.state = TurnState.IDLE
                self._cooldown_until = now + TURN_COOLDOWN_TIME
                self._enter_confirm_count = 0
                self._exit_confirm_count = 0


_prev_point_wall_error = 0.0


def find_wall_point(track_image, track_mask, direction):
    # looks at only one half of the frame (the side we're following) and
    # finds the closest black wall pixel at the bottom of that half
    height, width = track_image.shape[:2]

    side_floor = np.zeros_like(track_image)
    if direction == Direction.LEFT:
        side_floor[:, :width // 2] = track_image[:, :width // 2]
    else:
        side_floor[:, width // 2:] = track_image[:, width // 2:]

    side_wall = cv2.bitwise_not(side_floor)
    side_wall = cv2.bitwise_and(side_wall, side_wall, mask=track_mask)
    if direction == Direction.LEFT:
        side_wall[:, width // 2:] = 0
    else:
        side_wall[:, :width // 2] = 0

    contours, _ = cv2.findContours(side_wall, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    points = np.concatenate(contours)
    xs = points[:, 0, 0]
    ys = points[:, 0, 1]

    valid = xs < width // 2 if direction == Direction.LEFT else xs >= width // 2
    xs = xs[valid]
    ys = ys[valid]
    if xs.size == 0:
        return None

    # closest point to the robot = lowest in the frame, then furthest across
    max_y = np.max(ys)
    bottom = ys == max_y
    xs_bottom = xs[bottom]
    ys_bottom = ys[bottom]

    idx = np.argmax(xs_bottom)
    return int(xs_bottom[idx]), int(ys_bottom[idx])


def estimate_point_wall_error(track_image, track_mask, direction, target_x, target_y):
    # same error calc as follow_wall_point, just used to seed _prev_point_wall_error
    # before we start a PD loop so the first derivative term isn't a random jump
    point = find_wall_point(track_image, track_mask, direction)
    if point is None:
        return 0.0
    point_x, point_y = point
    error_y = max(0.0, target_y - point_y)
    error_x = (target_x - point_x) if direction == Direction.LEFT else (point_x - target_x)
    return error_y + error_x


def follow_wall_point(track_image, track_mask, direction, target_x, target_y, kp, kd, return_error=False,
                       min_angle=None, max_angle=None):
    # simple PD steering: track how far the wall point is from where we want it
    global _prev_point_wall_error
    low = STEER_MIN if min_angle is None else min_angle
    high = STEER_MAX if max_angle is None else max_angle

    point = find_wall_point(track_image, track_mask, direction)
    if point is None:
        angle = STEER_CENTER
        if return_error:
            return angle, _prev_point_wall_error
        return angle

    point_x, point_y = point

    error_y = max(0.0, target_y - point_y)
    error_x = (target_x - point_x) if direction == Direction.LEFT else (point_x - target_x)
    error = error_y + error_x

    derivative = error - _prev_point_wall_error
    control = (kp * error) + (kd * derivative)
    _prev_point_wall_error = error

    turn_sign = 1 if direction == Direction.LEFT else -1
    angle = STEER_CENTER + turn_sign * control
    angle = max(low, min(high, angle))

    if return_error:
        return angle, error
    return angle


def follow_wall_point_forced(direction, target_x, target_y, kp, kd,
                              forced_x, forced_y=FORCED_ALIGN_POINT_Y,
                              min_angle=None, max_angle=None):
    # same PD logic as follow_wall_point but using a fixed point instead of
    # one detected from the camera, useful for a short blind alignment step
    global _prev_point_wall_error
    low = STEER_MIN if min_angle is None else min_angle
    high = STEER_MAX if max_angle is None else max_angle

    point_x, point_y = forced_x, forced_y

    error_y = max(0.0, target_y - point_y)
    error_x = (target_x - point_x) if direction == Direction.LEFT else (point_x - target_x)
    error = error_y + error_x

    derivative = error - _prev_point_wall_error
    control = (kp * error) + (kd * derivative)
    _prev_point_wall_error = error

    turn_sign = 1 if direction == Direction.LEFT else -1
    angle = STEER_CENTER + turn_sign * control
    angle = max(low, min(high, angle))

    return angle


_prev_area_wall_error = 0.0


def mirror_roi(roi, width=FRAME_WIDTH):
    # flips a left-side ROI into the equivalent right-side one (and vice versa)
    x1, y1, x2, y2 = roi
    return [width - x2, y1, width - x1, y2]


def get_wall_rois(direction):
    # LEFT_WALL_ROI/RIGHT_WALL_ROI were tuned for driving one way round,
    # so when going the other way we just mirror them instead of re-tuning
    if direction == Direction.LEFT:
        return LEFT_WALL_ROI, RIGHT_WALL_ROI
    return mirror_roi(RIGHT_WALL_ROI), mirror_roi(LEFT_WALL_ROI)


def draw_wall_rois(frame, rois, color=(255, 204, 0)):
    for x1, y1, x2, y2 in rois:
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    return frame


def largest_wall_area(track_image, roi, min_area=50):
    # how much "wall" (black) shows up inside one of the side ROIs
    x1, y1, x2, y2 = roi
    region = track_image[y1:y2, x1:x2]
    if region.size == 0:
        return 0
    wall_mask = cv2.bitwise_not(region)
    contours, _ = cv2.findContours(wall_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return 0
    area = cv2.contourArea(max(contours, key=cv2.contourArea))
    return area if area > min_area else 0


def area_wall_follow_angle(track_image, direction, blue_area=0, orange_area=0, damped=False):
    # main lap-driving controller: compares how much wall is visible on each
    # side and steers toward the side with less wall (more open space)
    global _prev_area_wall_error

    kp = AREA_WALL_KP_DAMPED if damped else AREA_WALL_KP
    kd = AREA_WALL_KD_DAMPED if damped else AREA_WALL_KD

    roi_left, roi_right = get_wall_rois(direction)
    area_left = largest_wall_area(track_image, roi_left)
    area_right = largest_wall_area(track_image, roi_right)

    # if one side has basically nothing, treat it as a big opening so we commit to the turn
    if area_left < WALL_OPENING_AREA and area_right > 100:
        area_right = area_right * OPENING_BOOST_MULT + OPENING_BOOST_ADD
    elif area_right < WALL_OPENING_AREA and area_left > 100:
        area_left = area_left * OPENING_BOOST_MULT + OPENING_BOOST_ADD

    wall_error = (area_left - area_right) - WALL_CENTER_OFFSET
    derivative = wall_error - _prev_area_wall_error
    control = (wall_error * kp) + (derivative * kd)
    _prev_area_wall_error = wall_error

    angle = STEER_CENTER - control

    # neither wall visible at all, fall back on the corner marker to guess which way to turn
    if area_left == 0 and area_right == 0:
        turn_sign = 1 if direction == Direction.LEFT else -1
        if blue_area > TURN_MARKER_ENTER_AREA or orange_area > TURN_MARKER_ENTER_AREA:
            angle = STEER_CENTER + turn_sign * 35
        else:
            angle = STEER_CENTER + turn_sign * 20

    return max(STEER_MIN, min(STEER_MAX, angle))


class PillarNavigator:
    # handles dodging the green/red obstacle pillars and the inner/outer
    # wall corner cases that show up while doing it
    def __init__(self):
        self.last_steer_angle = STEER_CENTER
        self.state = WallState.NONE
        self.inner_wall_warning = False
        self.tracking_pillar = False

    def is_hitting_inner_wall(self, direction, track_image):
        # samples a line of points toward the inner corner to check if we're about to clip it
        if direction == Direction.RIGHT:
            near_point = (FRAME_HEIGHT - 70, FRAME_WIDTH - 170)
            far_point = (FRAME_HEIGHT - 130, FRAME_WIDTH - 220)
        else:
            near_point = (FRAME_HEIGHT - 70, 170)
            far_point = (FRAME_HEIGHT - 130, 220)

        y_vals = np.linspace(near_point[0], far_point[0], INNER_WALL_SAMPLE_POINTS)
        x_vals = np.linspace(near_point[1], far_point[1], INNER_WALL_SAMPLE_POINTS)

        for y, x in zip(y_vals, x_vals):
            y, x = int(round(y)), int(round(x))
            in_bounds = 0 <= y < FRAME_HEIGHT and 0 <= x < FRAME_WIDTH
            if in_bounds and track_image[y, x] == 0:
                return True
        return False

    def is_hitting_outer_wall(self, direction, track_image):
        # single point check straight ahead-ish, cheaper than the inner wall sampling
        # since the outer wall is a much simpler "are we about to hit this" case
        x, y = FRAME_WIDTH // 2, FRAME_HEIGHT - 138
        in_bounds = 0 <= y < FRAME_HEIGHT and 0 <= x < FRAME_WIDTH
        return in_bounds and track_image[y, x] == 0

    def find_nearest_pillar(self, green_mask, red_mask):
        # picks whichever pillar (either colour) is physically closest to the robot
        robot_point = (FRAME_WIDTH // 2, FRAME_HEIGHT)

        closest_distance = float("inf")
        closest = None

        for mask, is_green in ((green_mask, True), (red_mask, False)):
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area <= MIN_PILLAR_AREA:
                    continue

                x, y, w, h = cv2.boundingRect(cnt)
                x_center = x + w // 2
                y_center = y + h // 2

                distance = math.dist((x_center, y_center), robot_point)
                if distance >= closest_distance:
                    continue

                closest_distance = distance
                closest = (x_center, y_center, is_green)

        return closest

    def get_steer_angle(self, direction, green_mask, red_mask, track_image):
        # priority order here is: are we about to clip a wall because of a
        # dodge (inner/outer), then is there a pillar to actually dodge,
        # otherwise return None so the caller falls back to normal wall following
        self.inner_wall_warning = False

        found = self.find_nearest_pillar(green_mask, red_mask)
        pillar_present = found is not None

        outer_crash = self.is_hitting_outer_wall(direction, track_image)
        # only worth checking the inner wall if there's actually a pillar pushing us toward it
        inner_crash = self.is_hitting_inner_wall(direction, track_image) if pillar_present else False

        turn_into_corner = (STEER_MAX - 3) if direction == Direction.LEFT else (STEER_MIN + 3)

        if self.state == WallState.NONE:
            if inner_crash:
                self.state = WallState.INNER
                self.inner_wall_warning = True
                return None
            elif outer_crash:
                self.state = WallState.OUTER
                return turn_into_corner
        elif self.state == WallState.INNER:
            if not pillar_present or not inner_crash:
                self.state = WallState.NONE
            else:
                self.inner_wall_warning = True
                return None
        elif self.state == WallState.OUTER:
            if not outer_crash:
                self.state = WallState.NONE
            else:
                return turn_into_corner

        if found is None:
            self.tracking_pillar = False
            return None

        x_center, y_center, is_green = found

        if y_center > PILLAR_TRACK_START_Y:
            if y_center > PILLAR_TOO_CLOSE_Y:
                return None
            self.tracking_pillar = True
            return self.last_steer_angle

        self.tracking_pillar = True

        steer_angle = get_color_based_pillar_steer_angle(x_center, y_center, is_green)
        self.last_steer_angle = steer_angle
        return steer_angle


def get_color_based_pillar_steer_angle(x_center, y_center, is_green):
    # green pillars get passed on the right, red on the left, hence the target_x split
    target_x = GREEN_PILLAR_TARGET_X if is_green else RED_PILLAR_TARGET_X

    horizontal_distance = x_center - target_x
    vertical_distance = FRAME_HEIGHT - y_center

    pillar_angle_deg = np.degrees(np.arctan2(horizontal_distance, vertical_distance))

    if is_green:
        steer_angle = STEER_CENTER - ((pillar_angle_deg + PILLAR_STEER_OFFSET_DEG) * GREEN_PILLAR_KP)
    else:
        steer_angle = STEER_CENTER - ((pillar_angle_deg - PILLAR_STEER_OFFSET_DEG) * RED_PILLAR_KP)

    return max(STEER_MIN, min(STEER_MAX, steer_angle))


def get_forced_pillar_steer_angle(x_center, y_center, direction):
    # used during parking approach when we already know which side to aim for
    if direction == Direction.LEFT:
        aim_x = RED_PILLAR_TARGET_X
        offset_sign = -1
    else:
        aim_x = GREEN_PILLAR_TARGET_X
        offset_sign = 1

    horizontal_distance = x_center - aim_x
    vertical_distance = FRAME_HEIGHT - y_center

    pillar_angle_deg = np.degrees(np.arctan2(horizontal_distance, vertical_distance))

    steer_angle = STEER_CENTER - ((pillar_angle_deg + offset_sign * PILLAR_STEER_OFFSET_DEG) * PARK_WALL_KP)
    return max(STEER_MIN, min(STEER_MAX, steer_angle))


def find_parking_wall(pink_mask):
    # the parking wall marker, picks the one furthest up the frame (closest to being fully seen)
    contours, _ = cv2.findContours(pink_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    best_y = float("inf")
    best = None

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area <= MIN_PARK_WALL_AREA:
            continue

        x, y, w, h = cv2.boundingRect(cnt)
        x_center = x + w // 2
        y_center = y + h // 2

        if y_center >= best_y:
            continue

        best_y = y_center
        best = (x_center, y_center, area)

    return best


def get_parking_wall_steer_angle(direction, pink_mask):
    # angle-of-approach steering toward the pink parking marker, same idea as
    # the pillar steering above but aimed at the wall instead of an obstacle
    found = find_parking_wall(pink_mask)
    if found is None:
        return None, None, None
    x_center, y_center, area = found

    # too far or already basically on top of it, don't trust the angle yet
    if y_center < PARK_WALL_TOO_FAR_Y or y_center > PARK_WALL_TOO_CLOSE_Y:
        return None, x_center, y_center

    aim_x = FRAME_WIDTH if direction == Direction.LEFT else RED_PILLAR_TARGET_X

    horizontal_distance = x_center - aim_x
    vertical_distance = FRAME_HEIGHT - y_center

    wall_angle_deg = np.degrees(np.arctan2(horizontal_distance, vertical_distance))

    if direction == Direction.LEFT:
        steer_angle = STEER_CENTER - ((wall_angle_deg + PARK_WALL_STEER_OFFSET_DEG) * PARK_WALL_KP)
    else:
        steer_angle = STEER_CENTER - ((wall_angle_deg - PARK_WALL_STEER_OFFSET_DEG) * PARK_WALL_KP)

    steer_angle = max(PARK_STEER_MIN, min(PARK_STEER_MAX, steer_angle))
    return steer_angle, x_center, y_center


class RobotController:
    # top-level state machine, runs the whole match start to finish
    def __init__(self):
        self.state = RunState.WAIT_FOR_BUTTON
        self.picam2 = None
        self.status_led = LED(STATUS_LED_PIN)

        self.start_direction = None
        self.lap_counter = None
        self.navigator = None

        self._handlers = {
            RunState.WAIT_FOR_BUTTON: self._state_wait_for_button,
            RunState.WARM_UP_CAMERA: self._state_warm_up_camera,
            RunState.DETECT_START_DIRECTION: self._state_detect_start_direction,
            RunState.EXIT_START_PARK: self._state_exit_start_park,
            RunState.DRIVE_LAPS: self._state_drive_laps,
            RunState.APPROACH_PARKING_SPOT: self._state_approach_parking_spot,
        }

    def run(self):
        while self.state != RunState.FINISHED:
            handler = self._handlers[self.state]
            handler()
        self._cleanup()

    def _cleanup(self):
        if self.picam2 is not None:
            self.picam2.stop()
        serial_port.close()

    def _state_wait_for_button(self):
        # LED on = idle, waiting for the start button
        self.status_led.on()
        while GPIO.input(START_BUTTON_PIN) == GPIO.HIGH:
            pass
        self.status_led.off()
        self.state = RunState.WARM_UP_CAMERA

    def _state_warm_up_camera(self):
        # sensor_modes[1] is just the mode we settled on after testing, gives
        # decent FOV/framerate tradeoff for this resolution
        self.picam2 = Picamera2()
        sensor_mode = self.picam2.sensor_modes[1]
        sensor_width, sensor_height = sensor_mode["size"]
        config = self.picam2.create_video_configuration(
            raw={"size": (sensor_width, sensor_height)},
            main={"format": "RGB888", "size": (CAMERA_WIDTH, CAMERA_HEIGHT)},
            controls={"FrameRate": 30},
        )
        self.picam2.configure(config)
        self.picam2.start()

        # let auto exposure/white balance settle before we start reading frames for real
        end_time = time.time() + CAMERA_WARMUP_TIME
        while time.time() < end_time:
            capture_cropped_frame(self.picam2)

        self.state = RunState.DETECT_START_DIRECTION

    def _state_detect_start_direction(self):
        # whichever half of the frame has more open floor tells us if the loop goes left or right
        frame = capture_cropped_frame(self.picam2)
        grayscale_image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred_image = cv2.bilateralFilter(grayscale_image, 9, 75, 75)
        _, binary_image = cv2.threshold(blurred_image, GRAY_THRESHOLD, 255, cv2.THRESH_BINARY)

        height, width = binary_image.shape[:2]
        left_white = cv2.countNonZero(binary_image[:, :width // 2])
        right_white = cv2.countNonZero(binary_image[:, width // 2:])

        self.start_direction = Direction.RIGHT if right_white > left_white else Direction.LEFT
        self.state = RunState.EXIT_START_PARK

    def _state_exit_start_park(self):
        # scripted reverse-out-of-the-box move, branches depending on which
        # pillar we spot right after backing out
        direction = self.start_direction
        away_angle = PARK_STEER_MAX if direction == Direction.LEFT else PARK_STEER_MIN
        toward_angle = PARK_STEER_MIN if direction == Direction.LEFT else PARK_STEER_MAX

        set_steering_angle(away_angle, min_angle=PARK_STEER_MIN, max_angle=PARK_STEER_MAX)
        time.sleep(1)
        drive(MOTOR_FORWARD, PARK_SPEED, 1350)

        frame = capture_cropped_frame(self.picam2)
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        green_mask = get_color_mask(lab, "green")
        red_mask = get_color_mask(lab, "red")

        # just need this to see which pillar is in front of us right now, don't
        # care about its wall-dodging state so a throwaway navigator is fine
        navigator = PillarNavigator()
        seen_color = None
        found = navigator.find_nearest_pillar(green_mask, red_mask)
        if found is not None:
            _x, _y, is_green = found
            seen_color = "green" if is_green else "red"

        if direction == Direction.LEFT:
            if seen_color == "green":
                set_steering_angle(away_angle, min_angle=PARK_STEER_MIN, max_angle=PARK_STEER_MAX)
                drive(MOTOR_FORWARD, PARK_SPEED, 1200)
                stop()
                time.sleep(0.5)
                set_steering_angle(toward_angle, min_angle=PARK_STEER_MIN, max_angle=PARK_STEER_MAX)
                time.sleep(0.5)
                drive(MOTOR_FORWARD, PARK_SPEED, 2550)
                stop()
                time.sleep(0.5)
                set_steering_angle(STEER_CENTER)
                time.sleep(0.5)
                drive(MOTOR_REVERSE, PARK_SPEED, 2600)
            else:
                stop()
                time.sleep(0.5)
                set_steering_angle(toward_angle, min_angle=PARK_STEER_MIN, max_angle=PARK_STEER_MAX)
                time.sleep(0.5)
                drive(MOTOR_FORWARD, PARK_SPEED, 1500)
                time.sleep(0.5)
                set_steering_angle(STEER_CENTER, min_angle=PARK_STEER_MIN, max_angle=PARK_STEER_MAX)
                time.sleep(0.5)
                drive(MOTOR_REVERSE, PARK_SPEED, 2200)
        else:
            if seen_color == "red":
                set_steering_angle(away_angle, min_angle=PARK_STEER_MIN, max_angle=PARK_STEER_MAX)
                drive(MOTOR_FORWARD, PARK_SPEED, 1000)
                stop()
                time.sleep(0.5)
                set_steering_angle(toward_angle, min_angle=PARK_STEER_MIN, max_angle=PARK_STEER_MAX)
                time.sleep(0.5)
                drive(MOTOR_FORWARD, PARK_SPEED, 2800)
                stop()
                time.sleep(0.5)
            else:
                stop()
                time.sleep(0.5)
                set_steering_angle(toward_angle, min_angle=PARK_STEER_MIN, max_angle=PARK_STEER_MAX)
                time.sleep(0.5)
                drive(MOTOR_FORWARD, PARK_SPEED, 1100)
                time.sleep(0.5)

        set_steering_angle(STEER_CENTER)

        self.lap_counter = LapCounter()
        self.navigator = PillarNavigator()
        drive(MOTOR_FORWARD, DRIVE_SPEED)
        self.state = RunState.DRIVE_LAPS

    def _state_drive_laps(self):
        # main loop: wall-follow around the track, dodge pillars, count corners until laps are done
        direction = self.start_direction
        navigator = self.navigator
        lap_counter = self.lap_counter
        previous_angle = None
        set_steering_angle(STEER_CENTER)

        laps_complete_time = None
        LAPS_COMPLETE_GRACE_TIME = 0.35  # let a dodge finish before we bail out of the loop

        while True:
            raw_frame = self.picam2.capture_array()
            data = process_frame(raw_frame)

            frame = data["frame"]
            blue_mask = data["blue_mask"]
            orange_mask = data["orange_mask"]
            green_mask = data["green_mask"]
            red_mask = data["red_mask"]
            track_image = data["track_image"]
            track_mask = data["track_mask"]

            roi_left, roi_right = get_wall_rois(direction)
            draw_wall_rois(frame, [roi_left, roi_right])

            blue_area = cv2.countNonZero(cv2.bitwise_and(blue_mask, blue_mask, mask=track_mask))
            orange_area = cv2.countNonZero(cv2.bitwise_and(orange_mask, orange_mask, mask=track_mask))

            lap_counter.update(blue_mask, orange_mask, direction, track_mask)
            laps_complete = lap_counter.quarter_turns >= TOTAL_QUARTER_TURNS

            if laps_complete and laps_complete_time is None:
                laps_complete_time = time.time()

            green_mask_on_track = cv2.bitwise_and(green_mask, green_mask, mask=track_mask)
            red_mask_on_track = cv2.bitwise_and(red_mask, red_mask, mask=track_mask)

            pillar_angle = navigator.get_steer_angle(
                direction, green_mask_on_track, red_mask_on_track, track_image,
            )
            wall_angle = area_wall_follow_angle(
                track_image, direction, blue_area=blue_area, orange_area=orange_area,
                damped=navigator.inner_wall_warning,
            )

            # pillar dodging takes priority over normal wall following when active
            final_angle = pillar_angle if pillar_angle is not None else wall_angle

            angle = round(max(STEER_MIN, min(STEER_MAX, final_angle)))
            if previous_angle is None or previous_angle != angle:
                set_steering_angle(angle)
                previous_angle = angle

            if laps_complete:
                # don't stop mid-dodge just because the lap counter ticked over,
                # otherwise we can end the lap while half turned into a pillar
                dodge_in_progress = (
                    navigator.tracking_pillar
                    or navigator.state != WallState.NONE
                )
                grace_expired = (time.time() - laps_complete_time) >= LAPS_COMPLETE_GRACE_TIME

                if not dodge_in_progress or grace_expired:
                    break

        self.state = RunState.APPROACH_PARKING_SPOT

    def _state_approach_parking_spot(self):
        # drive toward the parking wall, still dodging pillars if any are in the way.
        # priority each frame is: pillar in front of us (if closer than the wall) >
        # the pink parking wall marker (once it's a reliable read) > default wall following
        direction = self.start_direction

        global _prev_point_wall_error
        navigator = PillarNavigator()

        raw_frame0 = self.picam2.capture_array()
        frame0 = crop_frame(raw_frame0, 0, CAMERA_WIDTH, CAMERA_HEIGHT - FRAME_HEIGHT, CAMERA_HEIGHT)
        lab0 = cv2.cvtColor(frame0, cv2.COLOR_BGR2LAB)
        pink_mask0 = get_color_mask(lab0, "pink")
        data0 = process_frame(raw_frame0, extra_masks=(pink_mask0,))
        target_x0 = APPROACH_WALL_TARGET_X_LEFT if direction == Direction.LEFT else APPROACH_WALL_TARGET_X_RIGHT
        _prev_point_wall_error = estimate_point_wall_error(
            data0["track_image"], data0["track_mask"], direction, target_x0, APPROACH_WALL_TARGET_Y
        )

        drive(MOTOR_FORWARD, PARK_SPEED)
        previous_angle = None

        while True:
            raw_frame = self.picam2.capture_array()
            frame = crop_frame(raw_frame, 0, CAMERA_WIDTH, CAMERA_HEIGHT - FRAME_HEIGHT, CAMERA_HEIGHT)
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            pink_mask = get_color_mask(lab, "pink")

            green_mask = get_color_mask(lab, "green")
            red_mask = get_color_mask(lab, "red")

            data = process_frame(raw_frame, extra_masks=(pink_mask,))
            track_image = data["track_image"]
            track_mask = data["track_mask"]

            inner_crash = navigator.is_hitting_inner_wall(direction, track_image)
            outer_crash = navigator.is_hitting_outer_wall(direction, track_image)

            green_mask_on_track = cv2.bitwise_and(green_mask, green_mask, mask=track_mask)
            red_mask_on_track = cv2.bitwise_and(red_mask, red_mask, mask=track_mask)
            pillar_found = navigator.find_nearest_pillar(green_mask_on_track, red_mask_on_track)

            pink_angle, pink_x, pink_y = get_parking_wall_steer_angle(direction, pink_mask)

            # if a pillar is nearer than the parking wall, deal with it first
            pillar_is_closer = (
                pillar_found is not None
                and pillar_found[1] >= PILLAR_TRACK_START_Y
                and (pink_y is None or pillar_found[1] > pink_y)
            )

            if pillar_is_closer:
                p_x, p_y, p_is_green = pillar_found
                if direction == Direction.RIGHT:
                    angle = get_color_based_pillar_steer_angle(p_x, p_y, p_is_green)
                else:
                    angle = get_forced_pillar_steer_angle(p_x, p_y, direction)
            elif pink_angle is not None:
                angle = pink_angle
            else:
                target_x = APPROACH_WALL_TARGET_X_LEFT if direction == Direction.LEFT else APPROACH_WALL_TARGET_X_RIGHT
                kp, kd = (INNER_WALL_KP, INNER_WALL_KD) if inner_crash else (APPROACH_WALL_KP, APPROACH_WALL_KD)
                wall_angle = follow_wall_point(track_image, track_mask, direction, target_x,
                                                APPROACH_WALL_TARGET_Y, kp, kd)
                angle = (STEER_MAX - 3) if outer_crash and direction == Direction.LEFT else wall_angle
                if outer_crash and direction == Direction.RIGHT:
                    angle = STEER_MIN + 3

            angle = round(max(STEER_MIN, min(STEER_MAX, angle)))
            if previous_angle is None or previous_angle != angle:
                set_steering_angle(angle)
                previous_angle = angle

            if pink_x is not None and pink_y is not None:
                aim_x = FRAME_WIDTH if direction == Direction.LEFT else RED_PILLAR_TARGET_X
                close_enough = pink_y >= PARK_APPROACH_TARGET_Y
                alongside = abs(pink_x - aim_x) <= PARK_APPROACH_X_TOLERANCE

                if close_enough and alongside:
                    stop()
                    self._reverse_into_parking_spot(direction)
                    self.state = RunState.FINISHED
                    return

    def _reverse_into_parking_spot(self, direction):
        # align alongside the parking wall, drive up a bit, then back into the spot.
        # first there's a short blind alignment step using a fixed point (camera
        # isn't reliable enough yet right after the approach), then we switch to
        # actually reading the wall, then finish with a scripted reverse wiggle
        follow_side = Direction.RIGHT if direction == Direction.LEFT else Direction.LEFT
        target_x = PARK_ENTRY_TARGET_X_LEFT if follow_side == Direction.LEFT else PARK_ENTRY_TARGET_X_RIGHT

        global _prev_point_wall_error

        forced_x = LEFT_FORCED_ALIGN_POINT_X if direction == Direction.LEFT else RIGHT_FORCED_ALIGN_POINT_X

        forced_error = (
            max(0.0, PARK_ENTRY_TARGET_Y - FORCED_ALIGN_POINT_Y)
            + ((target_x - forced_x) if follow_side == Direction.LEFT
               else (forced_x - target_x))
        )
        _prev_point_wall_error = forced_error
        previous_angle = None

        # short blind alignment step before we start trusting the camera again
        drive(MOTOR_FORWARD, PARK_SPEED)
        align_end_time = time.time() + FORCED_ALIGN_TIME
        while time.time() < align_end_time:
            angle = follow_wall_point_forced(follow_side, target_x, PARK_ENTRY_TARGET_Y,
                                              PARK_ENTRY_WALL_KP, PARK_ENTRY_WALL_KD,
                                              forced_x=forced_x,
                                              min_angle=PARK_STEER_MIN, max_angle=PARK_STEER_MAX)
            angle = round(max(PARK_STEER_MIN, min(PARK_STEER_MAX, angle)))
            if previous_angle is None or previous_angle != angle:
                set_steering_angle(angle)
                previous_angle = angle

        raw_frame0 = self.picam2.capture_array()
        frame0 = crop_frame(raw_frame0, 0, CAMERA_WIDTH, CAMERA_HEIGHT - FRAME_HEIGHT, CAMERA_HEIGHT)
        lab0 = cv2.cvtColor(frame0, cv2.COLOR_BGR2LAB)
        pink_mask0 = get_color_mask(lab0, "pink")
        data0 = process_frame(raw_frame0, extra_masks=(pink_mask0,))
        _prev_point_wall_error = estimate_point_wall_error(
            data0["track_image"], data0["track_mask"], follow_side, target_x, PARK_ENTRY_TARGET_Y
        )
        previous_angle = None

        end_time = time.time() + PARK_ENTRY_FORWARD_TIME
        while time.time() < end_time:
            raw_frame = self.picam2.capture_array()
            lab = cv2.cvtColor(crop_frame(raw_frame, 0, CAMERA_WIDTH, CAMERA_HEIGHT - FRAME_HEIGHT, CAMERA_HEIGHT),
                                cv2.COLOR_BGR2LAB)
            pink_mask = get_color_mask(lab, "pink")

            data = process_frame(raw_frame, extra_masks=(pink_mask,))
            track_image = data["track_image"]
            track_mask = data["track_mask"]

            angle = follow_wall_point(track_image, track_mask, follow_side, target_x,
                                       PARK_ENTRY_TARGET_Y, PARK_ENTRY_WALL_KP, PARK_ENTRY_WALL_KD,
                                       min_angle=PARK_STEER_MIN, max_angle=PARK_STEER_MAX)
            angle = round(max(PARK_STEER_MIN, min(PARK_STEER_MAX, angle)))
            if previous_angle is None or previous_angle != angle:
                set_steering_angle(angle)
                previous_angle = angle

        stop()
        time.sleep(0.3)

        set_steering_angle(STEER_CENTER)
        drive(MOTOR_REVERSE, PARK_SPEED)

        # keep reversing until the pink wall marker is clearly visible behind us
        while True:
            frame = capture_cropped_frame(self.picam2)
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            pink_mask = get_color_mask(lab, "pink")
            pink_area = cv2.countNonZero(pink_mask)

            if pink_area > PARK_WALL_SEEN_AREA:
                break

        stop()
        time.sleep(1.0)

        # from here it's a scripted wiggle to square up in the box, tuned per direction
        if direction == Direction.LEFT:
            set_steering_angle(STEER_CENTER)
            drive(MOTOR_FORWARD, PARK_SPEED, 1625)
            stop()
            time.sleep(1)

            set_steering_angle(PARK_STEER_MIN, min_angle=PARK_STEER_MIN, max_angle=PARK_STEER_MAX)
            time.sleep(0.5)
            drive(MOTOR_REVERSE, PARK_SPEED, 1000)
            stop()
            reset_tick_counter()
            time.sleep(0.5)

            set_steering_angle(STEER_CENTER, min_angle=PARK_STEER_MIN, max_angle=PARK_STEER_MAX)
            time.sleep(0.5)
            drive(MOTOR_REVERSE, PARK_SPEED, 725)
            stop()
            reset_tick_counter()
            time.sleep(0.5)

            set_steering_angle(PARK_STEER_MAX, min_angle=PARK_STEER_MIN, max_angle=PARK_STEER_MAX)
            time.sleep(0.5)
            drive(MOTOR_REVERSE, PARK_SPEED, 900)
            stop()
            reset_tick_counter()
            time.sleep(0.5)

            set_steering_angle(STEER_CENTER)

        else:
            set_steering_angle(STEER_CENTER)
            drive(MOTOR_FORWARD, PARK_SPEED, 1600)
            stop()
            time.sleep(1)

            set_steering_angle(PARK_STEER_MAX, min_angle=PARK_STEER_MIN, max_angle=PARK_STEER_MAX)
            time.sleep(0.5)
            drive(MOTOR_REVERSE, PARK_SPEED, 1000)
            stop()
            reset_tick_counter()
            time.sleep(0.5)

            set_steering_angle(STEER_CENTER, min_angle=PARK_STEER_MIN, max_angle=PARK_STEER_MAX)
            time.sleep(0.5)
            drive(MOTOR_REVERSE, PARK_SPEED, 480)
            stop()
            reset_tick_counter()
            time.sleep(0.5)

            set_steering_angle(PARK_STEER_MIN, min_angle=PARK_STEER_MIN, max_angle=PARK_STEER_MAX)
            time.sleep(0.5)
            drive(MOTOR_REVERSE, PARK_SPEED, 1150)
            stop()
            reset_tick_counter()
            time.sleep(0.5)

            set_steering_angle(STEER_CENTER)


if __name__ == "__main__":
    RobotController().run()
