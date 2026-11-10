from dataclasses import dataclass

from utils.constants import FRAME_HEIGHT, FRAME_WIDTH


@dataclass(frozen=True)
class ParkProfile:
    # Values that differ between a left run and a right run while parking.
    # The parking sequence is the same, the right run is a mirror image with its own tuning.

    # --- approaching the pink wall ---
    approach_speed: int
    pink_kp: float          # steering gain toward the pink wall
    pink_aim_x: int         # x position the robot aims the pink wall at
    pillar_aim_x: int       # x position the robot aims a pillar at while parking
    pillar_kp: float
    reach_y: int            # the pink wall must be at least this low in the frame...
    reach_x_tolerance: int  # ...and within this many pixels of pink_aim_x to count as arrived

    # --- driving forward past the spot along the outer wall ---
    entry_target_area: int  # single ROI wall area to hold
    entry_speed: int
    entry_time: float

    # --- reversing into the spot ---
    back_speed: int         # reverse until the pink wall is visible behind the robot
    back_steer_offset: int
    hop_steer_offset: int   # short forward hop to line up before the final turns
    hop_ticks: int
    turn_ticks: tuple       # encoder ticks of the three reverse turns
    pre_delay: float        # servo settle time before each reverse turn
    settle: float           # pause after each stop


PARK_PROFILE_LEFT_RUN = ParkProfile(
    approach_speed=140, pink_kp=1.5, pink_aim_x=FRAME_WIDTH - 40,
    pillar_aim_x=0, pillar_kp=2.2,
    reach_y=FRAME_HEIGHT - 140, reach_x_tolerance=100,
    entry_target_area=3750, entry_speed=100, entry_time=2.5,
    back_speed=130, back_steer_offset=2,
    hop_steer_offset=0, hop_ticks=1625, turn_ticks=(950, 675, 1000),
    pre_delay=0.3, settle=0.3,
)

PARK_PROFILE_RIGHT_RUN = ParkProfile(
    approach_speed=140, pink_kp=1.5, pink_aim_x=40,
    pillar_aim_x=FRAME_WIDTH, pillar_kp=2.2,
    reach_y=FRAME_HEIGHT - 150, reach_x_tolerance=40,
    entry_target_area=8000, entry_speed=100, entry_time=2.5,
    back_speed=130, back_steer_offset=3,
    hop_steer_offset=4, hop_ticks=1950, turn_ticks=(1100, 775, 1025),
    pre_delay=0.3, settle=0.3,
)
