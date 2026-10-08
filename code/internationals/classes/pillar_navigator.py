import math

import cv2
import numpy as np

from utils.constants import (
    AREA_WALL_KD_DAMPED,
    AREA_WALL_KP_DAMPED,
    FORCED_ALIGN_POINT_Y,
    FRAME_HEIGHT,
    FRAME_WIDTH,
    GREEN_PILLAR_KP,
    GREEN_PILLAR_TARGET_X,
    INNER_WALL_SAMPLE_POINTS,
    MIN_PARK_WALL_AREA,
    MIN_PILLAR_AREA,
    OPENING_BOOST_ADD,
    OPENING_BOOST_MULT,
    PARK_WALL_STEER_OFFSET_DEG,
    PILLAR_STEER_OFFSET_DEG,
    PILLAR_TOO_CLOSE_Y,
    PILLAR_TRACK_START_Y,
    RED_PILLAR_KP,
    RED_PILLAR_TARGET_X,
    STEER_CENTER,
    TURN_MARKER_ENTER_AREA,
    WALL_OPENING_AREA,
)
from utils.enums import Direction, WallState


def _line_points(near_point, far_point, n):
    y_vals = np.linspace(near_point[0], far_point[0], n).round().astype(int)
    x_vals = np.linspace(near_point[1], far_point[1], n).round().astype(int)
    return y_vals, x_vals


# the inner wall crash check samples the same points every frame so work them out once
INNER_WALL_POINTS = {
    Direction.RIGHT: _line_points((FRAME_HEIGHT - 60, FRAME_WIDTH - 170),
                                  (FRAME_HEIGHT - 120, FRAME_WIDTH - 220), INNER_WALL_SAMPLE_POINTS),
    Direction.LEFT: _line_points((FRAME_HEIGHT - 60, 170),
                                 (FRAME_HEIGHT - 120, 220), INNER_WALL_SAMPLE_POINTS),
}

# the outer wall crash check is one pixel straight ahead of the robot
OUTER_WALL_POINT = (FRAME_HEIGHT - 138, FRAME_WIDTH // 2)


class PillarNavigator:
    # works out every steering angle from the camera masks: the wall crash points,
    # pillar dodging, the parking wall and both kinds of wall following.
    # it never talks to the motors, it just hands angles back to the state machine.
    # profile is the ChallengeProfile, so the same maths runs with open or obstacle numbers
    def __init__(self, profile):
        self.profile = profile
        self.last_steer_angle = STEER_CENTER
        self.state = WallState.NONE
        self.inner_wall_warning = False
        self.last_pillar_color = None
        self.last_pillar_y = None

        # last error of each wall follower, needed for the D term
        self.prev_area_wall_error = 0.0
        self.prev_point_wall_error = 0.0

    def _clamp(self, angle):
        return max(self.profile.steer_min, min(self.profile.steer_max, angle))

    # ------------------------------------------------------------------
    # crash points
    # ------------------------------------------------------------------

    def is_hitting_inner_wall(self, direction, track_image):
        y_vals, x_vals = INNER_WALL_POINTS[direction]
        return not track_image[y_vals, x_vals].all()

    def is_hitting_outer_wall(self, direction, track_image):
        return track_image[OUTER_WALL_POINT] == 0

    # ------------------------------------------------------------------
    # pillars
    # ------------------------------------------------------------------

    def find_nearest_pillar(self, green_mask, red_mask):
        robot_point = (FRAME_WIDTH // 2, FRAME_HEIGHT)

        closest_distance = float("inf")
        closest = None

        for mask, is_green in ((green_mask, True), (red_mask, False)):
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area <= MIN_PILLAR_AREA:
                    continue

                x, y, w, h = cv2.boundingRect(cnt)
                x_center = x + w // 2
                y_center = y + h // 2

                distance = math.dist((x_center, y_center), robot_point)
                if distance >= closest_distance:
                    continue

                closest_distance = distance
                closest = (x_center, y_center, is_green)

        return closest

    def get_steer_angle(self, direction, green_mask, red_mask, track_image, force_right_avoid=False):
        # wall warnings first, then pillars, otherwise None so it falls back to wall following
        self.inner_wall_warning = False

        found = self.find_nearest_pillar(green_mask, red_mask)
        pillar_present = found is not None
        self.last_pillar_y = found[1] if pillar_present else None

        outer_crash = self.is_hitting_outer_wall(direction, track_image)
        # only check the inner wall if a pillar is pushing us toward it
        inner_crash = self.is_hitting_inner_wall(direction, track_image) if pillar_present else False

        turn_into_corner = ((self.profile.steer_max - 3) if direction == Direction.LEFT
                            else (self.profile.steer_min + 3))

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

        if found is None:
            return None

        x_center, y_center, is_green = found
        self.last_pillar_color = "green" if is_green else "red"

        if force_right_avoid:
            is_green = False  # always pass on the right

        if y_center > PILLAR_TRACK_START_Y:
            if y_center > PILLAR_TOO_CLOSE_Y:
                return None
            return self.last_steer_angle

        steer_angle = self.get_color_based_pillar_steer_angle(x_center, y_center, is_green)
        self.last_steer_angle = steer_angle
        return steer_angle

    def get_color_based_pillar_steer_angle(self, x_center, y_center, is_green):
        # green pillars get passed on the right, red on the left
        target_x = GREEN_PILLAR_TARGET_X if is_green else RED_PILLAR_TARGET_X

        horizontal_distance = x_center - target_x
        vertical_distance = FRAME_HEIGHT - y_center

        pillar_angle_deg = math.degrees(math.atan2(horizontal_distance, vertical_distance))

        if is_green:
            steer_angle = STEER_CENTER - ((pillar_angle_deg + PILLAR_STEER_OFFSET_DEG) * GREEN_PILLAR_KP)
        else:
            steer_angle = STEER_CENTER - ((pillar_angle_deg - PILLAR_STEER_OFFSET_DEG) * RED_PILLAR_KP)

        return self._clamp(steer_angle)

    def get_forced_pillar_steer_angle(self, x_center, y_center, aim_x, kp):
        # used while parking, always passes on the right
        horizontal_distance = x_center - aim_x
        vertical_distance = FRAME_HEIGHT - y_center

        pillar_angle_deg = math.degrees(math.atan2(horizontal_distance, vertical_distance))

        steer_angle = STEER_CENTER - ((pillar_angle_deg - PILLAR_STEER_OFFSET_DEG) * kp)
        return self._clamp(steer_angle)

    # ------------------------------------------------------------------
    # parking wall (pink)
    # ------------------------------------------------------------------

    @staticmethod
    def find_parking_wall(pink_mask):
        # picks the pink blob furthest up the frame
        contours, _ = cv2.findContours(pink_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        best_y = float("inf")
        best = None

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area <= MIN_PARK_WALL_AREA:
                continue

            x, y, w, h = cv2.boundingRect(cnt)
            x_center = x + w // 2
            y_center = y + h // 2

            if y_center >= best_y:
                continue

            best_y = y_center
            best = (x_center, y_center)

        return best

    def get_parking_wall_steer_angle(self, x_center, y_center, kp):
        horizontal_distance = x_center - FRAME_WIDTH
        vertical_distance = FRAME_HEIGHT - y_center

        wall_angle_deg = math.degrees(math.atan2(horizontal_distance, vertical_distance))

        steer_angle = STEER_CENTER - ((wall_angle_deg + PARK_WALL_STEER_OFFSET_DEG) * kp)
        return max(self.profile.park_steer_min, min(self.profile.park_steer_max, steer_angle))

    # ------------------------------------------------------------------
    # area wall following (used while driving laps, in both challenges)
    # ------------------------------------------------------------------

    @staticmethod
    def mirror_roi(roi, width=FRAME_WIDTH):
        x1, y1, x2, y2 = roi
        return [width - x2, y1, width - x1, y2]

    def get_wall_rois(self, direction):
        # ROIs were set for one direction, so mirror them for the other
        left_roi, right_roi = self.profile.left_wall_roi, self.profile.right_wall_roi
        if direction == Direction.LEFT:
            return left_roi, right_roi
        return self.mirror_roi(right_roi), self.mirror_roi(left_roi)

    @staticmethod
    def largest_wall_area(track_image, roi, min_area=50):
        x1, y1, x2, y2 = roi
        region = track_image[y1:y2, x1:x2]
        if region.size == 0:
            return 0
        wall_mask = cv2.bitwise_not(region)
        contours, _ = cv2.findContours(wall_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return 0
        area = cv2.contourArea(max(contours, key=cv2.contourArea))
        return area if area > min_area else 0

    def area_wall_follow_angle(self, track_image, direction, blue_area=0, orange_area=0, damped=False):
        # steer toward the side with less wall
        kp = AREA_WALL_KP_DAMPED if damped else self.profile.area_wall_kp
        kd = AREA_WALL_KD_DAMPED if damped else self.profile.area_wall_kd

        roi_left, roi_right = self.get_wall_rois(direction)
        area_left = self.largest_wall_area(track_image, roi_left)
        area_right = self.largest_wall_area(track_image, roi_right)

        # if one side is basically empty, treat it as an opening and commit to the turn
        if area_left < WALL_OPENING_AREA and area_right > 100:
            area_right = area_right * OPENING_BOOST_MULT + OPENING_BOOST_ADD
        elif area_right < WALL_OPENING_AREA and area_left > 100:
            area_left = area_left * OPENING_BOOST_MULT + OPENING_BOOST_ADD

        wall_error = area_left - area_right
        derivative = wall_error - self.prev_area_wall_error
        control = (wall_error * kp) + (derivative * kd)
        self.prev_area_wall_error = wall_error

        angle = STEER_CENTER - control

        # no walls at all, use the corner marker to pick how hard to turn
        if area_left == 0 and area_right == 0:
            turn_sign = 1 if direction == Direction.LEFT else -1
            if blue_area > TURN_MARKER_ENTER_AREA or orange_area > TURN_MARKER_ENTER_AREA:
                angle = STEER_CENTER + turn_sign * 35
            else:
                angle = STEER_CENTER + turn_sign * 20

        return self._clamp(angle)

    # ------------------------------------------------------------------
    # point wall following (used for the parking states)
    # ------------------------------------------------------------------

    @staticmethod
    def find_wall_point(track_image, track_mask, direction):
        # looks at only the half of the frame on the side we're following and
        # returns the wall pixel closest to the robot, or None if there isn't one
        width = track_image.shape[1]
        mid = width // 2

        # wall = black pixels that are inside the track outline
        side_wall = cv2.bitwise_and(cv2.bitwise_not(track_image), track_mask)
        if direction == Direction.LEFT:
            side_wall[:, mid:] = 0
        else:
            side_wall[:, :mid] = 0

        contours, _ = cv2.findContours(side_wall, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None

        points = np.concatenate(contours)
        xs = points[:, 0, 0]
        ys = points[:, 0, 1]

        # closest to the robot = lowest in the frame, then furthest across
        lowest = ys == ys.max()
        return int(xs[lowest].max()), int(ys.max())

    @staticmethod
    def point_wall_error(point, direction, target_x, target_y):
        # how far the wall point is from where we want it, as one number
        point_x, point_y = point
        error_y = max(0.0, target_y - point_y)
        error_x = (target_x - point_x) if direction == Direction.LEFT else (point_x - target_x)
        return error_y + error_x

    def estimate_point_wall_error(self, track_image, track_mask, direction, target_x, target_y):
        # used to seed prev_point_wall_error before a PD loop starts, so the
        # first derivative term isn't a random jump
        point = self.find_wall_point(track_image, track_mask, direction)
        if point is None:
            return 0.0
        return self.point_wall_error(point, direction, target_x, target_y)

    def _point_wall_angle(self, error, direction, kp, kd, min_angle, max_angle):
        derivative = error - self.prev_point_wall_error
        control = (kp * error) + (kd * derivative)
        self.prev_point_wall_error = error

        low = self.profile.steer_min if min_angle is None else min_angle
        high = self.profile.steer_max if max_angle is None else max_angle
        turn_sign = 1 if direction == Direction.LEFT else -1
        angle = STEER_CENTER + turn_sign * control
        return max(low, min(high, angle))

    def follow_wall_point(self, track_image, track_mask, direction, target_x, target_y, kp, kd,
                          min_angle=None, max_angle=None):
        # PD steering that tries to hold the wall point on the target
        point = self.find_wall_point(track_image, track_mask, direction)
        if point is None:
            return STEER_CENTER

        error = self.point_wall_error(point, direction, target_x, target_y)
        return self._point_wall_angle(error, direction, kp, kd, min_angle, max_angle)

    def follow_wall_point_forced(self, direction, target_x, target_y, kp, kd,
                                 forced_x, forced_y=FORCED_ALIGN_POINT_Y,
                                 min_angle=None, max_angle=None):
        # same PD as follow_wall_point but with a made-up wall point instead of
        # one from the camera, for a short blind alignment step
        error = self.point_wall_error((forced_x, forced_y), direction, target_x, target_y)
        return self._point_wall_angle(error, direction, kp, kd, min_angle, max_angle)
