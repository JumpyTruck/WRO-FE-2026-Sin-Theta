# Libraries
import cv2
import math
import numpy as np
import time
from picamera2 import Picamera2
import threading
from time import sleep
from queue import Queue
import serial

# =========================
# ESP32 SERIAL
# =========================
ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
time.sleep(2)

# =========================
# MOTOR COMMAND SENTINELS  (must match the ESP32 sketch)
# =========================
MOTOR_START_CMD = 888       # drive forward
MOTOR_STOP_CMD = 999
MOTOR_BACKTRACK_CMD = 777   # reverse -- ESP32 sketch must implement this case

kernel = np.ones((5, 5), np.uint8)   # a 5x5 square kernel

motor_command_queue = Queue()
servo_angle_queue = Queue()


# =========================
# LOW-LEVEL SERIAL SENDERS
# =========================
def send_motor_start():
    ser.write(f"{MOTOR_START_CMD}\n".encode())
    print("[motor] START sent to ESP32")


def send_motor_stop():
    ser.write(f"{MOTOR_STOP_CMD}\n".encode())
    print("[motor] STOP sent to ESP32")


def send_motor_backtrack():
    ser.write(f"{MOTOR_BACKTRACK_CMD}\n".encode())
    print("[motor] BACKTRACK sent to ESP32")


def send_angle(angle):
    ser.write(f"{angle}\n".encode())


# =========================
# THREADS (same structure/logic as before, PCA9685 calls swapped for serial)
# =========================
def motor_drive():
    current_command = None
    while True:
        command = motor_command_queue.get()
        if command is None:
            break
        if command == current_command:
            continue

        if command == "drive":
            print("Drive")
            send_motor_start()

        elif command == "backtrack":
            # brief brake helps some drivers before reversing
            send_motor_stop()
            time.sleep(0.05)
            send_motor_backtrack()
            print("BACKTRACK...")

        elif command == "stop":
            print("Stop")
            send_motor_stop()

        current_command = command


def servo_move():
    current_angle = None
    while True:
        angle = servo_angle_queue.get()  # Wait for new command

        if angle is None:
            # No "disable torque" equivalent over this serial protocol --
            # simply stop sending updates (ESP32 keeps last angle).
            current_angle = None
            print("Servo disabled")
            break
        else:
            #print("ANGLE VALUE:", angle)
            send_angle(angle)
            current_angle = angle

        time.sleep(0.005)


# Helper for largest contour info inside a binary ROI-mask
def largest_contour_info(mask, roi_origin):
    # mask should already be the ROI-sized mask (not full frame)
    contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
    if not contours:
        return 0, None, 0
    largest = max(contours, key=cv2.contourArea)
    area = int(cv2.contourArea(largest))
    x, y, w, h = cv2.boundingRect(largest)
    abs_x = x + roi_origin[0]
    abs_y = y + roi_origin[1]
    return area, (abs_x, abs_y, w, h), h


def main():
    t1 = threading.Thread(target=motor_drive, name='t1')
    t2 = threading.Thread(target=servo_move, name='t2')
    t1.start()
    t2.start()

    run()

    t1.join()
    t2.join()


def run():

    # Camera Setup -- use the full sensor via the raw stream so we get the
    # complete FOV (same approach as the open challenge code), then have
    # the ISP scale the "main" stream down to the resolution the rest of
    # this file's ROIs/logic expect (640x480).
    picam2 = Picamera2()

    sensor_mode = picam2.sensor_modes[1]
    sensor_width, sensor_height = sensor_mode["size"]

    config = picam2.create_video_configuration(
        raw={"size": (sensor_width, sensor_height)},
        main={"format": "RGB888", "size": (640, 480)},
        controls={"FrameRate": 30}
    )
    picam2.configure(config)
    picam2.start()

    # small warm-up so the sensor/AWB/AE settle before we trust any frame
    for _ in range(10):
        picam2.capture_array()

    # Define ROIs
    ROI_LEFT_WALL = [30, 250, 120, 470]
    ROI_RIGHT_WALL = [510, 250, 600, 470]
    ROI_MAIN = [0, 150, 640, 350]
    #before 180
    ROI_LINE = [200, 320, 440, 370]
    ROI_CENTER = [150, 270, 490, 330]
    ROI_BLACK = [250, 400, 390, 450]   # x1, y1 (top), x2, y2 (bottom)
    ROI_UPP1 = [230, 240, 280, 290]
    ROI_UPP2 = [400, 240, 450, 290]

    # PD Steering - Pillars
    kp = 0.042
    #0.042
    kd = 0.0035

    # PD Steering - Walls
    kp_walls = 0.035
    kd_walls = 0.003

    yKp = 0.0010  # How much it should steer relative to the y-axis of the pillar (more if closer)

    # Color Ranges
    rBlack = [np.array([0, 110, 112]), np.array([60, 149, 154])]
    rBlue = [np.array([0, 0, 0]), np.array([200, 255, 125])]
    rOrange = [np.array([0, 162, 176]), np.array([255, 196, 204])]
    rGreen = [np.array([50, 60, 0]), np.array([106, 119, 255])]
    #[[50, 60, 0], [106, 119, 255]]

    rRed = [np.array([22, 141, 0]), np.array([112, 255, 255])]
    
    #[[22, 141, 0], [112, 255, 255]]

    rMagenta = [np.array([0, 166, 107]), np.array([255, 196, 144])]

    # Thresholds General
    line_threshold = 50
    pillar_threshold = 550

    # Angles
    default_servo = 65
    max_turn_degree = 25
    STEER_SIGN = -1  # new robot's steering is mirrored vs the old one

    # Obstacle Avoidance PD / Pillars + Wall
    target = 0
    Green_grav_const = 600  # min area of an obstacle/pillar necessary for it to start detecting
    Red_grac_const = 700

    backtrack_active = False
    backtrack_end_time = 0.0
    backtrack_duration = 1.0   # how long the backtrack should last (s)

    # NOTE ON THE CW/CCW FIX:
    # Both pillar targets get a small inward nudge while mid-turn, but only
    # toward the side that matches the current turn direction -- this keeps
    # the two colors' cornering behavior mirror-symmetric so the robot
    # handles clockwise (right-turn) and counterclockwise (left-turn) tracks
    # equally well. See the per-frame update further down.
    redTarget_base = 120
    redTarget = redTarget_base
    greenTarget_base = 600
    greenTarget = greenTarget_base

    # ERRORS
    pillar_error = 0
    prev_pillar_error = 0
    wall_error = 0
    prev_wall_error = 0

    # FPS calculation setup
    prev_time = time.time()

    # =========================================================
    # TURNING STATE MACHINE
    # =========================================================
    # Track corners are marked with a strip of colored tape in ROI_LINE:
    #   blue   -> this is a LEFT-hand corner
    #   orange -> this is a RIGHT-hand corner
    # The direction of the FIRST corner marker seen locks the direction for
    # the rest of the run (WRO track direction is constant), so we never
    # act on the "wrong" color again -- eliminates the double-detection /
    # direction-flip bugs in the old logic.
    #
    # States:
    #   "idle"    -> normal wall/pillar following, watching for a corner marker
    #   "turning" -> corner marker confirmed, steering gets an extra bias
    #                push toward turn_dir on top of normal obstacle avoidance
    #
    # Entry and exit both require several consecutive confirming frames
    # (debounce) so a single noisy frame can't trigger or cancel a turn.
    # A cooldown after each turn stops the same marker from being counted
    # twice, and a max-duration failsafe forces the turn to end even if the
    # marker is never cleanly lost (e.g. glare, motion blur).

    turn_state = "idle"          # "idle" | "turning"
    turn_dir = None              # "left" | "right" (locked after first corner)
    turn_counter = 0
    TOTAL_TURNS = 12             # 4 corners x 3 laps -- tune to your track/start position

    ENTRY_CONFIRM_FRAMES = 2     # consecutive frames seeing the marker before we commit to a turn
    EXIT_CONFIRM_FRAMES = 4      # consecutive clear frames before we consider the turn finished
    TURN_MIN_DURATION = 0.35     # seconds -- minimum time spent turning before exit is allowed
    TURN_MAX_DURATION = 3.0      # seconds -- hard failsafe so we can never get stuck "turning"
    TURN_COOLDOWN = 0.6          # seconds after a turn ends before we re-arm marker detection

    blue_confirm = 0
    orange_confirm = 0
    exit_confirm_count = 0
    turn_start_time = 0.0
    turn_cooldown_until = 0.0

    TURN_BIAS_BASE = 15          # base steering push (deg) applied while turning
    TURN_BIAS_GREEN_BONUS = 8    # extra push while a green pillar is being tracked mid-turn
    TURN_BIAS_RED_BONUS = 4      # extra push while a red pillar is being tracked mid-turn

    angle = default_servo

    # -------- FUNCTIONS ---------

    def display_roi(img, ROIs, color):
        for ROI in ROIs:
            img = cv2.line(img, (ROI[0], ROI[1]), (ROI[2], ROI[1]), color, 4)
            img = cv2.line(img, (ROI[0], ROI[1]), (ROI[0], ROI[3]), color, 4)
            img = cv2.line(img, (ROI[2], ROI[3]), (ROI[2], ROI[1]), color, 4)
            img = cv2.line(img, (ROI[2], ROI[3]), (ROI[0], ROI[3]), color, 4)

        return img

    def get_contours(ROI, lab, ranges):

        segmented_area = lab[ROI[1]: ROI[3], ROI[0]:ROI[2]]

        # Protect against invalid region
        if segmented_area is None or segmented_area.size == 0:
            return []

        mask = cv2.inRange(segmented_area, ranges[0], ranges[1])
        kernel = np.ones((5, 5), np.uint8)
        erode = cv2.erode(mask, kernel, iterations=1)
        dilate = cv2.dilate(erode, kernel)
        list_contour = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]

        return list_contour

    def get_red_contours(ROI, lab, rRed):

        segmented_area = lab[ROI[1]: ROI[3], ROI[0]:ROI[2]]

        # Protect against invalid region
        if segmented_area is None or segmented_area.size == 0:
            return []

        mask1 = cv2.inRange(segmented_area, rRed[0], rRed[1])
        kernel = np.ones((5, 5), np.uint8)
        erode = cv2.erode(mask1, kernel, iterations=1)
        dilate = cv2.dilate(erode, kernel)
        list_contour = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]

        return list_contour, dilate

    def detect_contour(contour, ROI, frame):

        maxArea = 0

        for cnt in contour:
            try:
                area = cv2.contourArea(cnt)
                if area > 100:
                    approx = cv2.approxPolyDP(cnt, 0.01 * cv2.arcLength(cnt, True), True)
                    x, y, w, h = cv2.boundingRect(approx)
                    abs_x = x + ROI[0]
                    abs_y = y + ROI[1]
                    cv2.rectangle(frame, (abs_x, abs_y), (abs_x + w, abs_y + h), (0, 255, 0), 2)

                    if area > maxArea:
                        maxArea = area
            except:
                print("Looking for vals")

        return maxArea

    def filter_pillars(contours, frame, closest_pillar_distance, pillar_threshold, ROI):
        """
        Filter through contours to find current pillar and returns pillar data
        """

        pillars = []
        if contours == []:
            pass
        else:
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area <= pillar_threshold:
                    continue  # start over again until it finds a pillar above threshold

                approx = cv2.approxPolyDP(cnt, 0.01 * cv2.arcLength(cnt, True), True)
                x, y, w, h = cv2.boundingRect(approx)

                x += ROI[0]
                y += ROI[1]

                pillar_distance = math.dist([x + w // 2, y], [320, 480])  # center top to center_bottom screen
                if pillar_distance >= closest_pillar_distance:
                    continue  # try again

                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 1)

                pillars.append({
                    "x": x + w // 2,  # Center of width
                    "y": y,
                    "h": h,
                    "w": w,
                    "area": area,
                    "distance": pillar_distance
                })

        return pillars

    # ----- MAIN LOOP --------
    time.sleep(1)
    motor_command_queue.put("drive")
    servo_angle_queue.put(default_servo)
    areaLineBlue = 0
    areaLineOrange = 0
    while True:

        if areaLineBlue > line_threshold:
            print("DETECTING BLUE")
        if areaLineOrange > line_threshold:
            print("DETECTING ORANGE")

        pillar_detected = None  # Stores the current pillar and next one if spotted

        # Pillar Closest Data
        closest_pillar_distance = 10000  # relatively large num, meant to be overridee
        closest_pillar_color = None
        closest_pillar_x = None
        closest_pillar_y = None
        closest_pillar_area = 0

        # Bias each pillar's target inward by the same amount, but only on
        # the side that matches the CURRENT turn direction. This is what
        # makes left-turn (CCW) and right-turn (CW) cornering symmetric --
        # previously only the red target was adjusted (for left turns),
        # which left right turns with no equivalent correction and caused
        # clockwise runs to fight themselves through corners. Uses the turn
        # state carried over from the previous frame -- one frame of
        # latency, negligible.
        turning_left = (turn_state == "turning" and turn_dir == "left")
        turning_right = (turn_state == "turning" and turn_dir == "right")

        redTarget = redTarget_base + (20 if turning_left else 0)
        greenTarget = greenTarget_base - (20 if turning_right else 0)

        # Setup display
        frame = picam2.capture_array()
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2Lab)
        frame = display_roi(frame, [ROI_LEFT_WALL, ROI_RIGHT_WALL, ROI_MAIN, ROI_CENTER, ROI_LINE, ROI_BLACK], (255, 204, 0))

        y1 = 0
        y2 = frame.shape[0]

        # Get contours of the Line, wall, pillar
        cLeftWall = get_contours(ROI_LEFT_WALL, lab, rBlack)
        cRightWall = get_contours(ROI_RIGHT_WALL, lab, rBlack)
        cCenterWall = get_contours(ROI_CENTER, lab, rBlack)

        cListLineOrange = get_contours(ROI_LINE, lab, rOrange)
        cListLineBlue = get_contours(ROI_LINE, lab, rBlue)

        cListPillarGreen = get_contours(ROI_MAIN, lab, rGreen)
        cListPillarRed, dilate = get_red_contours(ROI_MAIN, lab, rRed)

        cListCoreRed = get_contours(ROI_CENTER, lab, rRed)
        cListCoreGreen = get_contours(ROI_CENTER, lab, rGreen)
        cListCoreBlack = get_contours(ROI_BLACK, lab, rBlack)

        # Center black: we'll create a mask and analyze largest contour
        center_seg_black = lab[ROI_BLACK[1]:ROI_BLACK[3], ROI_BLACK[0]:ROI_BLACK[2]]
        black_mask = cv2.inRange(center_seg_black, rBlack[0], rBlack[1])
        black_mask = cv2.morphologyEx(black_mask, cv2.MORPH_OPEN, kernel, iterations=1)
        black_mask = cv2.morphologyEx(black_mask, cv2.MORPH_CLOSE, kernel, iterations=1)

        # Area of Lines
        areaLineOrange = detect_contour(cListLineOrange, ROI_LINE, frame)
        areaLineBlue = detect_contour(cListLineBlue, ROI_LINE, frame)

        # Wall areas
        areaLeft = detect_contour(cLeftWall, ROI_LEFT_WALL, frame)
        areaRight = detect_contour(cRightWall, ROI_RIGHT_WALL, frame)

        # CENTER FOR BACKTRACK
        areaRedCenter = detect_contour(cListCoreRed, ROI_CENTER, frame)
        areaGreenCenter = detect_contour(cListCoreGreen, ROI_CENTER, frame)

        # Compute largest black contour info for ROI_BLACK
        areaBlackCenter, black_bbox, black_box_h = largest_contour_info(black_mask, ROI_BLACK)

        # ----- RED PILLAR DETECTION ------

        PillarsRed = filter_pillars(cListPillarRed, frame, closest_pillar_distance, pillar_threshold, ROI_MAIN)

        for pillar in PillarsRed:

            if (pillar["area"] < closest_pillar_area * 0.9) and (pillar["distance"] > closest_pillar_distance * 0.9):
                continue

            if pillar["x"] < 20:
                pillar_detected = False
                continue

            elif (pillar["y"] + pillar["h"]) < 155:
                pillar_detected = False
                continue

            else:
                closest_pillar_distance = pillar["distance"]
                closest_pillar_color = "red"
                closest_pillar_x = pillar["x"]
                closest_pillar_y = pillar["y"]
                closest_pillar_area = pillar["area"]
                pillar_detected = True

        # ----- GREEN PILLAR DETECTION ------

        PillarsGreen = filter_pillars(cListPillarGreen, frame, closest_pillar_distance, pillar_threshold, ROI_MAIN)

        for pillar in PillarsGreen:

            if (pillar["area"] < closest_pillar_area * 0.9) and (pillar["distance"] > closest_pillar_distance * 0.9):
                continue

            if pillar["x"] > greenTarget:
                pillar_detected = False
                continue

            elif (pillar["y"] + pillar["h"]) < 155:
                pillar_detected = False
                continue

            else:
                closest_pillar_distance = pillar["distance"]
                closest_pillar_color = "green"
                closest_pillar_x = pillar["x"]
                closest_pillar_y = pillar["y"]
                closest_pillar_area = pillar["area"]
                pillar_detected = True

        # ---- TARGET SELECTION ----

        if closest_pillar_color == "red" and closest_pillar_area > Red_grac_const:
            target = redTarget
            cv2.line(frame, (redTarget, y1), (redTarget, y2), (0, 0, 255), 2)
        elif closest_pillar_color == "green" and closest_pillar_area > Green_grav_const:
            target = greenTarget
            cv2.line(frame, (greenTarget, y1), (greenTarget, y2), (0, 255, 0), 2)
        else:
            target = 0

        # =========================================================
        # TURN STATE MACHINE UPDATE
        # =========================================================
        now = time.time()

        # Debounced marker detection (per color, every frame)
        blue_confirm = blue_confirm + 1 if areaLineBlue > line_threshold else 0
        orange_confirm = orange_confirm + 1 if areaLineOrange > line_threshold else 0

        if turn_state == "idle":
            if now >= turn_cooldown_until:
                # Lock direction on first confirmed marker of the run
                if turn_dir is None:
                    if blue_confirm >= ENTRY_CONFIRM_FRAMES:
                        turn_dir = "left"
                        print(">> Track direction locked: LEFT (blue)")
                    elif orange_confirm >= ENTRY_CONFIRM_FRAMES:
                        turn_dir = "right"
                        print(">> Track direction locked: RIGHT (orange)")

                # Enter a turn only for the locked color -- the other color
                # is ignored for the rest of the run, so it can never be
                # mistaken for a corner marker.
                if turn_dir == "left" and blue_confirm >= ENTRY_CONFIRM_FRAMES:
                    turn_state = "turning"
                    turn_start_time = now
                    exit_confirm_count = 0
                elif turn_dir == "right" and orange_confirm >= ENTRY_CONFIRM_FRAMES:
                    turn_state = "turning"
                    turn_start_time = now
                    exit_confirm_count = 0

        elif turn_state == "turning":
            active_area = areaLineBlue if turn_dir == "left" else areaLineOrange
            turn_elapsed = now - turn_start_time

            if active_area < line_threshold:
                exit_confirm_count += 1
            else:
                exit_confirm_count = 0

            turn_should_exit = (
                turn_elapsed >= TURN_MIN_DURATION and exit_confirm_count >= EXIT_CONFIRM_FRAMES
            ) or (turn_elapsed >= TURN_MAX_DURATION)

            if turn_should_exit:
                turn_counter += 1
                print(f">> Turn {turn_counter}/{TOTAL_TURNS} complete ({turn_dir.upper()})")
                turn_state = "idle"
                turn_cooldown_until = now + TURN_COOLDOWN
                blue_confirm = 0
                orange_confirm = 0
                exit_confirm_count = 0

        # ------ PILLAR AVOIDING / WALL FOLLOWING (computes base_angle) ------
        # Same PD math as before -- just no longer writes to the servo queue
        # directly, so it can be combined with the turn bias below in a
        # single, unambiguous steering command per frame.

        if pillar_detected == True and not (closest_pillar_color == "green" and areaLeft >= 9000) and not (closest_pillar_color == "red" and areaRight >= 9000):

            if (closest_pillar_color == "green" and areaGreenCenter > 4000) or (closest_pillar_color == "red" and areaRedCenter > 4000):
                if not backtrack_active:
                    backtrack_active = True
                    backtrack_end_time = time.time() + backtrack_duration
                    motor_command_queue.put("backtrack")

            if closest_pillar_x is not None:
                pillar_error = abs(target - closest_pillar_x)
                derivative_term = pillar_error - prev_pillar_error

                offset = (kp * pillar_error) + (kd * derivative_term)
                offset = max(0, min(offset, max_turn_degree))

                if closest_pillar_color == "red":
                    base_angle = int(default_servo + STEER_SIGN * offset)
                else:  # green
                    base_angle = int(default_servo - STEER_SIGN * offset)

                base_angle = max(default_servo - max_turn_degree, min(base_angle, default_servo + max_turn_degree))
            else:
                pillar_error = 0
                base_angle = default_servo

        else:
            pillar_error = 0
            wall_error = areaLeft - areaRight
            wall_derivative_term = wall_error - prev_wall_error
            base_angle = int(default_servo + STEER_SIGN * ((wall_error * kp_walls) + (wall_derivative_term * kd_walls)))
            base_angle = max(default_servo - max_turn_degree, min(base_angle, default_servo + max_turn_degree))
            print("WALL FOLLOWING VALUE:", base_angle)

        # ------ APPLY TURN BIAS ON TOP OF NORMAL STEERING ------
        # Obstacle avoidance keeps running unmodified; while turning we just
        # push the resulting angle further toward the turn direction, with
        # extra push if a pillar of a given color is currently being tracked.

        final_angle = base_angle
        if turn_state == "turning":
            bonus = 0
            if closest_pillar_color == "green":
                bonus = TURN_BIAS_GREEN_BONUS
            elif closest_pillar_color == "red":
                bonus = TURN_BIAS_RED_BONUS
            bias = TURN_BIAS_BASE + bonus

            if turn_dir == "left":
                final_angle = base_angle - STEER_SIGN * bias
            else:
                final_angle = base_angle + STEER_SIGN * bias

        final_angle = max(default_servo - max_turn_degree, min(final_angle, default_servo + max_turn_degree))
        angle = int(final_angle)
        servo_angle_queue.put(angle)

        # ------ WALL AVOIDING / BACKTRACK (unchanged) ------
        DEBUG_WALL = False  # set True to print debug info while tuning

        roi_black_height = ROI_BLACK[3] - ROI_BLACK[1]
        roi_black_width = ROI_BLACK[2] - ROI_BLACK[0]
        roi_area = float(max(1, roi_black_height * roi_black_width))

        black_area = float(areaBlackCenter)
        black_box_h = int(black_box_h) if black_box_h is not None else 0

        black_fraction = black_area / roi_area
        free_fraction = 1.0 - black_fraction

        free_frac_thresh = 0.90
        free_frac_thresh_turn = 0.90
        box_height_frac_thresh = 0.90
        box_height_thresh = int(roi_black_height * box_height_frac_thresh)

        if not backtrack_active:
            trigger_free_thresh = free_frac_thresh_turn if turn_state == "turning" else free_frac_thresh

            if (black_fraction >= trigger_free_thresh) and (black_box_h <= box_height_thresh):
                backtrack_active = True
                backtrack_end_time = time.time() + backtrack_duration
                servo_angle_queue.put(int(default_servo - STEER_SIGN * 3))
                motor_command_queue.put("stop")
                time.sleep(0.05)
                motor_command_queue.put("backtrack")

        if backtrack_active:
            if time.time() >= backtrack_end_time:
                motor_command_queue.put("drive")
                backtrack_active = False

        # --- RESET
        prev_pillar_error = pillar_error
        prev_wall_error = wall_error

        # Calculate FPS
        current_time = time.time()
        fps = 1 / (current_time - prev_time)
        prev_time = current_time

        # Display FPS on frame
        cv2.putText(frame, f"FPS: {fps:.2f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"Turn: {turn_state} {turn_dir or ''} ({turn_counter}/{TOTAL_TURNS})", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        cv2.imshow('USB CameFd', frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('d'):
            motor_command_queue.put("stop")
            servo_angle_queue.put(None)

        elif key == ord('q'):
            motor_command_queue.put("stop")
            servo_angle_queue.put(None)
            picam2.stop()
            cv2.destroyAllWindows()
            break

        if turn_counter >= TOTAL_TURNS:
            print(f"Completed {TOTAL_TURNS} turns, stopping.")
            motor_command_queue.put("stop")
            break

    servo_angle_queue.put(default_servo)


print("START")
main()
