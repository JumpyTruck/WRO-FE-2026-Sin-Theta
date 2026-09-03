### Mechanical Design Approach

This section shows the mechanical design of our robot, including our design choices, 3D-printed structure, steering, and rear drivetrain.

[All PNG, STP and STL files are in this directory](https://github.com/JumpyTruck/WRO-FE-2026-Sin-Theta/tree/main/models/CAD%203D%20Printed%20Parts).

---

#### 1. Basic Mechanical Choices

###### **1.1 Dimensions**

The chassis was designed around the Raspberry Pi, PCB, motor, battery, and steering system. We aimed for a narrow chassis with a high length-to-width ratio, inspired by Formula 1 cars. This helps maintain stability at higher speeds while keeping the turning radius small.

<img width="300" alt="Robot Dimensions" src="https://github.com/user-attachments/assets/64442db8-6418-4848-9620-d98065398cd8" />

###### **1.2 Wheel Choice**

We chose SPIKE Prime wheels (56 mm diameter, 14 mm thick) for their balance of grip, ground clearance, and compactness. Larger wheels would require more space for steering, while smaller wheels would reduce ground clearance.

<img width="300" alt="SPIKE Prime Wheels" src="https://github.com/user-attachments/assets/c58cb594-1c2b-4eea-ad30-3101f6c1c34f" />

###### **1.3 Differential**

We chose a metal differential instead of 3D-printing our own gears or using a LEGO differential. 3D-printed gears would wear faster and could have inconsistent meshing, while a LEGO differential would take up more space and increase the center of gravity.

The metal differential provides smoother gear engagement, better durability, and a compact layout.

<img width="300" alt="Metal Differential" src="https://github.com/user-attachments/assets/f853ef5c-e624-475d-b8e8-77dcb57b81c6" />

###### **1.4 Steering System**

Our previous design used parallel steering, where both front wheels turned by the same angle. This caused tire scrubbing because the wheels follow different turning radii.

We switched to Ackermann steering so the inside and outside wheels turn at different angles. This reduces tire scrubbing and allows the robot to corner more efficiently.

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

Our final chassis uses multiple modular 3D-printed layers. The plates were designed around the placement of the electronics, motor, battery, and camera system.

###### **2.1 Base Plate**

<table>
  <tr>
    <td align="center">
      <strong>CAD</strong><br>
      <img src="https://github.com/user-attachments/assets/f41fe5ae-92ba-4795-a446-b5e35cf6c5ec" width="600">
    </td>
    <td align="center">
      <strong>Installed</strong><br>
      <img src="https://github.com/user-attachments/assets/7763083b-e341-4566-9f6d-96d56026d52a" width="600">
    </td>
  </tr>
</table>

###### **2.2 Motor Mount**

<table>
  <tr>
    <td align="center">
      <strong>CAD</strong><br>
      <img src="https://github.com/user-attachments/assets/0b3a8db0-7c20-4b12-8429-7e93e67acfcd" width="600">
    </td>
    <td align="center">
      <strong>Installed</strong><br>
      <img src="https://github.com/user-attachments/assets/36cc248f-2dff-4693-afb2-fa60fcd70212" width="600">
    </td>
  </tr>
</table>

###### **2.3 Second Layer — PCB Holder**

<table>
  <tr>
    <td align="center">
      <strong>CAD</strong><br>
      <img src="https://github.com/user-attachments/assets/b5c74f6a-45d7-4465-8d6a-10aeed772797" width="600">
    </td>
    <td align="center">
      <strong>Installed</strong><br>
      <img src="https://github.com/user-attachments/assets/116feb86-e038-4e22-8e40-c2fecf43d38d" width="600">
    </td>
  </tr>
</table>

###### **2.4 Third Layer — Raspberry Pi Holder**

<table>
  <tr>
    <td align="center">
      <strong>CAD</strong><br>
      <img src="https://github.com/user-attachments/assets/9f6199da-c54a-4941-9f24-dc59db6bdc6c" width="600">
    </td>
    <td align="center">
      <strong>Installed</strong><br>
      <img src="https://github.com/user-attachments/assets/200b7d2b-a27e-4cb8-b80d-62d3f662c3f5" width="600">
    </td>
  </tr>
</table>

###### **2.5 Camera Mount**

<table>
  <tr>
    <td align="center">
      <strong>CAD</strong><br>
      <img src="https://github.com/user-attachments/assets/52265d96-f9a8-422e-a230-17455cd757dd" width="400">
    </td>
    <td align="center">
      <strong>Installed</strong><br>
      <img src="https://github.com/user-attachments/assets/082183fe-2382-4521-a2c9-c87eeff48f15" width="500">
    </td>
  </tr>
</table>

The final camera angle was set to **155°**.

---

#### 3. Steering CAD

The steering system was designed using Ackermann geometry. The CAD models below show the main components and the complete steering design.

<table>
  <tr>
    <td align="center">
      <img src="https://github.com/user-attachments/assets/a51595f1-feec-459c-8b97-6e5466f72686" width="380">
    </td>
    <td align="center">
      <img src="https://github.com/user-attachments/assets/c73a7ff1-f0e3-4ab9-9cf1-06bbb7221dc9" width="380">
    </td>
  </tr>
  <tr>
    <td align="center">
      <img src="https://github.com/user-attachments/assets/33989ee2-ef4d-4845-90af-049db58e81f0" width="380">
    </td>
    <td align="center">
      <img src="https://github.com/user-attachments/assets/1e36fc58-8f50-45b8-b875-371926bcabe4" width="380">
    </td>
  </tr>
</table>

<p align="center">
  <img src="https://github.com/user-attachments/assets/9723fcb5-6dab-4963-b5df-81f603e60325" width="700">
</p>

---

#### 4. Rear Axle & Drive CAD

The rear drivetrain was designed around the motor, differential, and rear wheels. The CAD models show the main drivetrain components and their overall design.

<table>
  <tr>
    <td align="center">
      <img src="https://github.com/user-attachments/assets/0ef57718-d420-4412-85b1-8dee268708e4" width="380">
    </td>
    <td align="center">
      <img src="https://github.com/user-attachments/assets/59c8193e-ff14-4034-82f1-83f2f6086f7d" width="380">
    </td>
  </tr>
  <tr>
    <td align="center">
      <img src="https://github.com/user-attachments/assets/7a0faa52-7937-44b5-be4f-8524e1fc855d" width="380">
    </td>
    <td align="center">
      <img src="https://github.com/user-attachments/assets/1f7bf237-cc1a-4aed-9857-74ee0228efb3" width="380">
    </td>
  </tr>
</table>

<p align="center">
  <img src="https://github.com/user-attachments/assets/3aeff81b-75b5-4ff3-892a-9b631c7bdd1b" width="700">
</p>
---

#### 5. Complete Robot


