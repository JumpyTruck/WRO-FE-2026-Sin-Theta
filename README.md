# WRO-FE-2026-Sinθ 

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

# Mobility Management

The mobility system was designed to maximize steering precision, stability, and reliability while remaining compact enough to navigate the WRO Future Engineers Game Mat. Every mechanical component was selected after multiple iterations and testing to improve turning performance, simplify maintenance, and increase consistency during competition.

---

## Robot Dimensions

The final robot measures:

| Specification | Value |
|--------------|------:|
| Length | 230 mm |
| Width | 105 mm |
| Height | 256 mm |
| Weight | 1001 g |

These dimensions were selected to provide a compact footprint while maintaining enough internal space for all electronic components and ensuring stable handling during high-speed cornering.

[More about Robot Dimensions Choice](models/README.md#14-design-inspiration--chassis-dimensions) 

---

## Drive System

| Component | Selected Part |
|-----------|---------------|
| Drive Motor | 12V DC Geared Motor |
| Motor Driver | Adafruit DRV8871 |

Our drivetrain uses a rear-wheel-drive configuration powered by a 12V DC geared motor. After evaluating multiple options, this combination provided the best balance of speed, torque, simplicity, and reliability for the competition.

The motor provides sufficient torque for the robot's mass while maintaining
the speed required for the competition course. Its integrated encoder also
provides speed and distance feedback for autonomous control.

### Motor Torque Calculation

The selected motor has a **rated torque of 1.8 kg·cm at 285 RPM** and a
**stall torque of 4 kg·cm**.

For our 56 mm diameter wheels:

\[
r = \frac{56}{2} = 28\text{ mm} = 0.028\text{ m}
\]

Converting the motor's rated torque:

\[
T_{rated} = 1.8 \times 0.0981
\]

\[
T_{rated} = 0.1766\text{ N·m}
\]

To verify that the motor is sufficient, we used a design acceleration target
of **2.0 m/s²** for our 1.001 kg robot.

The force required to achieve this acceleration is:

\[
F = ma
\]

\[
F = (1.001)(2.0)
\]

\[
F = 2.002\text{ N}
\]

The corresponding wheel torque required is:

\[
T_{required} = Fr
\]

\[
T_{required} = (2.002)(0.028)
\]

\[
T_{required} = 0.0561\text{ N·m}
\]

To account for losses through the differential, bearings, tires, and other
drivetrain components, we conservatively assume **70% drivetrain efficiency**:

\[
T_{actual\ required} =
\frac{0.0561}{0.70}
\]

\[
T_{actual\ required} \approx 0.0801\text{ N·m}
\]

Comparing this with the motor's rated torque:

\[
\text{Torque Margin} =
\frac{0.1766}{0.0801}
\]

\[
\boxed{\text{Torque Margin} \approx 2.20\times}
\]

Therefore, the motor's rated torque is approximately **2.2 times greater than
the torque required** to achieve our 2.0 m/s² design acceleration after
allowing for drivetrain losses.

This provides sufficient torque for reliable acceleration while leaving
additional torque available for normal drivetrain losses and changes in
operating conditions.


[More about Motor and Motor Driver Choice](schemes#1-motorization--power-system)

---

## Steering System

| Component | Selected Part |
|-----------|---------------|
| Steering Type | Ackermann Steering |
| Servo | Coreless Servo Black |

**Steering Motor: Servo motor for precise and simple steering**

[More about Servo Motor](schemes#13-steering-servo-mg90s)


To improve cornering accuracy and reduce tire scrub, the robot uses a 100% Ackermann steering geometry. The steering mechanism was redesigned through multiple iterations before reaching the final geometry shown below.

[Why We Chose Ackermann](models#12-steering-system)

<div align="center">

**Steering Animation**

*Insert GIF here*

</div>

<div align="center">

**Ackermann Geometry**

*Insert steering calculation / diagram here*

With a wheel base length of 7.18" and a front axle/track width of 3.00", the appropriate angle to meet the 100% ackermann geometry is ~12 degrees, as is delineated in the below sketch. For reference, a 100% ackermann means the imaginary lines visualized from either steering knuckle meet directly at the centre of the rear axle.

*I will insert image later*

</div>

[Steering CAD](mobility/README.md#chassis)

---

## Chassis Assembly

The chassis consists of three modular 3D-printed layers that simplify assembly and maintenance while providing rigid mounting locations for every component. This open-architecture design allows us to easily update and iterate upon our designs, while simultaneously allowing us to quickly repair our robot.

<div align="center">

<img width="1245" height="700" alt="firstplaterenamed" src="https://github.com/user-attachments/assets/7763083b-e341-4566-9f6d-96d56026d52a" />

<img width="1248" height="700" alt="secondplate" src="https://github.com/user-attachments/assets/116feb86-e038-4e22-8e40-c2fecf43d38d" />

<img width="1333" height="748" alt="thirdplate" src="https://github.com/user-attachments/assets/200b7d2b-a27e-4cb8-b80d-62d3f662c3f5" />


</div>

The modular construction allows individual sections to be removed without completely disassembling the robot, making repairs and modifications significantly easier during development.

[Pictures of Custom Mounts](mobility/README.md#chassis)

---

## Wheels & Differential


**Wheel selection: The robot uses LEGO SPIKE Prime wheels for their compact size, consistent grip, and lightweight construction**  
[More about Wheel Choice](models#1-mechanical-design-choices)

**Differential design:  Power is transferred through a rear metal differential, allowing both drive wheels to rotate at different speeds while cornering, improving stability and reducing mechanical stress.**  
[More about Differential Choice](models#13-rear-differential)

---

## Development Process

The final mobility system is the result of numerous design iterations involving the chassis, steering mechanism, and component placement. Each revision focused on improving steering precision, reducing weight, increasing rigidity, maximizing efficiency, and simplifying assembly.

*Insert timeline or iteration image here.*

**Complete development history:**  
[Mechanical Development](mobility/README.md#development)

# Obstacle Management

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
<img width="500" alt="roi_image" src="https://github.com/user-attachments/assets/70c2e6a1-26c4-4923-b3e5-98dfb3129433" />

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

<div align="center">

**Parking Sequence**

`Lap Complete → Find Pink → Align → Approach → Stop`

While approaching the parking area, the robot continues checking for nearby obstacles. If an obstacle is closer than the pink block, obstacle avoidance takes priority.

Once the pink block reaches the required distance and horizontal alignment, the robot stops and begins the final parking manoeuvre.

The final manoeuvre uses **encoder-based movements** to control the distance travelled during each forward, reverse, and turning movement.

---

## Autonomous Navigation Flowcharts

### Open Course

[Open-course flowchart]

### Obstacle Course

[Obstacle flowchart]

