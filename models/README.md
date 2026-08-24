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
      <img width="700" alt="Main Chassis (Base Plate)" src="https://github.com/user-attachments/assets/38c17ae5-48fb-4a5f-99c4-94e593c554bb" />
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
      <img width="700" alt="Top Motor Holder" src="https://github.com/user-attachments/assets/0b3a8db0-7c20-4b12-8429-7e93e67acfcd" />
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
      <img width="700" alt="Second Plate" src="https://github.com/user-attachments/assets/5adabe70-5d12-4f0e-9ed6-e42ea3047273" />
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
      <img width="700" alt="Third Plate" src="https://github.com/user-attachments/assets/e4239b84-6903-4bcc-9b0e-34eacd87c8df" />
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
Standalone piece so angle adjusts without touching the top plate. Set to 155°.

<table>
  <tr>
    <td align="center">
      <strong>Camera Mount — CAD</strong><br>
      <img width="700" alt="Third Plate" src="https://github.com/user-attachments/assets/b8cfc0db-c4f3-4c5e-a724-af3557645aaf" />
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
- Steering Arm: fixed at ~12° Ackermann angle, nylon spacers cut friction.
- Steering T: extends servo output to the steering bar.
- Steering Cross Link: links both knuckles, converts servo rotation into steering.

<table>
  <tr>
    <td align="center">
      <strong>Servo Holder</strong><br>
      <img width="380" alt="Servo Holder" src="https://github.com/user-attachments/assets/a51595f1-feec-459c-8b97-6e5466f72686" />
    </td>
    <td align="center">
      <strong>Steering Arm</strong><br>
      <img width="380" alt="Ackermann Steering Arm" src="https://github.com/user-attachments/assets/c73a7ff1-f0e3-4ab9-9cf1-06bbb7221dc9" />
    </td>
  </tr>
  <tr>
    <td align="center">
      <strong>Steering T</strong><br>
      <img width="380" alt="Steering T" src="https://github.com/user-attachments/assets/33989ee2-ef4d-4845-90af-049db58e81f0" />
    </td>
    <td align="center">
      <strong>Steering Cross Link</strong><br>
      <img width="380" alt="Steering Cross Link" src="https://github.com/user-attachments/assets/1e36fc58-8f50-45b8-b875-371926bcabe4" />
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
