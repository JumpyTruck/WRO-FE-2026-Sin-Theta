import time

import cv2
from picamera2 import Picamera2
import RPi.GPIO as GPIO
from gpiozero import LED

from classes.arduino_comms import ArduinoComms
from classes.lap_counter import LapCounter
from classes.pillar_navigator import PillarNavigator
from utils.challenge_profile import CHALLENGE_PROFILE_OBSTACLE, CHALLENGE_PROFILE_OPEN
from utils.constants import (
    APPROACH_WALL_KP,
    APPROACH_WALL_TARGET_X_LEFT,
    APPROACH_WALL_TARGET_Y,
    CAMERA_HEIGHT,
    CAMERA_WARMUP_TIME,
    CAMERA_WIDTH,
    CHALLENGE_PINK_MIN_AREA,
    EXIT_PARK_SPEED,
    EXIT_PARK_TICKS,
    FORCE_RIGHT_AVOID_DELAY_AFTER_GREEN,
    FORCE_RIGHT_AVOID_DELAY_AFTER_RED,
    FORCED_ALIGN_POINT_X,
    FORCED_ALIGN_POINT_Y,
    FORCED_ALIGN_TIME,
    FRAME_WIDTH,
    INNER_WALL_KD,
    INNER_WALL_KP,
    MOTOR_FORWARD,
    MOTOR_REVERSE,
    PARK_APPROACH_X_TOLERANCE,
    PARK_ENTRY_TARGET_X_RIGHT,
    PARK_ENTRY_TARGET_Y,
    PARK_SPEED,
    PARK_WALL_SEEN_AREA,
    PILLAR_ACCEL_MIN_Y,
    PILLAR_BOOST_SPEED,
    PILLAR_TRACK_START_Y,
    SPEED_DECEL_STEP,
    START_BUTTON_PIN,
    STATUS_LED_PIN,
    STEER_CENTER,
    TOTAL_QUARTER_TURNS,
    U_TURN_TICKS,
)
from utils.enums import Challenge, Direction, RunState
from utils.image_utils import (
    capture_cropped_frame,
    get_color_mask,
    on_track,
    process_frame,
    split_floor_from_walls,
)
from utils.park_profile import PARK_PROFILE_LEFT_RUN, PARK_PROFILE_RIGHT_RUN


class RobotController:
    # the state machine for the whole run. each state is one _state_ method
    # that does its job and then sets self.state to whatever comes next.
    #
    # open:     button > camera > detect challenge > laps > finished
    # obstacle: button > camera > detect challenge > direction > exit park > laps
    #           > (u-turn on a right run) > park > finished
    def __init__(self):
        self.state = RunState.WAIT_FOR_BUTTON
        self.arduino = ArduinoComms()
        self.picam2 = None

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(START_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self.status_led = LED(STATUS_LED_PIN)

        # the numbers for whichever challenge we're in, set by DETECT_CHALLENGE
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
            RunState.UTURN_TO_PARKING_WALL: self._state_uturn_to_parking_wall,
            RunState.APPROACH_PARKING_SPOT: self._state_approach_parking_spot,
        }

    def run(self):
        while self.state != RunState.FINISHED:
            handler = self._handlers[self.state]
            handler()
        self._cleanup()

    def _cleanup(self):
        if self.picam2 is not None:
            self.picam2.stop()
        self.arduino.close()

    def _pink_area(self):
        frame = capture_cropped_frame(self.picam2)
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        return cv2.countNonZero(get_color_mask(lab, "pink"))

    # ------------------------------------------------------------------
    # getting ready
    # ------------------------------------------------------------------

    def _state_wait_for_button(self):
        # LED on = waiting for the start button
        self.status_led.on()
        while GPIO.input(START_BUTTON_PIN) == GPIO.HIGH:
            time.sleep(0.005)
        self.status_led.off()
        self.state = RunState.WARM_UP_CAMERA

    def _state_warm_up_camera(self):
        self.picam2 = Picamera2()
        sensor_mode = self.picam2.sensor_modes[1]
        sensor_width, sensor_height = sensor_mode["size"]
        config = self.picam2.create_video_configuration(
            raw={"size": (sensor_width, sensor_height)},
            main={"format": "RGB888", "size": (CAMERA_WIDTH, CAMERA_HEIGHT)},
            controls={"FrameRate": 30},
        )
        self.picam2.configure(config)
        self.picam2.start()

        # let the exposure settle
        end_time = time.time() + CAMERA_WARMUP_TIME
        while time.time() < end_time:
            capture_cropped_frame(self.picam2)

        self.state = RunState.DETECT_CHALLENGE

    def _state_detect_challenge(self):
        # the obstacle challenge starts inside the parking spot, so the pink walls
        # are right in front of the camera. no pink means it's the open challenge
        if self._pink_area() >= CHALLENGE_PINK_MIN_AREA:
            self.profile = CHALLENGE_PROFILE_OBSTACLE
            self.state = RunState.DETECT_START_DIRECTION
        else:
            self.profile = CHALLENGE_PROFILE_OPEN
            self.start_direction = self.profile.fixed_direction
            self.state = RunState.DRIVE_LAPS

        self.arduino.use_profile(self.profile)

    def _state_detect_start_direction(self):
        # whichever half has more open floor is the direction
        frame = capture_cropped_frame(self.picam2)
        binary_image = split_floor_from_walls(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
                                              self.profile.gray_threshold)

        width = binary_image.shape[1]
        left_white = cv2.countNonZero(binary_image[:, :width // 2])
        right_white = cv2.countNonZero(binary_image[:, width // 2:])

        self.start_direction = Direction.RIGHT if right_white > left_white else Direction.LEFT
        self.state = RunState.EXIT_START_PARK

    def _state_exit_start_park(self):
        # turn away from the track and nose out of the box
        profile = self.profile
        left_run = self.start_direction == Direction.LEFT
        away_angle = profile.park_steer_max if left_run else profile.park_steer_min

        self.arduino.set_park_steering(away_angle)
        time.sleep(0.3)
        self.arduino.drive(MOTOR_FORWARD, EXIT_PARK_SPEED, EXIT_PARK_TICKS)

        self.arduino.set_steering_angle(STEER_CENTER)
        self.state = RunState.DRIVE_LAPS

    # ------------------------------------------------------------------
    # laps (both challenges)
    # ------------------------------------------------------------------

    def _state_drive_laps(self):
        profile = self.profile
        open_run = profile.challenge == Challenge.OPEN
        direction = self.start_direction
        # only an obstacle run going right has to turn around before it can park
        needs_uturn = not open_run and direction == Direction.RIGHT
        # open always counts the blue line, obstacle counts whichever line it reaches first
        counts_blue = open_run or direction == Direction.LEFT

        arduino = self.arduino
        capture = self.picam2.capture_array
        lap_counter = self.lap_counter = LapCounter(direction, profile)
        navigator = self.navigator = PillarNavigator(profile)

        # the u-turn happens after one extra corner
        turns_needed = TOTAL_QUARTER_TURNS + 1 if needs_uturn else TOTAL_QUARTER_TURNS
        laps_done_time = None

        current_speed = profile.drive_speed
        previous_speed = profile.drive_speed
        decelerating = False

        arduino.drive(MOTOR_FORWARD, profile.drive_speed)

        while True:
            data = process_frame(capture(), profile)
            track_image = data["track_image"]
            track_mask = data["track_mask"]

            blue_area = cv2.countNonZero(on_track(data["blue_mask"], track_mask))
            orange_area = cv2.countNonZero(on_track(data["orange_mask"], track_mask))

            lap_counter.update(blue_area if counts_blue else orange_area)
            quarter_turns = lap_counter.quarter_turns
            if not open_run and quarter_turns >= turns_needed:
                break
            if laps_done_time is None and quarter_turns >= TOTAL_QUARTER_TURNS:
                laps_done_time = time.time()

            pillar_angle = None
            if not open_run:
                # after the last lap, force right avoid once the delay for the last pillar colour has passed
                force_right_avoid = False
                if needs_uturn and laps_done_time is not None:
                    if navigator.last_pillar_color == "green":
                        delay = FORCE_RIGHT_AVOID_DELAY_AFTER_GREEN
                    else:
                        delay = FORCE_RIGHT_AVOID_DELAY_AFTER_RED
                    force_right_avoid = (time.time() - laps_done_time) >= delay

                pillar_angle = navigator.get_steer_angle(
                    direction,
                    on_track(data["green_mask"], track_mask),
                    on_track(data["red_mask"], track_mask),
                    track_image,
                    force_right_avoid,
                )

                # speed up when a pillar is in view, slow down as we pass it
                pillar_y = navigator.last_pillar_y
                if pillar_y is not None and pillar_y > PILLAR_TRACK_START_Y:
                    decelerating = True

                if decelerating:
                    current_speed = max(profile.drive_speed, current_speed - SPEED_DECEL_STEP)
                    if current_speed <= profile.drive_speed:
                        decelerating = False
                elif pillar_y is not None and pillar_y > PILLAR_ACCEL_MIN_Y:
                    current_speed = PILLAR_BOOST_SPEED
                else:
                    current_speed = profile.drive_speed

                if current_speed != previous_speed:
                    arduino.drive(MOTOR_FORWARD, current_speed)
                    previous_speed = current_speed

            wall_angle = navigator.area_wall_follow_angle(
                track_image, direction, blue_area=blue_area, orange_area=orange_area,
                damped=navigator.inner_wall_warning,
            )

            # pillar dodging takes priority over wall following
            final_angle = pillar_angle if pillar_angle is not None else wall_angle
            arduino.set_steering_angle(round(final_angle))

            # open keeps wall following for a bit after the last corner so it stops in the start section
            if open_run and laps_done_time is not None:
                if time.time() - laps_done_time >= profile.finish_drive_time:
                    break

        if open_run:
            arduino.stop()
            arduino.set_steering_angle(STEER_CENTER)
            self.state = RunState.FINISHED
        elif needs_uturn:
            arduino.stop()
            self.state = RunState.UTURN_TO_PARKING_WALL
        else:
            self.state = RunState.APPROACH_PARKING_SPOT

    # ------------------------------------------------------------------
    # parking (obstacle only)
    # ------------------------------------------------------------------

    def _state_uturn_to_parking_wall(self):
        # full lock for a set number of ticks, then the approach finds the pink wall
        self.arduino.set_park_steering(self.profile.park_steer_max)
        self.arduino.drive(MOTOR_FORWARD, PARK_SPEED, U_TURN_TICKS)
        self.arduino.stop()
        self.arduino.set_steering_angle(STEER_CENTER)
        time.sleep(0.2)
        self.state = RunState.APPROACH_PARKING_SPOT

    def _state_approach_parking_spot(self):
        # both runs park the same way, right run just does it after the u-turn
        park = (PARK_PROFILE_LEFT_RUN if self.start_direction == Direction.LEFT
                else PARK_PROFILE_RIGHT_RUN)

        # fresh navigator so nothing from the laps carries over into parking
        self.navigator = PillarNavigator(self.profile)
        self._approach_pink_wall(park)
        self._reverse_into_parking_spot(park)
        self.state = RunState.FINISHED

    def _approach_pink_wall(self, park):
        # pillar closer than the wall > pink wall > wall following
        profile = self.profile
        arduino = self.arduino
        navigator = self.navigator
        capture = self.picam2.capture_array

        # by now we're always going round like a left run, so the wall to follow is on the left
        follow_side = Direction.LEFT
        target_x = APPROACH_WALL_TARGET_X_LEFT
        target_y = APPROACH_WALL_TARGET_Y

        # start the wall follow error from a real frame so the first D term isn't a jump
        data = process_frame(capture(), profile, with_pink=True)
        navigator.prev_point_wall_error = navigator.estimate_point_wall_error(
            data["track_image"], data["track_mask"], follow_side, target_x, target_y)

        arduino.drive(MOTOR_FORWARD, park.approach_speed)

        while True:
            data = process_frame(capture(), profile, with_pink=True)
            track_image = data["track_image"]
            track_mask = data["track_mask"]

            pillar_found = navigator.find_nearest_pillar(on_track(data["green_mask"], track_mask),
                                                         on_track(data["red_mask"], track_mask))
            pink_found = navigator.find_parking_wall(data["pink_mask"])

            # if a pillar is nearer than the parking wall, deal with it first
            if pillar_found is not None and (pink_found is None or pillar_found[1] > pink_found[1]):
                angle = navigator.get_forced_pillar_steer_angle(pillar_found[0], pillar_found[1],
                                                                park.pillar_aim_x, park.pillar_kp)
            elif pink_found is not None:
                angle = navigator.get_parking_wall_steer_angle(pink_found[0], pink_found[1], park.pink_kp)
            else:
                inner_crash = navigator.is_hitting_inner_wall(follow_side, track_image)
                outer_crash = navigator.is_hitting_outer_wall(follow_side, track_image)
                kp, kd = ((INNER_WALL_KP, INNER_WALL_KD) if inner_crash
                          else (APPROACH_WALL_KP, park.approach_wall_kd))
                wall_angle = navigator.follow_wall_point(track_image, track_mask, follow_side,
                                                         target_x, target_y, kp, kd)
                angle = (profile.steer_max - 3) if outer_crash else wall_angle

            arduino.set_steering_angle(round(angle))

            if pink_found is not None:
                close_enough = pink_found[1] >= park.reach_y
                alongside = abs(pink_found[0] - FRAME_WIDTH) <= PARK_APPROACH_X_TOLERANCE
                if close_enough and alongside:
                    arduino.stop(immediate=True)
                    return

    def _reverse_into_parking_spot(self, park):
        # follow the parking wall forward past the spot, then back in
        profile = self.profile
        arduino = self.arduino
        navigator = self.navigator
        capture = self.picam2.capture_array

        # the parking wall is on our right now
        follow_side = Direction.RIGHT
        target_x = PARK_ENTRY_TARGET_X_RIGHT
        target_y = PARK_ENTRY_TARGET_Y

        time.sleep(0.5)

        # short blind alignment first, the camera isn't reliable enough right
        # after the approach so steer off a made-up wall point instead
        navigator.prev_point_wall_error = navigator.point_wall_error(
            (FORCED_ALIGN_POINT_X, FORCED_ALIGN_POINT_Y), follow_side, target_x, target_y)
        angle = navigator.follow_wall_point_forced(follow_side, target_x, target_y,
                                                   park.entry_kp, park.entry_kd,
                                                   FORCED_ALIGN_POINT_X, FORCED_ALIGN_POINT_Y,
                                                   profile.park_steer_min, profile.park_steer_max)
        arduino.drive(MOTOR_FORWARD, park.entry_speed)
        arduino.set_park_steering(round(angle))
        time.sleep(FORCED_ALIGN_TIME)

        # now follow the real wall, starting the error from a real frame again
        data = process_frame(capture(), profile, with_pink=True)
        navigator.prev_point_wall_error = navigator.estimate_point_wall_error(
            data["track_image"], data["track_mask"], follow_side, target_x, target_y)

        end_time = time.time() + park.entry_time
        while time.time() < end_time:
            data = process_frame(capture(), profile, with_pink=True)
            angle = navigator.follow_wall_point(data["track_image"], data["track_mask"], follow_side,
                                                target_x, target_y, park.entry_kp, park.entry_kd,
                                                profile.park_steer_min, profile.park_steer_max)
            arduino.set_park_steering(round(angle))

        arduino.stop()
        time.sleep(0.3)

        arduino.set_steering_angle(STEER_CENTER - 1)
        arduino.drive(MOTOR_REVERSE, park.back_speed)

        # reverse until the pink wall is visible behind us
        while self._pink_area() <= PARK_WALL_SEEN_AREA:
            pass

        arduino.stop(immediate=True)
        time.sleep(park.settle)

        arduino.set_steering_angle(STEER_CENTER)
        arduino.drive(MOTOR_FORWARD, PARK_SPEED, park.hop_ticks)
        arduino.stop(immediate=True)
        time.sleep(park.settle)

        # hard left, straight, hard right
        park_angles = (profile.park_steer_min, STEER_CENTER, profile.park_steer_max)
        for angle, ticks in zip(park_angles, park.turn_ticks):
            arduino.set_park_steering(angle)
            time.sleep(park.pre_delay)
            arduino.drive(MOTOR_REVERSE, PARK_SPEED, ticks)
            arduino.stop(immediate=True)
            time.sleep(park.settle)

        arduino.set_steering_angle(STEER_CENTER)


if __name__ == "__main__":
    RobotController().run()
