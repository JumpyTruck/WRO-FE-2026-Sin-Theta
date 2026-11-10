# Helper functions that turn a camera frame into the masks the robot steers from.
# Nothing in here remembers anything between frames, which is why it lives in utils and not a class.

from concurrent.futures import ThreadPoolExecutor

import cv2
import numpy as np

from utils.constants import (
    CAMERA_HEIGHT,
    CAMERA_WIDTH,
    CLEAN_KERNEL,
    COLOR_RANGES,
    FRAME_HEIGHT,
    FRAME_WIDTH,
    LINE_DETECT_MIN_AREA,
    MASK_POOL_WORKERS,
    MIN_PARK_WALL_AREA,
    MIN_PILLAR_AREA,
)
from utils.enums import Direction

# OpenCV releases the GIL, so one thread per colour mask really does use several cores
MASK_POOL = ThreadPoolExecutor(max_workers=MASK_POOL_WORKERS)

# every colour process_frame can return a mask for (pink is optional and handled separately)
MARKER_COLORS = ("blue", "orange", "green", "red")


def crop_frame(image, x_start, x_end, y_start, y_end):
    return image[y_start:y_end, x_start:x_end]


def crop_to_track(raw_frame):
    # keeps the bottom FRAME_HEIGHT rows, the top of the picture is above the walls
    return crop_frame(raw_frame, 0, CAMERA_WIDTH, CAMERA_HEIGHT - FRAME_HEIGHT, CAMERA_HEIGHT)


def capture_cropped_frame(picam2):
    return crop_to_track(picam2.capture_array())


def get_color_mask(lab_image, color):
    lower, upper = COLOR_RANGES[color]
    mask = cv2.inRange(lab_image, lower, upper)

    if not cv2.countNonZero(mask):
        return mask  # nothing found, cleaning would leave it empty anyway

    # open removes small specks, close fills small holes inside real blobs
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, CLEAN_KERNEL)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, CLEAN_KERNEL)
    return mask


def on_track(mask, track_mask):
    # drops anything the mask picked up outside the drivable area
    return cv2.bitwise_and(mask, track_mask)


def split_floor_from_walls(grayscale_image, gray_threshold):
    # floor comes out white, walls come out black
    blurred_image = cv2.bilateralFilter(grayscale_image, 9, 75, 75)
    _, binary_image = cv2.threshold(blurred_image, gray_threshold, 255, cv2.THRESH_BINARY)
    return binary_image


def get_track_boundary(binary_image, outline_epsilon):
    # finds the floor blob the robot is standing on and masks everything else out.
    # returns (track_image, track_mask)
    contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # a point just in front of the robot decides which floor blob is the track
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
    # one pass over a camera frame: crop, colour masks and the drivable track.
    # profile decides the threshold and which colours are worth masking
    frame = crop_to_track(raw_frame)
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)

    colors = list(profile.marker_colors) + (["pink"] if with_pink else [])
    futures = {color: MASK_POOL.submit(get_color_mask, lab, color) for color in colors}

    # the grayscale conversion runs on this thread while the masks are being computed
    grayscale_image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # colours this challenge does not use get an empty mask so callers never need to check
    empty_mask = np.zeros(frame.shape[:2], np.uint8)
    masks = {color: empty_mask for color in MARKER_COLORS}
    pink_mask = None
    marker_mask = empty_mask
    for color, future in futures.items():
        mask = future.result()
        if color == "pink":
            pink_mask = mask
        else:
            masks[color] = mask
        marker_mask = cv2.bitwise_or(marker_mask, mask)

    # painting markers white stops lines, pillars and the pink wall from being read as walls
    grayscale_image = cv2.bitwise_or(grayscale_image, marker_mask)
    binary_image = split_floor_from_walls(grayscale_image, profile.gray_threshold)
    clean_image = cv2.morphologyEx(binary_image, cv2.MORPH_CLOSE, CLEAN_KERNEL)

    track_image, track_mask = get_track_boundary(clean_image, profile.track_outline_epsilon)

    return {
        "frame": frame,
        "blue_mask": masks["blue"],
        "orange_mask": masks["orange"],
        "green_mask": masks["green"],
        "red_mask": masks["red"],
        "pink_mask": pink_mask,
        "track_image": track_image,
        "track_mask": track_mask,
    }


# ------------------------------------------------------------------
# open challenge: direction from the closest line
# ------------------------------------------------------------------

def get_line_y(mask):
    # lowest row of the frame that contains the line, or None if the line is not visible
    if cv2.countNonZero(mask) < LINE_DETECT_MIN_AREA:
        return None
    rows = np.flatnonzero(mask.any(axis=1))
    return int(rows[-1])


def detect_line_direction(blue_mask, orange_mask):
    # the line closest to the robot sits lowest in the frame (largest y).
    # orange closer = RIGHT, blue closer = LEFT, no line in view = None
    blue_y = get_line_y(blue_mask)
    orange_y = get_line_y(orange_mask)

    if blue_y is None and orange_y is None:
        return None
    if orange_y is None:
        return Direction.LEFT
    if blue_y is None:
        return Direction.RIGHT
    return Direction.LEFT if blue_y > orange_y else Direction.RIGHT


# ------------------------------------------------------------------
# drawing (overlays for the recorded video)
# ------------------------------------------------------------------

def draw_wall_rois(frame, rois, color=(255, 204, 0)):
    for x1, y1, x2, y2 in rois:
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    return frame


def get_detection_masks(frame):
    # pink wall and pillar masks of a cropped frame
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    return {color: get_color_mask(lab, color) for color in ("pink", "green", "red")}


def draw_detection_boxes(frame, masks=None):
    # boxes around the pink wall and the pillars, kept visible during blocking parking moves
    if masks is None:
        masks = get_detection_masks(frame)

    for color, box_color, min_area in (("pink", (255, 0, 255), MIN_PARK_WALL_AREA),
                                       ("green", (0, 255, 0), MIN_PILLAR_AREA),
                                       ("red", (0, 0, 255), MIN_PILLAR_AREA)):
        mask = masks.get(color)
        if mask is None or not cv2.countNonZero(mask):
            continue
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            if cv2.contourArea(cnt) <= min_area:
                continue
            x, y, w, h = cv2.boundingRect(cnt)
            cv2.rectangle(frame, (x, y), (x + w, y + h), box_color, 2)
    return frame
