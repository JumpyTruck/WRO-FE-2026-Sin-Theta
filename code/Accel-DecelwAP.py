"""
Obstacle challenge, merged:
  - Wall following: single-side "lowest wall point" PD tracker + dynamic
    target point, rescaled onto THIS robot's servo range (default_servo /
    max_turn_degree / STEER_SIGN below).
  - Polygon detection + red border: ported like the reference repo's
    ImageDrawingUtils.find_contour + draw_polygon.
  - Color detection: HSV/Lab masks as plain module-level constants + a
    function -- no color-utility class.
  - Pillar detection + avoidance: always finds the single red-or-green
    blob whose center is closest to the robot's bottom-center point, no
    ROI restriction, no minimum-y gate.
  - Crash avoidance: ported from the reference repo's CrashStates state
    machine.
      * OUTER crash (wall dead ahead) is a hard override: steer straight
        into the turn direction until the front dot clears.
      * INNER crash (riding too close to the side wall) is NOT a hard
        override. It sets `inner_wall_warning`, which tells wall-follow
        to swap its kp/kd to a fixed low pair (0.1 / 0) instead of being
        replaced by a fixed angle -- same as the reference repo. This
        keeps the steering command a continuous function of the live
        wall-scan the whole time, so there's no discontinuity/cold-start
        lag the instant the crash clears and pillar search resumes --
        which is what was causing the "goes straight, then suddenly
        turns" behavior near corners.
      * Pillar search is skipped only on frames where a crash state is
        currently active (same as the reference), and resumes on the
        very same frame a crash state clears -- no extra confirm delay.
      * Crash-point coordinates below are the retuned values (2026-08-04):
        inner points pulled higher up the frame (earlier warning), outer
        point collapsed to a single straight-ahead point shared by both
        directions.
        Updated 2026-08-05: ObstacleTracker's crash-point logic was
        re-pulled from the later "session 3" reference version. The
        OUTER crash point and RIGHT-direction INNER crash points were
        unchanged, but the LEFT-direction INNER crash points moved from
        (445, 470, 495) to (225, 200, 175) -- and ObstacleTracker now
        also carries `self.last_color`, set from `obstacle_angle`'s new
        `laps_complete` parameter, ported straight from that same
        reference (used there to remember which color pillar was passed
        last, for end-of-run parking logic). `run()` now computes
        `laps_complete` from the lap tracker and threads it into the
        `obstacle_angle` call so that tracking works, while the
        DRIVE_SPEED/OBSTACLE_SPEED switching from the previous version is
        left untouched.
  - Lap counting (2026-08-04, swapped in): no longer the color-SEQUENCE
    LapTracker (blue-then-orange / orange-then-blue). Instead, ported
    from the corner/turn hysteresis state machine: the robot only ever
    watches ONE marker color -- BLUE if going LEFT, ORANGE if going
    RIGHT -- masked against the current track polygon (not a fixed ROI
    box). Entry/exit uses TWO area thresholds with a dead-band between
    them (LINE_AREA_ENTER_THRESHOLD higher, LINE_AREA_EXIT_THRESHOLD
    lower), each confirmed over several consecutive frames
    (ENTRY_CONFIRM_FRAMES / EXIT_CONFIRM_FRAMES), plus a
    TURN_MIN_DURATION / TURN_MAX_DURATION window and a TURN_COOLDOWN
    afterward so one physical corner marker can't get counted twice.
    Pure counter -- does not touch steering.
  - Parking exit (2026-08-04): before the main lap-following loop starts,
    detect_exit_direction() looks at which half of the frame (left vs
    right) has more open floor and picks a direction; exit_parallel_park()
    then runs a fixed steer/forward/reverse sequence to clear the parking
    space, steering toward the open side. Symmetric for both directions.
    The direction picked here is now threaded through into run() (see
    2026-08-04 fix below) instead of being discarded.
  - Motor/servo serial link (2026-08-04): the Nano firmware speaks a
    plain-text protocol -- "SERVO,<angle>", "MOTOR,<dir>,<speed>", and
    "STOP" -- instead of magic sentinel integers, so the Pi can command
    an explicit motor speed. Replaced the old motor_command_queue /
    servo_angle_queue / motor_drive() / servo_move() thread machinery
    with three direct serial-write functions: set_servo_angle(),
    set_motor(), and stop_motor().
  - Obstacle-aware speed (2026-08-04, new): DRIVE_SPEED is now the
    normal cruising speed used whenever the robot is just wall-following
    with no pillar/crash override active. OBSTACLE_SPEED is a separate,
    higher speed sent for every frame where `obstacle_angle` (the
    crash/pillar override) is not None -- i.e. the robot is actively
    steering around a pillar or riding out a crash-avoidance turn. run()
    now tracks the last speed sent (`prevspeed`, mirroring the existing
    `prevang` pattern for the servo) and only re-sends MOTOR when the
    speed actually needs to flip, so it switches back and forth between
    the two speeds exactly in step with obstacle detection instead of
    being fixed once before the loop starts.
  - End-of-run park (2026-08-05, v3): the pink parking bay sits where the
    LAST corner of the course would normally turn. So the instant
    lap_tracker detects the ENTRY marker for what would be that final
    corner (quarter_lap_count == TOTAL_TURNS - 1 and its state flips to
    "turning"), run() abandons normal wall-follow/crash-avoidance/lap-
    counting entirely and:
      1. peek_toward_parking_spot() -- a brief, purely time-based nudge:
         steers slightly toward `direction` (left if Direction.LEFT,
         right if Direction.RIGHT) while driving forward at
         PARK_PEEK_SPEED for PARK_PEEK_DURATION seconds, just enough to
         swing the camera so the bay actually comes into view.
      2. follow_pink_block_to_park() takes over, actively tracking the
         pink block every frame (same closest-blob technique
         ObstacleTracker uses for red/green pillars) at
         PARK_APPROACH_SPEED, steering to keep the block on the robot's
         LEFT if `direction` is Direction.LEFT or on its RIGHT if
         Direction.RIGHT, until the block's bounding-box area crosses
         PARK_TARGET_AREA ("target met"), then stops.
    Step 1 is the only fixed-time piece; step 2 is fully vision-driven.

HSV/Lab ranges below are tuned for the actual track/lighting. GRAY_THRESHOLD,
kp/kd, and the crash-point offsets may still need further tuning.

=========================================================================
SERVO-INVERSION FIX (2026-07-29)
=========================================================================
The servo horn/linkage was remounted upside down, so a raw PWM angle that
used to steer the wheels RIGHT now physically steers them LEFT, and vice
versa. Rather than touch any of the steering math (PD control, crash
avoidance targets, pillar avoidance all still reason in the ORIGINAL
convention: MIN_ANGLE steers right, MAX_ANGLE steers left), the fix
mirrors the final angle around `default_servo` at the one and only point
it's handed to the hardware -- see `to_physical_angle()` and its use
inside `set_servo_angle()`. Since MIN_ANGLE = default_servo -
max_turn_degree and MAX_ANGLE = default_servo + max_turn_degree, mirroring
around the center exactly swaps MIN_ANGLE <-> MAX_ANGLE, so the whole
valid range maps onto itself -- no extra clamping needed.

If the servo ever gets remounted right-side up again, just flip
STEER_SIGN back to 1 and this correction switches off automatically.

=========================================================================
DIRECTION-THREADING FIX (2026-08-04)
=========================================================================
detect_exit_direction() picks LEFT or RIGHT based on which side of the
parking bay has more open floor, and exit_parallel_park() steers using
that value -- but previously run() ignored it entirely and hardcoded
`direction = Direction.LEFT` for the whole lap-following loop. That
meant crash points, wall-follow side, and the lap-counter marker color
never actually flipped to RIGHT no matter what parking-exit detected.
Fixed by having main() pass `exit_direction` into run(), which now takes
`direction` as a parameter instead of hardcoding it.
"""

import cv2
import math
import numpy as np
import serial
import time
from enum import Enum
from picamera2 import Picamera2

# =========================================================================
# ESP32 / MOTOR SERIAL
# =========================================================================
ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
time.sleep(2)

LAPS_TARGET = 3
TOTAL_TURNS = LAPS_TARGET * 4   # 4 corners per lap

# ---- speeds -------------------------------------------------------------
# Normal cruising speed used while wall-following with no obstacle
# override active.
DRIVE_SPEED = 200
# Speed used for every frame where the crash/pillar override
# (obstacle_angle) is actively steering the robot around something.
OBSTACLE_SPEED = 255


# =========================================================================
# SERIAL COMMAND FUNCTIONS
# =========================================================================
# The Nano understands three plain-text commands, one per line:
#   SERVO,<angle>          angle = 0-180 (physical/PWM angle)
#   MOTOR,<dir>,<speed>    dir = 0 stop / 1 forward / 2 backward, speed 0-255
#   STOP                   immediately coasts the motor (servo untouched)
# =========================================================================

def set_servo_angle(angle, duration=0.0, resend_interval=0.03):
    """
    Move the servo to `angle`, given in this file's LOGICAL angle
    convention (MIN_ANGLE = right, MAX_ANGLE = left). The physical-mount
    correction (to_physical_angle) is applied here, once, right before
    the value goes on the wire -- every other function in this file can
    keep reasoning in the logical convention.

    If duration <= 0 (default): sends the angle once and returns
    immediately -- use this for the normal per-frame steering updates in
    run().

    If duration > 0: keeps re-sending the same angle every
    `resend_interval` seconds until `duration` seconds have elapsed
    before returning. Useful for maneuvers (e.g. parking) where you want
    the servo held at an angle for a fixed time.
    """
    angle = max(MIN_ANGLE, min(MAX_ANGLE, angle))
    physical_angle = to_physical_angle(angle)

    if duration <= 0:
        ser.write(f"SERVO,{physical_angle}\n".encode())
        return

    end_time = time.time() + duration
    while time.time() < end_time:
        ser.write(f"SERVO,{physical_angle}\n".encode())
        time.sleep(resend_interval)


def set_motor(direction, speed):
    """
    Set motor direction and speed directly.
      direction: 0 = stop/coast, 1 = forward, 2 = backward
      speed: 0-255 PWM duty cycle
    """
    direction = max(0, min(2, int(direction)))
    speed = max(0, min(255, int(speed)))
    ser.write(f"MOTOR,{direction},{speed}\n".encode())


def stop_motor():
    """Immediately coast/stop the motor. Does not touch the servo."""
    ser.write("STOP\n".encode())


# =========================================================================
# CAMERA / FRAME GEOMETRY
# =========================================================================
CAMERA_PIC_WIDTH = 640
CAMERA_PIC_HEIGHT = 360
PIC_WIDTH = 640
PIC_HEIGHT = 280

GRAY_THRESHOLD = 80

# ---- lap-counting marker thresholds (masked-pixel count of the
# direction-relevant line within the track polygon) --------------------
LINE_AREA_ENTER_THRESHOLD = 150
LINE_AREA_EXIT_THRESHOLD = 60

# =========================================================================
# LAB COLOR RANGES -- L: 0-255 (lightness), a: 0-255 (green<-128->red),
# b: 0-255 (blue<-128->yellow). Retune against your actual track/camera.
# =========================================================================
BLUE_LOWER = np.array([42, 128, 90])
BLUE_UPPER = np.array([140, 149, 127])

ORANGE_LOWER = np.array([65, 131, 136])
ORANGE_UPPER = np.array([255, 159, 255])

GREEN_LOWER = np.array([0, 98, 0])
GREEN_UPPER = np.array([116, 122, 255])

# red = high 'a' channel (no hue wraparound issue like HSV had, so
# just one range now instead of two)
RED_LOWER = np.array([24, 148, 142])
RED_UPPER = np.array([148, 182, 166])

# pink = the end-of-run parking-bay marker. UNTUNED PLACEHOLDER -- sample
# the actual bay marker against your camera/lighting and retune, same
# way BLUE/ORANGE/GREEN/RED above were tuned.
PINK_LOWER = np.array([40, 153, 121])
PINK_UPPER = np.array([109, 179, 142])

MASK_CLEAN_KERNEL = np.ones((5, 5), np.uint8)


def calculate_color_mask(lab_img, color):
    """Returns a clean single-channel 0/255 mask for one of:
    "blue", "orange", "green", "red", "pink"."""
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
    LEFT = -1    # counterclockwise: robot follows the left wall, turns left at corners
    RIGHT = 1    # clockwise: robot follows the right wall, turns right at corners


# =========================================================================
# LAP / TURN COUNTER -- corner/turn hysteresis state machine (swapped in
# 2026-08-04, replacing the old color-sequence LapTracker). Pure counter,
# does not touch steering at all. Direction-aware: LEFT only ever watches
# BLUE, RIGHT only ever watches ORANGE, masked against the live track
# polygon so a stray patch of color outside the track can't trip it.
# Two area thresholds with a dead-band between them (enter high, exit
# low), each confirmed over several consecutive frames, plus a min/max
# turn duration and a cooldown afterward, prevent one physical corner
# marker from being counted twice.
# =========================================================================
ENTRY_CONFIRM_FRAMES = 3
EXIT_CONFIRM_FRAMES = 6
TURN_MIN_DURATION = 1.0
TURN_MAX_DURATION = 4.0
TURN_COOLDOWN = 1.5


class LapTracker:
    """
    Counts quarter-laps (corners) by watching the single direction-
    relevant marker color's masked pixel area (within the current track
    polygon) cross an ENTER threshold, holding for at least
    TURN_MIN_DURATION (or at most TURN_MAX_DURATION as a fallback), then
    confirming the marker has cleared below an EXIT threshold for
    EXIT_CONFIRM_FRAMES frames before counting the corner and starting a
    TURN_COOLDOWN before the next one can be detected.
    """

    def __init__(self):
        self.state = "idle"
        self.quarter_lap_count = 0
        self._confirm_count = 0
        self._exit_confirm_count = 0
        self._turn_start_time = 0.0
        self._cooldown_until = 0.0

    def process_image(self, blue_mask, orange_mask, direction, polygon_mask):
        """
        Mask the single direction-relevant marker color against the
        current track polygon and advance the entry/exit state machine.
        """
        now = time.time()
        marker_mask = blue_mask if direction == Direction.LEFT else orange_mask
        marker_mask = cv2.bitwise_and(marker_mask, marker_mask, mask=polygon_mask)
        marker_area = cv2.countNonZero(marker_mask)

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
                turn_elapsed >= TURN_MIN_DURATION and self._exit_confirm_count >= EXIT_CONFIRM_FRAMES
            ) or (turn_elapsed >= TURN_MAX_DURATION)
            if should_exit:
                self.quarter_lap_count += 1
                print(f"[lap] quarter-lap {self.quarter_lap_count}/{TOTAL_TURNS} "
                      f"({self.quarter_lap_count // 4} lap(s) + {self.quarter_lap_count % 4} quarter(s))")
                self.state = "idle"
                self._cooldown_until = now + TURN_COOLDOWN
                self._confirm_count = 0
                self._exit_confirm_count = 0


# =========================================================================
# SERVO / STEERING CALIBRATION
# =========================================================================
default_servo = 90
max_turn_degree = 50
STEER_SIGN = -1
MIN_ANGLE = default_servo - max_turn_degree   # original convention: MIN_ANGLE steers RIGHT
MAX_ANGLE = default_servo + max_turn_degree   # original convention: MAX_ANGLE steers LEFT


def to_physical_angle(logical_angle):
    """
    Converts a "logical" servo angle (computed everywhere else in this
    file using the ORIGINAL convention: MIN_ANGLE steers right, MAX_ANGLE
    steers left) into the actual PWM angle the hardware needs, given the
    servo horn is now mounted upside down. This is the ONLY place the
    physical flip is applied -- it lives inside set_servo_angle().
    """
    if STEER_SIGN == -1:
        return int(round(2 * default_servo - logical_angle))
    return int(round(logical_angle))


# =========================================================================
# WALL-FOLLOW PD
# =========================================================================
TARGET_X_LEFT = 0
TARGET_X_RIGHT = PIC_WIDTH
TARGET_Y = 220

Kp_wall = 0.4
Kd_wall = 0.125
prev_wall_error = 0.0

NBR_COLS = 10


def _find_black_from_bottom(img, col_range):
    h = img.shape[0]
    y_vals = []
    for x in col_range:
        found = 0  # nothing found -> treat as "far" (matches reference default)
        for y in reversed(range(h - 20)):
            if img[y, x] == 0:
                found = y
                break
        y_vals.append(found)
    return y_vals


def _find_black_sides(img, direction, row_range):
    w = img.shape[1]
    end_index = 0 if direction == Direction.LEFT else w - 1
    step = direction.value  # LEFT=-1, RIGHT=1
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
    """
    Normal PD wall-follow. Target point is direction-specific now:
    TARGET_X_LEFT (0) when following the left wall, TARGET_X_RIGHT (w)
    when following the right wall -- both at the same TARGET_Y row. No
    mirroring of the measured avg_x anymore; the raw measurement is
    compared straight against whichever target matches the side being
    followed, and direction.value handles the sign so the resulting
    steering command is identical to before -- this is just an explicit
    version of the same control law.
    """
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
    avg_x = np.mean(x_vals)   # raw measurement, no mirroring
    if avg_y >= h - 1:
        avg_y = h

    cv2.circle(display_frame, (int(avg_x), int(avg_y)), 8, (0, 0, 255), -1)
    cv2.circle(display_frame, (int(target_x), TARGET_Y), 8, (0, 255, 0), -1)

    error_y = TARGET_Y - avg_y
    error_x = STEER_SIGN * (avg_x - target_x)
    error = error_y + error_x

    derivative = error - prev_wall_error
    control = (kp * error) + (kd * derivative)
    prev_wall_error = error

    angle = default_servo + direction.value * control * -1
    angle = max(MIN_ANGLE, min(MAX_ANGLE, angle))
    return angle


# =========================================================================
# POLYGON MASK -- find_contour(img, white=1) + draw_polygon()
# =========================================================================
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


# =========================================================================
# PILLAR DETECTION + AVOIDANCE
# =========================================================================
LEFT_OBSTACLE_X_THRESHOLD = 0
RIGHT_OBSTACLE_X_THRESHOLD = PIC_WIDTH - LEFT_OBSTACLE_X_THRESHOLD
OBJECT_LINE_ANGLE_THRESHOLD = 45
GREEN_OBSTACLE_KP = 1.25
RED_OBSTACLE_KP = 1.25

TOO_LOW_Y = PIC_HEIGHT - 35
TOO_CLOSE_Y = PIC_HEIGHT - 20

CRASH_POINT_COLOR = (255, 0, 0)  # BGR, so crash-check dots don't blend into red/green pillars

# Minimum contour area for a red/green blob to be considered a pillar at all.
PILLAR_AREA_THRESHOLD = 275

# Fixed low kp/kd used by wall_follow_angle while riding an inner-wall
# crash, instead of substituting a fixed steer-away angle -- same idea as
# the reference repo's `if inner_wall_warning: kp = 0.1; kd = 0`.
INNER_CRASH_KP = 0.1
INNER_CRASH_KD = 0.0


class CrashState(Enum):
    NONE = 0
    INNER = 1
    OUTER = 2


class ObstacleTracker:
    def __init__(self):
        self.old_angle = default_servo
        self.old_is_green = False
        self.state = CrashState.NONE
        self.inner_wall_warning = False
        # Tracks the color of the last red/green pillar actually passed --
        # ported from the reference's `self.last_color`. Only updated once
        # laps are complete, same as the reference, so it reflects the
        # LAST obstacle of the run (used by end-of-run parking logic to
        # pick which angled-reverse duration to use).
        self.last_color = None  # None / "green" / "red"

    def check_inner_wall_crash(self, direction, polygon_image, display_frame):
        """3 points near the side wall on the INSIDE of the turn (the
        side matching `direction`). Returns True if ANY of the 3 see
        black (wall). Retuned (2026-08-04) higher up the frame for an
        earlier warning than the original set."""
        if direction == Direction.RIGHT:
            detection_points = [
                (PIC_HEIGHT - 140, PIC_WIDTH - 195),
                (PIC_HEIGHT - 110, PIC_WIDTH - 170),
                (PIC_HEIGHT - 80, PIC_WIDTH - 145),
            ]
        else:
            detection_points = [
                (PIC_HEIGHT - 140, 225),
                (PIC_HEIGHT - 110, 200),
                (PIC_HEIGHT - 80, 175),
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
        """Single point straight ahead. Returns True if it sees black
        (wall dead ahead). Retuned (2026-08-04) to one shared
        straight-ahead point regardless of direction."""
        detection_points = [(PIC_WIDTH // 2, PIC_HEIGHT - 135)]
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
        """
        Scan the red and green masks (already polygon-masked by the
        caller), keep every contour above PILLAR_AREA_THRESHOLD, and
        track whichever one's center is closest (straight-line distance)
        to a fixed point directly in front of the robot (bottom-center of
        the frame). No ROI restriction, no minimum-y gate -- whatever red
        or green blob is nearest wins, full stop, every frame.
        """
        robot_point = (PIC_WIDTH // 2, PIC_HEIGHT)

        closest_distance = float("inf")
        closest = None  # (x_center, y_center, w, h, is_green)

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
        """
        Crash/pillar state machine, ported from the reference repo's
        CrashStates handling:

          NONE:
            - inner crash  -> state=INNER, set inner_wall_warning, return
              None (wall-follow drives this frame with kp/kd swapped to
              the damped pair in run()). Pillar search is skipped this
              frame.
            - outer crash  -> state=OUTER, return a hard steer-into-the-
              turn angle. Pillar search is skipped this frame.
          INNER:
            - still crashed -> keep inner_wall_warning set, return None
              (pillar search stays skipped).
            - cleared       -> state=NONE, fall through to pillar search
              THIS SAME FRAME (no extra delay).
          OUTER:
            - still crashed -> keep returning the hard steer angle.
            - cleared       -> state=NONE, fall through to pillar search
              THIS SAME FRAME.

          Otherwise (no active crash state): normal closest-pillar
          detection/avoidance runs every frame.

        `laps_complete`: once True, every pillar actually chosen updates
        self.last_color -- ported from the reference's
        `if self.context_manager.has_completed_laps(): self.last_color = ...`
        -- so end-of-run logic can know which color the very last
        obstacle passed was.

        NOTE: the return value here (None vs a concrete angle) is also
        what run() uses to decide DRIVE_SPEED vs OBSTACLE_SPEED -- any
        non-None return (hard crash override OR active pillar-avoidance
        steering) counts as "currently going around an obstacle".
        """
        self.inner_wall_warning = False
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

        if y_center > TOO_LOW_Y:
            if y_center > TOO_CLOSE_Y:
                # right on top of it -- stop tracking, commit to the pass
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
        self.old_is_green = is_green
        return servo_angle


def crop_image(img, x_start, x_end, y_start, y_end):
    return img[y_start:y_end, x_start:x_end]


# =========================================================================
# PARKING-EXIT MANEUVER (TIME-BASED)
# =========================================================================
# Durations here are starting points -- test with the robot raised off the
# ground first, then at low stakes on the real course, and retune against
# your actual battery voltage / motor speed / servo throw. Reasons in the
# ORIGINAL logical angle convention used everywhere else in this file
# (MAX_ANGLE = left, MIN_ANGLE = right) -- set_servo_angle() applies the
# servo-mirror fix at the point of send, same as run() does.

# speed used during the parking exit -- separate from DRIVE_SPEED/
# OBSTACLE_SPEED so it can be tuned independently (parking usually wants
# to be gentler)
PARK_SPEED = 100


def detect_exit_direction(picam2):
    """
    Decide which way to steer for the parking exit by looking at which
    half of the frame has more open floor (white, after the same
    grayscale/threshold pipeline used elsewhere in this file) -- left
    half vs right half. More white on the right means more open space to
    the right (Direction.RIGHT); more white on the left means
    Direction.LEFT.
    """
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


def exit_parallel_park(direction):
    """
    Parking exit: steer hard toward the open side, drive forward, steer
    hard the other way, drive forward again, then straighten out and
    reverse to finish clearing the space. Symmetric for both directions
    -- `direction` (from detect_exit_direction) just picks which way is
    "away" vs "toward":
      Direction.LEFT  -> away = MAX_ANGLE, toward = MIN_ANGLE
      Direction.RIGHT -> away = MIN_ANGLE, toward = MAX_ANGLE

    Uses set_servo_angle() and set_motor() directly, no combined helper,
    so steering and driving stay two independent calls.
    """
    away_angle = MAX_ANGLE if direction == Direction.LEFT else MIN_ANGLE
    toward_angle = MIN_ANGLE if direction == Direction.LEFT else MAX_ANGLE

    print(f"[park] exiting, direction={direction.name}")

    set_servo_angle(away_angle)
    time.sleep(5)

    set_motor(1, PARK_SPEED)  # 1 = forward
    time.sleep(1.0)
    stop_motor()

    set_servo_angle(toward_angle)
    time.sleep(1)
    if direction == Direction.LEFT:
        set_motor(1, PARK_SPEED)
        time.sleep(1.2)
        stop_motor()
    elif direction == Direction.RIGHT:
        set_motor(1, PARK_SPEED);
        time.sleep(0.9)
        stop_motor()

    set_servo_angle(default_servo)
    time.sleep(1)

    if direction == Direction.LEFT:
        set_motor(2, DRIVE_SPEED)  # 2 = backward
        time.sleep(1.9)
        stop_motor()
    elif direction == Direction.RIGHT:
        set_motor(2, DRIVE_SPEED)
        time.sleep(1.1)
        stop_motor()

    set_servo_angle(default_servo)
    print("[park] exit complete, handing off to obstacle run()")


# =========================================================================
# END-OF-RUN PARK -- active pink-block following, 2026-08-05 v3
# =========================================================================
# The pink parking bay sits where the LAST corner of the course would
# otherwise turn. Instead of a fixed time-based maneuver, the robot now
# actively tracks the pink block every frame (same closest-blob technique
# ObstacleTracker.find_closest_pillar / obstacle_angle use for red/green
# pillars) and steers to keep the block on the robot's LEFT if `direction`
# is Direction.LEFT, or on the robot's RIGHT if Direction.RIGHT -- the
# same aim-point convention pillar-passing already uses (red passes on
# the left via LEFT_OBSTACLE_X_THRESHOLD, green passes on the right via
# RIGHT_OBSTACLE_X_THRESHOLD). It drives at PARK_APPROACH_SPEED the whole
# time and keeps closing in, purely vision-driven, until the block's
# bounding-box area crosses PARK_TARGET_AREA ("target met"), then stops.
# No fixed timers or hardcoded angles.

PARK_APPROACH_SPEED = 100

# Bounding-box area (px^2) of the tracked pink block at which the
# approach is considered "done" -- i.e. close enough to stop. UNTUNED
# PLACEHOLDER -- watch the debug rectangle in the video feed and adjust
# until it lines up with "close enough to call it parked".
PARK_TARGET_AREA = 2000

# Reuses the same angle-threshold idea as OBJECT_LINE_ANGLE_THRESHOLD /
# *_OBSTACLE_KP from pillar avoidance, but as its own pair so the park
# approach can be tuned independently of pillar passing.
PARK_LINE_ANGLE_THRESHOLD = OBJECT_LINE_ANGLE_THRESHOLD
PARK_OBSTACLE_KP = 1.25


def find_pink_block(pink_mask, display_frame):
    """
    Largest pink contour in the frame -- no polygon restriction, since
    the bay marker isn't necessarily inside the track polygon. Returns
    (x_center, y_center, area) for the biggest blob above
    PILLAR_AREA_THRESHOLD, or None if nothing qualifies.
    """
    contours, _ = cv2.findContours(pink_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    cnt = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(cnt)
    if area <= PILLAR_AREA_THRESHOLD:
        return None

    x, y, w, h = cv2.boundingRect(cnt)
    x_center = x + w // 2
    y_center = y + h // 2
    cv2.rectangle(display_frame, (x, y), (x + w, y + h), (255, 0, 255), 2)
    return x_center, y_center, w * h


def park_block_angle(direction, pink_mask, display_frame):
    """
    Steers to keep the pink block on the robot's LEFT if `direction` is
    Direction.LEFT, or on the robot's RIGHT if Direction.RIGHT -- same
    aim-point technique as ObstacleTracker.obstacle_angle's green/red
    pillar-passing logic. Returns (angle, block_area), or (None, None)
    if no block is currently visible.
    """
    found = find_pink_block(pink_mask, display_frame)
    if found is None:
        return None, None
    x_center, y_center, area = found

    aim_x = LEFT_OBSTACLE_X_THRESHOLD if direction == Direction.LEFT else RIGHT_OBSTACLE_X_THRESHOLD
    cv2.line(display_frame, (x_center, y_center), (aim_x, PIC_HEIGHT), (255, 0, 255), 2)

    rad_angle = np.arctan2(y_center - PIC_HEIGHT, x_center - aim_x)
    object_angle_deg = 90 + np.degrees(rad_angle)

    if direction == Direction.LEFT:
        servo_angle = default_servo - ((object_angle_deg - PARK_LINE_ANGLE_THRESHOLD) * PARK_OBSTACLE_KP)
    else:
        servo_angle = default_servo - ((object_angle_deg + PARK_LINE_ANGLE_THRESHOLD) * PARK_OBSTACLE_KP)

    servo_angle = max(MIN_ANGLE, min(MAX_ANGLE, servo_angle))
    return servo_angle, area


# Speed/steer/duration for the brief "peek" maneuver below -- purely
# time-based, no vision, so pink_mask detection isn't required to run it.
PARK_PEEK_SPEED = 100
# Slight steer offset off default_servo, same sign convention as
# `direction.value` elsewhere in this file: LEFT steers toward MAX_ANGLE
# (left), RIGHT steers toward MIN_ANGLE (right). UNTUNED PLACEHOLDER --
# just needs to be enough to swing the camera so the bay comes into view.
PARK_PEEK_STEER_OFFSET = 15   # degrees
PARK_PEEK_DURATION = 3.0      # seconds


def peek_toward_parking_spot(direction):
    """
    Runs once, right after the obstacle lap ends and before
    follow_pink_block_to_park() starts looking for the pink block:
    steers slightly toward `direction` (left if Direction.LEFT, right if
    Direction.RIGHT) while driving forward at PARK_PEEK_SPEED for
    PARK_PEEK_DURATION seconds. Purely so the camera swings enough to
    bring the parking bay into view before active tracking begins --
    time-based, no vision loop, same style as exit_parallel_park.
    """
    peek_angle = default_servo + (PARK_PEEK_STEER_OFFSET if direction == Direction.LEFT else -PARK_PEEK_STEER_OFFSET)
    peek_angle = max(MIN_ANGLE, min(MAX_ANGLE, peek_angle))

    print(f"[park] peeking toward the bay, direction={direction.name}")
    set_servo_angle(peek_angle)
    set_motor(1, PARK_PEEK_SPEED)  # 1 = forward
    time.sleep(PARK_PEEK_DURATION)


def follow_pink_block_to_park(picam2, direction):
    """
    End-of-run parking (2026-08-05 v3): actively tracks the pink bay
    marker every frame, steering to keep it on the robot's LEFT
    (Direction.LEFT) or RIGHT (Direction.RIGHT), driving at
    PARK_APPROACH_SPEED throughout. Keeps closing in frame-by-frame,
    purely from vision, until the block's bounding-box area crosses
    PARK_TARGET_AREA, then stops the motor and returns.
    """
    print(f"[park] lap complete -- actively tracking pink block, direction={direction.name}")
    set_motor(1, PARK_APPROACH_SPEED)  # 1 = forward
    prevang = None

    while True:
        raw_frame = picam2.capture_array()
        frame = crop_image(raw_frame, 0, CAMERA_PIC_WIDTH, CAMERA_PIC_HEIGHT - PIC_HEIGHT, CAMERA_PIC_HEIGHT)
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        pink_mask = calculate_color_mask(lab, "pink")

        angle, area = park_block_angle(direction, pink_mask, frame)

        if angle is not None:
            angle = round(angle)
            if prevang is None or prevang != angle:
                set_servo_angle(angle)
                prevang = angle

        cv2.imshow("frame", frame)
        cv2.imshow("pink mask", pink_mask)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            stop_motor()
            return

        if area is not None and area >= PARK_TARGET_AREA:
            print(f"[park] target met (area={area}) -- stopping")
            stop_motor()
            return


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
    for _ in range(10):
        picam2.capture_array()

    exit_direction = detect_exit_direction(picam2)
    exit_parallel_park(exit_direction)

    # start moving forward at the normal cruising speed -- run() takes
    # over from here and will bump this up to OBSTACLE_SPEED on any
    # frame where it's actively steering around a pillar/crash, and drop
    # back down to DRIVE_SPEED the instant that clears.
    set_motor(1, DRIVE_SPEED)

    # 2026-08-04 fix: thread the detected direction through into run()
    # instead of letting it default/hardcode to LEFT there.
    run(picam2, exit_direction)


def run(picam2, direction):
    tracker = ObstacleTracker()
    lap_tracker = LapTracker()
    prevang = None
    prevspeed = DRIVE_SPEED  # matches the set_motor(1, DRIVE_SPEED) call already sent in main()
    set_servo_angle(default_servo)

    while True:
        raw_frame = picam2.capture_array()
        frame = crop_image(raw_frame, 0, CAMERA_PIC_WIDTH, CAMERA_PIC_HEIGHT - PIC_HEIGHT, CAMERA_PIC_HEIGHT)

        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)

        # Compute each color mask exactly ONCE per frame -- these feed
        # both the wall/polygon pipeline below AND pillar detection, so
        # there's no reason to recompute green/red a second time inside
        # the tracker (that was doubling the masking cost every frame).
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
            cv2.polylines(frame, [polygon_points], True, (0, 0, 255), 2, lineType=cv2.LINE_AA)

        # ---- lap counting + final-turn trigger check --------------------
        # Pure counter, does not touch steering, UNLESS we detect the
        # ENTRY marker for what would be the last corner -- in which case
        # we abandon the main loop right here and hand off to the
        # end-of-run parking maneuver instead of taking that last turn.
        lap_tracker.process_image(blue_mask, orange_mask, direction, polygon_mask)
        laps_complete = lap_tracker.quarter_lap_count >= TOTAL_TURNS

        entering_last_turn = (
            lap_tracker.quarter_lap_count == TOTAL_TURNS - 1
            and lap_tracker.state == "turning"
        )
        if entering_last_turn:
            print("[park] last-turn marker detected -- skipping the turn, "
                  "switching to active pink-block tracking")
            peek_toward_parking_spot(direction)
            follow_pink_block_to_park(picam2, direction)
            break

        # pillar masks restricted to inside the track polygon, computed
        # once here and reused by the tracker
        green_mask_in_polygon = cv2.bitwise_and(green_mask, green_mask, mask=polygon_mask)
        red_mask_in_polygon = cv2.bitwise_and(red_mask, red_mask, mask=polygon_mask)

        # crash-avoidance / pillar-avoidance angle (may override wall-follow)
        obstacle_angle = tracker.obstacle_angle(
            direction, green_mask_in_polygon, red_mask_in_polygon, polygon_image, frame,
            laps_complete=laps_complete
        )

        # Wall-follow runs every frame regardless of obstacle_angle so its
        # debug point still draws, but its kp/kd drop to a fixed low pair
        # while riding an inner-wall crash -- this is what replaces the
        # old fixed "steer away" angle with a continuous, gentler
        # correction.
        wall_angle = wall_follow_angle(
            polygon_image, direction, frame, damped=tracker.inner_wall_warning
        )

        # Crash/pillar override wins if present, otherwise wall-follow drives.
        final_angle = obstacle_angle if obstacle_angle is not None else wall_angle

        angle = round(max(MIN_ANGLE, min(MAX_ANGLE, final_angle)))

        if prevang is None or prevang != angle:
            set_servo_angle(angle)
            prevang = angle

        # ---- obstacle-aware speed switching ----------------------------
        # obstacle_angle is only non-None while the crash/pillar override
        # is actively steering (hard OUTER-crash turn, or live pillar
        # avoidance) -- exactly the "going around an obstacle" case. Bump
        # to OBSTACLE_SPEED for that, drop back to DRIVE_SPEED the moment
        # it clears. Only resend MOTOR when the speed actually changes.
        is_avoiding_obstacle = obstacle_angle is not None
        target_speed = OBSTACLE_SPEED if is_avoiding_obstacle else DRIVE_SPEED
        if target_speed != prevspeed:
            set_motor(1, target_speed)
            prevspeed = target_speed

        cv2.imshow("frame", frame)
        cv2.imshow("polygon mask", polygon_mask)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            stop_motor()
            break

    picam2.stop()
    cv2.destroyAllWindows()
    ser.close()


if __name__ == "__main__":
    main()
