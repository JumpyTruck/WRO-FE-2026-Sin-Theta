### Mechanical Design — Full Details

The main README covers what our mobility system is; this page covers how we got there and the part-by-part breakdown of the chassis, steering, and rear axle. All STEP, STL, and PNG files are in [this folder](./CAD_3D_Printed_Pieces/).

---

## 1. Basic Design Choices

- **Dimensions:** Sized around the Pi, driver board, motor, and steering, with a ~50mm margin per side. Took inspiration from F1 cars — narrow, low chassis turns tighter and stays more stable at speed.

  *(insert initial sketches here)*

- **Wheel Choice:** SPIKE Prime wheels (56mm diameter, 14mm thick). Best balance of grip, clearance, and compactness — bigger hurts turning, smaller loses clearance.

  *(insert wheel image)*

- **Differential:** Went with metal over 3D-printed gears (wear fast, mesh poorly) or LEGO (bulkier, higher CG). Metal meshes smoother, lasts longer, and sits lower.

  *(insert differential image)*

- **Steering — Why Ackermann:** Last year we used parallel steering, which scrubbed tires through corners since both wheels turned on the same radius. Switched to Ackermann so each wheel turns its own correct radius.

  *(insert parallel vs Ackermann image)*

- **Ackermann Angle:** Wheelbase 7.18", track width 3.00" → ~12° knuckle angle for 100% Ackermann (knuckle lines meet at the center of the rear axle).

  *(insert calculation sketch)*

---

## 2. The Build

### 2.1 Structural Prototype
We started from scratch, using a LEGO chassis mockup to get a feel for dimensions before committing to a final design. This let us test motor placement, steering clearance, and differential fit cheaply before locking in the printed chassis shape.

*(insert prototype image)*

---

### 2.2 Chassis
Three stacked, modular plates — any layer pulls off without touching the others.

**Base Plate**
- Steering holder: trapezoid front section, 4 holes, servo cutout.
- Battery holder: front-mounted, low, counterbalances rear motor.
- Motor mount: mid-rear, upper/lower halves clamp the motor.
- Rear axle points: cutouts + mounts for axle supports.

<table>
  <tr>
    <td align="center">
      <strong>Base Plate — CAD</strong><br>
      <img src="CAD_3D_Printed_Pieces/Main_Chassis__Base_Plate_.png" width="700">
    </td>
  </tr>
  <tr>
    <td align="center">
      <strong>Base Plate — Installed</strong><br>
      <img src="https://github.com/user-attachments/assets/7763083b-e341-4566-9f6d-96d56026d52a" width="700">
    </td>
  </tr>
</table>

**Motor Mount — Top Half**
Clamps over the motor, bolts into the lower half.

<table>
  <tr>
    <td align="center">
      <strong>Motor Mount Top — CAD</strong><br>
      <img src="CAD_3D_Printed_Pieces/Top_Motor_Holder.png" width="700">
    </td>
  </tr>
  <tr>
    <td align="center">
      <strong>Motor Mount Top — Installed</strong><br>
      <img src="INSERT_INSTALLED_IMAGE_URL" width="700">
    </td>
  </tr>
</table>

---

**Second Story — PCB Holder**
Holds our custom PCB. Main rectangle seats the PCB, second smaller one houses the servo regulator (also fits our old PCB as backup).

<table>
  <tr>
    <td align="center">
      <strong>Second Story — CAD</strong><br>
      <img src="CAD_3D_Printed_Pieces/Second_Plate.png" width="700">
    </td>
  </tr>
  <tr>
    <td align="center">
      <strong>Second Story — Installed</strong><br>
      <img src="https://github.com/user-attachments/assets/116feb86-e038-4e22-8e40-c2fecf43d38d" width="700">
    </td>
  </tr>
</table>

---

**Third Story — Pi Holder**
Holds the Pi and camera mount. Partial wraparound wall, open sides for cables.

<table>
  <tr>
    <td align="center">
      <strong>Third Story — CAD</strong><br>
      <img src="CAD_3D_Printed_Pieces/Third_Plate.png" width="700">
    </td>
  </tr>
  <tr>
    <td align="center">
      <strong>Third Story — Installed</strong><br>
      <img src="https://github.com/user-attachments/assets/200b7d2b-a27e-4cb8-b80d-62d3f662c3f5" width="700">
    </td>
  </tr>
</table>

---

**Camera Mount**
Standalone piece so angle adjusts without touching the top plate. Set to 135°.

<table>
  <tr>
    <td align="center">
      <strong>Camera Mount — CAD</strong><br>
      <img src="INSERT_CAD_IMAGE_URL" width="700">
    </td>
  </tr>
  <tr>
    <td align="center">
      <strong>Camera Mount — Installed</strong><br>
      <img src="INSERT_INSTALLED_IMAGE_URL" width="700">
    </td>
  </tr>
</table>

---

### 2.3 Steering Assembly
- Steering holder: everything mounts here, servo inverted to line up with knuckles.
- Steering knuckle: fixed at ~12° Ackermann angle, nylon spacers cut friction.
- Steering T: extends servo output to the steering bar.
- Steering bar: links both knuckles, converts servo rotation into steering.

<table>
  <tr>
    <td align="center">
      <strong>Steering Holder</strong><br>
      <img src="CAD_3D_Printed_Pieces/Servo_Holder.png" width="380">
    </td>
    <td align="center">
      <strong>Steering Knuckle</strong><br>
      <img src="CAD_3D_Printed_Pieces/Ackermann_Steering_Arm.png" width="380">
    </td>
  </tr>
  <tr>
    <td align="center">
      <strong>Steering T</strong><br>
      <img src="CAD_3D_Printed_Pieces/Steering_T.png" width="380">
    </td>
    <td align="center">
      <strong>Steering Bar</strong><br>
      <img src="CAD_3D_Printed_Pieces/Steering_Cross_Link.png" width="380">
    </td>
  </tr>
</table>

<table>
  <tr>
    <td align="center">
      <strong>Full Steering Assembly — CAD</strong><br>
      <img src="INSERT_CAD_IMAGE_URL" width="700">
    </td>
  </tr>
  <tr>
    <td align="center">
      <strong>Full Steering Assembly — Installed</strong><br>
      <img src="INSERT_INSTALLED_IMAGE_URL" width="700">
    </td>
  </tr>
</table>

[Steering CAD Files](./CAD_3D_Printed_Pieces/)

---

### 2.4 Rear Axle Assembly
- Motor adapter: matches motor's D-shaft to the differential's square input.
- Input gear holder: keeps input gear aligned, no slipping.
- Differential holder: seats diff on its bearing, low friction.
- Axle supports: same idea, different bearing, stops sagging.
- Axles: custom metal axles adapt diff output to LEGO wheels.

<table>
  <tr>
    <td align="center">
      <strong>Motor Adapter</strong><br>
      <img src="INSERT_CAD_IMAGE_URL" width="380">
    </td>
    <td align="center">
      <strong>Input Gear Holder</strong><br>
      <img src="INSERT_CAD_IMAGE_URL" width="380">
    </td>
  </tr>
  <tr>
    <td align="center">
      <strong>Differential Holder</strong><br>
      <img src="INSERT_CAD_IMAGE_URL" width="380">
    </td>
    <td align="center">
      <strong>Axle Supports</strong><br>
      <img src="INSERT_CAD_IMAGE_URL" width="380">
    </td>
  </tr>
</table>

<table>
  <tr>
    <td align="center">
      <strong>Full Rear Axle Assembly — CAD</strong><br>
      <img src="INSERT_CAD_IMAGE_URL" width="700">
    </td>
  </tr>
  <tr>
    <td align="center">
      <strong>Full Rear Axle Assembly — Installed</strong><br>
      <img src="INSERT_INSTALLED_IMAGE_URL" width="700">
    </td>
  </tr>
</table>
