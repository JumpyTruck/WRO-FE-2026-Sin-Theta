from enum import Enum, auto


class Challenge(Enum):
    OPEN = auto()
    OBSTACLE = auto()


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
    DETECT_CHALLENGE = auto()
    DETECT_START_DIRECTION = auto()
    EXIT_START_PARK = auto()
    DRIVE_LAPS = auto()
    UTURN_TO_PARKING_WALL = auto()
    APPROACH_PARKING_SPOT = auto()
    FINISHED = auto()
