# WRO-FE-2026-Sinθ 

# Introduction
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

## Mechanical Design

Our mobility system was built to maximize steering precision, stability, and reliability while staying compact enough for the WRO Future Engineers mat. Every part below went through multiple iterations before we landed on the final version.

- **Dimensions:** 230mm length × 105mm width × 256mm height, 1001g total.
Compact enough for tight turns and clean component packaging, while staying stable through high-speed cornering.
[Why We Chose These Dimensions](models/README.md#14-design-inspiration--chassis-dimensions)

- **Drive Motor:** 12V DC geared motor with an integrated encoder, driven through an Adafruit DRV8871.
Gives us the torque/speed balance we needed for the robot's weight, and the encoder feedback lets us track speed and distance for autonomous control.
[More on Motor & Driver Choice](schemes#1-motorization--power-system)

- **Steering:** 100% Ackermann geometry, actuated by a coreless black servo.
With a 7.18" wheelbase and 3.00" front track width, the geometry works out to ~12° at full lock. This keeps the inside and outside wheels turning on the correct radii, cutting down on tire scrub through corners.
[Why We Chose Ackermann](models#12-steering-system) · [Steering CAD](mobility/README.md#chassis)

<div align="center">

![Chassis layer 1](https://github.com/user-attachments/assets/7763083b-e341-4566-9f6d-96d56026d52a)
![Chassis layer 2](https://github.com/user-attachments/assets/116feb86-e038-4e22-8e40-c2fecf43d38d)
![Chassis layer 3](https://github.com/user-attachments/assets/200b7d2b-a27e-4cb8-b80d-62d3f662c3f5)

</div>

- **Chassis:** Three modular 3D-printed layers, bolted together with dedicated mounting points for every component.
Any layer can be pulled off on its own, so a repair or a redesign never means tearing the whole robot apart.
[Custom Mounts](mobility/README.md#chassis)

- **Wheels:** LEGO SPIKE Prime wheels.
Small, consistent grip, and lightweight — no reason to machine our own when these already do the job.
[Why We Chose These Wheels](models#1-mechanical-design-choices)

- **Differential:** Rear metal differential.
Lets the two rear wheels spin at different speeds through a turn, which reduces scrub and stress on the drivetrain.
[Why We Chose This Differential](models#13-rear-differential)

- **Iterations:** The chassis, steering geometry, and mounts all went through several redesigns focused on precision, weight, rigidity, and ease of assembly.
[Full Development History](mobility/README.md#development)

# Software Architecture & Obstacle Strategy

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
<img width="500" alt="FEimg" src="https://github.com/user-attachments/assets/67cfe969-abe5-4fab-a21a-e3281df701fa" />

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


# Systems Thinking & Engineering Decisions

# Reproducibility & Github Organization

