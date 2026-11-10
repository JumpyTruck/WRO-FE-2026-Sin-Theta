import time

from utils.constants import (
    TURN_ENTER_CONFIRM_FRAMES,
    TURN_MARKER_ENTER_AREA,
    TURN_MARKER_EXIT_AREA,
    TURN_MAX_TIME,
)
from utils.enums import Direction, TurnState


class LapCounter:
    # Counts corners by watching the corner marker line grow and shrink.
    # A corner starts when the marker is large for a few frames in a row and counts once it has
    # shrunk again, so every corner adds exactly one quarter turn (4 quarter turns = 1 lap).
    def __init__(self, direction, profile):
        left = direction == Direction.LEFT
        self.exit_confirm_frames = (profile.turn_exit_confirm_frames_left if left
                                    else profile.turn_exit_confirm_frames_right)
        self.turn_min_time = profile.turn_min_time_left if left else profile.turn_min_time_right
        self.cooldown_time = profile.turn_cooldown_time

        self.state = TurnState.IDLE
        self.quarter_turns = 0
        self._enter_confirm_count = 0
        self._exit_confirm_count = 0
        self._turn_start_time = 0.0
        self._cooldown_until = 0.0

    def update(self, marker_area):
        # call once per frame with the marker pixels that are inside the track
        now = time.time()

        if self.state == TurnState.IDLE:
            # the cooldown stops the same marker from being counted twice
            if now >= self._cooldown_until:
                self._enter_confirm_count = (
                    self._enter_confirm_count + 1 if marker_area > TURN_MARKER_ENTER_AREA else 0
                )
                if self._enter_confirm_count >= TURN_ENTER_CONFIRM_FRAMES:
                    self.state = TurnState.TURNING
                    self._turn_start_time = now
                    self._exit_confirm_count = 0
                    self._enter_confirm_count = 0
        else:
            turn_elapsed = now - self._turn_start_time
            self._exit_confirm_count = (
                self._exit_confirm_count + 1 if marker_area < TURN_MARKER_EXIT_AREA else 0
            )
            should_exit = (
                (turn_elapsed >= self.turn_min_time and self._exit_confirm_count >= self.exit_confirm_frames)
                or (turn_elapsed >= TURN_MAX_TIME)  # safety net if the marker never shrinks
            )
            if should_exit:
                self.quarter_turns += 1
                self.state = TurnState.IDLE
                self._cooldown_until = now + self.cooldown_time
                self._enter_confirm_count = 0
                self._exit_confirm_count = 0
