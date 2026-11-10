from dataclasses import dataclass

from utils.constants import PARK_MAX_STEER_OFFSET, STEER_CENTER
from utils.enums import Challenge


@dataclass(frozen=True)
class ChallengeProfile:
    # Values that differ between the open challenge and the obstacle challenge.
    # The code is identical for both; it only reads its numbers from the profile that was picked.
    challenge: Challenge

    # --- camera ---
    gray_threshold: int           # splits floor (white) from walls (black)
    track_outline_epsilon: float  # how closely the track outline hugs the floor blob
    marker_colors: tuple          # colours that are masked on every frame

    # --- steering ---
    max_steer_offset: int         # how far either side of centre the servo may go

    # --- driving ---
    drive_speed: int
    finish_drive_time: float      # keep wall following this long after the last corner

    # --- lap counting ---
    turn_exit_confirm_frames_left: int
    turn_exit_confirm_frames_right: int
    turn_min_time_left: float
    turn_min_time_right: float
    turn_cooldown_time: float

    # --- wall following ---
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


# Open challenge: no pillars, so only the two corner lines are masked.
# Wall following uses a single ROI on the inner wall (the two ROIs are mirror images).
CHALLENGE_PROFILE_OPEN = ChallengeProfile(
    challenge=Challenge.OPEN,
    gray_threshold=100, track_outline_epsilon=0.001,
    marker_colors=("blue", "orange"),
    max_steer_offset=60,
    drive_speed=255, finish_drive_time=0.5,
    turn_exit_confirm_frames_left=2, turn_exit_confirm_frames_right=2,
    turn_min_time_left=0.25, turn_min_time_right=0.25,
    turn_cooldown_time=1.25,
    left_wall_roi=(0, 210, 128, 280), right_wall_roi=(512, 210, 640, 280),
    area_wall_kp=0.0055, area_wall_kd=0.001,
)

# Obstacle challenge: pillars are masked too. Wall following balances the area of two ROIs
# that are not symmetric, so the right ROI is mirrored for a left run and vice versa.
CHALLENGE_PROFILE_OBSTACLE = ChallengeProfile(
    challenge=Challenge.OBSTACLE,
    gray_threshold=110, track_outline_epsilon=0.00125,
    marker_colors=("blue", "orange", "green", "red"),
    max_steer_offset=60,
    drive_speed=200, finish_drive_time=0.0,
    turn_exit_confirm_frames_left=14, turn_exit_confirm_frames_right=4,
    turn_min_time_left=1.0, turn_min_time_right=0.0,
    turn_cooldown_time=0.85,
    left_wall_roi=(0, 80, 128, 200), right_wall_roi=(504, 60, 638, 198),
    area_wall_kp=0.09, area_wall_kd=0.0004,
)
