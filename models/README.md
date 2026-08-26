# Mobility & Mechanical Design

This section explains the design and integration of our robot's mechanical system. It covers how we selected and designed the chassis, wheels, differential, steering, and rear axle. Each component was chosen based on performance, reliability, durability, and the limited space within our chassis. The section also includes a full part-by-part build breakdown. All STL and PNG files are in [this folder](models/CAD%203D%20Printed%20Parts).

---

#### 1. Chassis & Dimensions

###### **1.1 Dimensions**

- Sized around the Pi, driver board, motor, and steering, with a **~50mm margin per side**
- Took inspiration from F1 cars — a narrow body with a bigger length-to-width ratio turns tighter and stays more stable at high speed

<img width="300" alt="IMG_1527" src="https://github.com/user-attachments/assets/64442db8-6418-4848-9620-d98065398cd8" />

---

#### 2. Wheels & Drivetrain

###### **2.1 Wheel Choice**

- We use **SPIKE Prime wheels (56mm diameter, 14mm thick)**
- Best balance of grip, clearance, and compactness — going bigger hurts turning, going smaller loses ground clearance

<img width="300" alt="Spike Wheels" src="https://github.com/user-attachments/assets/c58cb594-1c2b-4eea-ad30-3101f6c1c34f" />

---

###### **2.2 Differential**

- We use a **metal differential** over 3D-printed gears or LEGO
- 3D-printed gears wear fast and mesh poorly under repeated cornering load
- LEGO gearing is bulkier and raises the chassis's centre of gravity
- The metal differential meshes smoother, lasts longer, and sits lower in the chassis

<img width="300" alt="metal diff" src="https://github.com/user-attachments/assets/f853ef5c-e624-475d-b8e8-77dcb57b81c6" />

---

#### 3. Steering System

###### **3.1 Why Ackermann**

- Last year we used **parallel steering**, which scrubbed tires through corners since both wheels turned on the same radius
- We switched to **Ackermann steering** so each wheel turns its own correct radius through a corner

<table>
  <tr>
    <th align="center">Old</th>
    <th align="center">New</th>
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

###### **3.2 Steering Assembly**

- **Steering holder:** everything mounts here, servo inverted to line up with the knuckles
- **Steering arm:** fixed at a **~12° Ackermann angle**, with nylon spacers to cut friction
- **Steering T:** extends the servo output to the steering bar
- **Steering cross link:** links both knuckles, converting servo rotation into steering

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

#### 4. Rear Axle Assembly

###### **4.1 Components**

- **Motor adapter:** matches the motor's D-shaft to the differential's square input
- **Gear holder:** connects to the differential to hold it in place
- **Axle supports:** hold the axles in place via bearings, keeping them aligned and stopping sagging
- **Axles:** custom metal axles adapt the differential output to the LEGO wheels
- **VEX spacers:** added on the rear axles to push the wheels further outward, giving clearance so they don't rub against the chassis/body

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

---

###### **4.2 Full Assembly**

<table>
  <tr>
    <td align="center">
      <strong>Full Rear Axle Assembly — Installed</strong><br>
      <img width="700" alt="Rear Axle Assembly" src="https://github.com/user-attachments/assets/3aeff81b-75b5-4ff3-892a-9b631c7bdd1b" />
    </td>
  </tr>
</table>

---

#### 5. Chassis Build — Plates

###### **5.1 Base Plate**

- **Steering holder:** trapezoid front section, 4 holes, servo cutout
- **Battery holder:** front-mounted, low, counterbalances the rear motor
- **Motor mount:** mid-rear, upper/lower halves clamp the motor
- **Rear axle points:** cutouts and mounts for the axle supports

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
      <img src="https://github.com/user-attachments/assets/7763083b-e341-4566-9f6d-96d56026d52a" width="700">
    </td>
  </tr>
</table>

---

###### **5.2 Motor Mount — Top Half**

- Clamps over the motor and bolts into the lower half

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

###### **5.3 Second Story — PCB Holder**

- Holds our custom PCB
- Main rectangle seats the PCB; a second smaller cutout houses the servo regulator (also fits our old PCB as a backup)

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
      <img src="https://github.com/user-attachments/assets/116feb86-e038-4e22-8e40-c2fecf43d38d" width="700">
    </td>
  </tr>
</table>

---

###### **5.4 Third Story — Pi Holder**

- Holds the Raspberry Pi
- Partial wraparound wall with open sides for cables
- Includes the camera stand, which raises the camera for a clear view of the mat

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
      <img src="https://github.com/user-attachments/assets/200b7d2b-a27e-4cb8-b80d-62d3f662c3f5" width="700">
    </td>
  </tr>
</table>

---

###### **5.5 Camera Mount**

- Sits atop the stand and holds the camera
- Standalone piece, so the angle adjusts without touching the stand or top plate
- Set to **155°**

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

#### 6. Final Mechanical Integration

All components are integrated into the final chassis as a compact, three-story modular platform. The base plate carries the drivetrain, steering, and battery; the second story carries the custom PCB; the third story carries the Raspberry Pi and camera assembly.

Each layer pulls off independently without disturbing the others, keeping repair and iteration fast throughout the season.
