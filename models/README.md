### Current Mechanical Design

#### 1\. Chassis
The chassis the "backbone" of our robot, from which everything is built around, featuring a modular base that allows parts to be continuously iterated upon and easily replaced, making maintenance and updates a simple process.

###### **1.1 Steering Assembly Holder**
The front of the chassis is defined by a raised trapezoid-like section, featured with four mounting holes, from which the steering system is mounted. It is "insert measuremnt" thick, which not only allows for greater strength, it generates a positive rake (the front axle is lower in reference from the rear axle) which creates better stability in high-speed turning, while additionally providing a better angle for our camera to observe the game field. Additionally, it has the cutout in the middle to allow space for the servo motor.

<img width="280" alt="spike_wheels" src="https://github.com/user-attachments/assets/873b32bb-68e5-45ca-adc8-cf2fd2dda6f8">

---

###### **1.2 Battery Holder**
Our 12.8V [battery](schemes/README.md#14-battery-pack) is (add Dimentions), and weighs (add weight), demanding careful placement in our robot to ensure even balance and stability. Our [motor](schemes/README.md#11-dc-motor-selection) is hefty and powerful, and with it being rear-mounted [read more about motor mounting decision](models/README.md#13-motor-mount), it is necessary for the battery to be front-mounted. Furthermore, the battery being mounted as low as possible (over a mounting position akin to the pcb holder, to conserve length) helps to reduce the chance of tipping/rolling, increasing overall stability. 

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

###### **1.5 Rear Differential**
A metal differential drives the rear wheels, letting them rotate at different speeds through turns. We chose metal over 3D-printed gears for smoother cornering and better durability, and over LEGO-based alternatives for a lower centre of gravity.

<img width="336" alt="IMG_2312" src="https://github.com/user-attachments/assets/91a28dd0-2991-4b22-a469-cf7e6f4bac3d">

---

###### **1.6 Miscellaneous**
**Mounting Points**
Four mounting holes can be find directly before the battery holder as well as in between the mounting points for the rear axle assembly, larger then the other M3 screw-sized holes, are made for (insert measurement) VEX Standoffs upon which the [PCB Holder](models/README.md#21-pcb-holder-second-story) will be placed.

**General Shape**
The general shape of the chassis is a rectangle (insert dimensions) with cutaways at the mid-front, forming a trapezoid --> small rectangle --> large rectangle transition, necessary to provide the front wheels space to move and steer.

---

#### 2\. Steering System - 100% Ackermann
<img width="660" src="https://github.com/user-attachments/assets/786d707b-36d0-486a-b7bc-ed254cc347fb"><br><br>
###### **2.1 Steering Holder**
The steering holder is what all the parts of the steering assembly attach too, with an attachment point for the servo motor to fit inverted (to level the servo output with the steering knuckles), cutaways on either side for the steering knuckles, as well as a large swept cut out portion in the front to allow the servo output to move with freedom. It features a strong and sturdy design, with six "arms" to keep it strong, minimize weight, and to increase the coincident surface area between itself and the chassis, helping to stay sturdy and rooted down.

---

###### **2.2 Steering Knuckle**
The steering knuckle is the main point of the steering assembly, from which the wheels attach and the steering motion is incurred. In order to complete the 100% Ackermann Design (to reduce tire scrubbing and increase turning efficiency; inside turns more than the outside), the knuckles maintain a 12 degree angle pointing inwards toward the centre of the rear axle (thus 100% Ackermann). They are (insert dimension) long to provide as much space as possible for steering motion, to increase steering angle as much as possible. Additionally, thin 1/8th inch nylon spacers are placed on the inside of the wheel to reduce friction between the spinning wheels and 3d printed surfaces.

---

###### **2.3 Steering T**
This piece slips on top of the servo motor output to increase its overall length as well as to increase the mesh between the servo output (secured with two screws) and the steering bar (attached with an M3 screw).

---

###### **2.4 Steering Bar**
The steering bar connects across both steering knuckles with an attachment point in the centre for the steering T, converting the servo output to actual steering through the knuckles.

---

#### 3\. Rear Axle Assembly
###### **3.1 Motor Adapter**
This piece is an adapter for the "D"-Shape Motor output into the Square-cut input for the differential input gear, with slots that "hug" both the input and the output to increase mesh as much to possible, thus increasing motor --> wheel efficiency.

---

###### **3.2 Input Gear Holder**
The input gear holder is a stand that keep the differential input gear in place, for optimal mesh with the differential, and reduced slippage.

---

###### **3.3 Differential Holder**
These simple stands hold the differential in place, mounted on the differential's ball bearing to reduce rolling friction as much as possible.

---

###### **3.4 Axle Supports**
The same design for the differential holder and input gear holder, only with adjusted slots to hold a different set of ball bearing, through which our custom metal axles feed through, to reduce sagging, increase strength, and reduce friction.

---

###### **3.5 Axles**
These custom metal 3d printed axles are specially designed to perfectly convert the differential output into the LEGO axle necessary to drive the SPIKE Prime wheels, which are accompanied by LEGO rubber elements connected to the axle and then the wheel itself with a peg to ensure the wheel stays on snug, as well as to ensure as much rotation is transferred to the wheels as possible.

---

#### 3\. PCB Holder/Second Story Plate
The second story (or second plate) is the holder for the slave controller, responsible for orchestrating the movements of the motor and servo, by combining together instructions from the Raspberry Pi 4b, sending them through the motor driver and independent voltage regulators, and thus interpreting digital signals into physical movement.

The plate itself is a series of cut walls the form together two conjoined rectangles. The main rectangle accommodates the custom [PCB](schemes), with small cuts on either side for the USB --> Micro USB wire via which the Serial information is transmitted. The second, outer rectangle serves a double purpose: first to give a home to the independent servo voltage regulator, and second if we ever need to switch back to our original PCB, helping to maintain modularity and flexibility in our design.

Additionally, it maintains flared edges to which four mounting points designed for VEX Standoffs attach to; this is where the [Raspberry Pi Holder](models/#4-raspbeery-pi-4b-holder-third-story-plate) attaches atop.

---

#### 4\. Raspberry Pi 4b Holder/Third Story Plate
This is the topmost part of our robot, a spot at which not only the Raspberry Pi 4b sits, but the camera as well. It is a simple rectangle with the mounting points on the outer edges, accompanied by a simple wrap-around wall to hold the Raspberry Pi, except with two wall knocked off to maintain access to connection points.

Additionally, jetting out infront is the rising (insert dimension) mounting points for the camera holder, providing the camera with a high-up view, allowing it to get the optimal view of the game mat.

---

#### 5\. Camera Mount
In our design, the camera mount is its own independent and modualar piece, allowing for quick and easy adjustments to camera mounting angle if necessary. For now, it is angled to 135 degrees and has four mounting points for our [camera](schemes).

---

#### 6\. Wheel Selection
We chose **SPIKE Prime wheels (56mm diameter, 14mm thickness)** for the balance they strike between speed, torque, and stability. They're compact enough to keep the robot lightweight while still giving sufficient grip and clearance on the WRO mat.

<img width="280" alt="spike_wheels" src="https://github.com/user-attachments/assets/873b32bb-68e5-45ca-adc8-cf2fd2dda6f8">

