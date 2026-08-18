import cv2
import math
import numpy as np
import serial
import time
import threading
from enum import Enum
from picamera2 import Picamera2
import RPi.GPIO as GPIO
from gpiozero import LED


ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
time.sleep(2)

LAPS_TARGET = 3
TOTAL_TURNS = LAPS_TARGET * 4

DRIVE_SPEED = 200
OBSTACLE_SPEED = 255
PARK_SPEED = 100

BUTTON_PIN = 26

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def set_servo_angle(angle, duration=0.0, resend_interval=0.03):
    angle = max(MIN_ANGLE, min(MAX_ANGLE, angle))
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

BLUE_LOWER = np.array([40, 109, 76])
BLUE_UPPER = np.array([115, 174, 109])

ORANGE_LOWER = np.array([101, 128, 151])
ORANGE_UPPER = np.array([166, 164, 188])

GREEN_LOWER = np.array([50, 64, 111])
GREEN_UPPER = np.array([125, 117, 154])

RED_LOWER = np.array([53, 162, 139])
RED_UPPER = np.array([116, 196, 166])

PINK_LOWER = np.array([40, 153, 121])
PINK_UPPER = np.array([109, 179, 142])

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
EXIT_CONFIRM_FRAMES_LEFT = 6
EXIT_CONFIRM_FRAMES_RIGHT = 2
TURN_MIN_DURATION_LEFT = 1.0
TURN_MIN_DURATION_RIGHT = 0.0
TURN_MAX_DURATION = 4.0
TURN_COOLDOWN = 1.25


# =========================================================================
# DISPLAY -- one persistent window, updated by a dedicated thread that does
# NOTHING but render whatever frame was most recently handed to it. This
# thread never feeds anything back into the control loop -- run() and every
# parking function stay fully synchronous (capture -> process -> decide ->
# send command, one frame at a time). The only thing shared is the frame
# reference itself, so the display can never stall steering/motor timing
# the way calling cv2.imshow()/cv2.waitKey() directly in the control loop
# did.
# =========================================================================
_display_frame = None
_display_lock = threading.Lock()
_display_stop = threading.Event()


def set_display_frame(frame):
    global _display_frame
    with _display_lock:
        _display_frame = frame


def _display_loop():
    while not _display_stop.is_set():
        with _display_lock:
            frame = _display_frame
        if frame is not None:
            cv2.imshow("frame", frame)
        cv2.waitKey(1)


def start_display():
    thread = threading.Thread(target=_display_loop, daemon=True)
    thread.start()
    return thread


def stop_display(thread):
    _display_stop.set()
    thread.join()
    cv2.destroyAllWindows()


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


default_servo = 90
max_turn_degree = 60
STEER_SIGN = -1
MIN_ANGLE = default_servo - max_turn_degree
MAX_ANGLE = default_servo + max_turn_degree


def to_physical_angle(logical_angle):
    if STEER_SIGN == -1:
        return int(round(2 * default_servo - logical_angle))
    return int(round(logical_angle))


TARGET_X_LEFT = 0
TARGET_X_RIGHT = PIC_WIDTH
TARGET_Y = 220

Kp_wall = 0.35
Kd_wall = 0.1
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


LEFT_OBSTACLE_X_THRESHOLD = 0
RIGHT_OBSTACLE_X_THRESHOLD = PIC_WIDTH - LEFT_OBSTACLE_X_THRESHOLD
OBJECT_LINE_ANGLE_THRESHOLD = 45
GREEN_OBSTACLE_KP = 1.35
RED_OBSTACLE_KP = 1.35

TOO_LOW_Y = PIC_HEIGHT - 35
TOO_CLOSE_Y = PIC_HEIGHT - 20

CRASH_POINT_COLOR = (255, 0, 0)

PILLAR_AREA_THRESHOLD = 200

INNER_CRASH_KP = 0.15
INNER_CRASH_KD = 0.0


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

    def check_inner_wall_crash(self, direction, polygon_image, display_frame):
        if direction == Direction.RIGHT:
            detection_points = [
                (PIC_HEIGHT - 130, PIC_WIDTH - 200),
                (PIC_HEIGHT - 100, PIC_WIDTH - 175),
                (PIC_HEIGHT - 70, PIC_WIDTH - 150),
            ]
        else:
            detection_points = [
                (PIC_HEIGHT - 130, 200),
                (PIC_HEIGHT - 100, 175),
                (PIC_HEIGHT - 70, 150),
            ]
        crashed = False
        for y, x in detection_points:
            in_bounds = 0 <= y < PIC_HEIGHT and 0 <= x < PIC_WIDTH
            point_crashed = in_bounds and polygon_image[y, x] == 0
            if point_crashed:
                crashed = True
            if in_bounds:
                cv2.circle(display_frame, (x, y), 5, CRASH_POINT_COLOR, -1)
        return crashed

    def check_outer_wall_crash(self, direction, polygon_image, display_frame):
        detection_points = [(PIC_WIDTH // 2, PIC_HEIGHT - 130)]
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
                       laps_complete=False):
        self.inner_wall_warning = False
        self.last_pillar_y = None
        inner_crash = self.check_inner_wall_crash(direction, polygon_image, display_frame)
        outer_crash = self.check_outer_wall_crash(direction, polygon_image, display_frame)

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
            if not inner_crash:
                self.state = CrashState.NONE
            else:
                self.inner_wall_warning = True
                return None
        elif self.state == CrashState.OUTER:
            if not outer_crash:
                self.state = CrashState.NONE
            else:
                return turn_into_corner

        found = self.find_closest_pillar(green_mask, red_mask, display_frame)
        if found is None:
            return None
        x_center, y_center, is_green = found
        self.last_pillar_y = y_center

        if y_center > TOO_LOW_Y:
            if y_center > TOO_CLOSE_Y:
                return None
            return self.old_angle

        if is_green:
            if laps_complete:
                self.last_color = "green"
            cv2.line(display_frame, (x_center, y_center), (RIGHT_OBSTACLE_X_THRESHOLD, PIC_HEIGHT), (0, 255, 0), 2)
            rad_angle = np.arctan2(y_center - PIC_HEIGHT, x_center - RIGHT_OBSTACLE_X_THRESHOLD)
        else:
            if laps_complete:
                self.last_color = "red"
            cv2.line(display_frame, (x_center, y_center), (LEFT_OBSTACLE_X_THRESHOLD, PIC_HEIGHT), (0, 0, 255), 2)
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
    away_angle = MAX_ANGLE if direction == Direction.LEFT else MIN_ANGLE
    toward_angle = MIN_ANGLE if direction == Direction.LEFT else MAX_ANGLE

    print(f"[park] exiting, direction={direction.name}")

    set_servo_angle(away_angle)
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
            set_servo_angle(away_angle)
            set_motor(1, PARK_SPEED, 1100)
            stop_motor()
            time.sleep(1)
            set_servo_angle(toward_angle)
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
            set_servo_angle(toward_angle)
            time.sleep(1)
            set_motor(1, PARK_SPEED, 900)
            time.sleep(1)
            set_servo_angle(default_servo)
            time.sleep(1)
            set_motor(2, PARK_SPEED, 2300)
    if direction == Direction.RIGHT:
        if seen_color == "red":
            set_servo_angle(away_angle)
            set_motor(1, PARK_SPEED, 1150)
            stop_motor()
            time.sleep(1)
            set_servo_angle(toward_angle)
            time.sleep(1)
            set_motor(1, PARK_SPEED, 2750)
            stop_motor()
            time.sleep(1)
        else:
            stop_motor()
            time.sleep(1)
            set_servo_angle(toward_angle)
            time.sleep(1)
            set_motor(1, PARK_SPEED, 1200)
            time.sleep(1)

    set_servo_angle(default_servo)
    print("[park] exit complete, handing off to obstacle run()")


PARK_TARGET_Y = PIC_HEIGHT - 75
PARK_X_TOLERANCE = 80

PARK_LINE_ANGLE_THRESHOLD = 45
PARK_OBSTACLE_KP = 2.0

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
    aim_x = RIGHT_OBSTACLE_X_THRESHOLD if is_green else LEFT_OBSTACLE_X_THRESHOLD
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
        servo_angle = default_servo - ((object_angle_deg + PARK_LINE_ANGLE_THRESHOLD) * PARK_OBSTACLE_KP)
    else:
        servo_angle = default_servo - ((object_angle_deg - PARK_LINE_ANGLE_THRESHOLD) * PARK_OBSTACLE_KP)

    servo_angle = max(MIN_ANGLE, min(MAX_ANGLE, servo_angle))
    return servo_angle, x_center, y_center


PARK_ENTRY_STRAIGHTEN_OFFSET = 20
PARK_ENTRY_STRAIGHTEN_DURATION = 0.5

U_TURN_SPEED = 100
U_TURN_PINK_SEEN_THRESHOLD = 500
U_TURN_MAX_DURATION = 8.0


def perform_u_turn_to_pink(picam2):
    print("[park] U-turning left to find pink")
    set_servo_angle(MAX_ANGLE)
    set_motor(1, U_TURN_SPEED)

    start_time = time.time()
    while True:
        raw_frame = picam2.capture_array()
        frame = crop_image(raw_frame, 0, CAMERA_PIC_WIDTH, CAMERA_PIC_HEIGHT - PIC_HEIGHT, CAMERA_PIC_HEIGHT)
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        pink_mask = calculate_color_mask(lab, "pink")
        pink_area = cv2.countNonZero(pink_mask)

        set_display_frame(frame)

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
        if polygon_points is not None:
            cv2.fillPoly(polygon_mask, [polygon_points], 255)
            cv2.polylines(frame, [polygon_points], True, (0, 0, 255), 2, lineType=cv2.LINE_AA)

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

        set_display_frame(frame)

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
PARK_ENTRY_TARGET_Y = 270

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

    def _wallfollow_step(motor_dir, kp, kd, ticks):
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
        if polygon_points is not None:
            cv2.polylines(frame, [polygon_points], True, (0, 0, 255), 2, lineType=cv2.LINE_AA)

        angle = park_wall_follow_angle(
            polygon_image, follow_side, frame,
            target_x, PARK_ENTRY_TARGET_Y, kp, kd,
        )
        if motor_dir == 2:
            angle = 2 * (default_servo - 3) - angle

        angle = round(max(MIN_ANGLE, min(MAX_ANGLE, angle)))
        if prevang is None or prevang != angle:
            set_servo_angle(angle)
            prevang = angle

        moved = set_motor(motor_dir, PARK_SPEED, ticks)
        set_display_frame(frame)

        return moved

    print(f"[park] wall-following {follow_side.name} side, forward, {PARK_ENTRY_FORWARD_TICKS} ticks")
    global prev_wall_error
    prev_wall_error = 0.0
    ticks_done = 0
    while ticks_done < PARK_ENTRY_FORWARD_TICKS:
        chunk = min(PARK_ENTRY_TICK_CHUNK, PARK_ENTRY_FORWARD_TICKS - ticks_done)
        moved = _wallfollow_step(1, PARK_ENTRY_KP, PARK_ENTRY_KD, chunk)
        ticks_done += moved if moved is not None else chunk

    stop_motor()
    time.sleep(0.3)

    print(f"[park] reversing straight, until pink seen")
    if direction == Direction.LEFT:
        set_servo_angle(default_servo - 4)
    else:
        set_servo_angle(default_servo - 5)
    set_motor(2, PARK_SPEED)

    while True:
        raw_frame = picam2.capture_array()
        frame = crop_image(raw_frame, 0, CAMERA_PIC_WIDTH, CAMERA_PIC_HEIGHT - PIC_HEIGHT, CAMERA_PIC_HEIGHT)
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        pink_mask = calculate_color_mask(lab, "pink")
        pink_area = cv2.countNonZero(pink_mask)

        set_display_frame(frame)

        if pink_area > PARK_ENTRY_PINK_SEEN_THRESHOLD:
            break

    print(f"[park] pink seen again (area={pink_area}) -- finishing park sequence")
    stop_motor()
    time.sleep(1.0)

    if direction == Direction.LEFT:
        set_servo_angle(default_servo - 2)
    else:
        set_servo_angle(default_servo - 3)
    set_motor(1, PARK_SPEED, 1850)
    stop_motor()

    time.sleep(1)

    hard_turn_angle = MIN_ANGLE if direction == Direction.LEFT else MAX_ANGLE
    set_servo_angle(hard_turn_angle)
    time.sleep(1.0)
    if direction == Direction.LEFT:
        set_motor(2, PARK_SPEED, 1100)
    else:
        set_motor(2, PARK_SPEED, 1200)
    stop_motor()
    time.sleep(1)
    set_servo_angle(default_servo)
    time.sleep(1.0)
    if direction == Direction.LEFT:
        set_motor(2, PARK_SPEED, 315)
    else:
        set_motor(2, PARK_SPEED, 340)
    stop_motor()
    time.sleep(1)
    hard_turn_angle_1 = MAX_ANGLE if direction == Direction.LEFT else MIN_ANGLE
    set_servo_angle(hard_turn_angle_1)
    time.sleep(1)
    if direction == Direction.LEFT:
        set_motor(2, PARK_SPEED, 650)
    else:
        set_motor(2, PARK_SPEED, 655)
    stop_motor()
    time.sleep(1)

    hard_turn_angle_2 = MIN_ANGLE if direction == Direction.LEFT else MAX_ANGLE
    set_servo_angle(hard_turn_angle_2)
    time.sleep(1)
    if direction == Direction.LEFT:
        set_motor(1, PARK_SPEED, 95)
    else:
        set_motor(1, PARK_SPEED, 175)
    stop_motor()

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
        set_display_frame(frame)


def main():
    display_thread = start_display()

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

    run(picam2, exit_direction, display_thread)


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


def run(picam2, direction, display_thread):
    tracker = ObstacleTracker()
    lap_tracker = LapTracker()
    prevang = None
    prevspeed = DRIVE_SPEED
    set_servo_angle(default_servo)

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

        if polygon_points is not None:
            cv2.polylines(frame, [polygon_points], True, (0, 0, 255), 2, lineType=cv2.LINE_AA)

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

        green_mask_in_polygon = cv2.bitwise_and(green_mask, green_mask, mask=polygon_mask)
        red_mask_in_polygon = cv2.bitwise_and(red_mask, red_mask, mask=polygon_mask)

        obstacle_angle = tracker.obstacle_angle(
            direction, green_mask_in_polygon, red_mask_in_polygon, polygon_image, frame,
            laps_complete=laps_complete
        )
        wall_angle = wall_follow_angle(
            polygon_image, direction, frame, damped=tracker.inner_wall_warning
        )
        final_angle = obstacle_angle if obstacle_angle is not None else wall_angle
        angle = round(max(MIN_ANGLE, min(MAX_ANGLE, final_angle)))

        if prevang is None or prevang != angle:
            set_servo_angle(angle)
            prevang = angle

        is_avoiding_obstacle = obstacle_angle is not None
        target_speed = OBSTACLE_SPEED if is_avoiding_obstacle else DRIVE_SPEED
        if target_speed != prevspeed:
            set_motor(1, target_speed)
            prevspeed = target_speed

        set_display_frame(frame)

    picam2.stop()
    stop_display(display_thread)
    ser.close()


if __name__ == "__main__":
    print("running")
    print("Waiting for button press...")
    while GPIO.input(BUTTON_PIN) == GPIO.HIGH:
        LED(16).on()
        time.sleep(0.0)
    print("Start")
    main()