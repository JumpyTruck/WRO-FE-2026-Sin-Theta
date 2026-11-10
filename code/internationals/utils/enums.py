from enum import Enum, auto


class Challenge(Enum):
    # which of the two WRO FE challenges is being run
    OPEN = auto()
    OBSTACLE = auto()


class Direction(Enum):
    # direction the robot travels around the track
    LEFT = -1
    RIGHT = 1


class TurnState(Enum):
    # state of the LapCounter while it watches a corner marker
    IDLE = auto()
    TURNING = auto()


class WallState(Enum):
    # wall-proximity latch used by the PillarNavigator
    NONE = 0
    INNER = 1
    OUTER = 2


class RunState(Enum):
    # top-level states of the RobotController state machine
    WAIT_FOR_BUTTON = auto()
    WARM_UP_CAMERA = auto()
    DETECT_CHALLENGE = auto()
    DETECT_START_DIRECTION = auto()
    EXIT_START_PARK = auto()
    DRIVE_LAPS = auto()
    APPROACH_PARKING_SPOT = auto()
    FINISHED = auto()
