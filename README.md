# WRO-FE-2026-Sinθ 

## Introduction
Hello! This is our second year competing in WRO Future Engineers. Last year, two of us competed together on Team VHR Motors, and one of us was on Team The Robertos. This year we've come together to form Team Sinθ!

## The Team

## Performance Videos

### Open Challenge

### Obstacle Challenge

## The Robot

<table align="center">
  <tr>
    <td align="center">
      <b>Top View</b><br><br>
      <img width="220" alt="IMG_2360" src="https://github.com/user-attachments/assets/488c0949-fab7-4cdb-90b6-f47f4dfcaa29" />
    </td>
    <td align="center">
      <b>Right View</b><br><br>
      <img width="220" alt="IMG_2358" src="https://github.com/user-attachments/assets/101af993-0053-4d73-8710-59cf7fc3d8bc" />
    </td>
    <td align="center">
      <b>Front View</b><br><br>
      <img width="220"alt="IMG_2357" src="https://github.com/user-attachments/assets/9ec74514-c036-4e2a-9e0f-bb02dfa7063b" />
    </td>
  </tr>

  <tr>
    <td align="center">
      <b>Bottom View</b><br><br>
      <img width="220" alt="IMG_2361" src="https://github.com/user-attachments/assets/d67f76cc-255e-481e-a65d-cab145b7653c" />
    </td>
    <td align="center">
      <b>Left View</b><br><br>
      <img width="220" alt="IMG_2356" src="https://github.com/user-attachments/assets/09d1da9c-4b3d-48e9-953b-bf2d5d2d3519" />
    </td>
    <td align="center">
      <b>Rear View</b><br><br>
      <img width="220" alt="IMG_2359" src="https://github.com/user-attachments/assets/1868c46f-d27c-46af-9c2c-331342825c3c" />
    </td>
  </tr>
</table>


## Mobility & Mechanical Design

This section covers how our robot moves: the chassis structure, drivetrain, steering geometry, and wheels/differential. Each part was chosen and iterated on to maximize turning precision, stability, and reliability while keeping the robot compact enough for the WRO Future Engineers mat. Calculations behind our steering geometry and part choices are included below so the design can be understood and reproduced.

---

### 1) Robot Dimensions & Weight
The robot was sized to fit all electrical components while keeping the robot compact.
<img width="650" alt="Camera Dimensions Image" src="https://github.com/user-attachments/assets/df89dbee-9f2c-427c-88de-a55c871200e3"/>

[Why We Chose These Dimensions](models/README.md#1-basic-design-choices)

---

### 2) Drive System

For our drive system, we use a 12V DC Geared Motor. This motor has a built in encoder and since drivetrain needed enough torque to move the robot's mass while staying fast enough for the competition mat, without adding unnecessary complexity.

| Component | Selected Part |
|---|---|
| DC Motor | 12V DC Geared Motor |

The motor's integrated encoder gives us speed and distance feedback, which we use for autonomous control.

[More on Motor & Driver Choice](schemes#1-motorization--power-system)

---

### 3) Steering System

To reduce tire scrub and improve cornering accuracy, we use 100% Ackermann steering geometry instead of a simple parallel-arm setup. In 100% Ackermann steering, the inner wheel turns more than the outer wheel so every wheel is always turning on its own correct radius.

| Component | Selected Part |
|---|---|
| Steering Type | Ackermann Steering |
| Servo | Coreless Servo (Black) |

**Ackermann Angle Calculation**

With a wheelbase of 7.18" and a front track width of 3.00", we calculated the required steering angle as follows:

<img width="500" alt="427B2B3B-9996-4177-892A-580BC7953492" src="https://github.com/user-attachments/assets/ff6a7c61-41b9-4762-b412-8ba0603b11a1" />

This gives a target steering angle of ~12° at full lock to achieve true 100% Ackermann geometry.

[Why We Chose Ackermann](models/README.md#1-basic-design-choices)

---

### 4) Chassis Assembly

The chassis is built from three modular 3D-printed layers, each with dedicated mounting points for the electronics, motor, and steering assembly. This open, layered design means any section can be pulled off individually for repairs or upgrades, without disassembling the whole robot.

<div align="center">

<img width="1245" height="700" alt="First plate" src="https://github.com/user-attachments/assets/7763083b-e341-4566-9f6d-96d56026d52a" />
<img width="1248" height="700" alt="Second plate" src="https://github.com/user-attachments/assets/116feb86-e038-4e22-8e40-c2fecf43d38d" />
<img width="1333" height="748" alt="Third plate" src="https://github.com/user-attachments/assets/200b7d2b-a27e-4cb8-b80d-62d3f662c3f5" />

</div>

[More Pictures and Info Here](models/README.md#2-the-build)

---

### 5) Wheels & Differential

- **Wheels:** LEGO SPIKE Prime wheels — compact, consistent grip, and lightweight.
[Why We Chose These Wheels](models/README.md#1-basic-design-choices)

- **Differential:** Rear metal differential, allowing both drive wheels to rotate at different speeds while cornering. This reduces mechanical stress and improves stability through turns.
[Why We Chose This Differential](models/README.md#1-basic-design-choices)

---
## Power & Sensor Architecture

This is our PCB and how it works:
- An Arduino Nano handles low-level, time-sensitive motor and servo control — converting high-level commands into precise PWM signals in real time
- A Raspberry Pi 4B handles high-level perception and decision-making, using a single camera to read the environment and plan the robot's next move
- The Pi and Nano communicate over a serial connection, so the perception/decision code and the motor control code can be developed and updated independently

---

### 1. Battery

- 12.8V 2000mAh Li-ion battery pack (4S1P) — 4 cells in series for voltage, single parallel group for capacity
- Acts as the single main power source for the entire board
- Feeds three separate paths directly at 12.8V: the DRV8871 motor driver, the 5V buck converter, and the servo UBEC
- Chosen for a good balance of energy density, weight, and safe handling compared to a LiPo pack of similar capacity

---

### 2. 5V Buck Converter

- Steps the 12.8V battery rail down to a steady 5V supply
- Powers the Arduino Nano, the motor encoder, and the rest of the shared logic electronics off a single regulated rail
- A switching (buck) design rather than a linear regulator, so it can supply a higher output current with much less wasted heat
- Centralizing all 5V logic onto one converter keeps the wiring simple and avoids multiple separate regulators on the board

---

### 3. UBEC Voltage Regulator

- 2 to 8S LiPo UBEC rated for 8A, regulating the 12.8V battery rail down to 8.4V for the steering servo
- Runs on a completely separate power path from the buck converter and logic electronics
- This isolation means sudden current spikes from the servo (e.g., steering under load) can't drag down or brown out the 5V logic rail
- Rated well above the servo's normal draw to comfortably absorb its peak current demands

---

### 4. Arduino Nano

- Acts as the "slave" controller in the system, taking direction from the Raspberry Pi rather than making decisions itself
- Receives steering and speed values from the Pi over a serial connection every processing cycle
- Converts those values into the correct PWM duty cycles for the motor driver and servo
- Also reads the motor encoder to close the loop on speed and distance
- Runs entirely off the 5V buck converter rail, drawing very little current itself

| Specification | Value |
|---|---|
| Input Voltage | 5V |
| Normal Current | 0.05A |
| Peak Current | 0.10A |
| Power | 0.25W |

---

### 5. Motor Driver (DRV8871)

- Adafruit DRV8871 H-bridge motor driver, dedicated to driving the 12V 37D metal gear motor
- Powered directly from the 12.8V battery rail on its motor-power side, so the motor gets full, unregulated battery voltage
- Its logic/control side is fed low-current PWM signals from the Nano, keeping the high-current motor path electrically separate from the sensitive logic side
- Handles both direction and speed control for the drive motor from a single set of PWM inputs

---

### 6. Servo

- 12V 37D metal gear motor: the robot's drivetrain motor, driven through the DRV8871 and commanded by the Nano's PWM output
- 9g coreless servo (full metal gear, 4 KG·cm torque): the steering actuator, powered by the dedicated UBEC and commanded directly by the Nano
- Motor Encoder Port: routes the drive motor's encoder signal back to the Nano so it can measure actual speed/distance and correct for it, powered from the 5V buck converter rail
- Servo Port: a dedicated 3-wire connector (power, ground, PWM) that keeps the UBEC's power and the Nano's control signal cleanly routed to the servo
- M1/M2 Motor Output Ports: carry the DRV8871's high-current outputs straight from the battery rail to the motor, bypassing the 5V logic electronics entirely

---

### 7. Raspberry Pi 4B + Camera

- Raspberry Pi 4B: the robot's main processing unit, responsible for all high-level perception and decision-making
- Pi Camera Module 3 Wide: captures the competition mat in real time and feeds it into the onboard computer vision pipeline
- The vision pipeline identifies lane lines, obstacles, and track boundaries from each frame
- Once a frame is processed, the Pi sends the resulting steering and speed values to the Nano over serial
- Full camera-capture-to-command cycle runs at roughly 150ms, keeping the robot responsive while driving
- Powered off the same 5V buck converter rail as the rest of the logic electronics

| Specification | Value |
|---|---|
| Input Voltage | 5V |
| Normal Current | 0.70A |
| Peak Current | 1.20A |
| Power | 3.50W |

---

### 8. Full Power Budget

| Component | Input Voltage | Normal Current | Peak Current | Power |
|---|---|---|---|---|
| 12.8V 2000mAh 4S1P Li-ion Battery | 12.8V | 1.2A | 2.0A | 15.36W |
| DRV8871 Motor Driver | 12.8V | < 0.05A | < 0.1A | 0.64W |
| 12V 37D Metal Gear Motor | 12.8V | 0.40A | 1.00A | 5.12W |
| 5V DC-to-DC Buck Converter | 12.8V → 5V | 0.8A (out) | 1.5A (out) | 4.0W (out) |
| Arduino Nano | 5V | 0.05A | 0.10A | 0.25W |
| Raspberry Pi 4B + Pi Camera 3 Wide | 5V | 0.70A | 1.20A | 3.50W |
| Motor Encoder | 5V | 0.02A | 0.03A | 0.10W |
| 2 to 8S LiPo UBEC 8A | 12.8V → 8.4V | 0.33A (in) | 3.5A (in) | 2.8W (out) |
| 9g Coreless Servo | 8.4V | 0.50A | 3.0–5.0A | 4.2–25.2W |

---

### Bringing It All Together

- A single 5V buck converter powers all shared logic electronics off one clean rail, instead of multiple separate regulators
- A dedicated, isolated UBEC protects the board from servo current spikes so the rest of the electronics keep running smoothly
- A clean split between the Nano (actuation) and the Pi (perception/decision-making) keeps each system simple, testable, and independently upgradable
- Together, these choices give the robot a stable, competition-ready electrical system with reliable steering and motor control under load
---



---

## Software Architecture & Obstacle Strategy

The obstacle management system combines **computer vision, wall following, obstacle detection, crash protection, lap tracking, and autonomous parking** to navigate the WRO Future Engineers course.

- The Raspberry Pi processes the camera feed each frame and works out the robot's position relative to the walls and obstacles.
- A steering angle and motor speed are calculated from that frame.
- Commands are sent over serial to the motor controller in real time.

```python
ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)

def set_servo_angle(angle, duration=0.0, resend_interval=0.03, min_angle=None, max_angle=None):
    ...
    ser.write(f"SERVO,{physical_angle}\n".encode())

def set_motor(direction, speed, ticks=None):
    ...
    ser.write(f"MOTOR,{direction},{speed}\n".encode())
```

---

## Camera-Based Detection

- Every frame is cropped down to the relevant strip of the image before any processing happens.
- The cropped frame is converted from BGR into the **LAB colour space**, which is more stable under changing light than RGB.
- A separate mask is generated for each course colour: **Blue · Orange · Green · Red · Pink**.
- Each mask is cleaned with morphological open/close to strip noise and fill small gaps.

```python
frame = crop_image(raw_frame, 0, CAMERA_PIC_WIDTH, CAMERA_PIC_HEIGHT - PIC_HEIGHT, CAMERA_PIC_HEIGHT)
lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)

def calculate_color_mask(lab_img, color):
    if color == "blue":
        mask = cv2.inRange(lab_img, BLUE_LOWER, BLUE_UPPER)
    elif color == "orange":
        mask = cv2.inRange(lab_img, ORANGE_LOWER, ORANGE_UPPER)
    ...
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, MASK_CLEAN_KERNEL)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, MASK_CLEAN_KERNEL)
    return mask
```

- All the coloured regions (lines + pillars) are painted white and removed from the "wall" image.
- What's left is turned to grayscale, blurred, and thresholded so only the black walls remain.
- A **region of interest (ROI)** polygon is then fitted around the drivable area so later calculations only look at track, not background.

```python
non_wall_mask = cv2.bitwise_or(cv2.bitwise_or(blue_mask, orange_mask),
                               cv2.bitwise_or(green_mask, red_mask))
colormask_image[non_wall_mask > 0] = (255, 255, 255)

grayscale_image = cv2.cvtColor(colormask_image, cv2.COLOR_BGR2GRAY)
blurred_image = cv2.bilateralFilter(grayscale_image, 9, 75, 75)
_, binary_image = cv2.threshold(blurred_image, GRAY_THRESHOLD, 255, cv2.THRESH_BINARY)

polygon_image, polygon_points = draw_polygon(clean_image, clean_image)
```

<div align="center">

<b>Original Image</b><br><br>
<img width="500" alt="FEframe" src="https://github.com/user-attachments/assets/44a4c8ec-7285-4efb-81c2-64d730164e3c" />

<br><br>

<b>Mat ROI</b><br><br>
<img width="500" alt="roi_img" src="https://github.com/user-attachments/assets/bf9f8363-a913-4540-ab93-6496d6b0d15e" />

<br><br>

<b>Obstacles</b><br><br>
<img width="500" alt="obstaclemask" src="https://github.com/user-attachments/assets/5547e388-27f7-47b5-99c0-d11c96ab7267" />

<br><br>

<b>Blue Line</b><br><br>
<img width="500" alt="blueline" src="https://github.com/user-attachments/assets/67a684e8-f9d6-4233-be04-23a351eac95e" />

<br><br>

<b>Orange Line</b><br><br>
<img width="500" alt="orangeline" src="https://github.com/user-attachments/assets/ea2c966c-bf3d-491c-b23d-528c3a7366ce" />

<br><br>

<b>Parking</b><br><br>
<img width="500" alt="pinkparking" src="https://github.com/user-attachments/assets/5cc00415-8d91-419e-889f-fa8259658479" />

</div>

---

## Wall Following

- Two fixed **ROI boxes** are placed on the left and right of the frame, sized around where the walls normally sit.
- For `Direction.RIGHT`, both boxes are mirrored across the frame's centreline so the same logic works both ways.

```python
ROI_LEFT_WALL_BASE  = [0, 80, 128, 200]
ROI_RIGHT_WALL_BASE = [504, 60, 638, 198]

def get_wall_rois(direction):
    if direction == Direction.LEFT:
        return ROI_LEFT_WALL_BASE, ROI_RIGHT_WALL_BASE
    return _mirror_roi(ROI_RIGHT_WALL_BASE), _mirror_roi(ROI_LEFT_WALL_BASE)
```

- Inside each ROI, the largest black-wall contour is found and its **area** is measured — more wall pixels in the box means the robot is closer to that wall.

```python
def _largest_wall_contour_area(binary_img, roi, min_area=50):
    x1, y1, x2, y2 = roi
    region = binary_img[y1:y2, x1:x2]
    walls_as_white = cv2.bitwise_not(region)
    contours, _ = cv2.findContours(walls_as_white, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    area = cv2.contourArea(max(contours, key=cv2.contourArea))
    return area if area > min_area else 0
```

- The **difference** between the left and right areas is the error — if one side has way more wall than the other, the robot is off-centre toward the smaller side.

```python
wall_error = (area_left - area_right) - CENTER_OFFSET
```

- If one side's wall area drops very low (a corner or opening just appeared), the *other* side's area is artificially boosted so the controller reacts as if that wall were huge — this is what makes the robot snap hard into a turn.

```python
if area_left < LOW_THRESH and area_right > 100:
    area_right = area_right * BOOST_MULT + BOOST_ADD
elif area_right < LOW_THRESH and area_left > 100:
    area_left = area_left * BOOST_MULT + BOOST_ADD
```

- A **PD controller** turns the (boosted) area error into a steering correction, same idea as before but on areas instead of pixel positions:

$$Control = K_p(Error) + K_d(Error - PreviousError)$$

```python
derivative = wall_error - _prev_area_wall_error
control = (wall_error * kp) + (derivative * kd)
_prev_area_wall_error = wall_error

angle = default_servo - control
angle = max(MIN_ANGLE, min(MAX_ANGLE, angle))
```

- If *both* ROIs read zero (deep in a corner, no wall pixels at all), the robot falls back to a flat hard-over turn instead of trusting the PD math:

```python
if area_left == 0 and area_right == 0:
    turn_sign = 1 if direction == Direction.LEFT else -1
    angle = default_servo + turn_sign * 35 if (blue_area > LINE_AREA_ENTER_THRESHOLD or orange_area > LINE_AREA_ENTER_THRESHOLD) else default_servo + turn_sign * 20
```

- The debug overlay in-frame (`L=... R=...`) shows exactly these two ROI areas live.

---

## Obstacle Navigation

<img width="500" alt="anglecalculatorobstalce" src="https://github.com/user-attachments/assets/fda923f3-9adc-4583-a4ff-ac1dff17bb7b" />

- Green and red pillars are detected by finding coloured contours inside the ROI and keeping the **closest one to the robot**.

```python
def find_closest_pillar(self, green_mask, red_mask, display_frame):
    robot_point = (PIC_WIDTH // 2, PIC_HEIGHT)
    ...
    distance = math.dist((x_center, y_center), robot_point)
```

**Turning the pillar position into a steering angle — building a right triangle**

Once a pillar is found, three points define a right triangle in the image, exactly like the diagram above:

- **Vertex A — the aim point:** a fixed point on the bottom edge of the frame, offset to the left or right of centre (`LEFT_OBSTACLE_X_THRESHOLD` / `RIGHT_OBSTACLE_X_THRESHOLD`). This is the gap the robot is aiming to drive through.
- **Vertex B — the pillar centre:** `(x_center, y_center)`, the middle of the detected obstacle box.
- **Vertex C — directly below the pillar:** `(x_center, PIC_HEIGHT)`, straight down from the pillar to the bottom row of the frame.

That gives:

- **Opposite side** — the vertical drop from the pillar down to the bottom of the frame.
- **Adjacent side** — the horizontal distance between the pillar and the aim point.
- **Hypotenuse** — the red line drawn straight from the aim point to the pillar (this is the line rendered on-screen in the image).

- `θ` is the angle at vertex A, between the horizontal baseline and the hypotenuse — calculated straight from the two triangle legs with `arctan2`:

```python
rad_angle = np.arctan2(y_center - PIC_HEIGHT, x_center - RIGHT_OBSTACLE_X_THRESHOLD)  # green
rad_angle = np.arctan2(y_center - PIC_HEIGHT, x_center - LEFT_OBSTACLE_X_THRESHOLD)   # red

object_angle_deg = 90 + np.degrees(rad_angle)
```

- `arctan2(opposite, adjacent)` returns the angle off the horizontal axis; adding `90°` re-bases it so `0°` lines up with straight ahead of the robot instead of straight sideways.
- This `object_angle_deg` is then converted into a servo angle, offset by a fixed threshold and scaled by a gain constant so the robot steers wide enough to actually clear the pillar:

```python
if is_green:
    servo_angle = default_servo - ((object_angle_deg + OBJECT_LINE_ANGLE_THRESHOLD) * GREEN_OBSTACLE_KP)
else:
    servo_angle = default_servo - ((object_angle_deg - OBJECT_LINE_ANGLE_THRESHOLD) * RED_OBSTACLE_KP)

servo_angle = max(MIN_ANGLE, min(MAX_ANGLE, servo_angle))
```

- **Green pillar → pass on the right:** aim point is `RIGHT_OBSTACLE_X_THRESHOLD`, offset is added.
- **Red pillar → pass on the left:** aim point is `LEFT_OBSTACLE_X_THRESHOLD`, offset is subtracted.
- While a pillar is being avoided, this obstacle angle **overrides** wall following. Once the pillar is no longer detected, control returns to wall following automatically.

`Detect → Build Triangle → Calculate θ → Convert to Servo Angle → Steer Around → Clear → Resume Wall Following`

---

## Crash Detection

- A row of virtual points is checked against the wall mask to catch the robot cutting the **inner** wall while cornering.
- A single point near the bottom-centre of the frame checks the **outer** wall.
- If a point lands on black (wall), the robot enters a crash-protection state.

```python
def check_inner_wall_crash(self, direction, polygon_image, display_frame):
    ...
    point_crashed = in_bounds and polygon_image[y, x] == 0
    if point_crashed:
        crashed = True

def check_outer_wall_crash(self, direction, polygon_image, display_frame):
    detection_points = [(PIC_WIDTH // 2, PIC_HEIGHT - 138)]
    ...
```

- **Inner-wall warning** → the wall-follow PD gains are swapped for softer, "damped" gains (`INNER_CRASH_KP` / `INNER_CRASH_KD`) so the correction is smoother.
- **Outer-wall warning** → the robot applies a hard, fixed steering angle back toward the corner (`turn_into_corner`) instead of the normal PD correction.

---

## Lap Counter

- The robot counts **quarter-laps**, not full laps at once.
- Depending on the driving direction, either the **blue** or the **orange** marker mask is watched.
- A marker has to stay above `LINE_AREA_ENTER_THRESHOLD` for several consecutive frames before a turn is registered — this filters out false positives.
- Once the marker then drops below `LINE_AREA_EXIT_THRESHOLD` for enough frames (and a minimum turn duration has passed), the quarter-lap is logged and a cooldown starts so the same marker can't be counted twice.

```python
self._confirm_count = self._confirm_count + 1 if marker_area > LINE_AREA_ENTER_THRESHOLD else 0
if self._confirm_count >= ENTRY_CONFIRM_FRAMES:
    self.state = "turning"
    self._turn_start_time = now

...
should_exit = (
    turn_elapsed >= turn_min_duration and self._exit_confirm_count >= exit_confirm_frames
) or (turn_elapsed >= TURN_MAX_DURATION)
if should_exit:
    self.quarter_lap_count += 1
    self.state = "idle"
    self._cooldown_until = now + TURN_COOLDOWN
```

- The robot is configured for:

$$3\ laps \times 4 = 12\ quarter\text{-}laps$$

```python
LAPS_TARGET = 3
TOTAL_TURNS = LAPS_TARGET * 4
```

- Once the required number of turns is reached, the robot switches out of the driving loop and into the parking sequence.

---

## Parking

**Parking Detection**

- After the laps are done, the robot searches for the **pink parking block** using the same colour-mask + contour approach as the pillars.
- The block's position in the frame is used to steer toward the parking area.

```python
def find_pink_block(pink_mask, display_frame):
    contours, _ = cv2.findContours(pink_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    ...
```

**Parking Sequence**

`Lap Complete → Find Pink → Approach → Align → Park`

- The approach differs by track direction:

<div align="center">
<table>
  <tr>
    <td align="center" width="50%">

**Counter Clockwise**

After completing **12 quarters**, the robot detects and follows the pink parking block directly, aligning itself and continuing the approach until the required position is reached.

<br><br>
<img width="100%" alt="left parking approach" src="YOUR_LEFT_PARKING_GIF_URL" />

</td>
    <td align="center" width="50%">

**Clockwise**

After completing **13 quarters**, the robot performs a **U-turn** to face the parking area, then finds and follows the pink block before the final manoeuvre.

<br><br>
<img width="100%" alt="right parking approach" src="YOUR_RIGHT_PARKING_GIF_URL" />

</td>
  </tr>
</table>
</div>

```python
turns_needed = TOTAL_TURNS + 1 if direction == Direction.RIGHT else TOTAL_TURNS
laps_complete = lap_tracker.quarter_lap_count >= turns_needed

if laps_complete:
    if direction == Direction.RIGHT:
        stop_motor()
        perform_u_turn_to_pink(picam2)
    follow_pink_block_to_park(picam2, Direction.LEFT)
```

- While approaching, obstacle avoidance still takes priority over the pink block if a pillar is closer than the block:

```python
pillar_is_closer = pillar_found is not None and (
    pink_y is None or pillar_found[1] > pink_y
)
if pillar_is_closer:
    angle = forced_pillar_angle(p_x, p_y, False, frame)
elif pink_angle is not None:
    angle = pink_angle
```

- Once the pink block is close enough **and** horizontally aligned, the robot stops and hands off to the final manoeuvre:

```python
close_enough = pink_y >= PARK_TARGET_Y
alongside = abs(pink_x - aim_x) <= PARK_X_TOLERANCE
if close_enough and alongside:
    stop_motor()
    wall_follow_park_entry(picam2, direction)
```

- The final manoeuvre uses **encoder-based movements** (`set_motor(direction, speed, ticks)`) instead of timed driving, so each forward/reverse/turn step covers a consistent distance regardless of speed or surface.

```python
set_motor(2, 130, 1100)   # reverse a fixed number of encoder ticks
reset_ticks()
set_servo_angle(default_servo, min_angle=PARK_MIN_ANGLE, max_angle=PARK_MAX_ANGLE)
set_motor(2, 130, 385)
```

---

## Autonomous Navigation Flowcharts

### Open Course

[Open-course flowchart]

### Obstacle Course

[Obstacle flowchart]
---
## Systems Thinking & Engineering Decisions
---
## Reproducibility & Github Organization

