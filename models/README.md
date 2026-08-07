### Mechanical Design Process

#### 1\. Mechanical Design Choices

###### **1.1 Wheel Selection**
We chose **SPIKE Prime wheels (56mm diameter, 14mm thickness)** for the balance they strike between speed, torque, and stability. They're compact enough to keep the robot lightweight while still giving sufficient grip and clearance on the WRO mat.

<img width="280" alt="spike_wheels" src="https://github.com/user-attachments/assets/873b32bb-68e5-45ca-adc8-cf2fd2dda6f8">

---

###### **1.2 Steering System**
We tested different steering mechanisms to improve turning accuracy and reduce drifting.

<table>
<tr>
<td align="center" width="50%">
<b>Previous Design — Parallel Beam Steering</b><br><br>
<img width="220" src="https://github.com/user-attachments/assets/73cccba8-f506-4c5d-ad07-ef9bd6d4d4c9"><br><br>
Both wheels turned at the same angle, causing drift as the inner and outer wheels followed different turning paths.
</td>
<td align="center" width="50%">
<b>Final Design — Ackermann Steering</b><br><br>
<img width="220" src="https://github.com/user-attachments/assets/56d586ea-e4fe-49f3-8ea5-3422533bf388"><br><br>
Each wheel follows its own turning radius, reducing wheel slip and improving cornering accuracy.
</td>
</tr>
</table>

---

###### **1.3 Rear Differential**
A metal differential drives the rear wheels, letting them rotate at different speeds through turns. We chose metal over 3D-printed gears for smoother cornering and better durability, and over LEGO-based alternatives for a lower centre of gravity.

<img width="336" alt="IMG_2312" src="https://github.com/user-attachments/assets/91a28dd0-2991-4b22-a469-cf7e6f4bac3d">

---

###### **1.4 Design Inspiration & Chassis Dimensions**
Before designing our chassis, we sketched out different vehicle layouts and proportions, drawing inspiration from Formula One cars — a longer, narrower body for better stability and smoother, more controlled turning. Overall dimensions were chosen to stay compact while fitting the Raspberry Pi, custom PCB, DC motor, battery, and sensors, keeping a balanced centre of gravity without sacrificing agility.

<img width="252" alt="IMG_1527" src="https://github.com/user-attachments/assets/17898f3a-5b99-4380-ab8f-eba7226495c5">

---

#### 2\. Structural Design Process

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

###### **2.3 Iteration 3 — Final Optimized Chassis**
The final chassis fits all required components with an improved layout. The motor mount was redesigned with a top opening so the motor slides in like a "hat" mount, simplifying assembly. The battery pack sits centered on the chassis for a balanced centre of gravity.

**Improvements:** room for all electronics and structural parts, simpler motor mounting, centered battery placement, and better stability under acceleration and turning.

<img width="336" alt="IMG_2299" src="https://github.com/user-attachments/assets/d65b5031-916f-4674-9e84-d1f3296ae2f0">

---

###### **2.4 Final Robot Assembly**
The final robot brings together every mechanical improvement: the optimized chassis, Ackermann steering, rear differential, SPIKE Prime wheels, and integrated electronics mounting — built for reliability, balanced weight, and precise movement throughout the WRO Future Engineers challenge.

<img width="252" alt="IMG_1967" src="https://github.com/user-attachments/assets/0cca0d85-2654-46ef-bd2c-4e263146fa95">
