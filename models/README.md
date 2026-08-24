### Mechanical Design — Full Details

The main README covers what our mobility system is; this page covers how we got there and how every 3D-printed part fits together. If you want to reproduce or modify any part, this is where the actual design logic and part-by-part breakdown live. All STEP, STL, and PNG files are in [this folder](./CAD_3D_Printed_Pieces/).

---

## 1. Basic Design Choices

Before building anything, we made a few core decisions that everything else was designed around.

###### **1.1 Dimensions**
The chassis footprint wasn't picked first — it fell out of fitting the Pi, driver board, motor, and steering geometry together with enough margin (~50mm) around each side. We tested a few footprints before landing on the final size. A robot with a large length-to-width ratio turns like a car with a wide turning radius — great for straight-line stability, bad for tight courses. Keeping the chassis longer and narrower gave us a smaller turning radius, which mattered more once we started testing around the mat's pillars.

###### **1.2 Wheel Choice**
We chose **SPIKE Prime wheels (56mm diameter, 14mm thickness)**. Larger wheels would hurt maneuverability and eat up space we needed elsewhere for electronics; smaller wheels would reduce ground clearance and complicate the axle design. At 56mm, we get enough grip and clearance on the mat without adding unnecessary bulk or weight.

<img width="300" alt="Spike Prime wheel" src="https://github.com/user-attachments/assets/c5ac25da-1d0f-453b-8c17-f5e84693a9d4">

###### **1.3 Differential — Why Metal**
We considered three options for the rear differential: 3D-printed gears, a LEGO-based differential, and a metal differential. Printed gears wear down quickly under repeated load and mesh less precisely, which shows up as inconsistent cornering. A LEGO differential works but sits higher and bulkier, raising our center of gravity. We went with a compact metal differential — it meshes smoothly for consistent cornering, holds up over long-term use, and keeps our center of gravity lower than the LEGO alternative.

<img width="336" alt="Rear differential" src="https://github.com/user-attachments/assets/91a28dd0-2991-4b22-a469-cf7e6f4bac3d">

###### **1.4 Steering — Why We Moved to Ackermann**
Last year, our robot used parallel steering — both front wheels turned on the same fixed radius through a beam linkage. That works fine going straight, but through corners the inside and outside wheels both want to travel their own distinct arc; forcing them to turn equally causes the tires to scrub sideways against the mat, costing us speed and control precision.

This year we switched to Ackermann steering, where each wheel turns at its own angle so the inside wheel always turns sharper than the outside wheel. We first proved the geometry out in a LEGO Ackermann linkage before committing to a 3D-printed design built around our chassis.

**Ackermann Angle Calculation**

With a wheelbase of 7.18" and a front track width of 3.00", the required knuckle angle for 100% Ackermann geometry comes out to **~12°**. In 100% Ackermann steering, the imaginary lines extended from each knuckle pivot meet exactly at the center of the rear axle — this is what guarantees the inside and outside wheels are always turning on their own correct radius instead of fighting each other.

*(insert the calculation sketch / derivation image here)*

<img width="700" alt="Steering prototype to Ackermann" src="https://github.com/user-attachments/assets/f464be3b-9783-44a1-b989-7284e19a2d47">

---

## 2. In-Depth Build — Chassis, Steering, and Rear Axle

This section breaks down every printed part that makes up the chassis, steering assembly, and rear axle — what it does and how it's built.

### 2.1 Structural Prototype

Before finalizing the printed chassis, we built a LEGO structural prototype using 15-hole beams, L-beams, and frames to test how the steering and differential systems would connect. This confirmed motor placement (centrally located, axle feeding into the differential) and told us to keep the front of the chassis thin to leave room for the steering knuckles to swing through their full range.

<img width="700" alt="Structural prototype" src="https://github.com/user-attachments/assets/c30e563b-5177-4f33-b9d7-738bdfb9febb">

---

### 2.2 Chassis — Part by Part

The chassis is split into three stacked, modular plates. Splitting it this way means any single layer can be pulled and reprinted without touching the others.

###### **Base Plate — Steering Assembly Holder**
The front of the base plate is a raised, trapezoid-shaped section with four mounting holes for the steering assembly. Its thickness creates a slight positive rake — the front axle sits lower than the rear — which improves stability in high-speed cornering and gives the camera a better viewing angle over the mat. A center cutout leaves clearance for the steering servo.

<img width="280" alt="Steering assembly holder" src="https://github.com/user-attachments/assets/873b32bb-68e5-45ca-adc8-cf2fd2dda6f8">

###### **Base Plate — Battery Holder**
The battery mounts at the front of the chassis, low to the ground, to counterbalance the rear-mounted motor and keep the center of gravity down — both reduce the chance of tipping during hard turns. The front corners of the holder are cut back to clear the spinning front tires, reducing friction and wear over time.

###### **Base Plate — Motor Mount**
The motor sits mid-to-rear in a rear-wheel-drive layout, similar to a mid-engine car. This keeps the distance between motor and wheels as short as possible, minimizing drivetrain losses, while balancing weight toward the rear for more predictable turning. The mount splits into upper and lower halves — the motor drops into the lower half and is capped by the upper half, secured through four screws into the motor's mounting face.

###### **Base Plate — Rear Axle Mounting Points**
The rear section of the base plate has cutouts giving the differential room to spin freely, plus mounting points for the rear axle support pieces described in Section 2.4.

###### **Base Plate — Shape & Standoffs**
The plate transitions from a trapezoid at the front to a small rectangle to a larger rectangle at the rear — the narrowing gives the front wheels room to steer without hitting the frame. Oversized mounting holes near the battery holder and rear axle mounts carry VEX standoffs, which the second-story plate sits on top of.

<table>
  <tr>
    <td align="center"><strong>Base Plate CAD</strong><br>
      <img src="https://github.com/user-attachments/assets/ed26cf6f-1e57-44ea-9111-e2258d0c9bfd" width="700">
    </td>
  </tr>
  <tr>
    <td align="center"><strong>Base Plate Installed</strong><br>
      <img src="https://github.com/user-attachments/assets/85e35aba-d1d7-4a9b-9ccd-64304d10f4f9" width="700">
    </td>
  </tr>
</table>

---

###### **Second Story — PCB Holder**
This plate holds our custom PCB, which takes commands from the Raspberry Pi and drives the motor and servo through the motor driver and voltage regulators. It's shaped as two connected rectangles: the main one seats the PCB with side cutouts for the USB cable, and the smaller second rectangle houses the servo's voltage regulator — it also doubles as a mounting spot for our original PCB if we ever need to swap back, keeping the design flexible. Flared edges around the plate carry the four VEX standoffs that the third-story plate mounts onto.

<table>
  <tr>
    <td align="center"><strong>Second Story CAD</strong><br>
      <img src="https://github.com/user-attachments/assets/753e8e88-8ea8-4e7f-975f-84e3ff07923b" width="700">
    </td>
  </tr>
  <tr>
    <td align="center"><strong>Second Story Installed</strong><br>
      <img src="https://github.com/user-attachments/assets/a77fad93-acb5-4cf7-8e73-98f99a5fe356" width="700">
    </td>
  </tr>
</table>

---

###### **Third Story — Raspberry Pi Holder**
The top plate holds the Raspberry Pi and camera. It's a simple rectangle with mounting points around the edges and a partial wraparound wall to keep the Pi seated, with two sides left open for cable access. Mounting posts extend forward off the front edge to raise the camera mount up high, giving it a clear, unobstructed view over the front of the robot.

<table>
  <tr>
    <td align="center"><strong>Third Story CAD</strong><br>
      <img src="https://github.com/user-attachments/assets/31292077-ac72-448d-aec0-7736a08eae95" width="700">
    </td>
  </tr>
</table>

###### **Camera Mount**
A standalone, modular piece so we can adjust the camera angle without touching the rest of the top plate. It's currently set to 135° and has four mounting holes for the camera.

---

###### **Full Assembly Views**

<table>
  <tr>
    <td align="center"><strong>Left Side View</strong><br>
      <img src="https://github.com/user-attachments/assets/81fb3c33-7f9e-419c-99c4-76afcae5621d" width="700">
    </td>
  </tr>
  <tr>
    <td align="center"><strong>Top View</strong><br>
      <img src="https://github.com/user-attachments/assets/0c307909-5943-4f71-b58f-66a1c21ec9f9" width="700">
    </td>
  </tr>
  <tr>
    <td align="center"><strong>Bottom View</strong><br>
      <img src="https://github.com/user-attachments/assets/2bacd053-ec0a-4207-bb49-d4b5b8f2829f" width="700">
    </td>
  </tr>
</table>

---

### 2.3 Steering Assembly — Part by Part

<img width="660" alt="Steering assembly" src="https://github.com/user-attachments/assets/786d707b-36d0-486a-b7bc-ed254cc347fb">

###### **Steering Holder**
Every part of the steering assembly attaches to this piece. The servo mounts inverted so its output lines up level with the steering knuckles, with cutaways on both sides for the knuckles and a swept opening in front for the servo horn to move freely. Six support arms keep it rigid while minimizing weight and maximizing contact area with the chassis below.

###### **Steering Knuckle**
This is where each wheel attaches and where the steering motion actually happens. Each knuckle is fixed at the ~12° angle calculated in Section 1.4, angled inward toward the center of the rear axle to complete the 100% Ackermann geometry. The knuckle arms are kept as long as possible to maximize the achievable steering angle. Thin 1/8" nylon spacers sit between the wheel and the printed surfaces to reduce friction.

###### **Steering T**
Slides over the servo output to extend its reach and increase the contact area between the servo horn (secured with two screws) and the steering bar (secured with a single M3 screw).

###### **Steering Bar**
Connects both knuckles together, with a center attachment point for the steering T. This is the piece that actually converts the servo's rotation into both knuckles turning left or right in sync.

[Steering CAD Files](./CAD_3D_Printed_Pieces/)

---

### 2.4 Rear Axle Assembly — Part by Part

###### **Motor Adapter**
Adapts the motor's D-shaped output shaft to the square input of the differential's input gear. The slots hug both shapes tightly to maximize mesh and minimize power loss between the motor and wheels.

###### **Input Gear Holder**
A simple stand that keeps the differential's input gear aligned for consistent mesh and to prevent slipping under load.

###### **Differential Holder**
Holds the differential in place, seated on its ball bearing to keep rolling friction as low as possible.

###### **Axle Supports**
Built on the same design as the differential holder, but sized for a different bearing — these support our custom metal axles to prevent sagging and reduce friction as they spin.

###### **Axles**
Custom-machined metal axles convert the differential's output into the LEGO axle profile needed to drive the SPIKE Prime wheels. LEGO rubber connectors and a peg keep each wheel seated snugly and ensure as much rotational force as possible makes it to the wheel.

<img width="700" alt="Custom mounts and coupler" src="https://github.com/user-attachments/assets/835408aa-e0ad-429c-b7e4-860bc8e3e62b">
<img width="700" alt="Stepper coupler to differential" src="https://github.com/user-attachments/assets/3c08f9e3-0631-4f10-9adb-55721ab2cb71">
