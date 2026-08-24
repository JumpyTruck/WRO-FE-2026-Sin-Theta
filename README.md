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

<img width="500" alt="Ackermann Calculations" src="https://github.com/user-attachments/assets/b1abda45-6370-409a-8c45-db80839f1d7b" />

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
This section explains how the robot "sees" the track and decides how to steer — wall following, obstacle avoidance, crash safety, lap counting, and parking.

---

## 1) What the Camera Sees

Every frame is turned into a few simpler images that the rest of the code uses:

| Image | What it shows |
|---|---|
| **Frame** | The raw camera view, cropped to the useful area |
| **Masks** | One black/white mask per colour: blue, orange, green, red, pink |
| **Mask ROI** | Walls = black, drivable floor = white |

```python
frame = crop_image(raw_frame, 0, CAMERA_PIC_WIDTH, CAMERA_PIC_HEIGHT - PIC_HEIGHT, CAMERA_PIC_HEIGHT)
lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
blue_mask = calculate_color_mask(lab, "blue")
```

<div align="center">

<table>
<tr><td align="center"><b>Original Frame</b><br><img width="400" src="https://github.com/user-attachments/assets/44a4c8ec-7285-4efb-81c2-64d730164e3c"/></td>
<td align="center"><b>Mat ROI</b><br><img width="400" src="https://github.com/user-attachments/assets/bf9f8363-a913-4540-ab93-6496d6b0d15e"/></td></tr>
<tr><td align="center"><b>Obstacle Mask</b><br><img width="400" src="https://github.com/user-attachments/assets/5547e388-27f7-47b5-99c0-d11c96ab7267"/></td>
<td align="center"><b>Blue Line</b><br><img width="400" src="https://github.com/user-attachments/assets/67a684e8-f9d6-4233-be04-23a351eac95e"/></td></tr>
<tr><td align="center"><b>Orange Line</b><br><img width="400" src="https://github.com/user-attachments/assets/ea2c966c-bf3d-491c-b23d-528c3a7366ce"/></td>
<td align="center"><b>Parking Block</b><br><img width="400" src="https://github.com/user-attachments/assets/5cc00415-8d91-419e-889f-fa8259658479"/></td></tr>
</table>

</div>

---

## 2) Wall Following

Two small boxes (ROIs) sit on the left and right of the frame. Whichever side has **more black wall pixels** in its box, the robot is closer to that wall.

```python
area_left  = _largest_wall_contour_area(polygon_image, roi_left)
area_right = _largest_wall_contour_area(polygon_image, roi_right)
error = area_left - area_right
```

- A **PD controller** turns that error into a steering angle:

```python
control = (error * kp) + ((error - prev_error) * kd)
angle = default_servo - control
```

- If one side suddenly has almost no wall (an opening), the other side's number is boosted so the robot turns hard toward the gap.

---

## 3) Obstacle Avoidance

The robot builds a simple **right triangle** between itself and the pillar, then uses trig to work out the steering angle:

- **A** – the aim point (where the robot wants to end up, left or right of centre)
- **B** – the pillar's centre
- **C** – straight below the pillar

<div align="center">
  <img width="450" alt="obstacle_triangle_labeled" src="https://github.com/user-attachments/assets/ecedeb62-0d14-40cd-9f1c-848b308f0825" />
</div>

- The angle **θ** (between the base line and the line to the pillar) comes from `arctan2`:

```python
rad_angle = np.arctan2(y_center - PIC_HEIGHT, x_center - aim_x)
theta = 90 + np.degrees(rad_angle)
```

- That angle becomes the servo angle, offset depending on colour:

```python
if is_green:      # pass on the right
    servo_angle = default_servo - (theta + OFFSET) * GREEN_KP
else:              # pass on the left
    servo_angle = default_servo - (theta - OFFSET) * RED_KP
```

`Detect pillar → build triangle → get θ → steer around → resume wall following`

---

## 4) Crash Detection

Two safety checks run every frame:

```python
inner_crash = check_inner_wall_crash(direction, polygon_image, frame)
outer_crash = check_outer_wall_crash(direction, polygon_image, frame)
```

- **Inner wall too close** → smooth out the steering (softer PD gains).
- **Outer wall too close** → ignore normal steering and force a hard turn away.

---

## 5) Lap Counting

The robot counts **quarter-laps**, one per corner marker seen:

```python
LAPS_TARGET = 3
TOTAL_TURNS = LAPS_TARGET * 4   # 12 quarter-laps
```

- A marker must be seen for a few frames in a row before it counts (avoids false triggers).
- Once it disappears again, one quarter-lap is added and a short cooldown starts.

```python
if marker_seen_for_enough_frames:
    state = "turning"
if marker_gone_for_enough_frames:
    quarter_lap_count += 1
```

- After 12 quarter-laps, the robot switches into parking mode.

---

## 6) Parking

Once laps are done, the robot looks for the **pink block** and drives toward it.

```python
pink_found = find_pink_block(pink_mask, frame)
```

- If a pillar is closer than the pink block, avoiding it still comes first.
- Once close enough and lined up, the robot stops and runs a fixed parking manoeuvre using **encoder ticks** (not time) so every move is consistent:

```python
if close_enough and aligned:
    stop_motor()
    set_motor(2, 130, 1100)   # reverse a fixed distance
```

<div align="center">
<table>
<tr>
<td align="center" width="50%"><b>Counter Clockwise</b><br>Follows the pink block straight after the last turn.<br><img width="100%" 
<img width="500" height="450" alt="IMG_2594-ezgif com-video-to-gif-converter" src="https://github.com/user-attachments/assets/2b2381f4-c1f1-4e4a-8960-5962c048d737" />
<td align="center" width="50%"><b>Clockwise</b><br>Does a U-turn first, then follows the pink block.<br><img width="100%" 
<img width="500" height="450" alt="IMG_2596-ezgif com-video-to-gif-converter (1)" src="https://github.com/user-attachments/assets/b96c7a6a-3dda-4819-8dd1-4a5a56780e92" />
                                                                                                 
</tr>
</table>
</div>

---

## Autonomous Navigation Flowcharts

### Open Course

[Open-course flowchart]

### Obstacle Course

<img width="1000" alt="Obstacle Flowchart" src="https://github.com/user-attachments/assets/c1e98583-360a-493a-97bb-4f39abc578ab" />

---
## Systems Thinking & Engineering Decisions
---
## Reproducibility & Github Organization

