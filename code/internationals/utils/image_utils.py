# helper functions that turn a camera frame into the masks the robot steers from.
# nothing in here remembers anything between frames, which is why it's utils and not a class

import cv2
import numpy as np

from utils.constants import (
    CAMERA_HEIGHT,
    CAMERA_WIDTH,
    CLEAN_KERNEL,
    COLOR_RANGES,
    FRAME_HEIGHT,
    FRAME_WIDTH,
)

# every colour process_frame can hand back a mask for
MARKER_COLORS = ("blue", "orange", "green", "red")


def crop_frame(image, x_start, x_end, y_start, y_end):
    return image[y_start:y_end, x_start:x_end]


def crop_to_track(raw_frame):
    # keep the bottom FRAME_HEIGHT rows, the top of the picture is above the walls
    return crop_frame(raw_frame, 0, CAMERA_WIDTH, CAMERA_HEIGHT - FRAME_HEIGHT, CAMERA_HEIGHT)


def capture_cropped_frame(picam2):
    return crop_to_track(picam2.capture_array())


def get_color_mask(lab_image, color):
    lower, upper = COLOR_RANGES[color]
    mask = cv2.inRange(lab_image, lower, upper)

    # open then close to get rid of noise and fill gaps
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, CLEAN_KERNEL)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, CLEAN_KERNEL)
    return mask


def on_track(mask, track_mask):
    # drop anything the mask picked up outside the track
    return cv2.bitwise_and(mask, track_mask)


def split_floor_from_walls(grayscale_image, gray_threshold):
    # floor comes out white, walls come out black
    blurred_image = cv2.bilateralFilter(grayscale_image, 9, 75, 75)
    _, binary_image = cv2.threshold(blurred_image, gray_threshold, 255, cv2.THRESH_BINARY)
    return binary_image


def get_track_boundary(binary_image, outline_epsilon):
    contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # only keep the blob the robot is standing on
    robot_point = (FRAME_WIDTH / 2, FRAME_HEIGHT - 10)
    contour = None
    best_area = -1.0
    for cnt in contours:
        if cv2.pointPolygonTest(cnt, robot_point, False) >= 0:
            area = cv2.contourArea(cnt)
            if area > best_area:
                contour, best_area = cnt, area

    if contour is None:
        return binary_image, np.zeros_like(binary_image)

    epsilon = outline_epsilon * cv2.arcLength(contour, True)
    track_outline = cv2.approxPolyDP(contour, epsilon, True)

    track_mask = np.zeros_like(binary_image)
    cv2.fillPoly(track_mask, [track_outline], 255)
    return cv2.bitwise_and(binary_image, track_mask), track_mask


def process_frame(raw_frame, profile, with_pink=False):
    # profile is the ChallengeProfile for this run. it decides the threshold and
    # which colours are worth looking for (open only needs the blue line)
    frame = crop_to_track(raw_frame)
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)

    # colours this challenge doesn't use just get an empty mask
    empty_mask = np.zeros(frame.shape[:2], np.uint8)
    masks = {color: empty_mask for color in MARKER_COLORS}
    marker_mask = empty_mask.copy()
    for color in profile.marker_colors:
        masks[color] = get_color_mask(lab, color)
        marker_mask = cv2.bitwise_or(marker_mask, masks[color])

    pink_mask = None
    if with_pink:
        pink_mask = get_color_mask(lab, "pink")
        marker_mask = cv2.bitwise_or(marker_mask, pink_mask)

    # paint the markers white so they don't get read as a wall
    grayscale_image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    grayscale_image = cv2.bitwise_or(grayscale_image, marker_mask)
    binary_image = split_floor_from_walls(grayscale_image, profile.gray_threshold)
    clean_image = cv2.morphologyEx(binary_image, cv2.MORPH_CLOSE, CLEAN_KERNEL)

    track_image, track_mask = get_track_boundary(clean_image, profile.track_outline_epsilon)

    return {
        "blue_mask": masks["blue"],
        "orange_mask": masks["orange"],
        "green_mask": masks["green"],
        "red_mask": masks["red"],
        "pink_mask": pink_mask,
        "track_image": track_image,
        "track_mask": track_mask,
    }
