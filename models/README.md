### Current Mechanical Design

#### 1\. Chassis
The chassis the "backbone" of our robot, from which everything is built around, featuring a modular base that allows parts to be continuously iterated upon and easily replaced, making maintenance and updates a simple process.

###### **1.1 Steering Assembly Holder**
The front of the chassis is defined by a raised trapezoid-like section, featured with four mounting holes, from which the steering system is mounted. It is "insert measuremnt" thick, which not only allows for greater strength, it generates a positive rake (the front axle is lower in reference from the rear axle) which creates better stability in high-speed turning, while additionally providing a better angle for our camera to observe the game field.

<img width="280" alt="spike_wheels" src="https://github.com/user-attachments/assets/873b32bb-68e5-45ca-adc8-cf2fd2dda6f8">

---

###### **1.2 Battery Holder**
Our 12.8V [battery](schemes/README.md#14-battery-pack) is quite large heavy, demanding careful placement in our robot to ensure even balance and stability. Our [motor](schemes/README.md#11-dc-motor-selection) is hefty and powerful, and with it being rear-mounted [read more about motor mounting decision](models/README.md#13-motor-mount), it is necessary for the battery to be front-mounted. Furthermore, the battery being mounted as low as possible (over a mounting position akin to the pcb holder, to conserve length) helps to reduce the chance of tipping/rolling, increasing overall stability. 

Additionally, the battery holder has it front corners cut off 4/5 of the way up to reduced the rubbing friction from the front tires as they spin, thus increasing efficiency and limiting wear.

<img width="280" alt="spike_wheels" src="https://github.com/user-attachments/assets/873b32bb-68e5-45ca-adc8-cf2fd2dda6f8">

---

###### **1.3 Motor Mount**
The [motor](schemes/README.md#11-dc-motor-selection) is the heart of our robot, enabling to navigate the course, thus ensuring its ideal placement was of the utmost importance. The motor mount is placed in the mid-to-rear of the chassis with a rear wheel drive (akin to a M/R Car). This "mid-engine" layout allows easier turning (with the main weight placed in the rear) as well as greater efficiency as it form the shortest distance possible from the motor to the wheels, limiting losses to the drivetrain.

The motor itself is mounted through an array of mounting points found on its front face, that are mirrored onto the mount for attachment. Furthermore, the mount itself is split into an upper and a lower half which allows the motor to be placed, and then covered by the top half to be held in place by four long screws.

<img width="280" alt="spike_wheels" src="https://github.com/user-attachments/assets/873b32bb-68e5-45ca-adc8-cf2fd2dda6f8">

---

###### **1.4 Rear Axle Mounting Points**
The final, rear-most section of the chassis is defined by a myriad of cut-outs and mounting points, made to allow the differential space to spin freely, as well as places to attach the various supports for the rear axle assembly.

<img width="280" alt="spike_wheels" src="https://github.com/user-attachments/assets/873b32bb-68e5-45ca-adc8-cf2fd2dda6f8">

---

###### **1.5 Miscellaneous**
**Mounting Points**
Four mounting holes can be find directly before the battery holder as well as in between the mounting points for the rear axle assembly, larger then the other M3 screw-sized holes, are made for (insert measurement) VEX Standoffs upon which the [PCB Holder](models/README.md#21-pcb-holder-second-story) will be placed.

**General Shape**
The general shape of the chassis is a rectangle (insert dimensions) with cutaways at the mid-front, forming a trapezoid --> small rectangle --> large rectangle transition, necessary to provide the front wheels space to move and steer.

---

#### 2\. Steering System - 100% Ackermann
<img width="660" src="https://github.com/user-attachments/assets/786d707b-36d0-486a-b7bc-ed254cc347fb"><br><br>
The steering system utilized on our robot is a 100% ackermann steering (working out to about a 12 degree angle, see below image) which helps to prevent tire scrubbing, increasing overall robot efficiency, with the inner wheel steering more than the outer wheel. The steering knuckles are (insert dimesnsions) long, the longest possible to allow for the most room for movement, all to maximize steering angle (insert degree). The steering assembly is made up of around 

---

###### **1.3 Rear Differential**
A metal differential drives the rear wheels, letting them rotate at different speeds through turns. We chose metal over 3D-printed gears for smoother cornering and better durability, and over LEGO-based alternatives for a lower centre of gravity.

<img width="336" alt="IMG_2312" src="https://github.com/user-attachments/assets/91a28dd0-2991-4b22-a469-cf7e6f4bac3d">

---

###### **1.4 Design Inspiration & Chassis Dimensions**
Before designing our chassis, we sketched out different vehicle layouts and proportions, drawing inspiration from Formula One cars — a longer, narrower body for better stability and smoother, more controlled turning. Overall dimensions were chosen to stay compact while fitting the Raspberry Pi, custom PCB, DC motor, battery, and sensors, keeping a balanced centre of gravity without sacrificing agility.

<img width="252" alt="IMG_1527" src="https://github.com/user-attachments/assets/17898f3a-5b99-4380-ab8f-eba7226495c5">

---

#### 2\. Structural Design Process - Main Chassis Base

After finalizing the main mechanical choices, we developed multiple chassis iterations to optimize component placement, structural strength, and weight distribution.

###### **2.1 Iteration 1 — Initial Frame Design**
The first prototype was a basic structural frame with mounting points for the DC motor and servo. It didn't include mounting points for a second plate, making it hard to securely attach the Raspberry Pi, custom PCB, and camera.

**Issues:** no space for standoffs between plates, limited room for future components.

<img width="336" alt="IMG_2297" src="https://github.com/user-attachments/assets/c09e16ee-0dce-4a40-99b6-c4569ce3b0a5">

---

###### **2.2 Iteration 2 — Expanded Frame Design**
We increased the overall size and added standoff mounting holes so a second plate could hold the electronics. This introduced a new problem: no room left for the battery pack.

**Issues:** improved structural support, but insufficient space for the battery, leading to uneven weight distribution.

<img width="336" alt="IMG_2298" src="https://github.com/user-attachments/assets/b72d6ca1-537b-4b37-b571-bb60e22433d7">

---

###### **2.3 Iteration 3 — Initial Complete Chassis**
The initial complete chassis fits all required components with an improved layout. The motor mount was redesigned with a top opening so the motor slides in like a "hat" mount, simplifying assembly. The battery pack sits centered on the chassis for a balanced centre of gravity.

**Improvements:** room for all electronics and structural parts, simpler motor mounting, centered battery placement, and better stability under acceleration and turning.

<img width="336" alt="IMG_2299" src="https://github.com/user-attachments/assets/d65b5031-916f-4674-9e84-d1f3296ae2f0">

---

###### **2.4 Initial Robot Assembly**
The initial robot brings together every mechanical improvement: the optimized chassis, Ackermann steering, rear differential, SPIKE Prime wheels, and integrated electronics mounting — built for reliability, balanced weight, and precise movement throughout the WRO Future Engineers challenge.

<img width="252" alt="IMG_1967" src="https://github.com/user-attachments/assets/0cca0d85-2654-46ef-bd2c-4e263146fa95">

---

#### 3\. Structural Design Process - Second Story Plate

The second story (or second plate) is the holder for the slave controller, responsible for orchestrating the movements of the motor and servo, by combining together instructions from the Raspberry Pi 4b, sending them through the motor driver and independent voltage regulators, and thus interpreting digital signals into physical movement.

###### **3.1 Initial Design**

---
#### 4\. **4.0 Iteration 4 - Final Optimized Chassis/Robot Assembly**
The final chassis and robot design harmonizes multiple minor improvements to maximize our robots capabilities and efficiency.
Changes:
  - The rear standoffs have been repositioned further back to reduce rubbing frictions between themselves and the metal driving axles.
  - The frontal area of the chassis has been redesigned to accommodate the newly improved steering design.
  - The battery holder has had its corners removed to prevent rubbing friction with the front SPIKE wheels.
  - Nylon spacers feature at the front and rear axles to improve the wheels' stability, while reducing friction and catching, additionally rubber outer elements are added to improve the efficiency of rotating motion transferred into the wheels while keeping them firmly secured.
  - The portion too which the steering assembly attaches to in the front has been raised by 3/4" to generate positive rake (changing from the previous negative rake) in order to increase stability, improve the camera's view, as well as too reduce stress on the chassis.

<img width="2292" height="3058" alt="PXL_20260730_192531841 MP" src="https://github.com/user-attachments/assets/dd5e9801-0620-4be2-9a9e-7f1922619b95" />

###### **1.1 Wheel Selection**
We chose **SPIKE Prime wheels (56mm diameter, 14mm thickness)** for the balance they strike between speed, torque, and stability. They're compact enough to keep the robot lightweight while still giving sufficient grip and clearance on the WRO mat.

<img width="280" alt="spike_wheels" src="https://github.com/user-attachments/assets/873b32bb-68e5-45ca-adc8-cf2fd2dda6f8">

---

