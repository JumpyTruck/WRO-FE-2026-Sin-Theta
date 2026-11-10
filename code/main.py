import time

import cv2
import RPi.GPIO as GPIO
from gpiozero import LED
from picamera2 import Picamera2

from classes.arduino_comms import ArduinoComms
from classes.lap_counter import LapCounter
from classes.pillar_navigator import PillarNavigator
from classes.video_recorder import VideoRecorder
from utils.challenge_profile import CHALLENGE_PROFILE_OBSTACLE, CHALLENGE_PROFILE_OPEN
from utils.constants import (
    CAMERA_FRAME_RATE,
    CAMERA_HEIGHT,
    CAMERA_WARMUP_TIME,
    CAMERA_WIDTH,
    CHALLENGE_PINK_MIN_AREA,
    DEFAULT_START_DIRECTION,
    EXIT_PARK_SETTLE_TIME,
    EXIT_PARK_SPEED,
    EXIT_PARK_TICKS,
    EXIT_PARK_TURN_DELAY,
    FINISH_SETTLE_TIME,
    LINE_DETECT_TIMEOUT,
    MOTOR_FORWARD,
    MOTOR_REVERSE,
    PARK_PILLAR_MARGIN,
    PARK_PINK_HOLD_FRAMES,
    PARK_PINK_SMOOTH,
    PARK_SHORT_DELAY,
    PARK_SPEED,
    PARK_STOP_DELAY,
    PARK_STRAIGHTEN_STEER_OFFSET,
    PARK_STRAIGHTEN_TIME,
    PARK_WALL_SEEN_AREA,
    PILLAR_TOO_CLOSE_Y,
    RECORD_VIDEO,
    START_BUTTON_PIN,
    STATUS_LED_PIN,
    STEER_CENTER,
    TOTAL_QUARTER_TURNS,
)
from utils.enums import Challenge, Direction, RunState
from utils.image_utils import (
    MASK_POOL,
    capture_cropped_frame,
    detect_line_direction,
    draw_detection_boxes,
    get_color_mask,
    get_detection_masks,
    on_track,
    process_frame,
    split_floor_from_walls,
)
from utils.park_profile import PARK_PROFILE_LEFT_RUN, PARK_PROFILE_RIGHT_RUN


class RobotController:
    # The state machine for the whole run. Each state is one _state_ method that does its job
    # and then sets self.state to whatever comes next.
    #
    # open:     button > camera > detect challenge > detect direction (closest line) > laps > finished
    # obstacle: button > camera > detect challenge > detect direction (open floor) > exit park
    #           > laps > approach parking spot (pink wall, reverse in) > finished
    def __init__(self):
        self.state = RunState.WAIT_FOR_BUTTON
        self.arduino = ArduinoComms()
        self.recorder = VideoRecorder(self.arduino)  # also holds the run info drawn on the video
        self.picam2 = None

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(START_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self.status_led = LED(STATUS_LED_PIN)

        # the numbers for whichever challenge is running, set by DETECT_CHALLENGE
        self.profile = None
        self.start_direction = None
        self.lap_counter = None
        self.navigator = None

        self._handlers = {
            RunState.WAIT_FOR_BUTTON: self._state_wait_for_button,
            RunState.WARM_UP_CAMERA: self._state_warm_up_camera,
            RunState.DETECT_CHALLENGE: self._state_detect_challenge,
            RunState.DETECT_START_DIRECTION: self._state_detect_start_direction,
            RunState.EXIT_START_PARK: self._state_exit_start_park,
            RunState.DRIVE_LAPS: self._state_drive_laps,
            RunState.APPROACH_PARKING_SPOT: self._state_approach_parking_spot,
        }

    def run(self):
        try:
            while self.state != RunState.FINISHED:
                self._handlers[self.state]()
        finally:
            self._cleanup()

    def _cleanup(self):
        # always runs, so the motor stops and the video is saved even if something crashed
        if self.recorder.phase == "DONE":
            time.sleep(FINISH_SETTLE_TIME)
        try:
            self.arduino.stop(immediate=True)
        except Exception:
            pass
        self.recorder.stop()
        if self.picam2 is not None:
            self.picam2.stop()
        MASK_POOL.shutdown(wait=False)
        self.arduino.close()
        self.status_led.off()
        GPIO.cleanup()

    def _show(self, frame):
        # hands the finished overlay frame to the video thread
        self.recorder.submit(frame)

    def _pink_area(self):
        frame = capture_cropped_frame(self.picam2)
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        return cv2.countNonZero(get_color_mask(lab, "pink"))

    # ------------------------------------------------------------------
    # getting ready
    # ------------------------------------------------------------------

    def _state_wait_for_button(self):
        # LED on = waiting for the start button (active-low)
        self.status_led.on()
        while GPIO.input(START_BUTTON_PIN) == GPIO.HIGH:
            time.sleep(0.002)
        self.status_led.off()
        self.recorder.start_time = time.time()  # the run timer starts with the button press
        self.state = RunState.WARM_UP_CAMERA

    def _state_warm_up_camera(self):
        self.picam2 = Picamera2()
        sensor_width, sensor_height = self.picam2.sensor_modes[1]["size"]
        config = self.picam2.create_video_configuration(
            raw={"size": (sensor_width, sensor_height)},
            main={"format": "RGB888", "size": (CAMERA_WIDTH, CAMERA_HEIGHT)},
            controls={"FrameRate": CAMERA_FRAME_RATE},
        )
        self.picam2.configure(config)
        self.picam2.start()

        if RECORD_VIDEO:
            self.recorder.start()

        # throw away frames while auto exposure settles
        end_time = time.time() + CAMERA_WARMUP_TIME
        while time.time() < end_time:
            self.picam2.capture_array()

        self.state = RunState.DETECT_CHALLENGE

    def _state_detect_challenge(self):
        # the obstacle challenge starts inside the parking spot, so the pink walls are right in
        # front of the camera. no pink means it is the open challenge
        if self._pink_area() >= CHALLENGE_PINK_MIN_AREA:
            self.profile = CHALLENGE_PROFILE_OBSTACLE
        else:
            self.profile = CHALLENGE_PROFILE_OPEN

        self.arduino.use_profile(self.profile)
        self.recorder.cruise_speed = self.profile.drive_speed
        self.state = RunState.DETECT_START_DIRECTION

    def _state_detect_start_direction(self):
        if self.profile.challenge == Challenge.OPEN:
            self.start_direction = self._direction_from_closest_line()
            self.state = RunState.DRIVE_LAPS
        else:
            self.start_direction = self._direction_from_open_floor()
            self.state = RunState.EXIT_START_PARK

    def _direction_from_closest_line(self):
        # open challenge: the line closest to the robot gives the direction.
        # orange closer = RIGHT, blue closer = LEFT. falls back to the default if no line shows up in time
        deadline = time.time() + LINE_DETECT_TIMEOUT
        while time.time() < deadline:
            data = process_frame(self.picam2.capture_array(), self.profile)
            direction = detect_line_direction(data["blue_mask"], data["orange_mask"])
            if direction is not None:
                return direction
        return DEFAULT_START_DIRECTION

    def _direction_from_open_floor(self):
        # obstacle challenge: whichever half of the frame has more open floor is the direction
        frame = capture_cropped_frame(self.picam2)
        binary_image = split_floor_from_walls(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
                                              self.profile.gray_threshold)

        width = binary_image.shape[1]
        left_white = cv2.countNonZero(binary_image[:, :width // 2])
        right_white = cv2.countNonZero(binary_image[:, width // 2:])
        return Direction.RIGHT if right_white > left_white else Direction.LEFT

    def _state_exit_start_park(self):
        # turn away from the track and nose out of the parking box
        profile = self.profile
        self.recorder.phase = "PARKING"

        left_run = self.start_direction == Direction.LEFT
        away_angle = profile.park_steer_max if left_run else profile.park_steer_min

        self.arduino.set_park_steering(away_angle)
        time.sleep(EXIT_PARK_TURN_DELAY)
        self.arduino.drive(MOTOR_FORWARD, EXIT_PARK_SPEED, EXIT_PARK_TICKS)

        self.arduino.set_steering_angle(STEER_CENTER)
        time.sleep(EXIT_PARK_SETTLE_TIME)
        self.state = RunState.DRIVE_LAPS

    # ------------------------------------------------------------------
    # laps (both challenges)
    # ------------------------------------------------------------------

    def _state_drive_laps(self):
        profile = self.profile
        open_run = profile.challenge == Challenge.OPEN
        direction = self.start_direction
        # blue corner lines belong to a left run, orange ones to a right run
        counts_blue = direction == Direction.LEFT

        arduino = self.arduino
        lap_counter = self.lap_counter = LapCounter(direction, profile)
        navigator = self.navigator = PillarNavigator(profile)

        laps_done_time = None
        current_speed = profile.drive_speed
        previous_speed = profile.drive_speed

        self.recorder.phase = "LAPS"
        arduino.set_steering_angle(STEER_CENTER)
        arduino.drive(MOTOR_FORWARD, profile.drive_speed)

        while True:
            data = process_frame(self.picam2.capture_array(), profile)
            frame = data["frame"].copy()  # overlays are drawn on our own copy
            track_image = data["track_image"]
            track_mask = data["track_mask"]

            # only marker pixels inside the drivable area are counted
            blue_area = cv2.countNonZero(on_track(data["blue_mask"], track_mask))
            orange_area = cv2.countNonZero(on_track(data["orange_mask"], track_mask))
            marker_area = blue_area if counts_blue else orange_area

            lap_counter.update(marker_area)
            quarter_turns = lap_counter.quarter_turns
            self.recorder.quarter_turns = quarter_turns

            if laps_done_time is None and quarter_turns >= TOTAL_QUARTER_TURNS:
                laps_done_time = time.time()

            # open keeps wall following for a moment after the last corner, obstacle leaves at once
            if laps_done_time is not None and time.time() - laps_done_time >= profile.finish_drive_time:
                self._show(frame)
                break

            if open_run:
                angle = navigator.open_wall_follow_angle(
                    track_image, direction, marker_area,
                    first_quarter=(quarter_turns == 0), display_frame=frame,
                )
            else:
                # pillar dodging takes priority over wall following
                pillar_angle = navigator.get_steer_angle(
                    direction,
                    on_track(data["green_mask"], track_mask),
                    on_track(data["red_mask"], track_mask),
                    track_image, frame,
                )
                wall_angle = navigator.area_wall_follow_angle(
                    track_image, direction, blue_area=blue_area, orange_area=orange_area,
                    damped=navigator.inner_wall_warning, display_frame=frame,
                )
                angle = pillar_angle if pillar_angle is not None else wall_angle
                angle = navigator.clip_after_pillar(angle)

                # speed up when a pillar is far away, slow down as it gets close
                current_speed = navigator.update_drive_speed(current_speed)
                if current_speed != previous_speed:
                    arduino.drive(MOTOR_FORWARD, current_speed)
                    previous_speed = current_speed

            arduino.set_steering_angle(round(angle))
            self._show(frame)

        if open_run:
            arduino.stop()
            arduino.set_steering_angle(STEER_CENTER)
            self.recorder.end_time = time.time()  # freezes the timer
            self.recorder.phase = "DONE"
            print(f"run time: {self.recorder.elapsed():.2f} s")
            self.state = RunState.FINISHED
        else:
            self.state = RunState.APPROACH_PARKING_SPOT

    # ------------------------------------------------------------------
    # parking (obstacle challenge only)
    # ------------------------------------------------------------------

    def _state_approach_parking_spot(self):
        # both directions park the same way, the right run is just the mirror image with its own tuning
        self.recorder.phase = "PARKING"
        park = (PARK_PROFILE_LEFT_RUN if self.start_direction == Direction.LEFT
                else PARK_PROFILE_RIGHT_RUN)

        # fresh navigator so nothing from the laps carries over into parking
        self.navigator = PillarNavigator(self.profile)
        self._approach_pink_wall(park)
        self._reverse_into_parking_spot(park)

        self.arduino.set_steering_angle(STEER_CENTER)
        self.recorder.end_time = time.time()  # freezes the timer
        self.recorder.phase = "DONE"
        self.state = RunState.FINISHED

    def _approach_pink_wall(self, park):
        # steering priority: a pillar nearer than the wall > the pink wall > wall following
        profile = self.profile
        arduino = self.arduino
        navigator = self.navigator
        direction = self.start_direction

        smoothed_pink = None   # low-pass filtered pink steering angle
        pink_lost_frames = 0   # frames in a row without the pink wall

        arduino.drive(MOTOR_FORWARD, park.approach_speed)

        while True:
            data = process_frame(self.picam2.capture_array(), profile, with_pink=True)
            frame = data["frame"].copy()
            track_image = data["track_image"]
            track_mask = data["track_mask"]

            pillar_found = navigator.find_nearest_pillar(on_track(data["green_mask"], track_mask),
                                                         on_track(data["red_mask"], track_mask), frame)
            # pink is limited to the track like the pillars, so stray pixels cannot jerk the steering
            pink_found = navigator.find_parking_wall(on_track(data["pink_mask"], track_mask),
                                                     direction, frame)

            pink_angle = None
            pink_y = None
            if pink_found is not None:
                pink_angle = navigator.get_parking_wall_steer_angle(
                    direction, pink_found[0], pink_found[1], park.pink_aim_x, park.pink_kp, frame)
                pink_y = pink_found[1]

            # a pillar only wins if it is clearly nearer than the wall (the margin stops flip-flopping)
            # and has not been passed yet
            pillar_is_closer = (
                pillar_found is not None
                and pillar_found[1] < PILLAR_TOO_CLOSE_Y
                and (pink_y is None or pillar_found[1] > pink_y + PARK_PILLAR_MARGIN)
            )

            if pillar_is_closer:
                angle = navigator.get_forced_pillar_steer_angle(
                    pillar_found[0], pillar_found[1], park.pillar_aim_x, park.pillar_kp, direction, frame)
                smoothed_pink = None
                pink_lost_frames = 0
            elif pink_angle is not None:
                if smoothed_pink is None:
                    smoothed_pink = pink_angle
                else:
                    smoothed_pink = PARK_PINK_SMOOTH * smoothed_pink + (1 - PARK_PINK_SMOOTH) * pink_angle
                pink_lost_frames = 0
                angle = smoothed_pink
            elif smoothed_pink is not None and pink_lost_frames < PARK_PINK_HOLD_FRAMES:
                pink_lost_frames += 1
                angle = smoothed_pink  # the pink wall flickered out, hold the last steering
            else:
                smoothed_pink = None
                # no pink wall in view: wall follow with the gentle gains so it does not swing hard
                blue_area = cv2.countNonZero(on_track(data["blue_mask"], track_mask))
                orange_area = cv2.countNonZero(on_track(data["orange_mask"], track_mask))
                wall_angle = navigator.area_wall_follow_angle(
                    track_image, direction, blue_area=blue_area, orange_area=orange_area,
                    damped=True, display_frame=frame,
                )
                outer_crash = navigator.is_hitting_outer_wall(direction, track_image, frame)
                angle = navigator.turn_into_corner(direction) if outer_crash else wall_angle

            arduino.set_steering_angle(round(angle))
            self._show(frame)

            # arrived once the pink wall is low enough in the frame and lined up with the aim point
            if pink_found is not None:
                close_enough = pink_found[1] >= park.reach_y
                alongside = abs(pink_found[0] - park.pink_aim_x) <= park.reach_x_tolerance
                if close_enough and alongside:
                    arduino.stop(immediate=True)
                    return

    def _reverse_into_parking_spot(self, park):
        # drive forward past the spot along the outer wall, reverse until the pink wall shows up
        # behind the robot, then back in with three fixed reverse turns
        profile = self.profile
        arduino = self.arduino
        navigator = self.navigator
        direction = self.start_direction

        # the outer wall is on the opposite side to the driving direction
        follow_side = Direction.RIGHT if direction == Direction.LEFT else Direction.LEFT

        # small nudge to straighten out before following the wall
        left_run = direction == Direction.LEFT
        straighten_angle = (STEER_CENTER + PARK_STRAIGHTEN_STEER_OFFSET if left_run
                            else STEER_CENTER - PARK_STRAIGHTEN_STEER_OFFSET)
        arduino.set_steering_angle(straighten_angle, duration=PARK_STRAIGHTEN_TIME)
        arduino.set_steering_angle(STEER_CENTER)

        arduino.stop(immediate=True)
        time.sleep(PARK_STOP_DELAY)

        # forward along the outer wall for a fixed time
        arduino.drive(MOTOR_FORWARD, park.entry_speed)
        end_time = time.time() + park.entry_time
        while time.time() < end_time:
            data = process_frame(self.picam2.capture_array(), profile, with_pink=True)
            frame = data["frame"].copy()

            draw_detection_boxes(frame, {"pink": data["pink_mask"], "green": data["green_mask"],
                                         "red": data["red_mask"]})
            angle = navigator.single_wall_follow_angle(data["track_image"], follow_side,
                                                       park.entry_target_area, frame)
            arduino.set_steering_angle(round(angle))
            self._show(frame)

        arduino.stop(immediate=True)
        time.sleep(PARK_SHORT_DELAY)

        # reverse almost straight until the pink wall is visible behind the robot
        arduino.set_steering_angle(STEER_CENTER + park.back_steer_offset)
        arduino.drive(MOTOR_REVERSE, park.back_speed)
        while True:
            frame = capture_cropped_frame(self.picam2).copy()
            masks = get_detection_masks(frame)
            draw_detection_boxes(frame, masks)
            self._show(frame)
            if cv2.countNonZero(masks["pink"]) > PARK_WALL_SEEN_AREA:
                break

        arduino.stop(immediate=True)
        time.sleep(PARK_STOP_DELAY)

        # short forward hop to line up before the final reverse turns
        arduino.set_steering_angle(STEER_CENTER + park.hop_steer_offset)
        arduino.drive(MOTOR_FORWARD, PARK_SPEED, park.hop_ticks)
        arduino.stop(immediate=True)
        time.sleep(PARK_STOP_DELAY)

        # reverse turns: full lock toward the track, straight, then full lock the other way.
        # the two locks swap for a right run because it is the mirror image
        first_turn = profile.park_steer_min if left_run else profile.park_steer_max
        second_turn = profile.park_steer_max if left_run else profile.park_steer_min
        for angle, ticks in zip((first_turn, STEER_CENTER, second_turn), park.turn_ticks):
            arduino.set_park_steering(angle)
            time.sleep(park.pre_delay)
            arduino.drive(MOTOR_REVERSE, PARK_SPEED, ticks)
            arduino.stop(immediate=True)
            time.sleep(park.settle)


if __name__ == "__main__":
    RobotController().run()
