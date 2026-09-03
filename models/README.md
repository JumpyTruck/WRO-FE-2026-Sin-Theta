
### Mechanical Design Approach

[All PNG, STP and STL files are in this directory](./CAD_3D_Printed_Parts/)

#### 1. Basic Mechanical Choices

###### **1.1 Dimensions**

The chassis was designed around the Raspberry Pi, PCB, motor, battery, and steering system. We chose a relatively narrow design with a high length-to-width ratio, inspired by Formula 1 cars. This keeps the robot stable while allowing it to turn in a small space.

<img width="300" alt="Robot Dimensions" src="https://github.com/user-attachments/assets/64442db8-6418-4848-9620-d98065398cd8" />

###### **1.2 Wheel Choice**

We chose SPIKE Prime wheels (56mm diameter, 14mm thickness) because they provide a good balance of grip, ground clearance, and compactness. Larger wheels would require more space, while smaller wheels would reduce ground clearance.

<img width="300" alt="SPIKE Prime Wheels" src="https://github.com/user-attachments/assets/c58cb594-1c2b-4eea-ad30-3101f6c1c34f" />

###### **1.3 Differential**

We chose a metal differential instead of 3D-printing our own gears or using a LEGO differential. 3D-printed gears could wear faster and have inconsistent meshing, while a LEGO differential would take up more space and raise the center of gravity.

The metal differential provides smoother gear engagement, better durability, and a compact design.

<img width="300" alt="Metal Differential" src="https://github.com/user-attachments/assets/f853ef5c-e624-475d-b8e8-77dcb57b81c6" />

###### **1.4 Steering — Ackermann**

Our previous steering design used parallel steering, where both front wheels turned by the same angle. This caused tire scrubbing because the inside and outside wheels travel along different turning radii.

We switched to Ackermann steering so the inside and outside wheels turn at different angles. This reduces tire scrubbing and improves cornering.

<table>
  <tr>
    <th align="center">Previous — Parallel Steering</th>
    <th align="center">Final — Ackermann Steering</th>
  </tr>
  <tr>
    <td>
      <img src="https://github.com/user-attachments/assets/40b0c8e9-155e-43ce-810e-4c20fbef25d0" width="100%" />
    </td>
    <td>
      <img src="https://github.com/user-attachments/assets/5103d06f-3cf0-4587-87ff-aeea7164ea68" width="100%" />
    </td>
  </tr>
</table>

---

#### 2. Final 3D-Printed Structure

The final chassis is divided into three layers to organize the mechanical and electrical components while keeping the robot compact.

- **Base Plate:** Supports the steering system, battery, motor, and rear axle.
- **Second Layer:** Supports the custom PCB and servo regulator.
- **Third Layer:** Supports the Raspberry Pi and camera system.

<table>
  <tr>
    <td align="center">
      <strong>Base Plate CAD</strong><br>
      <img src="https://github.com/user-attachments/assets/f41fe5ae-92ba-4795-a446-b5e35cf6c5ec" width="700">
    </td>
    <td align="center">
      <strong>Second Layer CAD</strong><br>
      <img src="https://github.com/user-attachments/assets/b5c74f6a-45d7-4465-8d6a-10aeed772797" width="700">
    </td>
  </tr>
  <tr>
    <td align="center">
      <strong>Third Layer CAD</strong><br>
      <img src="https://github.com/user-attachments/assets/9f6199da-c54a-4941-9f24-dc59db6bdc6c" width="700">
    </td>
    <td align="center">
      <strong>Camera Mount CAD</strong><br>
      <img src="https://github.com/user-attachments/assets/52265d96-f9a8-422e-a230-17455cd757dd" width="500">
    </td>
  </tr>
</table>

---

#### 3. Mechanical CAD

The main mechanical components were designed specifically around the chassis dimensions and required movement.

- **Steering:** Custom 3D-printed Ackermann steering system designed around the front chassis.
- **Motor Mount:** Secures the drive motor while keeping it aligned with the drivetrain.
- **Rear Axle:** Supports the differential and keeps the rear wheels aligned.
- **Camera Mount:** Positions the camera at the required height and angle.
- **Component Mounts:** Custom holders keep the mechanical and electrical components securely positioned.

<table>
  <tr>
    <td align="center">
      <strong>Steering CAD</strong><br>
      <img src="https://github.com/user-attachments/assets/9723fcb5-6dab-4963-b5df-81f603e60325" width="700">
    </td>
  </tr>
  <tr>
    <td align="center">
      <strong>Motor Mount CAD</strong><br>
      <img src="https://github.com/user-attachments/assets/0b3a8db0-7c20-4b12-8429-7e93e67acfcd" width="700">
    </td>
  </tr>
  <tr>
    <td align="center">
      <strong>Rear Axle CAD</strong><br>
      <img src="https://github.com/user-attachments/assets/3aeff81b-75b5-4ff3-892a-9b631c7bdd1b" width="700">
    </td>
  </tr>
</table>

---

#### 4. Complete Robot CAD

The final CAD combines the chassis layers, steering system, rear drivetrain, camera mount, and component holders into one compact design.

<table>
  <tr>
    <td align="center">
      <strong>Left View</strong><br>
      <img src="https://github.com/user-attachments/assets/81fb3c33-7f9e-419c-99c4-76afcae5621d" width="700">
    </td>
  </tr>
  <tr>
    <td align="center">
      <strong>Top View</strong><br>
      <img src="https://github.com/user-attachments/assets/0c307909-5943-4f71-b58f-66a1c21ec9f9" width="700">
    </td>
  </tr>
  <tr>
    <td align="center">
      <strong>Bottom View</strong><br>
      <img src="https://github.com/user-attachments/assets/2bacd053-ec0a-4207-bb49-d4b5b8f2829f" width="700">
    </td>
  </tr>
</table>
