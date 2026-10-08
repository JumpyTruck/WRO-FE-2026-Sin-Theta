from dataclasses import dataclass

from utils.constants import FRAME_HEIGHT, PARK_SPEED, RED_PILLAR_TARGET_X


@dataclass(frozen=True)
class ParkProfile:
    # values that differ between a left run and a right run
    approach_speed: int
    approach_wall_kd: float
    pink_kp: float
    pillar_aim_x: int
    pillar_kp: float
    reach_y: int
    entry_speed: int
    entry_kp: float
    entry_kd: float
    entry_time: float
    back_speed: int
    hop_ticks: int
    turn_ticks: tuple
    pre_delay: float
    settle: float


PARK_PROFILE_LEFT_RUN = ParkProfile(
    approach_speed=135, approach_wall_kd=0.005, pink_kp=2.3,
    pillar_aim_x=RED_PILLAR_TARGET_X, pillar_kp=2,
    reach_y=FRAME_HEIGHT - 140,
    entry_speed=100, entry_kp=1.5, entry_kd=0.2, entry_time=2.5,
    back_speed=115, hop_ticks=1750, turn_ticks=(1025, 550, 1150),
    pre_delay=0.1, settle=0.3,
)

PARK_PROFILE_RIGHT_RUN = ParkProfile(
    approach_speed=125, approach_wall_kd=0.005, pink_kp=1.8,
    pillar_aim_x=50, pillar_kp=5,
    reach_y=FRAME_HEIGHT - 60,
    entry_speed=PARK_SPEED, entry_kp=1.5, entry_kd=0.2, entry_time=3,
    back_speed=PARK_SPEED, hop_ticks=1625, turn_ticks=(1025, 520, 1000),
    pre_delay=0.2, settle=0.2,
)
