import time
import math
from enum import Enum, auto

import cv2
import numpy as np
import serial
from picamera2 import Picamera2
import RPi.GPIO as GPIO
from gpiozero import LED


# ============================================================
# CONFIG: SERIAL & GPIO
# ============================================================
SERIAL_PORT_NAME = "/dev/ttyUSB0"
SERIAL_BAUD_RATE = 115200
SERIAL_TIMEOUT = 1
SERIAL_WARMUP_TIME = 2.0  # lets the motor controller board boot after opening the port

START_BUTTON_PIN = 26
STATUS_LED_PIN = 16


# ============================================================
# CONFIG: CAMERA / FRAME
# ============================================================
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 360
FRAME_WIDTH = 640
FRAME_HEIGHT = 280

CAMERA_WARMUP_TIME = 1.5

GRAY_THRESHOLD = 70  # black/white cutoff for turning the floor into a wall mask


# ============================================================
# CONFIG: LAB COLOR RANGES
# ============================================================
BLUE_LOWER = np.array([22, 131, 75])      # blue line
BLUE_UPPER = np.array([95, 158, 112])

ORANGE_LOWER = np.array([101, 128, 151])  # orange line
ORANGE_UPPER = np.array([166, 164, 188])

GREEN_LOWER = np.array([78, 66, 123])     # green obstacle
GREEN_UPPER = np.array([150, 109, 167])

RED_LOWER = np.array([53, 162, 139])      # red obstacle
RED_UPPER = np.array([116, 196, 166])

PINK_LOWER = np.array([39, 156, 115])     # parking wall
PINK_UPPER = np.array([94, 185, 141])

MASK_CLEAN_KERNEL = np.ones((5, 5), np.uint8)  # kernel used to clean noise from color masks


# ============================================================
# CONFIG: STEERING LIMITS
# ============================================================
STEER_CENTER = 97
MAX_STEER_OFFSET = 43
PARK_MAX_STEER_OFFSET = 55  # parking allows a wider steering range

STEER_MIN = STEER_CENTER - MAX_STEER_OFFSET
STEER_MAX = STEER_CENTER + MAX_STEER_OFFSET
PARK_STEER_MIN = STEER_CENTER - PARK_MAX_STEER_OFFSET
PARK_STEER_MAX = STEER_CENTER + PARK_MAX_STEER_OFFSET

STEER_SIGN = -1  # flips left/right if the servo is mounted reversed


# ============================================================
# CONFIG: DRIVE SPEEDS
# ============================================================
LAPS_TARGET = 3
TOTAL_QUARTER_TURNS = LAPS_TARGET * 4

DRIVE_SPEED = 200   # speed for all normal driving (laps and pillar avoidance)
PARK_SPEED = 100    # speed for all parking maneuvers

MOTOR_FORWARD = 1
MOTOR_REVERSE = 2

FORCE_RIGHT_AVOID_DELAY = 0.35  # seconds to wait after the final turn before forcing right-side avoidance


# ============================================================
# CONFIG: LAP / TURN COUNTING
# ============================================================
TURN_MARKER_ENTER_AREA = 150   # marker area big enough to count as entering a turn
TURN_MARKER_EXIT_AREA = 60     # marker area small enough to count as exiting a turn

TURN_ENTER_CONFIRM_FRAMES = 3          # frames the marker must be seen before a turn "starts"
TURN_EXIT_CONFIRM_FRAMES_LEFT = 18     # frames needed to confirm a left turn has "finished"
TURN_EXIT_CONFIRM_FRAMES_RIGHT = 2
TURN_MIN_TIME_LEFT = 1.0               # minimum time before a turn is allowed to finish
TURN_MIN_TIME_RIGHT = 0.0
TURN_MAX_TIME = 4.0                    # force-finish a turn if it takes too long
TURN_COOLDOWN_TIME = 1.25              # ignore new turn-starts for a bit after finishing one


# ============================================================
# CONFIG: AREA-BASED WALL FOLLOWING (main lap-driving method)
# ============================================================
LEFT_WALL_ROI = [0, 80, 128, 200]
RIGHT_WALL_ROI = [504, 60, 638, 198]

WALL_CENTER_OFFSET = 0     # subtracted from (left area - right area) so 0 means centered
WALL_OPENING_AREA = 700    # wall area below this means "no wall here" (corner/opening)
OPENING_BOOST_MULT = 2     # multiplies the other side's area near an opening
OPENING_BOOST_ADD = 25000  # then adds this, forcing a hard turn toward the opening

AREA_WALL_KP = 0.09
AREA_WALL_KD = 0.0004
AREA_WALL_KP_DAMPED = 0.01   # gentler gains used while the inner-wall warning is active
AREA_WALL_KD_DAMPED = 0.0


# ============================================================
# CONFIG: POINT-BASED WALL FOLLOWING (used only during parking, see follow_wall_point)
# ============================================================
SCAN_COLUMNS = 10

APPROACH_WALL_TARGET_X_LEFT = 0    # used while tracking the pink wall on final approach
APPROACH_WALL_TARGET_X_RIGHT = FRAME_WIDTH
APPROACH_WALL_TARGET_Y = 220
APPROACH_WALL_KP = 0.37
APPROACH_WALL_KD = 0.005

INNER_WALL_KP = 0.15  # used instead of the pair above whenever the inner-wall warning is active
INNER_WALL_KD = 0.0

PARK_ENTRY_TARGET_X_LEFT = 0    # used while wall-following forward past the spot before reversing in
PARK_ENTRY_TARGET_X_RIGHT = FRAME_WIDTH
PARK_ENTRY_TARGET_Y = 280
PARK_ENTRY_WALL_KP = 0.7
PARK_ENTRY_WALL_KD = 0.07
PARK_ENTRY_FORWARD_TIME = 3


# ============================================================
# CONFIG: OBSTACLE AVOIDANCE
# ============================================================
RED_PILLAR_TARGET_X = 15                                    # aim point when passing a red pillar (pass on the right)
GREEN_PILLAR_TARGET_X = FRAME_WIDTH - RED_PILLAR_TARGET_X   # aim point when passing a green pillar (pass on the left)

PILLAR_STEER_OFFSET_DEG = 45
GREEN_PILLAR_KP = 1.45
RED_PILLAR_KP = 1.45

PILLAR_TRACK_START_Y = FRAME_HEIGHT - 45   # pillar below this line -> start steering around it
PILLAR_TOO_CLOSE_Y = FRAME_HEIGHT - 20     # pillar below this line -> already passed, ignore it

MIN_PILLAR_AREA = 250  # ignore contours smaller than this (noise)

AFTER_PILLAR_CLIP_FRAMES = 15       # frames after passing a pillar where steering is clamped
AFTER_PILLAR_MAX_STEER_OFFSET = 50

INNER_WALL_SAMPLE_POINTS = 15

CRASH_MARKER_COLOR = (255, 0, 0)  # overlay color for wall-crash detection points


# ============================================================
# CONFIG: PARKING
# ============================================================
PARK_APPROACH_TARGET_Y = FRAME_HEIGHT - 75
PARK_APPROACH_X_TOLERANCE = 80

PARK_WALL_STEER_OFFSET_DEG = 45
PARK_WALL_KP = 2.2

MIN_PARK_WALL_AREA = 10   # ignore pink contours smaller than this (noise)
PARK_WALL_SEEN_AREA = 50  # pink area big enough to say "the wall is visible"

PARK_STRAIGHTEN_STEER_OFFSET = 20
PARK_STRAIGHTEN_TIME = 0.5

PARK_WALL_SEEN_AREA_UTURN = 500  # higher threshold during the U-turn to avoid a false trigger
U_TURN_MAX_TIME = 8.0            # safety timeout so the U-turn can't spin forever


# ============================================================
# ENUMS
# ============================================================
class Direction(Enum):
    LEFT = -1
    RIGHT = 1


class TurnState(Enum):
    """State of LapCounter's turn-marker watcher."""
    IDLE = auto()
    TURNING = auto()


class WallState(Enum):
    """State of PillarNavigator's wall-proximity watcher."""
    NONE = 0
    INNER = 1
    OUTER = 2


class RunState(Enum):
    """Top-level run state - see module docstring for the diagram."""
    WAIT_FOR_BUTTON = auto()
    WARM_UP_CAMERA = auto()
    DETECT_START_DIRECTION = auto()
    EXIT_START_PARK = auto()
    DRIVE_LAPS = auto()
    UTURN_TO_PARKING_WALL = auto()
    APPROACH_PARKING_SPOT = auto()
    FINISHED = auto()


# ============================================================
# HARDWARE LAYER (serial link to the motor/servo controller board)
# ============================================================
serial_port = serial.Serial(SERIAL_PORT_NAME, SERIAL_BAUD_RATE, timeout=SERIAL_TIMEOUT)
time.sleep(SERIAL_WARMUP_TIME)  # give the board a moment to boot before talking to it

GPIO.setmode(GPIO.BCM)
GPIO.setup(START_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def to_servo_angle(logical_angle):
    """Flip the logical angle if the servo is mounted reversed."""
    if STEER_SIGN == -1:
        return int(round(2 * STEER_CENTER - logical_angle))
    return int(round(logical_angle))


def set_steering_angle(angle, duration=0.0, resend_interval=0.03, min_angle=None, max_angle=None):
    """Send one steering angle, or keep re-sending it for `duration` seconds."""
    low = STEER_MIN if min_angle is None else min_angle
    high = STEER_MAX if max_angle is None else max_angle
    angle = max(low, min(high, angle))  # clamp to the allowed range
    servo_angle = to_servo_angle(angle)

    if duration <= 0:
        serial_port.write(f"SERVO,{servo_angle}\n".encode())
        return

    end_time = time.time() + duration
    while time.time() < end_time:
        serial_port.write(f"SERVO,{servo_angle}\n".encode())  # re-send since nothing else refreshes this angle
        time.sleep(resend_interval)


def drive(motor_direction, speed, ticks=None):
    """Drive continuously, or drive a fixed number of encoder ticks and block until done."""
    motor_direction = max(0, min(2, int(motor_direction)))
    speed = max(0, min(255, int(speed)))

    if ticks is not None:
        reset_tick_counter()
        return drive_ticks(motor_direction, speed, int(ticks))

    serial_port.write(f"MOTOR,{motor_direction},{speed}\n".encode())
    return None


def stop():
    serial_port.write("STOP\n".encode())


def drive_ticks(motor_direction, speed, ticks, timeout=11.0):
    """Blocking drive for a fixed number of encoder ticks; waits for a DONE reply."""
    motor_direction = max(0, min(2, int(motor_direction)))
    speed = max(0, min(255, int(speed)))
    ticks = int(abs(ticks))

    serial_port.reset_input_buffer()
    serial_port.write(f"MOVE,{motor_direction},{speed},{ticks}\n".encode())

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


# ============================================================
# VISION: FRAME / COLOR HELPERS
# ============================================================
def get_color_mask(lab_img, color):
    """Threshold a LAB image for one named color and clean up the mask."""
    thresholds = {
        "blue": (BLUE_LOWER, BLUE_UPPER),
        "orange": (ORANGE_LOWER, ORANGE_UPPER),
        "green": (GREEN_LOWER, GREEN_UPPER),
        "red": (RED_LOWER, RED_UPPER),
        "pink": (PINK_LOWER, PINK_UPPER),
    }
    lower, upper = thresholds.get(color, (None, None))
    if lower is None:
        mask = np.zeros(lab_img.shape[:2], dtype=np.uint8)  # unknown color name -> empty mask
    else:
        mask = cv2.inRange(lab_img, lower, upper)

    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, MASK_CLEAN_KERNEL)   # removes small noise specks
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, MASK_CLEAN_KERNEL)  # fills small holes in real blobs
    return mask


def crop_frame(img, x_start, x_end, y_start, y_end):
    return img[y_start:y_end, x_start:x_end]


def capture_cropped_frame(picam2):
    """Grab one frame and crop it to the working frame size."""
    raw_frame = picam2.capture_array()
    return crop_frame(raw_frame, 0, CAMERA_WIDTH, CAMERA_HEIGHT - FRAME_HEIGHT, CAMERA_HEIGHT)


def find_track_contours(binary_img, restrict_to_robot=0):
    """Return (biggest, second_biggest) contours in a binary image."""
    contours, _ = cv2.findContours(binary_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if restrict_to_robot:
        robot_point = (FRAME_WIDTH / 2, FRAME_HEIGHT - 10)  # point right in front of the robot
        contours = [cnt for cnt in contours if cv2.pointPolygonTest(cnt, robot_point, False) >= 0]
    if not contours:
        return None, None
    biggest = max(contours, key=cv2.contourArea)
    remaining = [cnt for cnt in contours if not np.array_equal(cnt, biggest)]
    if not remaining:
        return biggest, None
    second_biggest = max(remaining, key=cv2.contourArea)
    return biggest, second_biggest


def get_track_boundary(binary_img, target_img):
    """Find the drivable area in front of the robot and mask everything else out."""
    cnt, _ = find_track_contours(binary_img, restrict_to_robot=1)
    if cnt is None:
        return target_img, None
    epsilon = 0.001 * cv2.arcLength(cnt, True)
    mat_roi = cv2.approxPolyDP(cnt, epsilon, True)  # simplified contour describing the drivable area
    mask = np.zeros_like(binary_img)
    cv2.fillPoly(mask, [mat_roi], 255)
    result = cv2.bitwise_and(binary_img, mask)
    return result, mat_roi


def process_frame(raw_frame, extra_masks=()):
    """Crop the frame, build the color masks, and extract the drivable track area."""
    frame = crop_frame(raw_frame, 0, CAMERA_WIDTH, CAMERA_HEIGHT - FRAME_HEIGHT, CAMERA_HEIGHT)
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)

    blue_mask = get_color_mask(lab, "blue")
    orange_mask = get_color_mask(lab, "orange")
    green_mask = get_color_mask(lab, "green")
    red_mask = get_color_mask(lab, "red")

    colormask_image = frame.copy()
    marker_mask = cv2.bitwise_or(cv2.bitwise_or(blue_mask, orange_mask),
                                  cv2.bitwise_or(green_mask, red_mask))
    for mask in extra_masks:
        marker_mask = cv2.bitwise_or(marker_mask, mask)
    colormask_image[marker_mask > 0] = (255, 255, 255)  # paint markers/pillars white so they read as floor

    grayscale_image = cv2.cvtColor(colormask_image, cv2.COLOR_BGR2GRAY)
    blurred_image = cv2.bilateralFilter(grayscale_image, 9, 75, 75)
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
    }


# ============================================================
# LAP / TURN COUNTING
# ============================================================
class LapCounter:
    """Watches the blue/orange turn-marker lines and counts quarter-turns."""

    def __init__(self):
        self.state = TurnState.IDLE
        self.quarter_turns = 0
        self._enter_confirm_count = 0
        self._exit_confirm_count = 0
        self._turn_start_time = 0.0
        self._cooldown_until = 0.0

    def update(self, blue_mask, orange_mask, direction, track_mask):
        """Call once per frame; increments quarter_turns when a turn is confirmed finished."""
        now = time.time()
        marker_mask = blue_mask if direction == Direction.LEFT else orange_mask  # blue=left, orange=right
        marker_mask = cv2.bitwise_and(marker_mask, marker_mask, mask=track_mask)
        marker_area = cv2.countNonZero(marker_mask)

        exit_confirm_frames = (TURN_EXIT_CONFIRM_FRAMES_LEFT if direction == Direction.LEFT
                                else TURN_EXIT_CONFIRM_FRAMES_RIGHT)
        turn_min_time = TURN_MIN_TIME_LEFT if direction == Direction.LEFT else TURN_MIN_TIME_RIGHT

        if self.state == TurnState.IDLE:
            if now >= self._cooldown_until:
                self._enter_confirm_count = (
                    self._enter_confirm_count + 1 if marker_area > TURN_MARKER_ENTER_AREA else 0
                )
                if self._enter_confirm_count >= TURN_ENTER_CONFIRM_FRAMES:
                    self.state = TurnState.TURNING
                    self._turn_start_time = now
                    self._exit_confirm_count = 0
                    self._enter_confirm_count = 0
        else:  # TurnState.TURNING
            turn_elapsed = now - self._turn_start_time
            self._exit_confirm_count = (
                self._exit_confirm_count + 1 if marker_area < TURN_MARKER_EXIT_AREA else 0
            )
            should_exit = (
                (turn_elapsed >= turn_min_time and self._exit_confirm_count >= exit_confirm_frames)
                or (turn_elapsed >= TURN_MAX_TIME)  # safety: don't get stuck in TURNING forever
            )
            if should_exit:
                self.quarter_turns += 1
                self.state = TurnState.IDLE
                self._cooldown_until = now + TURN_COOLDOWN_TIME  # ignore re-triggers for a bit
                self._enter_confirm_count = 0
                self._exit_confirm_count = 0


# ============================================================
# WALL FOLLOWING: POINT-BASED (shared PD point-follower, see CONFIG above)
# ============================================================
_prev_point_wall_error = 0.0  # shared PD memory between calls


def scan_wall_distance_ahead(track_image, columns):
    """For each column, scan up from the bottom and return the first wall (black) row."""
    h = track_image.shape[0]
    rows_found = []
    for x in columns:
        found = 0
        for y in reversed(range(h - 20)):  # skip the very bottom rows (noisy near the robot)
            if track_image[y, x] == 0:
                found = y
                break
        rows_found.append(found)
    return rows_found


def scan_wall_distance_side(track_image, direction, rows):
    """For each row, scan in from the center toward `direction` and return the first wall column."""
    w = track_image.shape[1]
    edge_index = 0 if direction == Direction.LEFT else w - 1
    step = direction.value
    columns_found = []
    for y in rows:
        found = edge_index  # default: no wall found, assume it's off-frame
        for x in range(w // 2, edge_index, step):
            if track_image[y, x] == 0:
                found = x
                break
        columns_found.append(found)
    return columns_found


def follow_wall_point(track_image, direction, display_frame, target_x, target_y, kp, kd):
    """Estimate a wall point and PD-steer to keep it at (target_x, target_y)."""
    global _prev_point_wall_error
    h, w = track_image.shape[:2]

    columns = range(0, SCAN_COLUMNS) if direction == Direction.LEFT else range(w - SCAN_COLUMNS, w)
    rows = range(h - 3 * SCAN_COLUMNS, h - 2 * SCAN_COLUMNS)

    y_vals = scan_wall_distance_ahead(track_image, columns)
    x_vals = scan_wall_distance_side(track_image, direction, rows)

    avg_y = np.mean(y_vals)
    avg_x = np.mean(x_vals)
    if avg_y >= h - 1:
        avg_y = h  # no wall found ahead -> treat it as very far away

    cv2.circle(display_frame, (int(avg_x), int(avg_y)), 8, (0, 0, 255), -1)      # overlay: estimated wall point
    cv2.circle(display_frame, (int(target_x), int(target_y)), 8, (0, 255, 0), -1)  # overlay: target point

    error_y = target_y - avg_y
    error_x = (target_x - avg_x) if direction == Direction.LEFT else (avg_x - target_x)
    error = error_y + error_x

    derivative = error - _prev_point_wall_error
    control = (kp * error) + (kd * derivative)
    _prev_point_wall_error = error

    turn_sign = 1 if direction == Direction.LEFT else -1
    angle = STEER_CENTER + turn_sign * control
    return max(STEER_MIN, min(STEER_MAX, angle))


# ============================================================
# WALL FOLLOWING: AREA-BASED (main method used while driving laps)
# ============================================================
_prev_area_wall_error = 0.0  # shared PD memory between calls


def mirror_roi(roi, width=FRAME_WIDTH):
    """Flip an ROI box across the frame's centerline."""
    x1, y1, x2, y2 = roi
    return [width - x2, y1, width - x1, y2]


def get_wall_rois(direction):
    """Return (left_roi, right_roi) for the current driving direction."""
    if direction == Direction.LEFT:
        return LEFT_WALL_ROI, RIGHT_WALL_ROI
    return mirror_roi(RIGHT_WALL_ROI), mirror_roi(LEFT_WALL_ROI)  # RIGHT: mirror + swap (boxes aren't symmetric)


def largest_wall_area(track_image, roi, min_area=50):
    """Return the area of the largest wall blob inside `roi` (0 if none / too small)."""
    x1, y1, x2, y2 = roi
    region = track_image[y1:y2, x1:x2]
    if region.size == 0:
        return 0
    walls_as_white = cv2.bitwise_not(region)  # flip so walls (0) become the foreground (255)
    contours, _ = cv2.findContours(walls_as_white, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return 0
    area = cv2.contourArea(max(contours, key=cv2.contourArea))
    return area if area > min_area else 0


def draw_wall_rois(frame, rois, color=(255, 204, 0)):
    for x1, y1, x2, y2 in rois:
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    return frame


def area_wall_follow_angle(track_image, direction, blue_area=0, orange_area=0, damped=False):
    """PD-balance left vs right wall area to pick a steering angle."""
    global _prev_area_wall_error

    kp = AREA_WALL_KP_DAMPED if damped else AREA_WALL_KP
    kd = AREA_WALL_KD_DAMPED if damped else AREA_WALL_KD

    roi_left, roi_right = get_wall_rois(direction)
    area_left = largest_wall_area(track_image, roi_left)
    area_right = largest_wall_area(track_image, roi_right)

    # boost whichever side still has a wall when the other side opens up
    if area_left < WALL_OPENING_AREA and area_right > 100:
        area_right = area_right * OPENING_BOOST_MULT + OPENING_BOOST_ADD
    elif area_right < WALL_OPENING_AREA and area_left > 100:
        area_left = area_left * OPENING_BOOST_MULT + OPENING_BOOST_ADD

    wall_error = (area_left - area_right) - WALL_CENTER_OFFSET
    derivative = wall_error - _prev_area_wall_error
    control = (wall_error * kp) + (derivative * kd)
    _prev_area_wall_error = wall_error

    angle = STEER_CENTER - control

    if area_left == 0 and area_right == 0:
        # no walls seen on either side -> deep in a corner, hard-turn using the turn marker as a tiebreak
        turn_sign = 1 if direction == Direction.LEFT else -1
        if blue_area > TURN_MARKER_ENTER_AREA or orange_area > TURN_MARKER_ENTER_AREA:
            angle = STEER_CENTER + turn_sign * 35
        else:
            angle = STEER_CENTER + turn_sign * 20

    return max(STEER_MIN, min(STEER_MAX, angle))


# ============================================================
# PILLAR (OBSTACLE) AVOIDANCE
# ============================================================
class PillarNavigator:
    """Steers around red/green pillars; also watches for the robot getting too close to a wall."""

    def __init__(self):
        self.last_steer_angle = STEER_CENTER
        self.state = WallState.NONE
        self.inner_wall_warning = False
        self.tracking_pillar = False
        self.post_pass_frames = 0

    def is_hitting_inner_wall(self, direction, track_image, display_frame):
        """Sample a short line toward the inner wall; True if any sample point is a wall pixel."""
        if direction == Direction.RIGHT:
            near_point = (FRAME_HEIGHT - 70, FRAME_WIDTH - 160)
            far_point = (FRAME_HEIGHT - 130, FRAME_WIDTH - 210)
        else:
            near_point = (FRAME_HEIGHT - 70, 160)
            far_point = (FRAME_HEIGHT - 130, 210)

        y_vals = np.linspace(near_point[0], far_point[0], INNER_WALL_SAMPLE_POINTS)
        x_vals = np.linspace(near_point[1], far_point[1], INNER_WALL_SAMPLE_POINTS)

        crashed = False
        for y, x in zip(y_vals, x_vals):
            y, x = int(round(y)), int(round(x))
            in_bounds = 0 <= y < FRAME_HEIGHT and 0 <= x < FRAME_WIDTH
            if in_bounds and track_image[y, x] == 0:
                crashed = True
            if in_bounds:
                cv2.circle(display_frame, (x, y), 3, CRASH_MARKER_COLOR, -1)  # overlay

        cv2.line(display_frame, (int(near_point[1]), int(near_point[0])),
                 (int(far_point[1]), int(far_point[0])), CRASH_MARKER_COLOR, 1)
        return crashed

    def is_hitting_outer_wall(self, direction, track_image, display_frame):
        """Check a single point straight ahead of the robot for the outer wall."""
        check_point = (FRAME_WIDTH // 2, FRAME_HEIGHT - 138)
        x, y = check_point
        in_bounds = 0 <= y < FRAME_HEIGHT and 0 <= x < FRAME_WIDTH
        crashed = in_bounds and track_image[y, x] == 0
        if in_bounds:
            cv2.circle(display_frame, (x, y), 5, CRASH_MARKER_COLOR, -1)  # overlay
        return crashed

    def find_nearest_pillar(self, green_mask, red_mask, display_frame):
        """Return (x_center, y_center, is_green) of the pillar closest to the robot, or None."""
        robot_point = (FRAME_WIDTH // 2, FRAME_HEIGHT)

        closest_distance = float("inf")
        closest = None

        for mask, is_green in ((green_mask, True), (red_mask, False)):
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area <= MIN_PILLAR_AREA:
                    continue  # too small, probably noise

                x, y, w, h = cv2.boundingRect(cnt)
                x_center = x + w // 2
                y_center = y + h // 2

                distance = math.dist((x_center, y_center), robot_point)
                if distance >= closest_distance:
                    continue

                closest_distance = distance
                closest = (x_center, y_center, w, h, is_green)

        if closest is None:
            return None

        x_center, y_center, w, h, is_green = closest
        top_left = (x_center - w // 2, y_center - h // 2)
        bottom_right = (x_center + w // 2, y_center + h // 2)
        cv2.rectangle(display_frame, top_left, bottom_right,
                       (0, 255, 0) if is_green else (0, 0, 255), 2)  # overlay
        return x_center, y_center, is_green

    def get_steer_angle(self, direction, green_mask, red_mask, track_image, display_frame,
                         force_right_avoid=False):
        """Return a steering angle if avoiding a pillar or recovering from a wall warning, else None."""
        self.inner_wall_warning = False

        found = self.find_nearest_pillar(green_mask, red_mask, display_frame)
        pillar_present = found is not None

        outer_crash = self.is_hitting_outer_wall(direction, track_image, display_frame)
        inner_crash = self.is_hitting_inner_wall(direction, track_image, display_frame) if pillar_present else False

        turn_into_corner = (STEER_MAX - 3) if direction == Direction.LEFT else (STEER_MIN + 3)

        # wall-proximity state machine: latches into INNER/OUTER recovery and stays until the crash clears
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
            if self.tracking_pillar:
                self.post_pass_frames = AFTER_PILLAR_CLIP_FRAMES  # lost the pillar - clamp steering to avoid a jerk
            self.tracking_pillar = False
            return None

        x_center, y_center, is_green = found
        if force_right_avoid:
            is_green = False  # past the grace period, force right-side avoidance for a consistent approach

        if y_center > PILLAR_TRACK_START_Y:
            if y_center > PILLAR_TOO_CLOSE_Y:
                return None  # already passed it, ignore
            self.tracking_pillar = True
            return self.last_steer_angle  # too close to recompute cleanly, reuse the last angle

        self.tracking_pillar = True
        self.post_pass_frames = 0

        # aim a line from the pillar to its target point and measure the angle between them
        if is_green:
            cv2.line(display_frame, (x_center, y_center), (GREEN_PILLAR_TARGET_X, FRAME_HEIGHT), (0, 255, 0), 2)
            cv2.line(display_frame, (x_center, y_center), (x_center, FRAME_HEIGHT), (0, 255, 0), 2)
            rad_angle = np.arctan2(y_center - FRAME_HEIGHT, x_center - GREEN_PILLAR_TARGET_X)
        else:
            cv2.line(display_frame, (x_center, y_center), (RED_PILLAR_TARGET_X, FRAME_HEIGHT), (0, 0, 255), 2)
            cv2.line(display_frame, (x_center, y_center), (x_center, FRAME_HEIGHT), (0, 0, 255), 2)
            rad_angle = np.arctan2(y_center - FRAME_HEIGHT, x_center - RED_PILLAR_TARGET_X)

        pillar_angle_deg = 90 + np.degrees(rad_angle)

        if is_green:
            steer_angle = STEER_CENTER - ((pillar_angle_deg + PILLAR_STEER_OFFSET_DEG) * GREEN_PILLAR_KP)
        else:
            steer_angle = STEER_CENTER - ((pillar_angle_deg - PILLAR_STEER_OFFSET_DEG) * RED_PILLAR_KP)

        steer_angle = max(STEER_MIN, min(STEER_MAX, steer_angle))
        self.last_steer_angle = steer_angle
        return steer_angle


def get_forced_pillar_steer_angle(x_center, y_center, is_green, display_frame):
    """Steer around a pillar during the final parking approach, always aiming left."""
    aim_x = RED_PILLAR_TARGET_X
    color = (0, 255, 0) if is_green else (0, 0, 255)
    cv2.line(display_frame, (x_center, y_center), (aim_x, FRAME_HEIGHT), color, 2)

    rad_angle = np.arctan2(y_center - FRAME_HEIGHT, x_center - aim_x)
    pillar_angle_deg = 90 + np.degrees(rad_angle)

    offset_sign = 1 if is_green else -1
    steer_angle = STEER_CENTER - ((pillar_angle_deg + offset_sign * PILLAR_STEER_OFFSET_DEG) * PARK_WALL_KP)
    return max(STEER_MIN, min(STEER_MAX, steer_angle))


# ============================================================
# PARKING: FINDING THE PINK WALL
# ============================================================
def find_parking_wall(pink_mask, display_frame):
    """Return (x_center, y_center, area) of the pink wall blob deepest into the frame."""
    contours, _ = cv2.findContours(pink_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    best_y = float("inf")
    best = None

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area <= MIN_PARK_WALL_AREA:
            continue  # too small, probably noise

        x, y, w, h = cv2.boundingRect(cnt)
        x_center = x + w // 2
        y_center = y + h // 2

        if y_center >= best_y:
            continue  # not deeper into frame than the current best

        best_y = y_center
        best = (x_center, y_center, w, h, area)

    if best is None:
        return None

    x_center, y_center, w, h, area = best
    cv2.rectangle(display_frame, (x_center - w // 2, y_center - h // 2),
                  (x_center + w // 2, y_center + h // 2), (255, 0, 255), 2)  # overlay
    return x_center, y_center, area


def get_parking_wall_steer_angle(direction, pink_mask, display_frame):
    """Steer toward the pink parking wall marker."""
    found = find_parking_wall(pink_mask, display_frame)
    if found is None:
        return None, None, None
    x_center, y_center, area = found

    aim_x = GREEN_PILLAR_TARGET_X if direction == Direction.LEFT else RED_PILLAR_TARGET_X
    cv2.line(display_frame, (x_center, y_center), (aim_x, FRAME_HEIGHT), (255, 0, 255), 2)

    rad_angle = np.arctan2(y_center - FRAME_HEIGHT, x_center - aim_x)
    wall_angle_deg = 90 + np.degrees(rad_angle)

    if aim_x == GREEN_PILLAR_TARGET_X:
        steer_angle = STEER_CENTER - ((wall_angle_deg + PARK_WALL_STEER_OFFSET_DEG) * 1.8)
    else:
        steer_angle = STEER_CENTER - ((wall_angle_deg - PARK_WALL_STEER_OFFSET_DEG) * 1.8)

    steer_angle = max(PARK_STEER_MIN, min(PARK_STEER_MAX, steer_angle))
    return steer_angle, x_center, y_center


# ============================================================
# ROBOT CONTROLLER: THE STATE MACHINE
# ============================================================
class RobotController:
    """Owns the camera and per-run state; drives the RunState machine."""

    def __init__(self):
        self.state = RunState.WAIT_FOR_BUTTON
        self.picam2 = None
        self.status_led = LED(STATUS_LED_PIN)

        self.start_direction = None
        self.lap_counter = None
        self.navigator = None

        self._handlers = {  # maps each RunState to the method that handles it
            RunState.WAIT_FOR_BUTTON: self._state_wait_for_button,
            RunState.WARM_UP_CAMERA: self._state_warm_up_camera,
            RunState.DETECT_START_DIRECTION: self._state_detect_start_direction,
            RunState.EXIT_START_PARK: self._state_exit_start_park,
            RunState.DRIVE_LAPS: self._state_drive_laps,
            RunState.UTURN_TO_PARKING_WALL: self._state_uturn_to_parking_wall,
            RunState.APPROACH_PARKING_SPOT: self._state_approach_parking_spot,
        }

    def run(self):
        """Run the state machine until FINISHED, then clean up."""
        while self.state != RunState.FINISHED:
            handler = self._handlers[self.state]
            handler()  # each handler updates self.state before returning
        self._cleanup()

    def _cleanup(self):
        if self.picam2 is not None:
            self.picam2.stop()
        serial_port.close()

    # --- states ------------------------------------------------------

    def _state_wait_for_button(self):
        """Light the LED and block until the start button is pressed (active-low)."""
        self.status_led.on()
        while GPIO.input(START_BUTTON_PIN) == GPIO.HIGH:
            pass  # button not pressed yet
        self.status_led.off()
        self.state = RunState.WARM_UP_CAMERA

    def _state_warm_up_camera(self):
        """Start the camera and let a few frames pass so auto-exposure can settle."""
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

        end_time = time.time() + CAMERA_WARMUP_TIME
        while time.time() < end_time:
            capture_cropped_frame(self.picam2)  # discard frames while exposure settles

        self.state = RunState.DETECT_START_DIRECTION

    def _state_detect_start_direction(self):
        """Compare open floor on the left vs. right half of the frame to pick a track direction."""
        frame = capture_cropped_frame(self.picam2)
        grayscale_image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred_image = cv2.bilateralFilter(grayscale_image, 9, 75, 75)
        _, binary_image = cv2.threshold(blurred_image, GRAY_THRESHOLD, 255, cv2.THRESH_BINARY)

        h, w = binary_image.shape[:2]
        left_white = cv2.countNonZero(binary_image[:, :w // 2])
        right_white = cv2.countNonZero(binary_image[:, w // 2:])

        # more open floor on the right -> track goes right, and vice versa
        self.start_direction = Direction.RIGHT if right_white > left_white else Direction.LEFT
        self.state = RunState.EXIT_START_PARK

    def _state_exit_start_park(self):
        """Drive out of the starting spot (checking for a pillar first), then start the lap loop."""
        direction = self.start_direction
        away_angle = PARK_STEER_MAX if direction == Direction.LEFT else PARK_STEER_MIN
        toward_angle = PARK_STEER_MIN if direction == Direction.LEFT else PARK_STEER_MAX

        # first move: turn away from the track and nose out of the box
        set_steering_angle(away_angle, min_angle=PARK_STEER_MIN, max_angle=PARK_STEER_MAX)
        time.sleep(1)
        drive(MOTOR_FORWARD, PARK_SPEED, 1200)

        # look for a pillar right in front before committing to the rest of the exit
        frame = capture_cropped_frame(self.picam2)
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        green_mask = get_color_mask(lab, "green")
        red_mask = get_color_mask(lab, "red")

        navigator = PillarNavigator()
        seen_color = None
        found = navigator.find_nearest_pillar(green_mask, red_mask, frame.copy())
        if found is not None:
            _x, _y, is_green = found
            seen_color = "green" if is_green else "red"

        if direction == Direction.LEFT:
            if seen_color == "green":
                # green pillar in the way - take the long way around it
                set_steering_angle(away_angle, min_angle=PARK_STEER_MIN, max_angle=PARK_STEER_MAX)
                drive(MOTOR_FORWARD, PARK_SPEED, 1000)
                stop()
                time.sleep(1)
                set_steering_angle(toward_angle, min_angle=PARK_STEER_MIN, max_angle=PARK_STEER_MAX)
                time.sleep(1)
                drive(MOTOR_FORWARD, PARK_SPEED, 2600)
                stop()
                time.sleep(1)
                set_steering_angle(STEER_CENTER - 2)
                time.sleep(1)
                drive(MOTOR_REVERSE, PARK_SPEED, 2600)
            else:
                # clear path - short exit
                stop()
                time.sleep(1)
                set_steering_angle(toward_angle, min_angle=PARK_STEER_MIN, max_angle=PARK_STEER_MAX)
                time.sleep(1)
                drive(MOTOR_FORWARD, PARK_SPEED, 1500)
                time.sleep(1)
                set_steering_angle(STEER_CENTER, min_angle=PARK_STEER_MIN, max_angle=PARK_STEER_MAX)
                time.sleep(1)
                drive(MOTOR_REVERSE, PARK_SPEED, 2300)
        else:  # Direction.RIGHT
            if seen_color == "red":
                # red pillar in the way - take the long way around it
                set_steering_angle(away_angle, min_angle=PARK_STEER_MIN, max_angle=PARK_STEER_MAX)
                drive(MOTOR_FORWARD, PARK_SPEED, 1150)
                stop()
                time.sleep(1)
                set_steering_angle(toward_angle, min_angle=PARK_STEER_MIN, max_angle=PARK_STEER_MAX)
                time.sleep(1)
                drive(MOTOR_FORWARD, PARK_SPEED, 2750)
                stop()
                time.sleep(1)
            else:
                # clear path - short exit
                stop()
                time.sleep(1)
                set_steering_angle(toward_angle, min_angle=PARK_STEER_MIN, max_angle=PARK_STEER_MAX)
                time.sleep(1)
                drive(MOTOR_FORWARD, PARK_SPEED, 900)
                time.sleep(1)

        set_steering_angle(STEER_CENTER)

        self.lap_counter = LapCounter()
        self.navigator = PillarNavigator()
        drive(MOTOR_FORWARD, DRIVE_SPEED)
        self.state = RunState.DRIVE_LAPS

    def _state_drive_laps(self):
        """Wall-follow, count quarter-turns, and avoid pillars until all laps are done."""
        direction = self.start_direction
        navigator = self.navigator
        lap_counter = self.lap_counter
        previous_angle = None
        set_steering_angle(STEER_CENTER)

        # RIGHT-direction runs need one extra quarter-turn - the U-turn state counts as the last one
        turns_needed = TOTAL_QUARTER_TURNS + 1 if direction == Direction.RIGHT else TOTAL_QUARTER_TURNS
        final_turn_time = None  # grace-period timer, RIGHT-direction only

        while True:
            raw_frame = self.picam2.capture_array()
            data = process_frame(raw_frame)

            frame = data["frame"].copy()
            blue_mask = data["blue_mask"]
            orange_mask = data["orange_mask"]
            green_mask = data["green_mask"]
            red_mask = data["red_mask"]
            track_image = data["track_image"]
            track_mask = data["track_mask"]

            # only count marker/wall pixels inside the drivable area
            blue_area = cv2.countNonZero(cv2.bitwise_and(blue_mask, blue_mask, mask=track_mask))
            orange_area = cv2.countNonZero(cv2.bitwise_and(orange_mask, orange_mask, mask=track_mask))

            # overlay: ROI boxes + live wall areas
            roi_left, roi_right = get_wall_rois(direction)
            draw_wall_rois(frame, [roi_left, roi_right])
            debug_left_area = largest_wall_area(track_image, roi_left)
            debug_right_area = largest_wall_area(track_image, roi_right)
            cv2.putText(frame, f"L={debug_left_area} R={debug_right_area}", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            lap_counter.update(blue_mask, orange_mask, direction, track_mask)
            laps_complete = lap_counter.quarter_turns >= turns_needed

            if laps_complete:
                break  # direction-specific handoff happens below

            # start the grace-period timer the moment the final quarter-turn lands
            if (direction == Direction.RIGHT and final_turn_time is None
                    and lap_counter.quarter_turns >= TOTAL_QUARTER_TURNS):
                final_turn_time = time.time()

            force_right_avoid = (
                final_turn_time is not None
                and (time.time() - final_turn_time) >= FORCE_RIGHT_AVOID_DELAY
            )

            green_mask_on_track = cv2.bitwise_and(green_mask, green_mask, mask=track_mask)
            red_mask_on_track = cv2.bitwise_and(red_mask, red_mask, mask=track_mask)

            # pillar avoidance wins if it has an opinion, otherwise fall back to wall following
            pillar_angle = navigator.get_steer_angle(
                direction, green_mask_on_track, red_mask_on_track, track_image, frame,
                force_right_avoid=force_right_avoid,
            )
            wall_angle = area_wall_follow_angle(
                track_image, direction, blue_area=blue_area, orange_area=orange_area,
                damped=navigator.inner_wall_warning,
            )

            final_angle = pillar_angle if pillar_angle is not None else wall_angle

            if navigator.post_pass_frames > 0:
                # just passed a pillar - clamp steering for a few frames
                final_angle = max(STEER_CENTER - AFTER_PILLAR_MAX_STEER_OFFSET,
                                   min(final_angle, STEER_CENTER + AFTER_PILLAR_MAX_STEER_OFFSET))
                navigator.post_pass_frames -= 1

            angle = round(max(STEER_MIN, min(STEER_MAX, final_angle)))
            if previous_angle is None or previous_angle != angle:
                set_steering_angle(angle)  # only send a command when the angle actually changes
                previous_angle = angle

        if direction == Direction.RIGHT:
            stop()
            self.state = RunState.UTURN_TO_PARKING_WALL
        else:
            self.state = RunState.APPROACH_PARKING_SPOT

    def _state_uturn_to_parking_wall(self):
        """U-turn left until the pink parking wall marker comes into view (RIGHT-direction only)."""
        set_steering_angle(PARK_STEER_MAX, min_angle=PARK_STEER_MIN, max_angle=PARK_STEER_MAX)
        drive(MOTOR_FORWARD, PARK_SPEED)

        start_time = time.time()
        while True:
            frame = capture_cropped_frame(self.picam2)
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            pink_mask = get_color_mask(lab, "pink")
            pink_area = cv2.countNonZero(pink_mask)

            if pink_area > PARK_WALL_SEEN_AREA_UTURN:
                break
            if time.time() - start_time > U_TURN_MAX_TIME:
                break  # safety timeout, proceed anyway

        stop()
        set_steering_angle(STEER_CENTER)
        time.sleep(0.3)
        self.state = RunState.APPROACH_PARKING_SPOT

    def _state_approach_parking_spot(self):
        """Track the pink wall and any last pillar toward the spot, then reverse in (direction is always LEFT here)."""
        direction = Direction.LEFT

        global _prev_point_wall_error
        _prev_point_wall_error = 0.0  # reset PD memory before this new phase
        navigator = PillarNavigator()

        drive(MOTOR_FORWARD, PARK_SPEED)
        previous_angle = None

        while True:
            raw_frame = self.picam2.capture_array()
            frame = crop_frame(raw_frame, 0, CAMERA_WIDTH, CAMERA_HEIGHT - FRAME_HEIGHT, CAMERA_HEIGHT)
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            pink_mask = get_color_mask(lab, "pink")

            green_mask = get_color_mask(lab, "green")
            red_mask = get_color_mask(lab, "red")

            data = process_frame(raw_frame, extra_masks=(pink_mask,))  # treat pink wall as floor, not wall
            track_image = data["track_image"]
            track_mask = data["track_mask"]

            inner_crash = navigator.is_hitting_inner_wall(direction, track_image, frame)
            outer_crash = navigator.is_hitting_outer_wall(direction, track_image, frame)

            green_mask_on_track = cv2.bitwise_and(green_mask, green_mask, mask=track_mask)
            red_mask_on_track = cv2.bitwise_and(red_mask, red_mask, mask=track_mask)
            pillar_found = navigator.find_nearest_pillar(green_mask_on_track, red_mask_on_track, frame)

            pink_angle, pink_x, pink_y = get_parking_wall_steer_angle(direction, pink_mask, frame)

            # if a pillar is nearer than the pink wall, deal with the pillar first
            pillar_is_closer = pillar_found is not None and (pink_y is None or pillar_found[1] > pink_y)

            if pillar_is_closer:
                p_x, p_y, _is_green = pillar_found
                angle = get_forced_pillar_steer_angle(p_x, p_y, False, frame)
            elif pink_angle is not None:
                angle = pink_angle
            else:
                # pink wall not visible yet - fall back to plain wall following
                target_x = APPROACH_WALL_TARGET_X_LEFT if direction == Direction.LEFT else APPROACH_WALL_TARGET_X_RIGHT
                kp, kd = (INNER_WALL_KP, INNER_WALL_KD) if inner_crash else (APPROACH_WALL_KP, APPROACH_WALL_KD)
                wall_angle = follow_wall_point(track_image, direction, frame, target_x,
                                                APPROACH_WALL_TARGET_Y, kp, kd)
                angle = (STEER_MAX - 3) if outer_crash and direction == Direction.LEFT else wall_angle
                if outer_crash and direction == Direction.RIGHT:
                    angle = STEER_MIN + 3

            angle = round(max(STEER_MIN, min(STEER_MAX, angle)))
            if previous_angle is None or previous_angle != angle:
                set_steering_angle(angle)
                previous_angle = angle

            # reached the spot once close enough and lined up with the aim point
            if pink_x is not None and pink_y is not None:
                aim_x = GREEN_PILLAR_TARGET_X if direction == Direction.LEFT else RED_PILLAR_TARGET_X
                close_enough = pink_y >= PARK_APPROACH_TARGET_Y
                alongside = abs(pink_x - aim_x) <= PARK_APPROACH_X_TOLERANCE
                if close_enough and alongside:
                    stop()
                    self._reverse_into_parking_spot(direction)
                    self.state = RunState.FINISHED
                    return

    def _reverse_into_parking_spot(self, direction):
        """Wall-follow forward past the spot, then reverse in with a fixed sequence of hard turns."""
        follow_side = Direction.RIGHT if direction == Direction.LEFT else Direction.LEFT
        target_x = PARK_ENTRY_TARGET_X_LEFT if follow_side == Direction.LEFT else PARK_ENTRY_TARGET_X_RIGHT

        # small nudge to straighten out before wall-following forward
        straighten_angle = (STEER_CENTER + PARK_STRAIGHTEN_STEER_OFFSET if direction == Direction.LEFT
                             else STEER_CENTER - PARK_STRAIGHTEN_STEER_OFFSET)
        straighten_angle = max(STEER_MIN, min(STEER_MAX, straighten_angle))
        set_steering_angle(straighten_angle, duration=PARK_STRAIGHTEN_TIME)
        set_steering_angle(STEER_CENTER)

        stop()
        time.sleep(1)

        global _prev_point_wall_error
        _prev_point_wall_error = 0.0  # reset PD memory before this new phase
        previous_angle = None

        drive(MOTOR_FORWARD, PARK_SPEED)
        end_time = time.time() + PARK_ENTRY_FORWARD_TIME
        while time.time() < end_time:
            raw_frame = self.picam2.capture_array()
            frame = crop_frame(raw_frame, 0, CAMERA_WIDTH, CAMERA_HEIGHT - FRAME_HEIGHT, CAMERA_HEIGHT)
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            pink_mask = get_color_mask(lab, "pink")

            data = process_frame(raw_frame, extra_masks=(pink_mask,))
            track_image = data["track_image"]

            angle = follow_wall_point(track_image, follow_side, frame, target_x,
                                       PARK_ENTRY_TARGET_Y, PARK_ENTRY_WALL_KP, PARK_ENTRY_WALL_KD)
            angle = round(max(STEER_MIN, min(STEER_MAX, angle)))
            if previous_angle is None or previous_angle != angle:
                set_steering_angle(angle)
                previous_angle = angle

        stop()
        time.sleep(0.3)

        # reverse straight back until the pink wall comes back into view behind us
        set_steering_angle(STEER_CENTER - (3 if direction == Direction.LEFT else 5))
        drive(MOTOR_REVERSE, PARK_SPEED)

        while True:
            frame = capture_cropped_frame(self.picam2)
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            pink_mask = get_color_mask(lab, "pink")
            pink_area = cv2.countNonZero(pink_mask)

            if pink_area > PARK_WALL_SEEN_AREA:
                break

        stop()
        time.sleep(1.0)

        # one more short forward hop to line up before the final reverse-turn sequence
        set_steering_angle(STEER_CENTER - 3)
        drive(MOTOR_FORWARD, PARK_SPEED, 1770)
        stop()
        time.sleep(1)

        # fixed hard-turn sequence into the parking box; turn direction depends on which side we parked from
        hard_turn_angle = PARK_STEER_MIN if direction == Direction.LEFT else PARK_STEER_MAX
        set_steering_angle(hard_turn_angle, min_angle=PARK_STEER_MIN, max_angle=PARK_STEER_MAX)
        time.sleep(1.0)
        drive(MOTOR_REVERSE, PARK_SPEED, 1100)
        stop()
        reset_tick_counter()
        time.sleep(1)

        set_steering_angle(STEER_CENTER, min_angle=PARK_STEER_MIN, max_angle=PARK_STEER_MAX)
        time.sleep(1.0)
        drive(MOTOR_REVERSE, PARK_SPEED, 385)
        stop()
        reset_tick_counter()
        time.sleep(1)

        hard_turn_angle_1 = PARK_STEER_MAX if direction == Direction.LEFT else PARK_STEER_MIN
        set_steering_angle(hard_turn_angle_1, min_angle=PARK_STEER_MIN, max_angle=PARK_STEER_MAX)
        time.sleep(1)
        drive(MOTOR_REVERSE, PARK_SPEED, 470)
        stop()
        reset_tick_counter()
        time.sleep(1)

        hard_turn_angle_2 = PARK_STEER_MIN if direction == Direction.LEFT else PARK_STEER_MAX
        set_steering_angle(hard_turn_angle_2, min_angle=PARK_STEER_MIN, max_angle=PARK_STEER_MAX)
        time.sleep(1)
        drive(MOTOR_FORWARD, PARK_SPEED, 95)
        stop()
        reset_tick_counter()
        time.sleep(1)

        set_steering_angle(STEER_CENTER)


if __name__ == "__main__":
    RobotController().run()