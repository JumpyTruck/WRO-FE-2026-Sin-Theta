# Values shared by both challenges live here.
# Anything that differs between the open and obstacle challenge is stored in
# challenge_profile.py, and anything that differs between a left and a right run
# while parking is stored in park_profile.py.

import numpy as np

from utils.enums import Direction

# ------------------------------------------------------------------
# Serial link to the Arduino Nano (motor driver, steering servo, encoder)
# ------------------------------------------------------------------
SERIAL_PORT = "/dev/ttyUSB0"
BAUD_RATE = 115200
SERIAL_TIMEOUT = 1
SERIAL_WARMUP_TIME = 2.0  # the Nano resets when the port opens, so give it time to boot

# ------------------------------------------------------------------
# Raspberry Pi GPIO
# ------------------------------------------------------------------
START_BUTTON_PIN = 26  # active-low, wired to GND with the internal pull-up
STATUS_LED_PIN = 16    # lit while the robot waits for the start button

# ------------------------------------------------------------------
# Camera: the sensor frame is cropped to the lower part that actually sees the track
# ------------------------------------------------------------------
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 360
CAMERA_FRAME_RATE = 30
FRAME_WIDTH = 640
FRAME_HEIGHT = 280
CAMERA_WARMUP_TIME = 0.5  # lets auto exposure settle before the first real frame
MASK_POOL_WORKERS = 4     # colour masks are computed in parallel

# ------------------------------------------------------------------
# Video recording (debugging aid, drawn with a lap counter, timer and speed status)
# ------------------------------------------------------------------
RECORD_VIDEO = True
RECORD_DIR = "recordings"
RECORD_FPS = 30
RECORD_FOURCC = "MJPG"  # cheap to encode on a Raspberry Pi
RECORD_EXTENSION = ".avi"
FINISH_SETTLE_TIME = 1.5  # after the run: lets the servo settle and the video show DONE

# ------------------------------------------------------------------
# Detecting the challenge and the start direction
# ------------------------------------------------------------------
# The obstacle challenge starts inside the parking spot, so this much pink in
# view at the start means obstacle challenge. No pink means open challenge.
CHALLENGE_PINK_MIN_AREA = 500

# Open challenge: the line that is closer to the robot decides the direction
# (orange closer = RIGHT, blue closer = LEFT).
LINE_DETECT_MIN_AREA = 100   # a line must cover at least this many pixels to count
LINE_DETECT_TIMEOUT = 1.0    # how long to look for a line before using the default
DEFAULT_START_DIRECTION = Direction.RIGHT

# ------------------------------------------------------------------
# LAB colour ranges
# ------------------------------------------------------------------
BLUE_LOWER = np.array([22, 131, 75])
BLUE_UPPER = np.array([95, 158, 112])

ORANGE_LOWER = np.array([78, 146, 159])
ORANGE_UPPER = np.array([139, 167, 194])

GREEN_LOWER = np.array([87, 65, 136])
GREEN_UPPER = np.array([163, 112, 184])

RED_LOWER = np.array([61, 165, 140])
RED_UPPER = np.array([128, 190, 171])

PINK_LOWER = np.array([35, 140, 115])
PINK_UPPER = np.array([179, 198, 139])

CLEAN_KERNEL = np.ones((5, 5), np.uint8)  # removes specks and fills holes in colour masks

COLOR_RANGES = {
    "blue": (BLUE_LOWER, BLUE_UPPER),
    "orange": (ORANGE_LOWER, ORANGE_UPPER),
    "green": (GREEN_LOWER, GREEN_UPPER),
    "red": (RED_LOWER, RED_UPPER),
    "pink": (PINK_LOWER, PINK_UPPER),
}

# ------------------------------------------------------------------
# Steering
# ------------------------------------------------------------------
STEER_CENTER = 105         # servo angle that drives straight
STEER_SIGN = -1            # the servo is mounted so it turns the opposite way
PARK_MAX_STEER_OFFSET = 60 # parking is allowed the full steering lock

# ------------------------------------------------------------------
# Run configuration
# ------------------------------------------------------------------
LAPS_TARGET = 3
TOTAL_QUARTER_TURNS = LAPS_TARGET * 4  # every corner counts as one quarter turn

PARK_SPEED = 100
PILLAR_BOOST_SPEED = 255  # speed while a pillar is far away
SPEED_DECEL_STEP = 4      # speed removed per frame once the pillar is close

MOTOR_FORWARD = 1
MOTOR_REVERSE = 2

# ------------------------------------------------------------------
# Leaving the parking spot at the start (obstacle challenge)
# ------------------------------------------------------------------
EXIT_PARK_SPEED = PARK_SPEED
EXIT_PARK_TICKS = 950
EXIT_PARK_TURN_DELAY = 0.5   # time for the servo to reach full lock before moving
EXIT_PARK_SETTLE_TIME = 0.5  # time for the servo to centre before driving the laps

# ------------------------------------------------------------------
# Corner marker detection (lap counting)
# ------------------------------------------------------------------
TURN_MARKER_ENTER_AREA = 150  # marker pixels needed to say a corner has started
TURN_MARKER_EXIT_AREA = 60    # marker pixels below which the corner is over
TURN_ENTER_CONFIRM_FRAMES = 3
TURN_MAX_TIME = 2.0           # a corner is forced to finish after this long

# ------------------------------------------------------------------
# Area wall following (two ROIs, used on the obstacle laps and the parking approach)
# ------------------------------------------------------------------
WALL_OPENING_AREA = 700    # wall area below this means there is no wall (an opening)
OPENING_BOOST_MULT = 2     # the opposite side is boosted so the robot commits to the opening
OPENING_BOOST_ADD = 25000

AREA_WALL_KP_DAMPED = 0.0018  # softer gains used while the inner wall warning is active
AREA_WALL_KD_DAMPED = 0.0

NO_WALL_MARKER_STEER = 35  # degrees toward the corner when no wall is seen and a marker is
NO_WALL_STEER = 20         # degrees toward the corner when no wall and no marker is seen

# ------------------------------------------------------------------
# Single ROI wall following (forward drive along the outer wall while parking)
# ------------------------------------------------------------------
SINGLE_WALL_ROI_LEFT = (0, 160, 128, 280)
SINGLE_WALL_ROI_RIGHT = (512, 160, 640, 280)
SINGLE_WALL_KP = 0.012
SINGLE_WALL_KD = 0.01
SINGLE_WALL_NO_WALL_STEER = 20  # degrees toward the wall when the ROI sees nothing

# ------------------------------------------------------------------
# Open challenge wall following (one ROI on the inner wall)
# ------------------------------------------------------------------
OPEN_WALL_TARGET_AREA = 6000  # wall area to hold: less = farther from the wall, more = closer

# First quarter: the distance the robot starts at is held instead of OPEN_WALL_TARGET_AREA.
FIRST_QUARTER_CORNER_TURN = True
FIRST_QUARTER_CORNER_STEER = 50       # hard turn when the wall disappears at the first corner
FIRST_QUARTER_CORNER_MARKER_AREA = 50 # marker pixels that already mean "first corner"

# Corner boost: when the wall area collapses in one frame, the gains are multiplied
# for a short window so the robot snaps into the turn.
CORNER_DROP_RATIO = 0.25
CORNER_MIN_PREV_AREA = 800
CORNER_BOOST_FRAMES = 10
CORNER_KP_BOOST = 2
CORNER_KD_BOOST = 5
CORNER_MAX_STEER = 50
CORNER_NO_WALL_STEER = 50

# ------------------------------------------------------------------
# Pillar (obstacle) avoidance
# ------------------------------------------------------------------
RED_PILLAR_TARGET_X = 50
GREEN_PILLAR_TARGET_X = FRAME_WIDTH - RED_PILLAR_TARGET_X

PILLAR_STEER_OFFSET_DEG = 45
GREEN_PILLAR_KP = 2.2
RED_PILLAR_KP = 2.2

PILLAR_TRACK_START_Y = FRAME_HEIGHT - 130  # pillar below this line: start steering around it
PILLAR_TOO_CLOSE_Y = FRAME_HEIGHT - 15     # pillar below this line: already passed, ignore it

MIN_PILLAR_AREA = 200

AFTER_PILLAR_CLIP_FRAMES = 15        # frames of limited steering after a pillar is passed
AFTER_PILLAR_MAX_STEER_OFFSET = 50

# ------------------------------------------------------------------
# Wall crash points (sampled on the track image)
# ------------------------------------------------------------------
INNER_WALL_SAMPLE_POINTS = 15
INNER_WALL_NEAR_Y = FRAME_HEIGHT - 50
INNER_WALL_NEAR_X = 180   # distance from the side of the frame
INNER_WALL_FAR_Y = FRAME_HEIGHT - 110
INNER_WALL_FAR_X = 220
OUTER_WALL_CHECK_Y = FRAME_HEIGHT - 138  # one point straight ahead of the robot
CRASH_MARKER_COLOR = (255, 0, 0)

# ------------------------------------------------------------------
# Parking
# ------------------------------------------------------------------
PARK_WALL_STEER_OFFSET_DEG = 40
PARK_PINK_MAX_OFFSET = 40    # steering limit (degrees from centre) while following the pink wall
PARK_PINK_SMOOTH = 0.4       # weight of the previous pink angle (0 = no smoothing)
PARK_PINK_HOLD_FRAMES = 4    # frames the last pink angle is held when the pink wall drops out
PARK_PILLAR_MARGIN = 5       # a pillar must be this many pixels lower than the pink wall to win

MIN_PARK_WALL_AREA = 200
PARK_WALL_SEEN_AREA = 40     # pink pixels needed to say the wall is visible (reversing step)
PARK_WALL_MIN_Y = FRAME_HEIGHT - 230  # a pink wall higher than this is too far away
PARK_WALL_MAX_Y = FRAME_HEIGHT - 30   # a pink wall lower than this is too close

PARK_STRAIGHTEN_STEER_OFFSET = 20
PARK_STRAIGHTEN_TIME = 0.5
PARK_STOP_DELAY = 0.5   # pause after a stop before the next manoeuvre
PARK_SHORT_DELAY = 0.3
