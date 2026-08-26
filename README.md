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

[Why We Chose These Dimensions](models/README.md#11-dimensions)

---

### 2) Drive System

For our drive system, we use a 12V DC Geared Motor. This motor has a built in encoder and since drivetrain needed enough torque to move the robot's mass while staying fast enough for the competition mat, without adding unnecessary complexity.

| Component | Selected Part |
|---|---|
| DC Motor | 12V DC Geared Motor |

The motor's integrated encoder gives us speed and distance feedback, which we use for autonomous control.

[More on Motor Choice](electrical#1-motor--drive-system)

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

[Why We Chose Ackermann](models/README.md#14-steering--ackermann)

---

### 4) Chassis Assembly

The chassis is built from three modular 3D-printed layers, each with dedicated mounting points for the electronics, motor, and steering assembly. This open, layered design means any section can be pulled off individually for repairs or upgrades, without disassembling the whole robot.

<div align="center">

<img width="1245" height="700" alt="First plate" src="https://github.com/user-attachments/assets/7763083b-e341-4566-9f6d-96d56026d52a" />
<img width="1248" height="700" alt="Second plate" src="https://github.com/user-attachments/assets/116feb86-e038-4e22-8e40-c2fecf43d38d" />
<img width="1333" height="748" alt="Third plate" src="https://github.com/user-attachments/assets/200b7d2b-a27e-4cb8-b80d-62d3f662c3f5" />

</div>

[More Pictures and Info Here](models/README.md#21-chassis)

---

### 5) Wheels & Differential

- **Wheels:** LEGO SPIKE Prime wheels — compact, consistent grip, and lightweight.
[Why We Chose These Wheels](models/README.md#12-wheel-choice)

- **Differential:** Rear metal differential, allowing both drive wheels to rotate at different speeds while cornering. This reduces mechanical stress and improves stability through turns.
[Why We Chose This Differential](models/README.md#13-differential)

---
## Power & Sensor Architecture

This is our PCB and how it works:
- An Arduino Nano handles low-level, time-sensitive motor and servo control — converting high-level commands into precise PWM signals in real time
- A Raspberry Pi 4B handles high-level perception and decision-making, using a single camera to read the environment and plan the robot's next move
- The Pi and Nano communicate over a serial connection, so the perception/decision code and the motor control code can be developed and updated independently

**Here is our Electrical Architecture**

<img width="1000"  alt="Sin Theta Electrical Flowchart" src="https://github.com/user-attachments/assets/c0ca1881-e3d9-4d92-8d50-80c13f9feb66" />


---

### 1. Battery

- 12.8V 2000mAh Li-ion battery pack (4S1P) — 4 cells in series for voltage, single parallel group for capacity
- Acts as the single main power source for the entire board
- Feeds three separate paths directly at 12.8V: the DRV8871 motor driver, the 5V buck converter, and the servo UBEC
- Chosen for a good balance of energy density, weight, and safe handling compared to a LiPo pack of similar capacity

[More Info on Battery](electrical#3-main-power-system)

---

### 2. 5V Buck Converter

- Steps the 12.8V battery rail down to a steady 5V supply
- Powers the Arduino Nano, the motor encoder, and the rest of the shared logic electronics off a single regulated rail
- A switching (buck) design rather than a linear regulator, so it can supply a higher output current with much less wasted heat
- Centralizing all 5V logic onto one converter keeps the wiring simple and avoids multiple separate regulators on the board

[More Info on Buck Converter](electrical#32-5v-dc-dc-buck-converter)

---

### 3. UBEC Voltage Regulator

- 2 to 8S LiPo UBEC rated for 8A, regulating the 12.8V battery rail down to 8.4V for the steering servo
- Runs on a completely separate power path from the buck converter and logic electronics
- This isolation means sudden current spikes from the servo (e.g., steering under load) can't drag down or brown out the 5V logic rail
- Rated well above the servo's normal draw to comfortably absorb its peak current demands

[More Info on UBEC](electrical#22-ubec-voltage-regulator)

---

### 4. Arduino Nano

- Acts as the "slave" controller in the system, taking direction from the Raspberry Pi rather than making decisions itself
- Receives steering and speed values from the Pi over a serial connection every processing cycle
- Converts those values into the correct PWM duty cycles for the motor driver and servo
- Also reads the motor encoder to close the loop on speed and distance
- Runs entirely off the 5V buck converter rail, drawing very little current itself

[More Info on Arduino Nano](electrical#52-motor-controller-arduino-nano)

---

### 5. Motor Driver (DRV8871)

- Adafruit DRV8871 H-bridge motor driver, dedicated to driving the 12V 37D metal gear motor
- Powered directly from the 12.8V battery rail on its motor-power side, so the motor gets full, unregulated battery voltage
- Its logic/control side is fed low-current PWM signals from the Nano, keeping the high-current motor path electrically separate from the sensitive logic side
- Handles both direction and speed control for the drive motor from a single set of PWM inputs

[More Info on Motor Driver](electrical#52-motor-controller-arduino-nano)

---

### 6. Servo

- 12V 37D metal gear motor: the robot's drivetrain motor, driven through the DRV8871 and commanded by the Nano's PWM output
- 9g coreless servo (full metal gear, 4 KG·cm torque): the steering actuator, powered by the dedicated UBEC and commanded directly by the Nano
- Motor Encoder Port: routes the drive motor's encoder signal back to the Nano so it can measure actual speed/distance and correct for it, powered from the 5V buck converter rail
- Servo Port: a dedicated 3-wire connector (power, ground, PWM) that keeps the UBEC's power and the Nano's control signal cleanly routed to the servo
- M1/M2 Motor Output Ports: carry the DRV8871's high-current outputs straight from the battery rail to the motor, bypassing the 5V logic electronics entirely

[More Info on Servo](electrical#21-steering-servo)

---

### 7. Raspberry Pi 4B + Camera

- Raspberry Pi 4B: the robot's main processing unit, responsible for all high-level perception and decision-making
- Pi Camera Module 3 Wide: captures the competition mat in real time and feeds it into the onboard computer vision pipeline
- The vision pipeline identifies lane lines, obstacles, and track boundaries from each frame
- Once a frame is processed, the Pi sends the resulting steering and speed values to the Nano over serial
- Full camera-capture-to-command cycle runs at roughly 150ms, keeping the robot responsive while driving
- Powered off the same 5V buck converter rail as the rest of the logic electronics

[More Info on Raspberry Pi](electrical#41-raspberry-pi-camera-module-3-wide)

[More Info on Camera](electrical#51-main-controller-raspberry-pi-4b)

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

## Software Architecture & Obstacle Strategy

This section explains how the computer vision pipeline drives steering decisions for the robot. It covers:

* Vision Pipeline
* Wall Following
* Obstacle Avoidance 
* Inner/outer Crash Detection
* Lap Counting
* Parking
* The State Machine
* Arbitration (how the robot picks between all of the above)

---
### Raspberry Pi + Arduino Nano

- Robot's brain is split across two boards
- **Raspberry Pi** — runs the camera, does the computer vision, decides what to do next
- **Arduino Nano** — takes commands from the Pi, drives the motor and servo
- Connected over a **USB serial cable**
- Pi sends simple commands, Nano carries them out and reports back when a move is done

For full message formats and protocol details, see [Communication Protocol](code/md/serial_communication.md)

---

### 1) Vision Pipeline

Every raw frame is turned into a few simpler images that everything else in the code works from:

- **Frame** — the raw camera view, cropped to the useful area
- **Colour masks** — one black/white mask per colour: blue, orange, green, red, pink
- **Mat ROI** — the drivable floor, walls = black, floor = white

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

### 2) Wall Following

- Two small boxes (ROIs) sit on the left and right of the frame
- Whichever side has **more black wall pixels** inside its box, the robot is closer to that wall
- The difference between the two areas is the "error" fed into a PD controller

```python
area_left = largest_wall_area(track_image, roi_left)
area_right = largest_wall_area(track_image, roi_right)
wall_error = area_left - area_right

control = (wall_error * kp) + (derivative * kd)
angle = STEER_CENTER - control
```

- **Proportional term** (`wall_error * kp`) — steers harder the more unbalanced the two sides are
- **Derivative term** (`derivative * kd`) — smooths the response so it doesn't overcorrect frame to frame
- If one side suddenly reads almost no wall (an opening), that side's area gets boosted so the controller reacts as if that wall were huge, forcing a hard turn toward the gap:

```python
if area_left < WALL_OPENING_AREA and area_right > 100:
    area_right = area_right * OPENING_BOOST_MULT + OPENING_BOOST_ADD
```
---

### 3) Obstacle Avoidance

To steer around a pillar, the robot needs two numbers:

- **How far the pillar is from the aim x** (sideways) — one leg of the triangle
- **How far the pillar is from the robot** (forward distance) — the other leg
- With both legs known, trigonometry (`arctan2`) gives the angle between them — that angle is how much to steer

```python
rad_angle = np.arctan2(y_center - FRAME_HEIGHT, x_center - aim_x)
pillar_angle_deg = 90 + np.degrees(rad_angle)
```

<div align="center">
  <img width="450" alt="obstacle_triangle_labeled" src="https://github.com/user-attachments/assets/ecedeb62-0d14-40cd-9f1c-848b308f0825" />
</div>

That angle becomes the steering angle, nudged by a fixed offset and a colour-specific gain — green and red pillars are passed on opposite sides:

```python
if is_green:   # pass on the left
    steer_angle = STEER_CENTER - ((pillar_angle_deg + PILLAR_STEER_OFFSET_DEG) * GREEN_PILLAR_KP)
else:          # pass on the right
    steer_angle = STEER_CENTER - ((pillar_angle_deg - PILLAR_STEER_OFFSET_DEG) * RED_PILLAR_KP)
```

---

### 4) Crash Detection

Two safety checks run every frame on the track mask:

```python
outer_crash = navigator.is_hitting_outer_wall(direction, track_image, frame)
inner_crash = navigator.is_hitting_inner_wall(direction, track_image, frame)
```

- **Outer wall too close (blue dot)** → ignore normal steering entirely, force a hard turn away from it
- **Inner wall too close (blue line)** → don't force a turn, just soften the wall-following gains so the correction is gentler:

```python
kp = AREA_WALL_KP_DAMPED if damped else AREA_WALL_KP
```

Both checks latch into a small state — once triggered, the robot stays in recovery until the crash condition actually clears.

---

### 5) Lap Counter

- Counts **quarter-turns**, one for every corner marker passed
- A marker must be seen for a few frames in a row before it counts as "entering" a turn, to avoid false triggers
- Once the marker's been gone for a few frames in a row, the quarter-turn counts as finished

After 12 quarter-turns, the robot switches into parking mode.

---

### 6) Parking

- Looks for the **pink block** and drives toward it
- If a pillar is closer than the pink block, avoiding the pillar still takes priority
- Once close enough and lined up, stops and reverses in using a fixed sequence of hard turns

The final manoeuvre uses **encoder ticks** rather than time for every move, so it covers the same distance no matter the speed:

<div align="center">
<table>
<tr>
<td align="center" width="50%"><b>Counter Clockwise</b><br>Follows the pink block straight after the last turn.<br>
<img width="400" alt="IMG_2594-ezgif com-video-to-gif-converter" src="https://github.com/user-attachments/assets/2b2381f4-c1f1-4e4a-8960-5962c048d737" />
</td>
<td align="center" width="50%"><b>Clockwise</b><br>Does a U-turn first, then follows the pink block.<br>
<img width="400" alt="IMG_2596-ezgif com-video-to-gif-converter (1)" src="https://github.com/user-attachments/assets/b96c7a6a-3dda-4819-8dd1-4a5a56780e92" />
</td>
</tr>
</table>
</div>

---

### 7) The State Machine

The whole run is one state machine that moves forward through these states in order:

- **Wait for button** — LED on, idle until the start button is pressed
- **Warm up camera** — a few frames thrown away so auto-exposure settles
- **Detect start direction** — compares open floor on the left vs. right half of the frame
- **Exit start park** — a fixed manoeuvre out of the starting box, checking for a pillar first
- **Drive laps** — the main loop: wall-follow, dodge pillars, count quarter-turns
- **U-turn to parking wall** — clockwise runs only; turns to face the pink wall
- **Approach parking spot** — tracks the pink wall until lined up, then reverses in

```python
while self.state != RunState.FINISHED:
    handler = self._handlers[self.state]
    handler()
```

---

### 8) Arbitration

Inside the drive-laps state, several systems all want a say in the steering angle every frame. Checked in this priority order, highest first:

1. **Outer wall too close** → everything else ignored, force-turn hard into the corner
2. **Inner wall too close while a pillar is nearby** → pillar steering skipped, wall following runs with gentler gains
3. **Obstacle Avoidance** → pillar-avoidance steering wins
4. **Wall Following** → normal wall following runs

```python
final_angle = pillar_angle if pillar_angle is not None else wall_angle
```

`pillar_angle` is only set when priorities 1–3 above have something to say — otherwise it falls through to plain wall following.

---

### Autonomous Navigation Flowcharts

### Open Course

[Open-course flowchart]

### Obstacle Course

<img width="1000" alt="Obstacle Flowchart" src="https://github.com/user-attachments/assets/c1e98583-360a-493a-97bb-4f39abc578ab" />

---
## Systems Thinking & Engineering Decisions
Building this robot meant constantly balancing the needs of four interconnected subsystems — Power, Sensors, Software, and Mobility — where a change in one almost always had a ripple effect on the others. Many of our design choices can't be fully understood by looking at a single subsystem in isolation; they only make sense when viewed as trade-offs made to satisfy multiple competing constraints at once. This section walks through the key decisions we made, the alternatives we considered, why we moved away from them, and the hard constraints — from competition rules to physics — that shaped the final design.

---

### Trade-offs

#### Raspberry Pi + Arduino Nano split (instead of one board doing everything)
- Raspberry Pi handles the camera and vision processing
- Arduino Nano handles motor control
- Splitting the load this way means:
  - Pi isn't bogged down running motor control loops alongside vision processing → faster, more responsive image processing
  - Nano handles motor timing exactly when needed, without waiting on the Pi's CPU scheduling
  - Each board does one job well instead of one board doing two jobs poorly
- Net result: faster code overall, cleaner separation of responsibilities, easier debugging when something goes wrong (you know which board to check)

#### Skipped extra distance and gyro sensors
- Decided against adding more sensors (e.g. distance sensors) beyond what was essential
- Reason 1 (software): more sensors = more data to read, process, and fuse every loop cycle → slows down the control loop
  - With only the PiCam 3 Wide, our processing cycle takes approximately 150 ms. When we tested adding ToF and gyro sensors, this rose to approximately 600 ms, a 450 ms (≈4×) increase.
- Reason 2 (real-world/practical): more sensors also means more wiring, more points of failure, and more calibration to maintain — in a competition setting, every extra wire is a chance for a connector to come loose or a sensor to drift out of calibration between runs, which costs more reliability than the extra data is worth
- Kept the sensor suite minimal and let the camera do most of the heavy lifting (also a learning opportunity to challenge ourselfs with only using the camera) 

#### Fixed speed instead of variable speed
- Tested variable speed (slowing near obstacles, full speed in open path)
- Found variable speed introduced **inconsistency** — behavior varied run to run depending on exactly when/where the speed transition kicked in
- Since our focus is on **consistency and accuracy** rather than raw lap time, we chose fixed speed instead
- A predictable, repeatable speed profile made the robot's behavior easier to tune and trust across multiple runs

| Speed | Accuracy | Time (without parking) |
|---|---|---|
| Fixed Speed | 90% | 52s |
| Variable Speed | 80% | 42s |

#### LAB color space instead of HSV
- Originally considered HSV for color detection
- Switched to LAB color space instead
- LAB gave noticeably better detection results and higher accuracy in our testing, especially under our lighting conditions
- Worth the switch even though HSV is more commonly used

#### Battery placed at the center of the plate
- Battery is the heaviest single component on the robot
- Placed it at the center of the first (bottom) plate rather than off to a side or at the front/back
- Centering the heaviest mass gives the robot a balanced center of gravity — weight is distributed evenly front-to-back and side-to-side
- This improves stability and predictability during turns, since the robot isn't nose-heavy, tail-heavy, or lopsided

---

### Constraints

#### Competition rule against differential drive
- Not allowed to use differential drive, so the design had to go front-steering from the start
- Front-steering directly ties turning radius to chassis length (`R = L / sin(θ)`), and the outer radius grows further with the robot's width (`R(outer) = R(center) + W/2`)
- This meant the drivetrain, motor, and steering assembly had to be packed tightly and deliberately, back to back, just to keep the turning radius manageable for parking maneuvers
- A rule about *drive type* ended up dictating chassis layout and packaging density

#### Hard weight capping of 1.5 kg
- Total weight is capped, but weight *distribution* mattered just as much as the total
- Every gram added anywhere on the robot competes with every other component for that budget
- This constraint forced trade-offs between convenience (e.g. easy battery access) and performance (e.g. low, centered center of mass) — performance won

#### Power budget tied to runtime requirement
- Needed the robot to run for over an hour on a single charge
- Every power-hungry addition has a knock-on effect: more power draw → bigger/heavier battery → slower robot
- This constraint quietly ruled out any component or approach that looked good in isolation but would have pushed the power draw too high

#### Control loop speed requirement
- The sense-think-act loop has to run fast enough to react before the robot reaches an obstacle or wall
- This constraint is why processing got split across two boards (Pi + Nano) in the first place — one board waiting on the other would violate this requirement
- It also ruled out anything (extra sensors, heavier vision models, etc.) that would add latency without a proportional benefit

---
### Risk and Failures

#### PCB Version 1: Thermal Failure

- After several test runs, the robot consistently shut down after about three corner turns, a repeatable pattern that pointed to a systematic issue rather than a random fault
- The L298 motor driver and 7805 voltage regulator were extremely hot to the touch during runs
- The 7805's datasheet showed it was reaching approximately 150 to 175°C, far above its rated maximum junction temperature, triggering its built in thermal shutdown to prevent permanent damage
- A power dissipation calculation confirmed the cause: the 7805 was burning off the full 7.8V drop at approximately 2A as heat, dissipating roughly **15.6W**, far more than a small TO-220 package can shed in free air without a heatsink
- Based on the regulator's junction to ambient thermal resistance, this dissipation translated to a theoretical temperature rise of nearly 242.85°C above ambient, mathematically guaranteeing thermal shutdown under our load, matching what we observed on the mat
- A power budget of the 5V rail (ESP32, servo, encoder) showed a peak of 1.03A on paper, but we measured 1.47A in practice, since real corner turns draw current from all three components simultaneously rather than one at a time

**Temporary Fix:**
- Attached an aluminum VEX piece to the 7805 as a heat sink to increase surface area and improve convective cooling
- This increased runtime from 1½ to 2¼ laps before shutdown, a 50% improvement, confirming heat (not a wiring fault) was the root cause
- The regulator still eventually overheated, since it had to continuously dissipate 15.6W, more heat than a small heat sink without forced airflow can carry away indefinitely

**Root Cause and Decision:**
- Since the heat sink helped but didn't fully solve the shutdowns, we ruled out PCB layout, wiring, or a component defect
- A linear regulator's efficiency is roughly Vout/Vin (5V / 12.8V ≈ 39%), meaning over 60% of the power on the 5V rail was converted directly into waste heat regardless of cooling
- We redesigned the power system around a switching (buck) converter, which achieves 85 to 95% efficiency instead of ~39%, dramatically cutting generated heat for the same output current

**PCB 1**

<img width="700" alt="PCB1 Labled" src="https://github.com/user-attachments/assets/3ba568ac-9926-49b1-bb8d-95997c263cd1" />


---

#### PCB Version 2: Motor Driver and Servo Failure

- After building the new PCB with the DRV8871 motor driver, the motor driver would not reliably power the motor, and plugging in the servo caused it to draw power from everything else, shutting down the ESP32, motor driver, and other electronics

**Failures Identified:**
- Signal mismatch: the ESP32 outputs a 0 to 3.3V PWM signal, but the DRV8871 performs best with 5V PWM, preventing reliable motor control
- Power isolation issue: the servo had no dedicated regulated power path, so its current spikes pulled down the shared supply rail and browned out the rest of the electronics

**Fixes Implemented:**
- Switched from the ESP32 to an Arduino Nano, which outputs a full 5V PWM signal the DRV8871 needs to operate reliably
- Added a dedicated 7805 regulator to the servo line to isolate it from the rest of the electronics
- Added a heatsink to that 7805 to manage the heat from the voltage conversion

**Servo Failure:**
- The MG90S servo couldn't handle the voltage load and burned out, and the 7805 was still overheating despite the heatsink
- We determined the servo needed a higher power unit rated for greater load, along with a regulator matched to the servo's input voltage to minimize the voltage drop and resulting heat

**Servo Solution:**
- Replaced the 5V servo with a 9g Coreless Servo (Full Metal Gear, 4 KG·cm torque, 4.8 to 8.4V)
- Added a dedicated 2 to 8S LiPo UBEC-8A, set to 8.4V
- Torque headroom: at 4 KG·cm, the new servo has enough margin above our steering load to avoid operating near stall, the condition that destroyed the original
- Full metal gears: since the original failure was mechanical as well as electrical, metal gears were needed to resist the stripping that plastic gears suffer under repeated high torque corrections
- Wide voltage range (4.8 to 8.4V) with a coreless motor: running at higher voltage increases torque and speed without redesigning the control signal path, and a coreless motor is faster and more efficient than a brushed motor of the same size
- The UBEC gives the servo its own regulated rail, solving the power sharing and brownout issue, is adjustable to exactly 8.4V to match the servo's max rating, is rated for 8A continuous against the servo's 3.0 to 5.0A peak draw, and safely accepts our 12.8V (4S) input well within its 2 to 8S range

**PCB Final Version with Implemented Changed**

<img width="500" alt="Final PCB Labeled" src="https://github.com/user-attachments/assets/91913f3f-8f83-4f09-9dc7-5200de732312" />

---

#### VM Pin Wiring Issue

- While wiring the DRV8871, we connected the Raspberry Pi, servo, and Arduino Nano to the driver's VM pin
- The VM pin is internally tied to the driver's P+ pin, which connects directly to the battery, so it was carrying the full 12.8V battery voltage instead of a regulated logic level
- The Pi, servo, and Nano all expected a regulated 5V (or their own rated) supply, and receiving 12.8V directly overloaded the DRV8871, causing it to blow up
- This taught us that the VM pin is a motor power input, not a general purpose output, and logic level components or the servo should never draw from it directly, each needs its own properly regulated supply

---

#### Iterations
The image shows the main robot iterations during development. Each version was tested and improved based on issues with stability, steering, and reliability.
<img width="1192" height="670" alt="Iteratonswdescription" src="https://github.com/user-attachments/assets/a82d7041-7978-48cf-935f-de3a5805f6b8" />

---
### Reproducibility & Github Organization

This repository documents the design, build, and code for our WRO robot — including the mechanical models, custom PCB/electronics, full parts list, and the engineering journal tracking our design decisions along the way. Use the sections below to navigate to whatever you need, whether that's rebuilding the robot from scratch or understanding why we made the choices we did.

---

### How to Assemble the Robot

Step-by-step mechanical assembly instructions, 3D models, and CAD files.

[Go to Assembly](models/README.md#2-the-assembly)

---

### How to Wire All Components

Here is a schematic which shows the entire electrical architecture of our robot

[Go to Schematic](electrical/Electrical_Schematic.png)

---
### Setting Up the Raspberry Pi

For installing dependencies, setting up a virtual environment, and getting the Pi ready to run this code, see [Raspberry Pi Setup Guide](code/md/raspberrypi_setup.md)

---

### Parts List

| Category | Component | Price |
|---|---|---|
| Processing Controller | Raspberry Pi 4b | $230.95 [Raspberry Pi Setup Guide](https://www.pishop.ca/product/raspberry-pi-4-model-b-8gb/?src=raspberrypi) |
| Slave Controller | Arduino Nano | $25.70 |
| Vision | Raspberry Pi Camera Module 3 Wide | $50.95 |
| Motor | 12V 37D Metal Gearmotor | $26.88 |
| Motor Driver | Adafruit DRV8871 | $7.50 |
| Servo | 8.4V High-Torque Coreless Servo | $17.00 |
| Servo Power Convertor | 8.4V 10A UBEC | $25.99|
| Power Convertor | 5V DC-DC Buck Converter | $2.80 |
| Battery Pack | IFR 18650 4S1P 12.8V 2000mAh Li-ion Battery Pack | $39.99 |

---

### Engineering Journal

Our full engineering journal — including trade-offs, constraints, and the reasoning behind every major decision — is documented here.

[Go to Engineering Journal](./docs/engineering-journal.md)
