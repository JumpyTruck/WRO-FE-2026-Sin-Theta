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

The Raspberry Pi processes the camera feed and determines the robot's position relative to the walls and obstacles. Steering commands are then sent to the motor controller in real time.

---

## Camera-Based Detection

The Raspberry Pi camera provides the main visual information for navigation. Each frame is cropped to the relevant area and converted to the **LAB colour space**.

Separate masks are created for the following colours:

**Blue · Orange · Green · Red · Pink**

The masks are cleaned to remove noise and fill small gaps.

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

The coloured regions are removed from the wall image. The remaining image is converted to grayscale and thresholded to detect the black walls.

A **region of interest (ROI)** is then created around the detected track area, ensuring that navigation calculations only use the relevant part of the image.

---

## Wall Following

The robot uses the detected black wall to maintain a consistent position around from the inner wall throughout the run.

Multiple points along the wall are sampled and averaged to obtain a stable, lowest wall position (red dot). This position is compared with a predefined target point (green dot).

\[
Error = Error_x + Error_y
\]

A **PD controller** converts this error into a steering correction:

\[
Control = K_p(Error) + K_d(Error - PreviousError)
\]

The resulting correction is converted into a servo angle and limited to the robot's steering range.

This allows the robot to continuously correct its position while following either the left or right wall.


---

## Obstacle Navigation

**Obstacle Detection**

The robot detects **green and red obstacles** on the course.

The camera seaches for coloured contours and selects the closest valid pillar and draws a box around the obstacle. Its position is then used to calculate the angle required to safely pass the obstacle.

**Obstacle Navigation**

`Detect → Calculate Angle → Steer Around → Clear → Resume Wall Following`

While an obstacle is being avoided, the obstacle steering angle takes priority over the normal wall-following angle.

Once the obstacle is cleared, the robot automatically returns to wall following.


---

## Crash Detection

Several virtual detection points are placed within the camera image to prevent the robot from getting too close to the walls.

- **Inner wall line** detect the inside wall while cornering.
- **Outer wall point** detects when the outer wall becomes too close.

If a point reaches the detected wall region, the robot enters a crash-protection state.

For an inner-wall warning, the wall-following controller is damped to make the steering correction smoother. If the outer wall is too close, the robot applies a stronger correction away from the wall.

---

## Lap Counter

The robot tracks **quarter-laps** rather than counting an entire lap at once.

The appropriate **blue or orange marker** is monitored depending on the robot's direction. A marker must be detected for several consecutive frames before a turn is registered, reducing false detections.

After the marker disappears for the required number of frames, the quarter-lap is counted.

A cooldown is then applied to prevent the same marker from being counted twice.

The robot is configured for:

\[
3\text{ laps} \times 4 = 12\text{ quarter-laps}
\]

Once the required number of turns is completed, the robot switches to the parking sequence.

---

## Parking

**Parking Detection**

After completing the required laps, the robot searches for the **pink parking block**.

The pink block is detected using a colour mask and contour detection. Its position in the camera image is then used to steer the robot toward the parking area.


**Parking Sequence**

`Lap Complete → Find Pink → Approach → Align→ Park`


The parking approach depends on the **direction of the track**. The robot uses two different parking strategies:

<div align="center">

<table>
  <tr>
    <td align="center" width="50%">

**Counter Clockwise**

<br>

After completing **12 quarters**, the robot detects and follows the pink parking block. It aligns itself with the parking area and continues the approach until the required position is reached.

<br><br>

<img width="100%" alt="left parking approach" src="YOUR_LEFT_PARKING_GIF_URL" />

</td>

<td align="center" width="50%">

**Clockwise**

<br>

After completing **13 quarters**, the robot performs a **U-turn** to face the parking area. It then detects and follows the pink parking block before completing the final parking manoeuvre.

<br><br>

<img width="100%" alt="right parking approach" src="YOUR_RIGHT_PARKING_GIF_URL" />

</td>
  </tr>
</table>

</div>

While approaching the parking area, the robot continues checking for nearby obstacles. If an obstacle is closer than the pink block, obstacle avoidance takes priority.

Once the pink block reaches the required distance and horizontal alignment, the robot stops and begins the final parking manoeuvre.

The final manoeuvre uses **encoder-based movements** to control the distance travelled during each forward, reverse, and turning movement. This allows the robot to perform the parking sequence consistently in both directions.

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

