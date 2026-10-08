# numbers that are the same for both challenges live here.
# anything that changes between open and obstacle is in challenge_profile.py

import numpy as np

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
CAMERA_WARMUP_TIME = 0.3

# --- picking the challenge at the start ---
# this much pink in view means we're sitting in the parking spot, so it's the obstacle challenge
CHALLENGE_PINK_MIN_AREA = 500

# LAB colour ranges
BLUE_LOWER = np.array([22, 131, 75])
BLUE_UPPER = np.array([95, 158, 112])

ORANGE_LOWER = np.array([78, 146, 159])
ORANGE_UPPER = np.array([139, 167, 194])

GREEN_LOWER = np.array([60, 63, 121])
GREEN_UPPER = np.array([153, 107, 171])

RED_LOWER = np.array([62, 158, 140])
RED_UPPER = np.array([100, 203, 174])

PINK_LOWER = np.array([57, 149, 106])
PINK_UPPER = np.array([110, 192, 143])

CLEAN_KERNEL = np.ones((5, 5), np.uint8)

COLOR_RANGES = {
    "blue": (BLUE_LOWER, BLUE_UPPER),
    "orange": (ORANGE_LOWER, ORANGE_UPPER),
    "green": (GREEN_LOWER, GREEN_UPPER),
    "red": (RED_LOWER, RED_UPPER),
    "pink": (PINK_LOWER, PINK_UPPER),
}

# --- steering ---
STEER_CENTER = 97  # servo angle that drives straight
STEER_SIGN = -1  # servo turns the opposite way
PARK_MAX_STEER_OFFSET = 60  # parking needs a bit more lock

# --- run config ---
LAPS_TARGET = 3
TOTAL_QUARTER_TURNS = LAPS_TARGET * 4  # each corner = one quarter turn

PARK_SPEED = 85

PILLAR_BOOST_SPEED = 255
PILLAR_ACCEL_MIN_Y = 0
SPEED_DECEL_STEP = 20

MOTOR_FORWARD = 1
MOTOR_REVERSE = 2

# --- leaving the parking spot at the start ---
EXIT_PARK_SPEED = 100
EXIT_PARK_TICKS = 900

# --- right run finish ---
FORCE_RIGHT_AVOID_DELAY_AFTER_GREEN = 0.9
FORCE_RIGHT_AVOID_DELAY_AFTER_RED = 0.4
U_TURN_TICKS = 2500

# --- corner marker detection for lap counting ---
TURN_MARKER_ENTER_AREA = 150
TURN_MARKER_EXIT_AREA = 60

TURN_ENTER_CONFIRM_FRAMES = 3
TURN_MAX_TIME = 2.0

# --- area wall following ---
WALL_OPENING_AREA = 700
OPENING_BOOST_MULT = 2
OPENING_BOOST_ADD = 25000

AREA_WALL_KP_DAMPED = 0.0015  # softer gains near the inner wall
AREA_WALL_KD_DAMPED = 0.0

# --- point-based wall following used when approaching / parking ---
# the target is where we want the nearest wall point to sit in the frame
APPROACH_WALL_TARGET_X_LEFT = 0
APPROACH_WALL_TARGET_Y = FRAME_HEIGHT - 1
APPROACH_WALL_KP = 0.37

INNER_WALL_KP = 0.15
INNER_WALL_KD = 0.0

PARK_ENTRY_TARGET_X_RIGHT = FRAME_WIDTH
PARK_ENTRY_TARGET_Y = FRAME_HEIGHT - 1

# pretend wall point used for the short blind alignment before the parking wall follow
FORCED_ALIGN_TIME = 0.5
FORCED_ALIGN_POINT_X = FRAME_WIDTH - 60
FORCED_ALIGN_POINT_Y = 280

# --- pillar (obstacle) avoidance ---
RED_PILLAR_TARGET_X = 65
GREEN_PILLAR_TARGET_X = FRAME_WIDTH - RED_PILLAR_TARGET_X

PILLAR_STEER_OFFSET_DEG = 45
GREEN_PILLAR_KP = 2.3
RED_PILLAR_KP = 2.3

PILLAR_TRACK_START_Y = FRAME_HEIGHT - 60
PILLAR_TOO_CLOSE_Y = FRAME_HEIGHT

MIN_PILLAR_AREA = 200

INNER_WALL_SAMPLE_POINTS = 15

# --- parking ---
PARK_APPROACH_X_TOLERANCE = 80

PARK_WALL_STEER_OFFSET_DEG = 45

MIN_PARK_WALL_AREA = 10
PARK_WALL_SEEN_AREA = 200
