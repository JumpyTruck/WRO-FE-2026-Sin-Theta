# Mobility & Mechanical Design

This page covers the mechanical design of our robot — the reasoning behind our design choices, and a part-by-part breakdown of the chassis, steering, and rear axle, along with how to assemble it.

All STL and PNG files are in [this folder](https://github.com/JumpyTruck/WRO-FE-2026-Sin-Theta/tree/main/models/CAD%203D%20Printed%20Parts).

---

## 1. Basic Design Choices

### 1.1 Dimensions

Sized around the Pi, driver board, motor, and steering, with a ~50 mm margin per side. Took inspiration from F1 cars — narrow, bigger length-to-width ratio turns tighter and stays more stable at high speed.

<img width="300" alt="IMG_1527" src="https://github.com/user-attachments/assets/64442db8-6418-4848-9620-d98065398cd8" />

---

### 1.2 Wheel Choice

SPIKE Prime wheels (56 mm diameter, 14 mm thick). Best balance of grip, clearance, and compactness — bigger hurts turning, smaller loses clearance.

<img width="300" alt="Spike Wheels" src="https://github.com/user-attachments/assets/c58cb594-1c2b-4eea-ad30-3101f6c1c34f" />

---

### 1.3 Differential

Went with metal over 3D-printed gears (wear fast, mesh poorly) or LEGO (bulkier, higher CG). Metal meshes smoother, lasts longer, and sits lower.

<img width="300" alt="metal diff" src="https://github.com/user-attachments/assets/f853ef5c-e624-475d-b8e8-77dcb57b81c6" />

---

### 1.4 Steering — Ackermann

Last year we used parallel steering, which scrubbed tires through corners since both wheels turned on the same radius. Switched to Ackermann so each wheel turns its own correct radius.

<table>
  <tr>
    <th align="center">Old</th>
    <th align="center">New</th>
  </tr>
  <tr>
    <td align="center">
      <img src="https://github.com/user-attachments/assets/40b0c8e9-155e-43ce-810e-4c20fbef25d0" width="100%" />
    </td>
    <td align="center">
      <img src="https://github.com/user-attachments/assets/5103d06f-3cf0-4587-87ff-aeea7164ea68" width="100%" />
    </td>
  </tr>
</table>

---

## 2. The Assembly

### 2.1 Chassis

Three stacked, modular plates — any layer pulls off without touching the others.

#### Base Plate

- Steering holder: trapezoid front section, 4 holes, servo cutout.
- Battery holder: front-mounted, low, counterbalances rear motor.
- Motor mount: mid-rear, upper/lower halves clamp the motor.
- Rear axle points: cutouts + mounts for axle supports.

<table>
  <tr>
    <td align="center">
      <strong>Base Plate — CAD</strong><br>
      <img width="700" alt="Main_Chassis__Base_Plate__flipped" src="https://github.com/user-attachments/assets/f41fe5ae-92ba-4795-a446-b5e35cf6c5ec" />
    </td>
  </tr>
  <tr>
    <td align="center">
      <strong>Base Plate — Installed</strong><br>
      <img width="700" alt="Base Plate Installed" src="https://github.com/user-attachments/assets/7763083b-e341-4566-9f6d-96d56026d52a" />
    </td>
  </tr>
</table>

#### Motor Mount — Top Half

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
      <img width="700" alt="IMG_2587" src="https://github.com/user-attachments/assets/36cc248f-2dff-4693-afb2-fa60fcd70212" />
    </td>
  </tr>
</table>

---

#### Second Story — PCB Holder

Holds our custom PCB. Main rectangle seats the PCB, second smaller one houses the servo regulator (also fits our old PCB as backup).

<table>
  <tr>
    <td align="center">
      <strong>Second Story — CAD</strong><br>
      <img width="700" alt="Second_Plate_flipped" src="https://github.com/user-attachments/assets/b5c74f6a-45d7-4465-8d6a-10aeed772797" />
    </td>
  </tr>
  <tr>
    <td align="center">
      <strong>Second Story — Installed</strong><br>
      <img width="700" alt="Second Story Installed" src="https://github.com/user-attachments/assets/116feb86-e038-4e22-8e40-c2fecf43d38d" />
    </td>
  </tr>
</table>

---

#### Third Story — Pi Holder

Holds the Pi. Partial wraparound wall, open sides for cables, includes the Camera Stand which raises the camera for a clear view of the mat.

<table>
  <tr>
    <td align="center">
      <strong>Third Story — CAD</strong><br>
      <img width="700" alt="Third_Plate_flipped" src="https://github.com/user-attachments/assets/9f6199da-c54a-4941-9f24-dc59db6bdc6c" />
    </td>
  </tr>
  <tr>
    <td align="center">
      <strong>Third Story — Installed</strong><br>
      <img width="700" alt="Third Story Installed" src="https://github.com/user-attachments/assets/200b7d2b-a27e-4cb8-b80d-62d3f662c3f5" />
    </td>
  </tr>
</table>

---

#### Camera Mount

Sits atop the stand and holds the camera. Standalone piece so angle adjusts without touching the stand or top plate. Set to 155°.

<table>
  <tr>
    <td align="center">
      <strong>Camera Mount — CAD</strong><br>
      <img width="300" alt="Camera Mount" src="https://github.com/user-attachments/assets/52265d96-f9a8-422e-a230-17455cd757dd" />
    </td>
  </tr>
</table>

<table>
  <tr>
    <td align="center">
      <strong>Full Camera Assembly — Installed</strong><br>
      <img width="500" alt="camerainstalled" src="https://github.com/user-attachments/assets/082183fe-2382-4521-a2c9-c87eeff48f15" />
    </td>
  </tr>
</table>

---

### 2.2 Steering Assembly

- **Steering holder:** everything mounts here, servo inverted to line up with knuckles.
- **Steering Arm:** fixed at ~12° Ackermann angle, nylon spacers cut friction.
- **Steering T:** extends servo output to the steering bar.
- **Steering Cross Link:** links both knuckles, converts servo rotation into steering.

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
      <strong>Full Steering Assembly — Installed</strong><br>
      <img width="700" alt="IMG_2589" src="https://github.com/user-attachments/assets/9723fcb5-6dab-4963-b5df-81f603e60325" />
    </td>
  </tr>
</table>

---

### 2.3 Rear Axle Assembly

- **Motor adapter:** matches motor's D-shaft to the differential's square input. (Print in PETG for toughness and ductility)
- **Gear holder:** connects to the differential to hold it in place.
- **Axle supports:** hold the axles in place via bearings, keep them aligned and stop sagging.
- **Axles:** custom metal axles adapt diff output to LEGO wheels.
- **VEX spacers:** added on the rear axles to push the wheels further outward, giving clearance so they don't rub against the chassis/body.

<table>
  <tr>
    <td align="center">
      <strong>Motor Adapter</strong><br>
      <img width="380" alt="Motor Adapter" src="https://github.com/user-attachments/assets/0ef57718-d420-4412-85b1-8dee268708e4" />
    </td>
    <td align="center">
      <strong>Gear Holder</strong><br>
      <img width="380" alt="Gear Holder" src="https://github.com/user-attachments/assets/59c8193e-ff14-4034-82f1-83f2f6086f7d" />
    </td>
  </tr>
  <tr>
    <td align="center">
      <strong>Axles</strong><br>
      <img width="380" alt="Rear Axle" src="https://github.com/user-attachments/assets/7a0faa52-7937-44b5-be4f-8524e1fc855d" />
    </td>
    <td align="center">
      <strong>Axle Support</strong><br>
      <img width="380" alt="Axle Support" src="https://github.com/user-attachments/assets/1f7bf237-cc1a-4aed-9857-74ee0228efb3" />
    </td>
  </tr>
</table>

<table>
  <tr>
    <td align="center">
      <strong>Full Rear Axle Assembly — Installed</strong><br>
      <img width="700" alt="Rear Axle Assembly" src="https://github.com/user-attachments/assets/3aeff81b-75b5-4ff3-892a-9b631c7bdd1b" />
    </td>
  </tr>
</table>

### 2.4 Bumper
Our robot features a protruding bumper from the nose of the robot, serving a multitude of purposes:
  1) Prevents the robot from becoming stuck on any wall or obstacle.
  2) The thick tape securing the bumper acts as a shock absorber to reduce stress on the chassis and rest of the robot during crashes.
  3) And of course, a F1 inspired car must have a front bumper so we had to add it, sporting our team name “Sin Theta”, letting everyone know which team is running for.
