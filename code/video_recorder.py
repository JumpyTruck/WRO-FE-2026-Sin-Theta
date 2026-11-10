import os
import time
from threading import Lock, Thread

import cv2

from utils.constants import (
    FRAME_HEIGHT,
    FRAME_WIDTH,
    LAPS_TARGET,
    RECORD_DIR,
    RECORD_EXTENSION,
    RECORD_FOURCC,
    RECORD_FPS,
    TOTAL_QUARTER_TURNS,
)

FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 0.45
LAP_COLOR = (255, 255, 255)
TIMER_COLOR = (0, 255, 255)
TIMER_DONE_COLOR = (90, 255, 90)  # the timer turns green once the run is finished
SPEED_COLOR = (0, 165, 255)


class VideoRecorder(Thread):
    # Records the whole run to a video file at a fixed rate on its own thread, so writing the
    # video never slows the vision loop down. The main loop hands over each finished frame with
    # submit(). While the main loop is blocked (driving by ticks, sleeping) the last frame is
    # repeated, so the lap counter and timer keep updating and the video never freezes.
    # The run information drawn on the video (laps, timer, speed status) is stored on this object:
    # the main loop writes it, this thread reads it.
    def __init__(self, arduino):
        super().__init__(daemon=True)
        self.arduino = arduino    # source of the commanded speed and the reverse flag
        self.start_time = None    # set when the start button is pressed
        self.end_time = None      # set when the run ends, which freezes the timer
        self.quarter_turns = 0
        self.cruise_speed = 0     # normal lap speed of the active challenge
        self.phase = "READY"      # READY, LAPS, PARKING, DONE

        self._lock = Lock()
        self._frame = None
        self._running = False

    def elapsed(self):
        if self.start_time is None:
            return 0.0
        end = self.end_time if self.end_time is not None else time.time()
        return max(0.0, end - self.start_time)

    def status(self):
        if self.phase == "DONE":
            return "DONE"
        if self.arduino.reversing:
            return "REVERSE"
        if self.phase == "PARKING":
            return "SLOW"
        if self.phase == "LAPS":
            if self.arduino.speed > self.cruise_speed:
                return "ACCEL"
            return "FAST" if self.arduino.speed > 0 else "STOP"
        return "READY"

    def start(self):
        self._running = True
        super().start()

    def submit(self, frame):
        # only swaps a reference, so it is cheap enough to call every frame
        if self._running:
            with self._lock:
                self._frame = frame

    def draw_overlay(self, frame):
        # draws plain text in the top-left corner of the frame, in place
        quarters_done = min(self.quarter_turns, TOTAL_QUARTER_TURNS)
        lap = min(quarters_done // 4 + 1, LAPS_TARGET)
        quarter = quarters_done - (lap - 1) * 4
        cv2.putText(frame, f"LAP {lap}/{LAPS_TARGET}  Q {quarter}/4", (10, 20),
                    FONT, FONT_SCALE, LAP_COLOR, 1, cv2.LINE_AA)

        tenths = int(self.elapsed() * 10)
        timer_color = TIMER_DONE_COLOR if self.end_time is not None else TIMER_COLOR
        cv2.putText(frame, f"TIME {tenths // 600:02d}:{(tenths % 600) / 10:04.1f}", (10, 40),
                    FONT, FONT_SCALE, timer_color, 1, cv2.LINE_AA)

        cv2.putText(frame, f"SPEED: {self.status()}", (10, 60),
                    FONT, FONT_SCALE, SPEED_COLOR, 1, cv2.LINE_AA)

    def run(self):
        os.makedirs(RECORD_DIR, exist_ok=True)
        path = os.path.join(RECORD_DIR, time.strftime("run_%Y%m%d_%H%M%S") + RECORD_EXTENSION)
        writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*RECORD_FOURCC),
                                 RECORD_FPS, (FRAME_WIDTH, FRAME_HEIGHT))
        if not writer.isOpened():
            print("VideoRecorder: could not open the video file, recording disabled")
            return
        print(f"VideoRecorder: recording to {path}")

        period = 1.0 / RECORD_FPS
        next_tick = time.time()
        try:
            while self._running:
                with self._lock:
                    frame = self._frame
                if frame is not None:
                    frame = frame.copy()  # never draw on a frame the main loop still uses
                    self.draw_overlay(frame)
                    writer.write(frame)

                next_tick += period
                delay = next_tick - time.time()
                if delay > 0:
                    time.sleep(delay)
                else:
                    next_tick = time.time()  # fell behind, do not try to catch up
        finally:
            writer.release()
            print("VideoRecorder: saved")

    def stop(self):
        self._running = False
        if self.is_alive():
            self.join(timeout=3.0)
