import math

import cv2
import numpy as np

from utils.constants import (
    AFTER_PILLAR_CLIP_FRAMES,
    AFTER_PILLAR_MAX_STEER_OFFSET,
    AREA_WALL_KD_DAMPED,
    AREA_WALL_KP_DAMPED,
    CORNER_BOOST_FRAMES,
    CORNER_DROP_RATIO,
    CORNER_KD_BOOST,
    CORNER_KP_BOOST,
    CORNER_MAX_STEER,
    CORNER_MIN_PREV_AREA,
    CORNER_NO_WALL_STEER,
    CRASH_MARKER_COLOR,
    FIRST_QUARTER_CORNER_MARKER_AREA,
    FIRST_QUARTER_CORNER_STEER,
    FIRST_QUARTER_CORNER_TURN,
    FRAME_HEIGHT,
    FRAME_WIDTH,
    GREEN_PILLAR_KP,
    GREEN_PILLAR_TARGET_X,
    INNER_WALL_FAR_X,
    INNER_WALL_FAR_Y,
    INNER_WALL_NEAR_X,
    INNER_WALL_NEAR_Y,
    INNER_WALL_SAMPLE_POINTS,
    MIN_PARK_WALL_AREA,
    MIN_PILLAR_AREA,
    NO_WALL_MARKER_STEER,
    NO_WALL_STEER,
    OPEN_WALL_TARGET_AREA,
    OPENING_BOOST_ADD,
    OPENING_BOOST_MULT,
    OUTER_WALL_CHECK_Y,
    PARK_PINK_MAX_OFFSET,
    PARK_WALL_MAX_Y,
    PARK_WALL_MIN_Y,
    PARK_WALL_STEER_OFFSET_DEG,
    PILLAR_BOOST_SPEED,
    PILLAR_STEER_OFFSET_DEG,
    PILLAR_TOO_CLOSE_Y,
    PILLAR_TRACK_START_Y,
    RED_PILLAR_KP,
    RED_PILLAR_TARGET_X,
    SINGLE_WALL_KD,
    SINGLE_WALL_KP,
    SINGLE_WALL_NO_WALL_STEER,
    SINGLE_WALL_ROI_LEFT,
    SINGLE_WALL_ROI_RIGHT,
    SPEED_DECEL_STEP,
    STEER_CENTER,
    TURN_MARKER_ENTER_AREA,
    WALL_OPENING_AREA,
)
from utils.enums import Direction, WallState
from utils.image_utils import draw_wall_rois


def _line_points(near_point, far_point, n):
    # n evenly spaced (y, x) sample points between two points
    y_vals = np.linspace(near_point[0], far_point[0], n).round().astype(int)
    x_vals = np.linspace(near_point[1], far_point[1], n).round().astype(int)
    return y_vals, x_vals


# The inner wall crash check samples the same line every frame, so it is worked out once.
# The line runs from near the robot to further ahead on the inner side.
INNER_WALL_POINTS = {
    Direction.RIGHT: _line_points((INNER_WALL_NEAR_Y, FRAME_WIDTH - INNER_WALL_NEAR_X),
                                  (INNER_WALL_FAR_Y, FRAME_WIDTH - INNER_WALL_FAR_X),
                                  INNER_WALL_SAMPLE_POINTS),
    Direction.LEFT: _line_points((INNER_WALL_NEAR_Y, INNER_WALL_NEAR_X),
                                 (INNER_WALL_FAR_Y, INNER_WALL_FAR_X),
                                 INNER_WALL_SAMPLE_POINTS),
}

# The outer wall crash check is a single pixel straight ahead of the robot, as (y, x).
OUTER_WALL_POINT = (OUTER_WALL_CHECK_Y, FRAME_WIDTH // 2)


class PillarNavigator:
    # Works out every steering angle from the camera masks: wall crash checks, pillar
    # avoidance, the pink parking wall and the three kinds of wall following.
    # It never talks to the motors, it only hands angles back to the state machine.
    # profile is the ChallengeProfile, so the same maths runs with open or obstacle numbers.
    def __init__(self, profile):
        self.profile = profile

        # pillar avoidance
        self.last_steer_angle = STEER_CENTER
        self.state = WallState.NONE
        self.inner_wall_warning = False
        self.tracking_pillar = False
        self.post_pass_frames = 0
        self.last_pillar_y = None

        # memory of the wall followers, needed for their D terms
        self.prev_area_wall_error = 0.0
        self.prev_single_wall_area = None
        self.prev_open_wall_area = None
        self.first_quarter_target = None
        self.corner_frames_left = 0

    def _clamp(self, angle):
        return max(self.profile.steer_min, min(self.profile.steer_max, angle))

    def turn_into_corner(self, direction):
        # near-full lock toward the inside of the corner
        if direction == Direction.LEFT:
            return self.profile.steer_max - 3
        return self.profile.steer_min + 3

    # ------------------------------------------------------------------
    # wall crash checks
    # ------------------------------------------------------------------

    def is_hitting_inner_wall(self, direction, track_image, display_frame=None):
        # true if any sample point on the inner side lies on a wall pixel
        y_vals, x_vals = INNER_WALL_POINTS[direction]
        if display_frame is not None:
            for y, x in zip(y_vals, x_vals):
                cv2.circle(display_frame, (int(x), int(y)), 3, CRASH_MARKER_COLOR, -1)
            cv2.line(display_frame, (int(x_vals[0]), int(y_vals[0])),
                     (int(x_vals[-1]), int(y_vals[-1])), CRASH_MARKER_COLOR, 1)
        return not track_image[y_vals, x_vals].all()

    def is_hitting_outer_wall(self, direction, track_image, display_frame=None):
        # true if the point straight ahead lies on a wall pixel
        if display_frame is not None:
            cv2.circle(display_frame, (OUTER_WALL_POINT[1], OUTER_WALL_POINT[0]), 5, CRASH_MARKER_COLOR, -1)
        return bool(track_image[OUTER_WALL_POINT] == 0)

    # ------------------------------------------------------------------
    # pillars
    # ------------------------------------------------------------------

    def find_nearest_pillar(self, green_mask, red_mask, display_frame=None):
        # returns (x_center, y_center, is_green) of the pillar closest to the robot, or None
        robot_point = (FRAME_WIDTH // 2, FRAME_HEIGHT)

        closest_distance = float("inf")
        closest = None

        for mask, is_green in ((green_mask, True), (red_mask, False)):
            if not cv2.countNonZero(mask):
                continue
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                if cv2.contourArea(cnt) <= MIN_PILLAR_AREA:
                    continue

                x, y, w, h = cv2.boundingRect(cnt)
                x_center = x + w // 2
                y_center = y + h // 2

                distance = math.dist((x_center, y_center), robot_point)
                if distance >= closest_distance:
                    continue

                closest_distance = distance
                closest = (x_center, y_center, w, h, is_green)

        if closest is None:
            return None

        x_center, y_center, w, h, is_green = closest
        if display_frame is not None:
            cv2.rectangle(display_frame, (x_center - w // 2, y_center - h // 2),
                          (x_center + w // 2, y_center + h // 2),
                          (0, 255, 0) if is_green else (0, 0, 255), 2)
        return x_center, y_center, is_green

    def get_steer_angle(self, direction, green_mask, red_mask, track_image, display_frame=None):
        # Priority: wall warnings, then pillar avoidance. Returns None when neither applies,
        # which tells the state machine to fall back to wall following.
        self.inner_wall_warning = False

        found = self.find_nearest_pillar(green_mask, red_mask, display_frame)
        pillar_present = found is not None
        self.last_pillar_y = found[1] if pillar_present else None

        outer_crash = self.is_hitting_outer_wall(direction, track_image, display_frame)
        # the inner wall only matters while a pillar is pushing the robot toward it
        inner_crash = (self.is_hitting_inner_wall(direction, track_image, display_frame)
                       if pillar_present else False)

        turn_into_corner = self.turn_into_corner(direction)

        # wall state machine: it latches into INNER or OUTER and stays there until the crash clears
        if self.state == WallState.NONE:
            if inner_crash:
                self.state = WallState.INNER
                self.inner_wall_warning = True
                return None
            elif outer_crash:
                self.state = WallState.OUTER
                return turn_into_corner
        elif self.state == WallState.INNER:
            if not pillar_present or not inner_crash:
                self.state = WallState.NONE
            else:
                self.inner_wall_warning = True
                return None
        elif self.state == WallState.OUTER:
            if not outer_crash:
                self.state = WallState.NONE
            else:
                return turn_into_corner

        if not pillar_present:
            if self.tracking_pillar:
                self.post_pass_frames = AFTER_PILLAR_CLIP_FRAMES  # pillar just left the view
            self.tracking_pillar = False
            return None

        x_center, y_center, is_green = found

        if y_center > PILLAR_TRACK_START_Y:
            if y_center > PILLAR_TOO_CLOSE_Y:
                return None  # already passed it
            self.tracking_pillar = True
            return self.last_steer_angle  # too close to recompute cleanly, keep the last angle

        self.tracking_pillar = True
        self.post_pass_frames = 0

        steer_angle = self.get_color_based_pillar_steer_angle(x_center, y_center, is_green, display_frame)
        self.last_steer_angle = steer_angle
        return steer_angle

    def get_color_based_pillar_steer_angle(self, x_center, y_center, is_green, display_frame=None):
        # a line is aimed from the pillar to a target point at the bottom of the frame and the
        # angle of that line is turned into a steering angle
        target_x = GREEN_PILLAR_TARGET_X if is_green else RED_PILLAR_TARGET_X
        if display_frame is not None:
            self._draw_aim(display_frame, x_center, y_center, target_x, (0, 255, 0) if is_green else (0, 0, 255))

        horizontal_distance = x_center - target_x
        vertical_distance = FRAME_HEIGHT - y_center
        pillar_angle_deg = math.degrees(math.atan2(horizontal_distance, vertical_distance))

        if is_green:
            steer_angle = STEER_CENTER - ((pillar_angle_deg + PILLAR_STEER_OFFSET_DEG) * GREEN_PILLAR_KP)
        else:
            steer_angle = STEER_CENTER - ((pillar_angle_deg - PILLAR_STEER_OFFSET_DEG) * RED_PILLAR_KP)

        return self._clamp(steer_angle)

    def get_forced_pillar_steer_angle(self, x_center, y_center, aim_x, kp, direction, display_frame=None):
        # used on the parking approach: the pillar is always passed on the outer wall side
        # (left for a left run, right for a right run) whatever its colour
        if display_frame is not None:
            self._draw_aim(display_frame, x_center, y_center, aim_x, (0, 255, 255))

        horizontal_distance = x_center - aim_x
        vertical_distance = FRAME_HEIGHT - y_center
        pillar_angle_deg = math.degrees(math.atan2(horizontal_distance, vertical_distance))

        offset = -PILLAR_STEER_OFFSET_DEG if direction == Direction.LEFT else PILLAR_STEER_OFFSET_DEG
        steer_angle = STEER_CENTER - ((pillar_angle_deg + offset) * kp)
        return self._clamp(steer_angle)

    def clip_after_pillar(self, angle):
        # for a few frames after passing a pillar the steering is limited so the robot does not jerk back
        if self.post_pass_frames <= 0:
            return angle
        self.post_pass_frames -= 1
        return max(STEER_CENTER - AFTER_PILLAR_MAX_STEER_OFFSET,
                   min(angle, STEER_CENTER + AFTER_PILLAR_MAX_STEER_OFFSET))

    def update_drive_speed(self, current_speed):
        # no pillar: cruise. pillar far away: boost. pillar close: slow down step by step
        cruise_speed = self.profile.drive_speed
        if self.last_pillar_y is None:
            return cruise_speed
        if self.last_pillar_y > PILLAR_TRACK_START_Y:
            return max(cruise_speed, current_speed - SPEED_DECEL_STEP)
        return PILLAR_BOOST_SPEED

    @staticmethod
    def _draw_aim(display_frame, x_center, y_center, aim_x, color):
        cv2.line(display_frame, (x_center, y_center), (aim_x, FRAME_HEIGHT), color, 2)
        cv2.line(display_frame, (x_center, y_center), (x_center, FRAME_HEIGHT), color, 2)

    # ------------------------------------------------------------------
    # parking wall (pink)
    # ------------------------------------------------------------------

    @staticmethod
    def find_parking_wall(pink_mask, direction, display_frame=None):
        # Of the two largest pink blobs the largest is used, unless the second one is further
        # toward the track side. Walls that are too high (far) or too low (close) are ignored.
        # returns (x_center, y_center) or None
        if not cv2.countNonZero(pink_mask):
            return None
        contours, _ = cv2.findContours(pink_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        blobs = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area <= MIN_PARK_WALL_AREA:
                continue
            x, y, w, h = cv2.boundingRect(cnt)
            blobs.append((area, x + w // 2, y + h // 2, w, h))

        if not blobs:
            return None

        blobs.sort(key=lambda blob: blob[0], reverse=True)
        best = blobs[0]
        if len(blobs) > 1:
            second = blobs[1]
            further = second[1] > best[1] if direction == Direction.RIGHT else second[1] < best[1]
            if further:
                best = second

        _, x_center, y_center, w, h = best
        if y_center > PARK_WALL_MAX_Y or y_center < PARK_WALL_MIN_Y:
            return None

        if display_frame is not None:
            cv2.rectangle(display_frame, (x_center - w // 2, y_center - h // 2),
                          (x_center + w // 2, y_center + h // 2), (255, 0, 255), 2)
        return x_center, y_center

    def get_parking_wall_steer_angle(self, direction, x_center, y_center, aim_x, kp, display_frame=None):
        # steers toward the pink wall with a gentle gain and a tight steering limit
        if display_frame is not None:
            self._draw_aim(display_frame, x_center, y_center, aim_x, (255, 0, 255))

        horizontal_distance = x_center - aim_x
        vertical_distance = FRAME_HEIGHT - y_center
        wall_angle_deg = math.degrees(math.atan2(horizontal_distance, vertical_distance))

        offset = PARK_WALL_STEER_OFFSET_DEG if direction == Direction.LEFT else -PARK_WALL_STEER_OFFSET_DEG
        steer_angle = STEER_CENTER - ((wall_angle_deg + offset) * kp)
        return max(STEER_CENTER - PARK_PINK_MAX_OFFSET, min(STEER_CENTER + PARK_PINK_MAX_OFFSET, steer_angle))

    # ------------------------------------------------------------------
    # wall following: two ROIs (obstacle laps and parking approach)
    # ------------------------------------------------------------------

    @staticmethod
    def mirror_roi(roi, width=FRAME_WIDTH):
        x1, y1, x2, y2 = roi
        return [width - x2, y1, width - x1, y2]

    def get_wall_rois(self, direction):
        # the ROIs are tuned for a left run, so a right run mirrors them and swaps the sides
        left_roi, right_roi = self.profile.left_wall_roi, self.profile.right_wall_roi
        if direction == Direction.LEFT:
            return left_roi, right_roi
        return self.mirror_roi(right_roi), self.mirror_roi(left_roi)

    @staticmethod
    def largest_wall_area(track_image, roi, min_area=50):
        # area of the biggest wall blob inside the ROI, 0 if there is none
        x1, y1, x2, y2 = roi
        region = track_image[y1:y2, x1:x2]
        if region.size == 0:
            return 0
        wall_mask = cv2.bitwise_not(region)  # walls are black in the track image
        contours, _ = cv2.findContours(wall_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return 0
        area = cv2.contourArea(max(contours, key=cv2.contourArea))
        return area if area > min_area else 0

    def area_wall_follow_angle(self, track_image, direction, blue_area=0, orange_area=0,
                               damped=False, display_frame=None):
        # PD controller that balances the wall area of the left ROI against the right ROI
        kp = AREA_WALL_KP_DAMPED if damped else self.profile.area_wall_kp
        kd = AREA_WALL_KD_DAMPED if damped else self.profile.area_wall_kd

        roi_left, roi_right = self.get_wall_rois(direction)
        if display_frame is not None:
            draw_wall_rois(display_frame, (roi_left, roi_right))
        area_left = self.largest_wall_area(track_image, roi_left)
        area_right = self.largest_wall_area(track_image, roi_right)

        # when one side opens up, the other side is boosted so the robot commits to the turn
        if area_left < WALL_OPENING_AREA and area_right > 100:
            area_right = area_right * OPENING_BOOST_MULT + OPENING_BOOST_ADD
        elif area_right < WALL_OPENING_AREA and area_left > 100:
            area_left = area_left * OPENING_BOOST_MULT + OPENING_BOOST_ADD

        wall_error = area_left - area_right
        derivative = wall_error - self.prev_area_wall_error
        control = (wall_error * kp) + (derivative * kd)
        self.prev_area_wall_error = wall_error

        angle = STEER_CENTER - control

        # no wall on either side means the robot is deep in a corner, the marker decides how hard to turn
        if area_left == 0 and area_right == 0:
            turn_sign = 1 if direction == Direction.LEFT else -1
            if blue_area > TURN_MARKER_ENTER_AREA or orange_area > TURN_MARKER_ENTER_AREA:
                angle = STEER_CENTER + turn_sign * NO_WALL_MARKER_STEER
            else:
                angle = STEER_CENTER + turn_sign * NO_WALL_STEER

        return self._clamp(angle)

    # ------------------------------------------------------------------
    # wall following: single ROI (forward drive along the outer wall while parking)
    # ------------------------------------------------------------------

    def single_wall_follow_angle(self, track_image, side, target_area, display_frame=None):
        # holds one wall at target_area. more area = too close so steer away, less = steer toward
        roi = SINGLE_WALL_ROI_LEFT if side == Direction.LEFT else SINGLE_WALL_ROI_RIGHT
        if display_frame is not None:
            draw_wall_rois(display_frame, [roi])

        wall_area = self.largest_wall_area(track_image, roi)
        turn_sign = 1 if side == Direction.LEFT else -1  # +1 = toward the wall

        if wall_area == 0:
            self.prev_single_wall_area = None  # avoids a derivative kick when the wall comes back
            return self._clamp(STEER_CENTER + turn_sign * SINGLE_WALL_NO_WALL_STEER)

        wall_error = wall_area - target_area
        derivative = 0.0 if self.prev_single_wall_area is None else wall_area - self.prev_single_wall_area
        control = (wall_error * SINGLE_WALL_KP) + (derivative * SINGLE_WALL_KD)
        self.prev_single_wall_area = wall_area

        angle = STEER_CENTER - control if side == Direction.LEFT else STEER_CENTER + control
        return self._clamp(angle)

    # ------------------------------------------------------------------
    # wall following: open challenge (single ROI on the inner wall, with corner handling)
    # ------------------------------------------------------------------

    def open_wall_follow_angle(self, track_image, direction, marker_area, first_quarter,
                               display_frame=None):
        # Keeps the inner wall at a target area with a PD controller.
        # First quarter: the target is the area seen when the wall first appeared, and the robot
        # drives straight while no wall is visible.
        # Later quarters: the target is OPEN_WALL_TARGET_AREA.
        # Corners: when the wall area collapses in one frame, the gains are boosted for a short window.
        roi = self.get_wall_rois(direction)[0 if direction == Direction.LEFT else 1]
        if display_frame is not None:
            draw_wall_rois(display_frame, [roi])

        wall_area = self.largest_wall_area(track_image, roi)
        turn_sign = 1 if direction == Direction.LEFT else -1  # +1 = toward the wall

        # corner detection, checked before prev_open_wall_area is reset so a drop to 0 is caught
        if self.prev_open_wall_area is not None and self.prev_open_wall_area >= CORNER_MIN_PREV_AREA:
            drop = self.prev_open_wall_area - wall_area
            if drop > CORNER_DROP_RATIO * self.prev_open_wall_area:
                self.corner_frames_left = CORNER_BOOST_FRAMES
        in_corner = self.corner_frames_left > 0
        if in_corner:
            self.corner_frames_left -= 1

        if first_quarter:
            if wall_area == 0:
                self.prev_open_wall_area = None
                wall_seen_before = self.first_quarter_target is not None
                if FIRST_QUARTER_CORNER_TURN and (wall_seen_before
                                                  or marker_area > FIRST_QUARTER_CORNER_MARKER_AREA):
                    # the wall vanished after it was being followed (or the marker shows): first corner
                    angle = STEER_CENTER + turn_sign * FIRST_QUARTER_CORNER_STEER
                else:
                    angle = STEER_CENTER
                return self._clamp(angle)

            if self.first_quarter_target is None:
                self.first_quarter_target = wall_area  # lock in the starting distance
            target_area = self.first_quarter_target
        else:
            target_area = OPEN_WALL_TARGET_AREA

        wall_error = wall_area - target_area
        derivative = 0.0 if self.prev_open_wall_area is None else wall_area - self.prev_open_wall_area
        kp = self.profile.area_wall_kp * (CORNER_KP_BOOST if in_corner else 1.0)
        kd = self.profile.area_wall_kd * (CORNER_KD_BOOST if in_corner else 1.0)
        control = (wall_error * kp) + (derivative * kd)
        self.prev_open_wall_area = wall_area

        angle = STEER_CENTER - control if direction == Direction.LEFT else STEER_CENTER + control

        # no wall visible after the first quarter: turn toward the wall, harder if a corner is happening
        if wall_area == 0:
            if in_corner:
                angle = STEER_CENTER + turn_sign * CORNER_NO_WALL_STEER
            elif marker_area > TURN_MARKER_ENTER_AREA:
                angle = STEER_CENTER + turn_sign * NO_WALL_MARKER_STEER
            else:
                angle = STEER_CENTER + turn_sign * NO_WALL_STEER

        if in_corner:
            angle = max(STEER_CENTER - CORNER_MAX_STEER, min(STEER_CENTER + CORNER_MAX_STEER, angle))
        return self._clamp(angle)
