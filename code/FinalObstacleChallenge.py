import cv2
import math
import numpy as np
import serial
import time
from enum import Enum
from picamera2 import Picamera2
import RPi.GPIO as GPIO
from gpiozero import LED


ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
time.sleep(2)

LAPS_TARGET = 3
TOTAL_TURNS = LAPS_TARGET * 4

DRIVE_SPEED = 200
OBSTACLE_SPEED = 200
PARK_SPEED = 100

BUTTON_PIN = 26

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def set_servo_angle(angle, duration=0.0, resend_interval=0.03, min_angle=None, max_angle=None):
    low = MIN_ANGLE if min_angle is None else min_angle
    high = MAX_ANGLE if max_angle is None else max_angle
    angle = max(low, min(high, angle))
    physical_angle = to_physical_angle(angle)

    if duration <= 0:
        ser.write(f"SERVO,{physical_angle}\n".encode())
        return

    end_time = time.time() + duration
    while time.time() < end_time:
        ser.write(f"SERVO,{physical_angle}\n".encode())
        time.sleep(resend_interval)


def set_motor(direction, speed, ticks=None):
    direction = max(0, min(2, int(direction)))
    speed = max(0, min(255, int(speed)))

    if ticks is not None:
        reset_ticks()
        moved = move_ticks(direction, speed, int(ticks))
        print(f"[motor] ticks: wanted {int(ticks)}, moved {moved}")
        return moved

    ser.write(f"MOTOR,{direction},{speed}\n".encode())
    return None


def stop_motor():
    ser.write("STOP\n".encode())


CAMERA_PIC_WIDTH = 640
CAMERA_PIC_HEIGHT = 360
PIC_WIDTH = 640
PIC_HEIGHT = 280

GRAY_THRESHOLD = 70

LINE_AREA_ENTER_THRESHOLD = 150
LINE_AREA_EXIT_THRESHOLD = 60

BLUE_LOWER = np.array([22, 131, 75])
BLUE_UPPER = np.array([95, 158, 112])

ORANGE_LOWER = np.array([101, 128, 151])
ORANGE_UPPER = np.array([166, 164, 188])

GREEN_LOWER = np.array([78, 66, 123])
GREEN_UPPER = np.array([150, 109, 167])

RED_LOWER = np.array([53, 162, 139])
RED_UPPER = np.array([116, 196, 166])

PINK_LOWER = np.array([39, 156, 115])
PINK_UPPER = np.array([94, 185, 141])

MASK_CLEAN_KERNEL = np.ones((5, 5), np.uint8)


def calculate_color_mask(lab_img, color):
    if color == "blue":
        mask = cv2.inRange(lab_img, BLUE_LOWER, BLUE_UPPER)
    elif color == "orange":
        mask = cv2.inRange(lab_img, ORANGE_LOWER, ORANGE_UPPER)
    elif color == "green":
        mask = cv2.inRange(lab_img, GREEN_LOWER, GREEN_UPPER)
    elif color == "red":
        mask = cv2.inRange(lab_img, RED_LOWER, RED_UPPER)
    elif color == "pink":
        mask = cv2.inRange(lab_img, PINK_LOWER, PINK_UPPER)
    else:
        mask = np.zeros(lab_img.shape[:2], dtype=np.uint8)

    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, MASK_CLEAN_KERNEL)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, MASK_CLEAN_KERNEL)
    return mask


class Direction(Enum):
    LEFT = -1
    RIGHT = 1


ENTRY_CONFIRM_FRAMES = 3
EXIT_CONFIRM_FRAMES_LEFT = 18
EXIT_CONFIRM_FRAMES_RIGHT = 2
TURN_MIN_DURATION_LEFT = 1.0
TURN_MIN_DURATION_RIGHT = 0.0
TURN_MAX_DURATION = 4.0
TURN_COOLDOWN = 1.25


def show_frame(frame):
    """One shared window for the whole program. Returns True if 'q' was pressed
    (caller decides what to stop — this does NOT set a global flag, so pressing
    q only breaks the loop that's currently calling this)."""
    cv2.imshow("frame", frame)
    key = cv2.waitKey(1) & 0xFF
    return key == ord('q')
   
class LapTracker:
    def __init__(self):
        self.state = "idle"
        self.quarter_lap_count = 0
        self._confirm_count = 0
        self._exit_confirm_count = 0
        self._turn_start_time = 0.0
        self._cooldown_until = 0.0

    def process_image(self, blue_mask, orange_mask, direction, polygon_mask):
        now = time.time()
        marker_mask = blue_mask if direction == Direction.LEFT else orange_mask
        marker_mask = cv2.bitwise_and(marker_mask, marker_mask, mask=polygon_mask)
        marker_area = cv2.countNonZero(marker_mask)

        exit_confirm_frames = EXIT_CONFIRM_FRAMES_LEFT if direction == Direction.LEFT else EXIT_CONFIRM_FRAMES_RIGHT
        turn_min_duration = TURN_MIN_DURATION_LEFT if direction == Direction.LEFT else TURN_MIN_DURATION_RIGHT

        if self.state == "idle":
            if now >= self._cooldown_until:
                self._confirm_count = self._confirm_count + 1 if marker_area > LINE_AREA_ENTER_THRESHOLD else 0
                if self._confirm_count >= ENTRY_CONFIRM_FRAMES:
                    self.state = "turning"
                    self._turn_start_time = now
                    self._exit_confirm_count = 0
                    self._confirm_count = 0
        else:
            turn_elapsed = now - self._turn_start_time
            self._exit_confirm_count = (
                self._exit_confirm_count + 1 if marker_area < LINE_AREA_EXIT_THRESHOLD else 0
            )
            should_exit = (
                turn_elapsed >= turn_min_duration and self._exit_confirm_count >= exit_confirm_frames
            ) or (turn_elapsed >= TURN_MAX_DURATION)
            if should_exit:
                self.quarter_lap_count += 1
                print(f"[lap] quarter-lap {self.quarter_lap_count}/{TOTAL_TURNS} "
                      f"({self.quarter_lap_count // 4} lap(s) + {self.quarter_lap_count % 4} quarter(s))")
                self.state = "idle"
                self._cooldown_until = now + TURN_COOLDOWN
                self._confirm_count = 0
                self._exit_confirm_count = 0


default_servo = 97
max_turn_degree = 43
PARK_MAX_TURN_DEGREE = 55
MIN_ANGLE = default_servo - max_turn_degree
MAX_ANGLE = default_servo + max_turn_degree
TURN_ACCUM_STEP = 16   # degrees added per frame while turning
PARK_MIN_ANGLE = default_servo - PARK_MAX_TURN_DEGREE   # 35
PARK_MAX_ANGLE = default_servo + PARK_MAX_TURN_DEGREE   # 145
STEER_SIGN = -1


def to_physical_angle(logical_angle):
    if STEER_SIGN == -1:
        return int(round(2 * default_servo - logical_angle))
    return int(round(logical_angle))


TARGET_X_LEFT = 0
TARGET_X_RIGHT = PIC_WIDTH
TARGET_Y = 220

Kp_wall = 0.37
Kd_wall = 0.005
prev_wall_error = 0.0

NBR_COLS = 10


def _find_black_from_bottom(img, col_range):
    h = img.shape[0]
    y_vals = []
    for x in col_range:
        found = 0
        for y in reversed(range(h - 20)):
            if img[y, x] == 0:
                found = y
                break
        y_vals.append(found)
    return y_vals


def _find_black_sides(img, direction, row_range):
    w = img.shape[1]
    end_index = 0 if direction == Direction.LEFT else w - 1
    step = direction.value
    x_vals = []
    for y in row_range:
        found = end_index
        for x in range(w // 2, end_index, step):
            if img[y, x] == 0:
                found = x
                break
        x_vals.append(found)
    return x_vals


def wall_follow_angle(polygon_image, direction, display_frame, damped=False):
    global prev_wall_error
    h, w = polygon_image.shape[:2]

    kp = INNER_CRASH_KP if damped else Kp_wall
    kd = INNER_CRASH_KD if damped else Kd_wall

    target_x = TARGET_X_LEFT if direction == Direction.LEFT else TARGET_X_RIGHT

    cols = range(0, NBR_COLS) if direction == Direction.LEFT else range(w - NBR_COLS, w)
    rows = range(h - 3 * NBR_COLS, h - 2 * NBR_COLS)

    y_vals = _find_black_from_bottom(polygon_image, cols)
    x_vals = _find_black_sides(polygon_image, direction, rows)

    avg_y = np.mean(y_vals)
    avg_x = np.mean(x_vals)
    if avg_y >= h - 1:
        avg_y = h

    cv2.circle(display_frame, (int(avg_x), int(avg_y)), 8, (0, 0, 255), -1)
    cv2.circle(display_frame, (int(target_x), TARGET_Y), 8, (0, 255, 0), -1)

    error_y = TARGET_Y - avg_y
    if direction == Direction.LEFT:
        error_x = target_x - avg_x
    else:
        error_x = avg_x - target_x
    error = error_y + error_x

    derivative = error - prev_wall_error
    control = (kp * error) + (kd * derivative)
    prev_wall_error = error

    turn_sign = 1 if direction == Direction.LEFT else -1
    angle = default_servo + turn_sign * control
    angle = max(MIN_ANGLE, min(MAX_ANGLE, angle))
    return angle

# --- Area-based wall follow (ported from old script, used ONLY in run()'s obstacle dodging) ---
# ROIs sized/positioned relative to PIC_WIDTH/PIC_HEIGHT (640x280), not hardcoded.
# Fixed pixel ROIs, measured for direction == Direction.LEFT. The right-hand box
# isn't a mirror of the left one (128px wide, y:80-200 vs 134px wide, y:60-198),
# so for Direction.RIGHT we flip both boxes across the frame's vertical centerline
# and swap which one plays "left"/"right", instead of reusing them as-is.
ROI_LEFT_WALL_BASE  = [0, 80, 128, 200]
ROI_RIGHT_WALL_BASE = [504, 60, 638, 198]

CENTER_OFFSET = 0     # subtract from (area_left - area_right) so 0 = truly centered
LOW_THRESH    = 700   # below this = 'basically no wall on this side' -> corner/opening
BOOST_MULT    = 2
BOOST_ADD     = 25000

AREA_KP_WALLS = 0.09
AREA_KD_WALLS = 0.0004
AREA_KP_WALLS_DAMPED = 0.01
AREA_KD_WALLS_DAMPED = 0.0

_prev_area_wall_error = 0.0


def _mirror_roi(roi, width=PIC_WIDTH):
    x1, y1, x2, y2 = roi
    return [width - x2, y1, width - x1, y2]


def get_wall_rois(direction):
    """(roi_left, roi_right) for the current driving direction."""
    if direction == Direction.LEFT:
        return ROI_LEFT_WALL_BASE, ROI_RIGHT_WALL_BASE
    return _mirror_roi(ROI_RIGHT_WALL_BASE), _mirror_roi(ROI_LEFT_WALL_BASE)


def _largest_wall_contour_area(binary_img, roi, min_area=50):
    """binary_img: 0=wall, 255=free (e.g. polygon_image). Returns area of the
    largest wall blob inside roi, or 0 if none / too small."""
    x1, y1, x2, y2 = roi
    region = binary_img[y1:y2, x1:x2]
    if region.size == 0:
        return 0
    walls_as_white = cv2.bitwise_not(region)
    contours, _ = cv2.findContours(walls_as_white, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return 0
    area = cv2.contourArea(max(contours, key=cv2.contourArea))
    return area if area > min_area else 0


def draw_debug_rois(frame, rois, color=(255, 204, 0)):
    for x1, y1, x2, y2 in rois:
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    return frame


def area_based_wall_follow_angle(binary_img, direction, blue_area=0, orange_area=0, damped=False):
    """Same 'boost the far side when the near side vanishes' trick as the reference
    script: when one ROI's wall area drops under LOW_THRESH (a corner/opening just
    appeared on that side), the other side's area is scaled up (BOOST_MULT) and
    pushed up by a flat BOOST_ADD, so the PD term below reacts as if that wall were
    huge and steers hard toward the opening. That IS the sharp-turn behavior -- no
    separate turning state machine needed here."""
    global _prev_area_wall_error

    kp = AREA_KP_WALLS_DAMPED if damped else AREA_KP_WALLS
    kd = AREA_KD_WALLS_DAMPED if damped else AREA_KD_WALLS

    roi_left, roi_right = get_wall_rois(direction)
    area_left = _largest_wall_contour_area(binary_img, roi_left)
    area_right = _largest_wall_contour_area(binary_img, roi_right)

    if area_left < LOW_THRESH and area_right > 100:
        area_right = area_right * BOOST_MULT + BOOST_ADD
    elif area_right < LOW_THRESH and area_left > 100:
        area_left = area_left * BOOST_MULT + BOOST_ADD

    wall_error = (area_left - area_right) - CENTER_OFFSET
    derivative = wall_error - _prev_area_wall_error
    control = (wall_error * kp) + (derivative * kd)
    _prev_area_wall_error = wall_error

    angle = default_servo - control

    # both sides completely empty -> deep in a corner with no wall pixels at all.
    # Fall back to a flat hard-over turn, same as the reference's
    # total_left == total_right == 0 branch, using the marker colour as the
    # direction tiebreak the way the reference used driving_direction.
    if area_left == 0 and area_right == 0:
        turn_sign = 1 if direction == Direction.LEFT else -1
        if blue_area > LINE_AREA_ENTER_THRESHOLD or orange_area > LINE_AREA_ENTER_THRESHOLD:
            angle = default_servo + turn_sign * 35
        else:
            angle = default_servo + turn_sign * 20

    angle = max(MIN_ANGLE, min(MAX_ANGLE, angle))
    return angle

#__________________________________________________________

def find_contour(img, white=0):
    contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if white == 1:
        target_pt = (PIC_WIDTH / 2, PIC_HEIGHT - 10)
        contours = [cnt for cnt in contours if cv2.pointPolygonTest(cnt, target_pt, False) >= 0]
    if not contours:
        return None, None
    biggest_contour = max(contours, key=cv2.contourArea)
    contours = [cnt for cnt in contours if not np.array_equal(cnt, biggest_contour)]
    if not contours:
        return biggest_contour, None
    second_biggest_contour = max(contours, key=cv2.contourArea)
    return biggest_contour, second_biggest_contour


def draw_polygon(binary_img, target_img):
    cnt, _ = find_contour(binary_img, 1)
    if cnt is None:
        return target_img, None
    epsilon = 0.001 * cv2.arcLength(cnt, True)
    polygon = cv2.approxPolyDP(cnt, epsilon, True)
    mask = np.zeros_like(binary_img)
    cv2.fillPoly(mask, [polygon], 255)
    result = cv2.bitwise_and(binary_img, mask)
    return result, polygon


LEFT_OBSTACLE_X_THRESHOLD = 15
RIGHT_OBSTACLE_X_THRESHOLD = PIC_WIDTH - LEFT_OBSTACLE_X_THRESHOLD
PARK_OBSTACLE_X_THRESHOLD = PIC_WIDTH	
OBJECT_LINE_ANGLE_THRESHOLD = 45
GREEN_OBSTACLE_KP = 1.45
RED_OBSTACLE_KP = 1.45

TOO_LOW_Y = PIC_HEIGHT - 45
TOO_CLOSE_Y = PIC_HEIGHT - 20

CRASH_POINT_COLOR = (255, 0, 0)

PILLAR_AREA_THRESHOLD = 250

INNER_CRASH_KP = 0.15
INNER_CRASH_KD = 0.0

POST_PASS_CLIP_FRAMES = 15
POST_PASS_MAX_OFFSET = 50

INNER_CRASH_LINE_SAMPLES = 15


class CrashState(Enum):
    NONE = 0
    INNER = 1
    OUTER = 2


class ObstacleTracker:
    def __init__(self):
        self.old_angle = default_servo
        self.state = CrashState.NONE
        self.inner_wall_warning = False
        self.last_color = None
        self.last_pillar_y = None
        self.tracking_pillar = False
        self.tracking_color = None
        self.post_pass_frames = 0        

    def check_inner_wall_crash(self, direction, polygon_image, display_frame):
        if direction == Direction.RIGHT:
            low_point = (PIC_HEIGHT - 70, PIC_WIDTH - 160)   # closest to robot
            high_point = (PIC_HEIGHT - 130, PIC_WIDTH - 210) # farthest from robot
        else:
            low_point = (PIC_HEIGHT - 70, 160)
            high_point = (PIC_HEIGHT - 130, 210)

        y_vals = np.linspace(low_point[0], high_point[0], INNER_CRASH_LINE_SAMPLES)
        x_vals = np.linspace(low_point[1], high_point[1], INNER_CRASH_LINE_SAMPLES)

        crashed = False
        for y, x in zip(y_vals, x_vals):
            y, x = int(round(y)), int(round(x))
            in_bounds = 0 <= y < PIC_HEIGHT and 0 <= x < PIC_WIDTH
            point_crashed = in_bounds and polygon_image[y, x] == 0
            if point_crashed:
                crashed = True
            if in_bounds:
                cv2.circle(display_frame, (x, y), 3, CRASH_POINT_COLOR, -1)

        cv2.line(display_frame, (int(low_point[1]), int(low_point[0])),
                 (int(high_point[1]), int(high_point[0])), CRASH_POINT_COLOR, 1)

        return crashed

    def check_outer_wall_crash(self, direction, polygon_image, display_frame):
        detection_points = [(PIC_WIDTH // 2, PIC_HEIGHT - 138)] #Original is 145
        crashed = False
        for x, y in detection_points:
            in_bounds = 0 <= y < PIC_HEIGHT and 0 <= x < PIC_WIDTH
            point_crashed = in_bounds and polygon_image[y, x] == 0
            if point_crashed:
                crashed = True
            if in_bounds:
                cv2.circle(display_frame, (x, y), 5, CRASH_POINT_COLOR, -1)
        return crashed

    def find_closest_pillar(self, green_mask, red_mask, display_frame):
        robot_point = (PIC_WIDTH // 2, PIC_HEIGHT)

        closest_distance = float("inf")
        closest = None

        for mask, is_green in ((green_mask, True), (red_mask, False)):
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area <= PILLAR_AREA_THRESHOLD:
                    continue

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
                       (0, 255, 0) if is_green else (0, 0, 255), 2)

        return x_center, y_center, is_green

    def obstacle_angle(self, direction, green_mask, red_mask, polygon_image, display_frame,
                       laps_complete=False, force_right_avoid=False):
        self.inner_wall_warning = False
        self.last_pillar_y = None

        # find pillar first so we know whether an obstacle is actually present
        found = self.find_closest_pillar(green_mask, red_mask, display_frame)
        obstacle_present = found is not None

        # outer crash always active
        outer_crash = self.check_outer_wall_crash(direction, polygon_image, display_frame)

        # inner crash only checked/valid when an obstacle is actually present
        inner_crash = False
        if obstacle_present:
            inner_crash = self.check_inner_wall_crash(direction, polygon_image, display_frame)

        turn_into_corner = (MAX_ANGLE - 3) if direction == Direction.LEFT else (MIN_ANGLE + 3)

        if self.state == CrashState.NONE:
            if inner_crash:
                self.state = CrashState.INNER
                self.inner_wall_warning = True
                return None
            elif outer_crash:
                self.state = CrashState.OUTER
                return turn_into_corner
        elif self.state == CrashState.INNER:
            if not obstacle_present or not inner_crash:
                # obstacle gone (or no longer triggering inner) -> drop inner crash state
                self.state = CrashState.NONE
            else:
                self.inner_wall_warning = True
                return None
        elif self.state == CrashState.OUTER:
            if not outer_crash:
                self.state = CrashState.NONE
            else:
                return turn_into_corner

        if found is None:
            if self.tracking_pillar:
                self.post_pass_frames = POST_PASS_CLIP_FRAMES
            self.tracking_pillar = False
            return None

        x_center, y_center, is_green = found
        # force every pillar to be treated as "red" (right-side avoidance) once the
        # 0.5s grace window after the 12th quarter-turn (RIGHT direction) has passed
        if force_right_avoid:
            is_green = False

        self.last_pillar_y = y_center

        if y_center > TOO_LOW_Y:
            if y_center > TOO_CLOSE_Y:
                #if self.tracking_pillar:
                 #   self.post_pass_frames = POST_PASS_CLIP_FRAMES
                #self.tracking_pillar = False
                return None
            self.tracking_pillar = True
            self.tracking_color = "green" if is_green else "red"
            return self.old_angle

        self.tracking_pillar = True
        self.tracking_color = "green" if is_green else "red"
        self.post_pass_frames = 0 

        if is_green:
            if laps_complete:
                self.last_color = "green"
            cv2.line(display_frame, (x_center, y_center), (RIGHT_OBSTACLE_X_THRESHOLD, PIC_HEIGHT), (0, 255, 0), 2)
            cv2.line(display_frame, (x_center, y_center), (x_center, PIC_HEIGHT), (0, 255, 0), 2)
            rad_angle = np.arctan2(y_center - PIC_HEIGHT, x_center - RIGHT_OBSTACLE_X_THRESHOLD)
        else:
            if laps_complete:
                self.last_color = "red"
            cv2.line(display_frame, (x_center, y_center), (LEFT_OBSTACLE_X_THRESHOLD, PIC_HEIGHT), (0, 0, 255), 2)
            cv2.line(display_frame, (x_center, y_center), (x_center, PIC_HEIGHT), (0, 0, 255), 2)
            rad_angle = np.arctan2(y_center - PIC_HEIGHT, x_center - LEFT_OBSTACLE_X_THRESHOLD)

        object_angle_deg = 90 + np.degrees(rad_angle)

        if is_green:
            servo_angle = default_servo - ((object_angle_deg + OBJECT_LINE_ANGLE_THRESHOLD) * GREEN_OBSTACLE_KP)
        else:
            servo_angle = default_servo - ((object_angle_deg - OBJECT_LINE_ANGLE_THRESHOLD) * RED_OBSTACLE_KP)

        servo_angle = max(MIN_ANGLE, min(MAX_ANGLE, servo_angle))
        self.old_angle = servo_angle
        return servo_angle

def crop_image(img, x_start, x_end, y_start, y_end):
    return img[y_start:y_end, x_start:x_end]


def _process_frame(raw_frame):
    frame = crop_image(raw_frame, 0, CAMERA_PIC_WIDTH, CAMERA_PIC_HEIGHT - PIC_HEIGHT, CAMERA_PIC_HEIGHT)
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)

    blue_mask = calculate_color_mask(lab, "blue")
    orange_mask = calculate_color_mask(lab, "orange")
    green_mask = calculate_color_mask(lab, "green")
    red_mask = calculate_color_mask(lab, "red")

    colormask_image = frame.copy()
    non_wall_mask = cv2.bitwise_or(cv2.bitwise_or(blue_mask, orange_mask),
                                   cv2.bitwise_or(green_mask, red_mask))
    colormask_image[non_wall_mask > 0] = (255, 255, 255)

    grayscale_image = cv2.cvtColor(colormask_image, cv2.COLOR_BGR2GRAY)
    blurred_image = cv2.bilateralFilter(grayscale_image, 9, 75, 75)
    _, binary_image = cv2.threshold(blurred_image, GRAY_THRESHOLD, 255, cv2.THRESH_BINARY)
    clean_image = cv2.morphologyEx(binary_image, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))

    polygon_image, polygon_points = draw_polygon(clean_image, clean_image)
    polygon_mask = np.zeros_like(clean_image)
    if polygon_points is not None:
        cv2.fillPoly(polygon_mask, [polygon_points], 255)

    return {
        "raw_frame": raw_frame,
        "frame": frame,
        "blue_mask": blue_mask,
        "orange_mask": orange_mask,
        "green_mask": green_mask,
        "red_mask": red_mask,
        "polygon_image": polygon_image,
        "polygon_points": polygon_points,
        "polygon_mask": polygon_mask,
    }


def detect_exit_direction(picam2):
    raw_frame = picam2.capture_array()
    frame = crop_image(raw_frame, 0, CAMERA_PIC_WIDTH, CAMERA_PIC_HEIGHT - PIC_HEIGHT, CAMERA_PIC_HEIGHT)

    grayscale_image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred_image = cv2.bilateralFilter(grayscale_image, 9, 75, 75)
    _, binary_image = cv2.threshold(blurred_image, GRAY_THRESHOLD, 255, cv2.THRESH_BINARY)

    h, w = binary_image.shape[:2]
    left_half = binary_image[:, :w // 2]
    right_half = binary_image[:, w // 2:]

    left_white = cv2.countNonZero(left_half)
    right_white = cv2.countNonZero(right_half)

    print(f"[park] left_white={left_white}  right_white={right_white}")
    return Direction.RIGHT if right_white > left_white else Direction.LEFT


def exit_parallel_park(direction, picam2):
    away_angle = PARK_MAX_ANGLE if direction == Direction.LEFT else PARK_MIN_ANGLE
    toward_angle = PARK_MIN_ANGLE if direction == Direction.LEFT else PARK_MAX_ANGLE

    print(f"[park] exiting, direction={direction.name}")

    set_servo_angle(away_angle, min_angle=PARK_MIN_ANGLE, max_angle=PARK_MAX_ANGLE)
    time.sleep(1)

    set_motor(1, PARK_SPEED, 1200)

    raw_frame = picam2.capture_array()
    frame = crop_image(raw_frame, 0, CAMERA_PIC_WIDTH, CAMERA_PIC_HEIGHT - PIC_HEIGHT, CAMERA_PIC_HEIGHT)
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    green_mask = calculate_color_mask(lab, "green")
    red_mask = calculate_color_mask(lab, "red")

    pillar_tracker = ObstacleTracker()
    seen_color = None
    found = pillar_tracker.find_closest_pillar(green_mask, red_mask, frame.copy())
    if found is not None:
        _x, _y, is_green = found
        seen_color = "green" if is_green else "red"

    print(f"[park] pillar check after first away-turn: {seen_color}")
    if direction == Direction.LEFT:
        if seen_color == "green":
            set_servo_angle(away_angle, min_angle=PARK_MIN_ANGLE, max_angle=PARK_MAX_ANGLE)
            set_motor(1, PARK_SPEED, 1000)
            stop_motor()
            time.sleep(1)
            set_servo_angle(toward_angle, min_angle=PARK_MIN_ANGLE, max_angle=PARK_MAX_ANGLE)
            time.sleep(1)
            set_motor(1, PARK_SPEED, 2600)
            stop_motor()
            time.sleep(1)
            set_servo_angle(default_servo - 2)
            time.sleep(1)
            set_motor(2, PARK_SPEED, 2600)
        else:
            stop_motor()
            time.sleep(1)
            set_servo_angle(toward_angle, min_angle=PARK_MIN_ANGLE, max_angle=PARK_MAX_ANGLE)
            time.sleep(1)
            set_motor(1, PARK_SPEED, 1500)
            time.sleep(1)
            set_servo_angle(default_servo, min_angle=PARK_MIN_ANGLE, max_angle=PARK_MAX_ANGLE)
            time.sleep(1)
            set_motor(2, PARK_SPEED, 2300)
    if direction == Direction.RIGHT:
        if seen_color == "red":
            set_servo_angle(away_angle, min_angle=PARK_MIN_ANGLE, max_angle=PARK_MAX_ANGLE)
            set_motor(1, PARK_SPEED, 1150)
            stop_motor()
            time.sleep(1)
            set_servo_angle(toward_angle, min_angle=PARK_MIN_ANGLE, max_angle=PARK_MAX_ANGLE)
            time.sleep(1)
            set_motor(1, PARK_SPEED, 2750)
            stop_motor()
            time.sleep(1)
        else:
            stop_motor()
            time.sleep(1)
            set_servo_angle(toward_angle, min_angle=PARK_MIN_ANGLE, max_angle=PARK_MAX_ANGLE)
            time.sleep(1)
            set_motor(1, PARK_SPEED, 900)
            time.sleep(1)

    set_servo_angle(default_servo)
    print("[park] exit complete, handing off to obstacle run()")


PARK_TARGET_Y = PIC_HEIGHT - 75
PARK_X_TOLERANCE = 80

PARK_LINE_ANGLE_THRESHOLD = 45
PARK_OBSTACLE_KP = 2.2

PINK_AREA_THRESHOLD = 10


def find_pink_block(pink_mask, display_frame):
    contours, _ = cv2.findContours(pink_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    farthest_y = float("inf")
    farthest = None

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area <= PINK_AREA_THRESHOLD:
            continue

        x, y, w, h = cv2.boundingRect(cnt)
        x_center = x + w // 2
        y_center = y + h // 2

        if y_center >= farthest_y:
            continue

        farthest_y = y_center
        farthest = (x_center, y_center, w, h, area)

    if farthest is None:
        return None

    x_center, y_center, w, h, area = farthest
    cv2.rectangle(display_frame, (x_center - w // 2, y_center - h // 2),
                  (x_center + w // 2, y_center + h // 2), (255, 0, 255), 2)
    return x_center, y_center, area


PINK_SEARCH_TURN_ANGLE_OFFSET = 30
PINK_SEARCH_TURN_SPEED = 90
PINK_SEARCH_TURN_DURATION = 1.5


def hardcoded_pink_search_turn(picam2):
    print("[park] pink not visible -- hardcoded left search turn")
    turn_angle = default_servo + PINK_SEARCH_TURN_ANGLE_OFFSET
    turn_angle = max(MIN_ANGLE, min(MAX_ANGLE, turn_angle))

    set_servo_angle(turn_angle)
    set_motor(1, PINK_SEARCH_TURN_SPEED)
    time.sleep(PINK_SEARCH_TURN_DURATION)
    stop_motor()

    set_servo_angle(default_servo)
    time.sleep(0.3)
    print("[park] search turn complete")


def forced_pillar_angle(x_center, y_center, is_green, display_frame):
    aim_x = LEFT_OBSTACLE_X_THRESHOLD
    color = (0, 255, 0) if is_green else (0, 0, 255)
    cv2.line(display_frame, (x_center, y_center), (aim_x, PIC_HEIGHT), color, 2)

    rad_angle = np.arctan2(y_center - PIC_HEIGHT, x_center - aim_x)
    object_angle_deg = 90 + np.degrees(rad_angle)

    threshold_sign = 1 if is_green else -1
    servo_angle = default_servo - ((object_angle_deg + threshold_sign * OBJECT_LINE_ANGLE_THRESHOLD) * PARK_OBSTACLE_KP)

    return max(MIN_ANGLE, min(MAX_ANGLE, servo_angle))


def park_block_angle(direction, pink_mask, display_frame):
    found = find_pink_block(pink_mask, display_frame)
    if found is None:
        return None, None, None
    x_center, y_center, area = found

    aim_x = RIGHT_OBSTACLE_X_THRESHOLD if direction == Direction.LEFT else LEFT_OBSTACLE_X_THRESHOLD
    cv2.line(display_frame, (x_center, y_center), (aim_x, PIC_HEIGHT), (255, 0, 255), 2)

    rad_angle = np.arctan2(y_center - PIC_HEIGHT, x_center - aim_x)
    object_angle_deg = 90 + np.degrees(rad_angle)

    if aim_x == RIGHT_OBSTACLE_X_THRESHOLD:
        servo_angle = default_servo - ((object_angle_deg + PARK_LINE_ANGLE_THRESHOLD) * 1.8)
    else:
        servo_angle = default_servo - ((object_angle_deg - PARK_LINE_ANGLE_THRESHOLD) * 1.8)

    servo_angle = max(PARK_MIN_ANGLE, min(PARK_MAX_ANGLE, servo_angle))
    return servo_angle, x_center, y_center


PARK_ENTRY_STRAIGHTEN_OFFSET = 20
PARK_ENTRY_STRAIGHTEN_DURATION = 0.5

U_TURN_SPEED = 100
U_TURN_PINK_SEEN_THRESHOLD = 500
U_TURN_MAX_DURATION = 8.0


def perform_u_turn_to_pink(picam2):
    print("[park] U-turning left to find pink")
    #stop_motor()
    #time.sleep(1)
    set_servo_angle(PARK_MAX_ANGLE, min_angle=PARK_MIN_ANGLE, max_angle=PARK_MAX_ANGLE)
    #time.sleep(1)
    set_motor(1, U_TURN_SPEED)

    start_time = time.time()
    while True:
        raw_frame = picam2.capture_array()
        frame = crop_image(raw_frame, 0, CAMERA_PIC_WIDTH, CAMERA_PIC_HEIGHT - PIC_HEIGHT, CAMERA_PIC_HEIGHT)
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        pink_mask = calculate_color_mask(lab, "pink")
        pink_area = cv2.countNonZero(pink_mask)

        show_frame(frame)
        #key = cv2.waitKey(1) & 0xFF
      #  if key == ord('q'):
         #   stop_motor()
         #   return

        if pink_area > U_TURN_PINK_SEEN_THRESHOLD:
            print(f"[park] pink found during U-turn (area={pink_area}) -- straightening")
            break

        if time.time() - start_time > U_TURN_MAX_DURATION:
            print("[park] U-turn safety timeout hit -- proceeding anyway")
            break

    stop_motor()
    set_servo_angle(default_servo)
    time.sleep(0.3)


def follow_pink_block_to_park(picam2, direction):
    print(f"[park] lap complete -- actively tracking pink block, direction={direction.name}")

    if direction == Direction.RIGHT:
        raw_frame = picam2.capture_array()
        frame = crop_image(raw_frame, 0, CAMERA_PIC_WIDTH, CAMERA_PIC_HEIGHT - PIC_HEIGHT, CAMERA_PIC_HEIGHT)
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        pink_mask = calculate_color_mask(lab, "pink")
        pink_area = cv2.countNonZero(pink_mask)

        if pink_area < PARK_ENTRY_PINK_SEEN_THRESHOLD:
            hardcoded_pink_search_turn(picam2)

    set_motor(1, PARK_SPEED)
    prevang = None
    global prev_wall_error
    prev_wall_error = 0.0
    tracker = ObstacleTracker()

    while True:
        raw_frame = picam2.capture_array()
        frame = crop_image(raw_frame, 0, CAMERA_PIC_WIDTH, CAMERA_PIC_HEIGHT - PIC_HEIGHT, CAMERA_PIC_HEIGHT)
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        pink_mask = calculate_color_mask(lab, "pink")

        blue_mask = calculate_color_mask(lab, "blue")
        orange_mask = calculate_color_mask(lab, "orange")
        green_mask = calculate_color_mask(lab, "green")
        red_mask = calculate_color_mask(lab, "red")

        colormask_image = frame.copy()
        non_wall_mask = cv2.bitwise_or(cv2.bitwise_or(blue_mask, orange_mask),
                                       cv2.bitwise_or(green_mask, red_mask))
        non_wall_mask = cv2.bitwise_or(non_wall_mask, pink_mask)
        colormask_image[non_wall_mask > 0] = (255, 255, 255)

        grayscale_image = cv2.cvtColor(colormask_image, cv2.COLOR_BGR2GRAY)
        blurred_image = cv2.bilateralFilter(grayscale_image, 9, 75, 75)
        _, binary_image = cv2.threshold(blurred_image, GRAY_THRESHOLD, 255, cv2.THRESH_BINARY)
        clean_image = cv2.morphologyEx(binary_image, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))

        polygon_image, polygon_points = draw_polygon(clean_image, clean_image)
        polygon_mask = np.zeros_like(clean_image)
        #if polygon_points is not None:
         #   cv2.fillPoly(polygon_mask, [polygon_points], 255)
          #  cv2.polylines(frame, [polygon_points], True, (0, 0, 255), 2, lineType=cv2.LINE_AA)

        inner_crash = tracker.check_inner_wall_crash(direction, polygon_image, frame)
        outer_crash = tracker.check_outer_wall_crash(direction, polygon_image, frame)

        green_mask_in_polygon = cv2.bitwise_and(green_mask, green_mask, mask=polygon_mask)
        red_mask_in_polygon = cv2.bitwise_and(red_mask, red_mask, mask=polygon_mask)
        pillar_found = tracker.find_closest_pillar(green_mask_in_polygon, red_mask_in_polygon, frame)

        pink_angle, pink_x, pink_y = park_block_angle(direction, pink_mask, frame)

        pillar_is_closer = pillar_found is not None and (
            pink_y is None or pillar_found[1] > pink_y
        )

        if pillar_is_closer:
            p_x, p_y, _actual_is_green = pillar_found
            angle = forced_pillar_angle(p_x, p_y, False, frame)
        elif pink_angle is not None:
            angle = pink_angle
        else:
            wall_angle = wall_follow_angle(polygon_image, direction, frame, damped=inner_crash)
            if outer_crash:
                angle = (MAX_ANGLE - 3) if direction == Direction.LEFT else (MIN_ANGLE + 3)
            else:
                angle = wall_angle

        angle = round(max(MIN_ANGLE, min(MAX_ANGLE, angle)))
        if prevang is None or prevang != angle:
            set_servo_angle(angle)
            prevang = angle

        show_frame(frame)
       # key = cv2.waitKey(1) & 0xFF
      #  if key == ord('q'):
       #     stop_motor()
        #    return

        if pink_x is not None and pink_y is not None:
            aim_x = RIGHT_OBSTACLE_X_THRESHOLD if direction == Direction.LEFT else LEFT_OBSTACLE_X_THRESHOLD
            close_enough = pink_y >= PARK_TARGET_Y
            alongside = abs(pink_x - aim_x) <= PARK_X_TOLERANCE
            if close_enough and alongside:
                print(f"[park] target met (x={pink_x}, y={pink_y}) -- stopping")
                stop_motor()
                wall_follow_park_entry(picam2, direction)
                return


PARK_ENTRY_TARGET_X_LEFT = 0
PARK_ENTRY_TARGET_X_RIGHT = PIC_WIDTH
PARK_ENTRY_TARGET_Y = 280

PARK_ENTRY_KP = 0.7
PARK_ENTRY_KD = 0.07

PARK_ENTRY_FORWARD_DURATION = 3

PARK_ENTRY_PINK_SEEN_THRESHOLD = 50

PARK_ENTRY_FORWARD_TICKS = 2000   # total distance to drive forward during wall-follow, in encoder ticks
PARK_ENTRY_TICK_CHUNK = 40       # how many ticks to drive between each steering re-check


def wall_follow_park_entry(picam2, direction):
    follow_side = Direction.RIGHT if direction == Direction.LEFT else Direction.LEFT
    target_x = (PARK_ENTRY_TARGET_X_LEFT if follow_side == Direction.LEFT
                else PARK_ENTRY_TARGET_X_RIGHT)

    straighten_angle = (default_servo + PARK_ENTRY_STRAIGHTEN_OFFSET if direction == Direction.LEFT
                         else default_servo - PARK_ENTRY_STRAIGHTEN_OFFSET)
    straighten_angle = max(MIN_ANGLE, min(MAX_ANGLE, straighten_angle))
    print(f"[park] straightening nudge toward {direction.name} before wall-follow")
    set_servo_angle(straighten_angle, duration=PARK_ENTRY_STRAIGHTEN_DURATION)
    set_servo_angle(default_servo)

    stop_motor()
    time.sleep(1)

    prevang = None

    def _wallfollow_step(kp, kd):
        nonlocal prevang
        raw_frame = picam2.capture_array()
        frame = crop_image(raw_frame, 0, CAMERA_PIC_WIDTH, CAMERA_PIC_HEIGHT - PIC_HEIGHT, CAMERA_PIC_HEIGHT)
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)

        blue_mask = calculate_color_mask(lab, "blue")
        orange_mask = calculate_color_mask(lab, "orange")
        green_mask = calculate_color_mask(lab, "green")
        red_mask = calculate_color_mask(lab, "red")
        pink_mask = calculate_color_mask(lab, "pink")

        colormask_image = frame.copy()
        non_wall_mask = cv2.bitwise_or(cv2.bitwise_or(blue_mask, orange_mask),
                                       cv2.bitwise_or(green_mask, red_mask))
        non_wall_mask = cv2.bitwise_or(non_wall_mask, pink_mask)
        colormask_image[non_wall_mask > 0] = (255, 255, 255)

        grayscale_image = cv2.cvtColor(colormask_image, cv2.COLOR_BGR2GRAY)
        blurred_image = cv2.bilateralFilter(grayscale_image, 9, 75, 75)
        _, binary_image = cv2.threshold(blurred_image, GRAY_THRESHOLD, 255, cv2.THRESH_BINARY)
        clean_image = cv2.morphologyEx(binary_image, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))

        polygon_image, polygon_points = draw_polygon(clean_image, clean_image)
        #if polygon_points is not None:
         #   cv2.polylines(frame, [polygon_points], True, (0, 0, 255), 2, lineType=cv2.LINE_AA)

        angle = park_wall_follow_angle(
            polygon_image, follow_side, frame,
            target_x, PARK_ENTRY_TARGET_Y, kp, kd,
        )

        angle = round(max(MIN_ANGLE, min(MAX_ANGLE, angle)))
        if prevang is None or prevang != angle:
            set_servo_angle(angle)
            prevang = angle

        show_frame(frame)

    print(f"[park] wall-following {follow_side.name} side, forward, {PARK_ENTRY_FORWARD_DURATION}s")
    global prev_wall_error
    prev_wall_error = 0.0
    set_motor(1, PARK_SPEED)
    end_time = time.time() + PARK_ENTRY_FORWARD_DURATION
    while time.time() < end_time:
        _wallfollow_step(PARK_ENTRY_KP, PARK_ENTRY_KD)

    stop_motor()
    time.sleep(0.3)

    print(f"[park] reversing straight, until pink seen")
    if direction == Direction.LEFT:
        set_servo_angle(default_servo - 3)
    else:
        set_servo_angle(default_servo - 5)
    set_motor(2, PARK_SPEED)

    while True:
        raw_frame = picam2.capture_array()
        frame = crop_image(raw_frame, 0, CAMERA_PIC_WIDTH, CAMERA_PIC_HEIGHT - PIC_HEIGHT, CAMERA_PIC_HEIGHT)
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        pink_mask = calculate_color_mask(lab, "pink")
        pink_area = cv2.countNonZero(pink_mask)

        show_frame(frame)
       # key = cv2.waitKey(1) & 0xFF

      #  if key == ord('q'):
       #     stop_motor()
        #    return

        if pink_area > PARK_ENTRY_PINK_SEEN_THRESHOLD:
            break

    print(f"[park] pink seen again (area={pink_area}) -- finishing park sequence")
    stop_motor()
    time.sleep(1.0)

    if direction == Direction.LEFT:
        set_servo_angle(default_servo - 3)
    else:
        set_servo_angle(default_servo - 3)
    set_motor(1, PARK_SPEED, 1770)
    stop_motor()

    time.sleep(1)

    hard_turn_angle = PARK_MIN_ANGLE if direction == Direction.LEFT else PARK_MAX_ANGLE
    set_servo_angle(hard_turn_angle, min_angle=PARK_MIN_ANGLE, max_angle=PARK_MAX_ANGLE)
    time.sleep(1.0)
    #if direction == Direction.LEFT:
    set_motor(2, 130, 1100)
   # else:
    #    set_motor(2, PARK_SPEED, 1200)
    stop_motor()
    reset_ticks()
    time.sleep(1)
    set_servo_angle(default_servo, min_angle=PARK_MIN_ANGLE, max_angle=PARK_MAX_ANGLE)
    time.sleep(1.0)
   # if direction == Direction.LEFT:
    set_motor(2, 130, 385)
    #else:
     #   set_motor(2, PARK_SPEED, 340)
    stop_motor()
    reset_ticks()
    time.sleep(1)
    hard_turn_angle_1 = PARK_MAX_ANGLE if direction == Direction.LEFT else PARK_MIN_ANGLE
    set_servo_angle(hard_turn_angle_1, min_angle=PARK_MIN_ANGLE, max_angle=PARK_MAX_ANGLE)
    time.sleep(1)
    #if direction == Direction.LEFT:
    set_motor(2, 130, 470)
    #else:
  #  set_motor(2, PARK_SPEED, 655)
    stop_motor()
    reset_ticks()
    time.sleep(1)

    hard_turn_angle_2 = PARK_MIN_ANGLE if direction == Direction.LEFT else PARK_MAX_ANGLE
    set_servo_angle(hard_turn_angle_2, min_angle=PARK_MIN_ANGLE, max_angle=PARK_MAX_ANGLE)
    time.sleep(1)
    #if direction == Direction.LEFT:
    set_motor(1, PARK_SPEED, 95)
    #else:
     #   set_motor(1, PARK_SPEED, 175)
    stop_motor()
    reset_ticks()
    time.sleep(1)
    set_servo_angle(default_servo)
    print("[park] park sequence complete")
    return


def park_wall_follow_angle(polygon_image, follow_side, display_frame, target_x, target_y, kp, kd):
    global prev_wall_error
    h, w = polygon_image.shape[:2]

    cols = range(0, NBR_COLS) if follow_side == Direction.LEFT else range(w - NBR_COLS, w)
    rows = range(h - 3 * NBR_COLS, h - 2 * NBR_COLS)

    y_vals = _find_black_from_bottom(polygon_image, cols)
    x_vals = _find_black_sides(polygon_image, follow_side, rows)

    avg_y = np.mean(y_vals)
    avg_x = np.mean(x_vals)
    if avg_y >= h - 1:
        avg_y = h

    cv2.circle(display_frame, (int(avg_x), int(avg_y)), 8, (0, 0, 255), -1)
    cv2.circle(display_frame, (int(target_x), target_y), 8, (0, 255, 0), -1)

    error_y = target_y - avg_y
    if follow_side == Direction.LEFT:
        error_x = target_x - avg_x
    else:
        error_x = avg_x - target_x
    error = error_y + error_x

    derivative = error - prev_wall_error
    control = (kp * error) + (kd * derivative)
    prev_wall_error = error

    turn_sign = 1 if follow_side == Direction.LEFT else -1
    angle = default_servo + turn_sign * control
    angle = max(MIN_ANGLE, min(MAX_ANGLE, angle))
    return angle


CAMERA_WARMUP_DURATION = 1.5


def camera_warmup(picam2):
    end_time = time.time() + CAMERA_WARMUP_DURATION
    while time.time() < end_time:
        raw_frame = picam2.capture_array()
        frame = crop_image(raw_frame, 0, CAMERA_PIC_WIDTH, CAMERA_PIC_HEIGHT - PIC_HEIGHT, CAMERA_PIC_HEIGHT)
        show_frame(frame)
      #  cv2.waitKey(1)


def main():
    picam2 = Picamera2()
    sensor_mode = picam2.sensor_modes[1]
    sensor_width, sensor_height = sensor_mode["size"]
    config = picam2.create_video_configuration(
        raw={"size": (sensor_width, sensor_height)},
        main={"format": "RGB888", "size": (CAMERA_PIC_WIDTH, CAMERA_PIC_HEIGHT)},
        controls={"FrameRate": 30}
    )
    picam2.configure(config)
    picam2.start()

    camera_warmup(picam2)

    exit_direction = detect_exit_direction(picam2)
    exit_parallel_park(exit_direction, picam2)

    set_motor(1, DRIVE_SPEED)

    run(picam2, exit_direction)


def move_ticks(direction, speed, ticks, timeout=11.0):
    direction = max(0, min(2, int(direction)))
    speed = max(0, min(255, int(speed)))
    ticks = int(abs(ticks))

    ser.reset_input_buffer()
    ser.write(f"MOVE,{direction},{speed},{ticks}\n".encode())

    deadline = time.time() + timeout
    while time.time() < deadline:
        line = ser.readline().decode(errors="ignore").strip()
        if not line:
            continue
        if line.startswith("DONE"):
            parts = line.split(",")
            moved = int(parts[1]) if len(parts) > 1 else None
            if len(parts) > 2 and parts[2] == "TIMEOUT":
                print(f"[move_ticks] hit Nano-side timeout after {moved} ticks (wanted {ticks})")
            return moved
    print(f"[move_ticks] WARNING: no DONE reply within {timeout}s")
    return None


def reset_ticks():
    ser.reset_input_buffer()
    ser.write(b"RESET\n")
    ser.readline()


def run(picam2, direction):
    tracker = ObstacleTracker()
    lap_tracker = LapTracker()
    prevang = None
    prevspeed = DRIVE_SPEED
    set_servo_angle(default_servo)

    # once quarter_lap_count hits TOTAL_TURNS (the 12th quarter) on a RIGHT run,
    # start a grace timer. For FORCE_PILLAR_DELAY seconds, everything runs
    # completely normally (crash-state machine, wall-follow, colored pillar
    # avoidance). After that window elapses, every pillar found is forced to be
    # treated as if it were on the right (i.e. "red"-style avoidance), regardless
    # of its actual detected color, so the final extra quarter-turn is always
    # consistent going into perform_u_turn_to_pink().
    right_final_turn_start_time = None
    FORCE_PILLAR_DELAY = 0.35  # seconds
    turn_accum_angle = default_servo

    while True:
        raw_frame = picam2.capture_array()
        latest = _process_frame(raw_frame)

        frame = latest["frame"].copy()
        blue_mask = latest["blue_mask"]
        orange_mask = latest["orange_mask"]
        green_mask = latest["green_mask"]
        red_mask = latest["red_mask"]
        polygon_image = latest["polygon_image"]
        polygon_mask = latest["polygon_mask"]
        polygon_points = latest["polygon_points"]
        blue_area = cv2.countNonZero(cv2.bitwise_and(blue_mask, blue_mask, mask=polygon_mask))
        orange_area = cv2.countNonZero(cv2.bitwise_and(orange_mask, orange_mask, mask=polygon_mask))

        if polygon_points is not None:
           # cv2.polylines(frame, [polygon_points], True, (0, 0, 255), 2, lineType=cv2.LINE_AA)
            roi_left, roi_right = get_wall_rois(direction)
            draw_debug_rois(frame, [roi_left, roi_right])
            _dbg_l = _largest_wall_contour_area(polygon_image, roi_left)
            _dbg_r = _largest_wall_contour_area(polygon_image, roi_right)
            cv2.putText(frame, f"L={_dbg_l} R={_dbg_r}", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        lap_tracker.process_image(blue_mask, orange_mask, direction, polygon_mask)

        turns_needed = TOTAL_TURNS + 1 if direction == Direction.RIGHT else TOTAL_TURNS
        laps_complete = lap_tracker.quarter_lap_count >= turns_needed

        if laps_complete:
            if direction == Direction.RIGHT:
                print("[park] extra quarter complete -- U-turning to find pink")
                stop_motor()
                perform_u_turn_to_pink(picam2)
            else:
                print("[park] last turn fully completed -- switching to "
                      "active pink-block tracking")

            follow_pink_block_to_park(picam2, Direction.LEFT)
            break

        # mark the moment the 12th quarter completes (RIGHT direction only)
        if (direction == Direction.RIGHT
                and right_final_turn_start_time is None
                and lap_tracker.quarter_lap_count >= TOTAL_TURNS):
            right_final_turn_start_time = time.time()
            print("[park] 12th quarter done -- 0.5s grace period before forcing "
                  "right-side pillar avoidance")

        force_pillar_mode = (
            right_final_turn_start_time is not None
            and (time.time() - right_final_turn_start_time) >= FORCE_PILLAR_DELAY
        )

        green_mask_in_polygon = cv2.bitwise_and(green_mask, green_mask, mask=polygon_mask)
        red_mask_in_polygon = cv2.bitwise_and(red_mask, red_mask, mask=polygon_mask)

        obstacle_angle = tracker.obstacle_angle(
            direction, green_mask_in_polygon, red_mask_in_polygon, polygon_image, frame,
            laps_complete=laps_complete, force_right_avoid=force_pillar_mode
        )
        wall_angle = area_based_wall_follow_angle(
            polygon_image, direction, blue_area=blue_area, orange_area=orange_area,
            damped=tracker.inner_wall_warning
        )

        final_angle = obstacle_angle if obstacle_angle is not None else wall_angle

        if tracker.post_pass_frames > 0:
            final_angle = max(default_servo - POST_PASS_MAX_OFFSET,
                               min(final_angle, default_servo + POST_PASS_MAX_OFFSET))
            tracker.post_pass_frames -= 1

        angle = round(max(MIN_ANGLE, min(MAX_ANGLE, final_angle)))

        if prevang is None or prevang != angle:
            set_servo_angle(angle)
            prevang = angle

        is_avoiding_obstacle = obstacle_angle is not None
        target_speed = OBSTACLE_SPEED if is_avoiding_obstacle else DRIVE_SPEED
        if target_speed != prevspeed:
            set_motor(1, target_speed)
            prevspeed = target_speed

        show_frame(frame)
      #  key = cv2.waitKey(1) & 0xFF
       # if key == ord('q'):
         #   stop_motor()
         #   break

    picam2.stop()
    cv2.destroyAllWindows()
    ser.close()


if __name__ == "__main__":
    print("running")
    print("Waiting for button press...")
    while GPIO.input(BUTTON_PIN) == GPIO.HIGH:
        LED(16).on()
        time.sleep(0.0)
    print("Start")
    main()

