# WRO-FE-2026-Untitled

## The Robot

<table align="center">
  <tr>
    <td align="center">
      <b>Top View</b><br><br>
      <img width="220" alt="IMG_2360" src="https://github.com/user-attachments/assets/488c0949-fab7-4cdb-90b6-f47f4dfcaa29" />
    </td>
    <td align="center">
      <b>Right View</b><br><br>
      <img width="220" alt="IMG_2358" src="https://github.com/user-attachments/assets/101af993-0053-4d73-8710-59cf7fc3d8bc" />
    </td>
    <td align="center">
      <b>Front View</b><br><br>
      <img width="220"alt="IMG_2357" src="https://github.com/user-attachments/assets/9ec74514-c036-4e2a-9e0f-bb02dfa7063b" />
    </td>
  </tr>

  <tr>
    <td align="center">
      <b>Bottom View</b><br><br>
      <img width="220" alt="IMG_2361" src="https://github.com/user-attachments/assets/d67f76cc-255e-481e-a65d-cab145b7653c" />
    </td>
    <td align="center">
      <b>Left View</b><br><br>
      <img width="220" alt="IMG_2356" src="https://github.com/user-attachments/assets/09d1da9c-4b3d-48e9-953b-bf2d5d2d3519" />
    </td>
    <td align="center">
      <b>Rear View</b><br><br>
      <img width="220" alt="IMG_2359" src="https://github.com/user-attachments/assets/1868c46f-d27c-46af-9c2c-331342825c3c" />
    </td>
  </tr>
</table>

# Mobility Management

The mobility system was designed to maximize steering precision, stability, and reliability while remaining compact enough to navigate the WRO Future Engineers field. Every mechanical component was selected after multiple iterations and testing to improve turning performance, simplify maintenance, and increase consistency during competition.

---

## Robot Dimensions

The final robot measures:

| Specification | Value |
|--------------|------:|
| Length | XXX mm |
| Width | XXX mm |
| Height | XXX mm |
| Weight | XXX g |

These dimensions were selected to provide a compact footprint while maintaining enough internal space for all electronic components and ensuring stable handling during high-speed cornering.

📄 **More about our design decisions:**  
[Robot Dimensions](mobility/README.md#robot-dimensions)

---

## Drive System

| Component | Selected Part |
|-----------|---------------|
| Drive Motor | 12V DC Geared Motor |
| Motor Driver | DRV8871 |

Our drivetrain uses a rear-wheel-drive configuration powered by a 12V DC geared motor. After evaluating multiple options, this combination provided the best balance of speed, torque, simplicity, and reliability for the competition.

📄 **Motor selection, calculations, and testing:**  
[Drive Motor & Driver](mobility/README.md#drive-system)

---

## Steering System

| Component | Selected Part |
|-----------|---------------|
| Steering Type | Ackermann Steering |
| Servo | MG90S Metal Gear Servo |

To improve cornering accuracy and reduce tire scrub, the robot uses Ackermann steering geometry. The steering mechanism was redesigned through multiple iterations before reaching the final geometry shown below.

<div align="center">

**Steering Animation**

*Insert GIF here*

</div>

<div align="center">

**Ackermann Geometry**

*Insert steering calculation / diagram here*

</div>

📄 **Complete steering development and calculations:**  
[Steering System](mobility/README.md#steering-system)

---

## Chassis Design

The chassis consists of three modular 3D-printed layers that simplify assembly and maintenance while providing rigid mounting locations for every component.

<div align="center">

### Bottom Plate

*Image*

### Middle Plate

*Image*

### Top Plate

*Image*

</div>

The modular construction allows individual sections to be removed without completely disassembling the robot, making repairs and modifications significantly easier during development.

📄 **Complete chassis design:**  
[Chassis Design](mobility/README.md#chassis)

---

## Wheels & Differential

The robot uses LEGO SPIKE Prime wheels for their compact size, consistent grip, and lightweight construction. Power is transferred through a rear differential, allowing both drive wheels to rotate at different speeds while cornering, improving stability and reducing mechanical stress.

📄 **Wheel selection:**  
[Wheel Choice](mobility/README.md#wheels)

📄 **Differential design:**  
[Differential](mobility/README.md#differential)

---

## Development Process

The final mobility system is the result of numerous design iterations involving the chassis, steering mechanism, and component placement. Each revision focused on improving steering precision, reducing weight, increasing rigidity, and simplifying assembly.

*Insert timeline or iteration image here.*

📄 **Complete development history:**  
[Mechanical Development](mobility/README.md#development)
