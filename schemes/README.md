### Electrical Design Process

#### 1\. Motorization & Power System

###### **1.1 DC Motor Selection**
We use a **12V 37D metal gearmotor with an 11PPR encoder**, running at **510 RPM**. We required 300–500 RPM at the motor, which — with our 56 mm diameter wheels (≈175.93 mm circumference) — gives a theoretical wheel speed of roughly 0.88–1.47 m/s: fast enough for the course without making acceleration, braking, and precise positioning difficult. We also required a minimum torque of ≥1.5–2.0 kg·cm to overcome the robot's weight, rolling resistance, and drivetrain friction while leaving margin for acceleration, without running the motor near its stall torque (which causes excess current draw and heat). The built-in encoder lets the controller measure actual wheel rotation in ticks rather than relying on time-based movement, which drifts with battery voltage, friction, load, and surface conditions. Its metal gearbox reduces the motor's raw speed into usable torque, and its compact 37D form factor and 56 mm × 14 mm wheel compatibility fit our chassis (max 300 × 200 × 300 mm) alongside the battery, PCB, sensors, and steering system.

At 12.8 V, the motor draws **0.40 A normal / 1.00 A peak (5.12 W)**.

<img width="215" alt="motorimg" src="IMAGE">

---

###### **1.2 Motor Driver: Adafruit DRV8871**
The **Adafruit DRV8871** drives the DC motor with the current the Arduino Nano can't supply directly. It operates on 6.5–45 V, so it runs directly off our 12.8 V battery, and its 3.6 A continuous / 6 A peak current rating comfortably exceeds our battery's ~2 A max output, so the driver is never the bottleneck. It gives PWM-based speed control, forward/reverse direction control, and built-in overcurrent, thermal shutdown, undervoltage, and short-circuit protection. Its MOSFET switching design also produces a much smaller voltage drop and far less heat than a bipolar H-bridge driver (e.g. the L298N's ~2 V drop), so the motor receives nearly the full battery voltage — all in a small enough package for our limited space.

At 12.8 V, the driver itself draws **<0.05 A normal / <0.1 A peak (0.64 W)**.

<img width="200" alt="motordruiv" src="IMAGE">

---

###### **1.3 Steering Servo: 8.4V High-Torque Coreless Servo**
Our original 5 V steering servo did not produce enough torque to reliably turn the steering mechanism under load; repeated stalling stressed and eventually damaged its internal components. We replaced it with an **8.4 V high-torque coreless servo**, which offers precise angle control, fast response, and enough torque to steer without stalling, in a compact size that fits our chassis without issue.

At 8.4 V, the servo draws **0.50 A normal / 3.0–5.0 A peak (4.2–25.2 W)**.

<img width="215" alt="newservo" src="https://github.com/user-attachments/assets/9455e3b6-741a-4784-834f-df74e1c16b89" />

---

###### **1.4 Battery Pack**
Power comes from an **IFR 18650 4S1P 12.8V 2000mAh Li-ion battery pack** (a Lefant/OKP Life replacement pack originally designed for robot vacuums). Its 4S1P configuration (four cells in series) gives a stable 12.8 V nominal output that directly matches the operating voltage of our DC motor and DRV8871 motor driver, and its 2000 mAh (2 Ah) capacity comfortably powers the motor, Raspberry Pi, sensors, and control electronics for a full run without a significant voltage drop, all in a compact, lightweight form factor.

Normal draw is **1.2 A / 2.0 A peak (15.36 W)**.

<img width="220" alt="batteryimg" src="IMAGE">

---

###### **1.5 Buck Converter (5V DC-DC)**
Since our components run at different voltages, a **switching buck converter** steps the 12.8 V battery voltage down to 5 V for the Arduino Nano, Raspberry Pi, sensors, and other 5 V electronics. We originally used a linear 7805 regulator for this conversion, but it dissipated roughly 15.6 W while stepping 12.8 V down to 5 V at ~2 A, driving its temperature to 150–175 °C and triggering thermal shutdown after only a few corner turns. The switching buck converter performs the same conversion far more efficiently, protecting components from damage and keeping performance consistent throughout a run.

Output is **0.8 A normal / 1.5 A peak (4.0 W)**.

<img width="350" alt="buck_converter" src="IMAGE">

---

###### **1.6 UBEC: 8.4V 10A**
A dedicated **8.4 V 10 A UBEC** regulates battery power specifically for the steering servo. The previous 5 V servo's current spikes were pulling power from the rest of the electronics, causing other components to brown out under load. The UBEC gives the servo its own regulated, high-current supply independent of the main electronics, letting the high-torque servo operate without stalling and without affecting anything else on the board.

Input draw is **0.33 A normal / 3.5 A peak, delivering 2.8 W output**.

<img width="220" alt="ubec" src="IMAGE">

---

#### 2\. Electrical Components

###### **2.1 Main Controller: Raspberry Pi 4B**
The **Raspberry Pi 4B** is our main controller, handling camera input, object and line detection, navigation calculations, and communication with the motor controller.

At 5 V, it draws **0.70 A normal / 1.20 A peak (3.50 W)** together with the camera module.

<img width="220" alt="raspberrypi4bimg" src="IMAGE">

---

###### **2.2 Motor Controller: Arduino Nano**
The **Arduino Nano** acts as a dedicated motor controller, handling DC motor speed and servo steering, and receiving commands from the Pi over serial communication, keeping motor control isolated from delays caused by image processing. We initially used an ESP32 in this role, but its 3.3 V PWM logic did not reliably trigger the DRV8871. The Nano outputs a 5 V PWM signal, matching what the DRV8871 needs for reliable operation, and its compact 45 × 18 mm size and 1–3 second code upload time also suited our board and testing needs.

At 5 V, it draws **0.05 A normal / 0.10 A peak (0.25 W)**.

<img width="220" alt="arduinonano" src="IMAGE">

---

###### **2.3 Camera: Raspberry Pi Camera Module 3 Wide**
The **Raspberry Pi Camera Module 3 Wide** was chosen for its wider field of view, giving the robot better line and object detection coverage during autonomous navigation. It's also our only sensor: with the PiCam alone, our processing cycle takes ~150 ms, but adding Time-of-Flight or ultrasonic sensors increased this to ~600 ms, a roughly 4x slowdown. Since the robot needs to continuously process camera data and issue movement corrections while driving, that added latency would make the robot react more slowly and reduce navigation accuracy. Because the PiCam already provides the visual information our computer vision algorithm needs from a single image, we prioritized processing speed and responsiveness over adding redundant distance sensors.

<img width="215" alt="picamimg" src="IMAGE">

---

###### **2.4 Custom PCB**
A custom-designed PCB organizes wiring between components, giving cleaner cable management, reliable connections, a compact fit inside the chassis, and easier debugging. It includes a dedicated **servo port** (power, ground, PWM), isolated from the main power rail after servo current spikes were found to cause shutdowns elsewhere, and a dedicated **motor encoder port** for wheel encoder feedback, enabling closed-loop control of distance and speed.

<img width="215" alt="pcb" src="IMAGE">

---

#### 3\. Power Budget

| Component | Input Voltage | Normal Current | Peak Current | Power Consumption (P = V×I) |
|---|---|---|---|---|
| 12.8 V 2000 mAh 4S1P Li-ion Battery | 12.8 V | 1.2 A | 2.0 A | 15.36 W |
| DRV8871 Motor Driver | 12.8 V | <0.05 A | <0.1 A | 0.64 W |
| 12 V 37D Metal Gear Motor | 12.8 V | 0.40 A | 1.00 A | 5.12 W |
| 5 V DC-DC Buck Converter | 12.8 V → 5 V | 0.8 A (out) | 1.5 A (out) | 4.0 W (out) |
| Arduino Nano | 5 V | 0.05 A | 0.10 A | 0.25 W |
| Raspberry Pi 4B + Pi Camera 3 Wide | 5 V | 0.70 A | 1.20 A | 3.50 W |
| Motor Encoders | 5 V | 0.02 A | 0.03 A | 0.10 W |
| 8.4 V 10 A UBEC | 12.8 V → 8.4 V | 0.33 A (in) | 3.5 A (in) | 2.8 W (out) |
| 8.4 V High-Torque Coreless Servo | 8.4 V | 0.50 A | 3.0–5.0 A | 4.2–25.2 W |

---

#### 4\. Electrical Integration
All components are integrated into the final chassis as a compact, reliable system: the Raspberry Pi handles high-level decision-making from the camera feed, while the Arduino Nano manages real-time motor and steering control, isolated on its own logic and power paths after earlier testing showed shared power rails caused shutdowns under load.

<img width="250" alt="elec" src="IMAGE">
