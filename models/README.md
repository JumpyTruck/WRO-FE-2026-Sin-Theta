### Mechanical Design — Full Details

The main README covers what our mobility system is; this page covers how we got there and the part-by-part breakdown of what makes up the chassis, steering, and rear axle. All STEP, STL, and PNG files are in [this folder](./CAD_3D_Printed_Pieces/).

---

## 1. Basic Design Choices

- **Dimensions**
  - Sized the chassis around fitting the Pi, driver board, motor, and steering geometry with a ~50mm margin on each side.
  - A longer, narrower chassis gives a smaller turning radius than a wide one — important for maneuvering around pillars on the mat.

- **Wheel Choice**
  - **SPIKE Prime wheels (56mm diameter, 14mm thick)**
  - Larger wheels hurt maneuverability and take up space needed for electronics; smaller wheels reduce ground clearance and complicate the axle design.
  - 56mm gave us the best grip-to-size ratio without extra bulk or weight.

  *(insert image of SPIKE Prime wheel)*

- **Differential — Why Metal**
  - Considered: 3D-printed gears, LEGO-based differential, metal differential.
  - Printed gears wear down fast and mesh less precisely → inconsistent cornering.
  - LEGO differential works, but sits bulkier and raises the center of gravity.
  - **Chose metal** — smoother mesh, more durable, and more compact, keeping our center of gravity lower.

  *(insert image of rear differential)*

- **Steering — Why Ackermann**
  - Last year's robot used **parallel steering** (both front wheels turning on the same fixed radius).
  - This caused tire scrub through corners since the inside and outside wheel actually travel different arcs.
  - This year we moved to **Ackermann steering**, where each wheel turns at its own angle, inside wheel sharper than outside.
  - Proved the geometry with a LEGO Ackermann prototype before designing the 3D-printed version.

  *(insert image: parallel steering vs Ackermann prototype)*

- **Ackermann Angle Calculation**
  - Wheelbase: 7.18" | Front track width: 3.00"
  - Required knuckle angle for 100% Ackermann geometry: **~12°**
  - 100% Ackermann means the lines projected from each knuckle pivot meet exactly at the center of the rear axle, so each wheel always turns on its correct radius.

  *(insert calculation sketch / derivation image)*

---

## 2. The Build — Chassis, Steering, and Rear Axle

### 2.1 Structural Prototype

- Built a LEGO structural prototype (15-hole beams, L-beams, frames) to test how steering and the differential would connect before printing anything.
- Confirmed motor placement (centered, axle feeding into the differential) and that the front needed to stay thin for steering clearance.

*(insert image of LEGO structural prototype)*

---

### 2.2 Chassis

Three stacked, modular 3D-printed plates — any single layer can be pulled and reprinted without touching the others.

**Base Plate**
- **Steering holder:** raised trapezoid section at the front, 4 mounting holes, center cutout for the servo.
- **Battery holder:** front-mounted, low to the ground, to counterbalance the rear motor and lower the center of gravity. Front corners trimmed to clear the spinning front tires.
- **Motor mount:** mid-to-rear placement (mid-engine layout), split into upper/lower halves that clamp around the motor with 4 screws.
- **Rear axle mounting points:** cutouts for the differential to spin freely, plus attachment points for the axle supports.
- **Shape:** trapezoid → small rectangle → large rectangle, giving the front wheels room to steer. Oversized holes carry VEX standoffs for the second-story plate.

**Second Story — PCB Holder**
- Holds our custom PCB (interprets Pi commands, drives motor + servo).
- Two connected rectangles: main one seats the PCB with USB cutouts, second smaller one houses the servo voltage regulator (also fits our original PCB as a backup).
- Flared edges carry standoffs for the third-story plate.

**Third Story — Raspberry Pi Holder**
- Simple rectangle, mounting points on the edges, partial wraparound wall for the Pi (two sides open for cable access).
- Forward-mounting posts raise the camera mount up high for a clear view of the mat.

**Camera Mount**
- Standalone, modular piece so the angle can be adjusted without touching the top plate.
- Currently set to 135°, 4 mounting holes.

<div align="center">

<img width="1245" alt="First plate" src="https://github.com/user-attachments/assets/7763083b-e341-4566-9f6d-96d56026d52a" />
<img width="1248" alt="Second plate" src="https://github.com/user-attachments/assets/116feb86-e038-4e22-8e40-c2fecf43d38d" />
<img width="1333" alt="Third plate" src="https://github.com/user-attachments/assets/200b7d2b-a27e-4cb8-b80d-62d3f662c3f5" />

</div>

*(insert CAD renders of each plate next to these installed photos, so each part can be seen both designed and built)*

---

### 2.3 Steering Assembly

- **Steering holder:** everything mounts here. Servo sits inverted so its output lines up with the knuckles. Six support arms for rigidity + max contact area with the chassis.
- **Steering knuckle:** where the wheel attaches and turns. Fixed at the ~12° Ackermann angle, arms kept as long as possible to maximize steering range. 1/8" nylon spacers reduce friction against the wheel.
- **Steering T:** slips over the servo output, extends reach, links servo horn to the steering bar.
- **Steering bar:** connects both knuckles, converts servo rotation into synced left/right steering.

*(insert image of assembled steering system)*
[Steering CAD Files](./CAD_3D_Printed_Pieces/)

---

### 2.4 Rear Axle Assembly

- **Motor adapter:** converts the motor's D-shaft output to the differential's square input, hugging both shapes tightly for max mesh.
- **Input gear holder:** keeps the differential's input gear aligned, prevents slipping.
- **Differential holder:** seats the differential on its ball bearing to minimize rolling friction.
- **Axle supports:** same design as the differential holder, different bearing size — holds the custom metal axles to prevent sagging.
- **Axles:** custom metal axles convert the differential output into the LEGO axle profile for the SPIKE Prime wheels, secured with LEGO rubber connectors and a peg.

*(insert image of rear axle assembly, motor adapter, and axle supports)*
