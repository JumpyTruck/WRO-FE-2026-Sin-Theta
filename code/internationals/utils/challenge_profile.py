from dataclasses import dataclass
from typing import Optional

from utils.constants import PARK_MAX_STEER_OFFSET, STEER_CENTER
from utils.enums import Challenge, Direction


@dataclass(frozen=True)
class ChallengeProfile:
    # values that differ between the open challenge and the obstacle challenge.
    # the code is the same for both, it just reads its numbers from whichever profile got picked
    challenge: Challenge

    # --- camera ---
    gray_threshold: int            # splits floor (white) from wall (black)
    track_outline_epsilon: float   # how tightly the track outline hugs the floor blob
    marker_colors: tuple           # colours we look for on every frame

    # --- steering ---
    max_steer_offset: int          # how far either side of centre we let it steer

    # --- driving ---
    drive_speed: int
    finish_drive_time: float       # open only: keep driving this long after the last corner
    # open only: it never works out which way round it's going, so it's told one.
    # None means look at the camera and work it out
    fixed_direction: Optional[Direction]

    # --- lap counting ---
    turn_exit_confirm_frames_left: int
    turn_exit_confirm_frames_right: int
    turn_min_time_left: float
    turn_min_time_right: float
    turn_cooldown_time: float

    # --- area wall following ---
    left_wall_roi: tuple
    right_wall_roi: tuple
    area_wall_kp: float
    area_wall_kd: float

    @property
    def steer_min(self):
        return STEER_CENTER - self.max_steer_offset

    @property
    def steer_max(self):
        return STEER_CENTER + self.max_steer_offset

    @property
    def park_steer_min(self):
        return STEER_CENTER - PARK_MAX_STEER_OFFSET

    @property
    def park_steer_max(self):
        return STEER_CENTER + PARK_MAX_STEER_OFFSET


CHALLENGE_PROFILE_OPEN = ChallengeProfile(
    challenge=Challenge.OPEN,
    gray_threshold=75, track_outline_epsilon=0.001,
    marker_colors=("blue",),
    max_steer_offset=43,
    drive_speed=255, finish_drive_time=1.0,
    # normal wall following doesn't care about this. it's only used by the backup
    # at the end of area_wall_follow_angle, when neither wall ROI sees any wall
    fixed_direction=Direction.RIGHT,
    turn_exit_confirm_frames_left=2, turn_exit_confirm_frames_right=2,
    turn_min_time_left=0.25, turn_min_time_right=0.25,
    turn_cooldown_time=0.2,
    left_wall_roi=(0, 84, 128, 210), right_wall_roi=(512, 84, 640, 210),
    area_wall_kp=0.003, area_wall_kd=0.0001,
)

CHALLENGE_PROFILE_OBSTACLE = ChallengeProfile(
    challenge=Challenge.OBSTACLE,
    gray_threshold=110, track_outline_epsilon=0.003,
    marker_colors=("blue", "orange", "green", "red"),
    max_steer_offset=60,
    drive_speed=200, finish_drive_time=0.0,
    fixed_direction=None,
    turn_exit_confirm_frames_left=10, turn_exit_confirm_frames_right=13,
    turn_min_time_left=1.0, turn_min_time_right=0.0,
    turn_cooldown_time=0.5,
    left_wall_roi=(0, 80, 128, 200), right_wall_roi=(504, 60, 638, 198),
    area_wall_kp=0.09, area_wall_kd=0.0004,
)
