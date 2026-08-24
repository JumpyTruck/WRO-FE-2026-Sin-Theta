### Electrical Design Process

This section explains the design and integration of our robot's electrical system. It covers how we selected and connected the motor, steering system, power components, vision system, controllers, and custom PCB. Each component was chosen based on performance, reliability, power requirements, and the limited space within our chassis. The section also includes our power budget and final electrical integration.

---

#### 1. Motor & Drive System

###### **1.1 DC Motor Selection**

We use a **12V 37D metal gearmotor with an 11PPR encoder**, running at **510 RPM**. We required 300–500 RPM at the motor, which — with our 56 mm diameter wheels (≈175.93 mm circumference) — gives a theoretical wheel speed of roughly **0.88–1.47 m/s**: fast enough for the course without making acceleration, braking, and precise positioning difficult.

We also required a minimum torque of **≥1.5–2.0 kg·cm** to overcome the robot's weight, rolling resistance, and drivetrain friction while leaving margin for acceleration, without running the motor near its stall torque, which causes excess current draw and heat.

The built-in encoder lets the controller measure actual wheel rotation in ticks rather than relying on time-based movement, which drifts with battery voltage, friction, load, and surface conditions. Its metal gearbox reduces the motor's raw speed into usable torque, and its compact 37D form factor and 56 mm × 14 mm wheel compatibility fit our chassis (max 300 × 200 × 300 mm) alongside the battery, PCB, sensors, and steering system.

At 12.8 V, the motor draws **0.40 A normal / 1.00 A peak (5.12 W)**.

<img width="475"  alt="12V 37D Metal Gearmotor IMAGE" src="https://github.com/user-attachments/assets/ce9867de-050d-4366-aa7b-8baa1db68f33" />

---

###### **1.2 Motor Driver — Adafruit DRV8871**

The **Adafruit DRV8871** drives the DC motor with the current the Arduino Nano can't supply directly. It operates on **6.5–45 V**, so it runs directly off our 12.8 V battery, and its **3.6 A continuous / 6 A peak** current rating comfortably exceeds our battery's ~2 A max output, so the driver is never the bottleneck.

It provides PWM-based speed control, forward/reverse direction control, and built-in overcurrent, thermal shutdown, undervoltage, and short-circuit protection.

Its MOSFET switching design also produces a much smaller voltage drop and far less heat than a bipolar H-bridge driver (e.g. the L298N's ~2 V drop), so the motor receives nearly the full battery voltage — all in a small enough package for our limited space.

At 12.8 V, the driver itself draws **<0.05 A normal / <0.1 A peak (0.64 W)**.

<img width="475" alt="DRV8871 IMAGE" src="https://github.com/user-attachments/assets/83273570-c3b0-4a69-9b48-00a380b825cb" />

---

#### 2. Steering System

###### **2.1 Steering Servo**

Our original 5 V steering servo did not produce enough torque to reliably turn the steering mechanism under load; repeated stalling stressed and eventually damaged its internal components.

We replaced it with an **8.4 V high-torque coreless servo**, which offers precise angle control, fast response, and enough torque to steer without stalling, in a compact size that fits our chassis without issue.

At 8.4 V, the servo draws **0.50 A normal / 3.0–5.0 A peak (4.2–25.2 W)**.

<table>
  <tr>
    <!-- Left Column: Servo Image -->
    <td valign="top" width="30%">
      <img width="215" alt="newservo" src="https://github.com/user-attachments/assets/9455e3b6-741a-4784-834f-df74e1c16b89">
    </td>
    <!-- Right Column: Specs Table -->
    <td valign="top" width="70%">
      <table>
        <thead>
          <tr>
            <th>Component</th>
            <th>Voltage</th>
            <th>Normal Current</th>
            <th>Peak Current</th>
            <th>Power</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>9g Coreless Servo</td>
            <td>8.4V</td>
            <td>0.50A</td>
            <td>3.0–5.0A</td>
            <td>4.2–25.2W</td>
          </tr>
        </tbody>
      </table>
    </td>
  </tr>
</table>

---

###### **2.2 UBEC Voltage Regulator**

A dedicated **8.4 V 10 A UBEC** regulates battery power specifically for the steering servo.

The previous 5 V servo's current spikes were pulling power from the rest of the electronics, causing other components to brown out under load. The UBEC gives the servo its own regulated, high-current supply independent of the main electronics, letting the high-torque servo operate without stalling and without affecting anything else on the board.

Input draw is **0.33 A normal / 3.5 A peak**, delivering **2.8 W output**.

<img width="475" alt="UBEC Voltage Regulator IMAGE" src="https://github.com/user-attachments/assets/bea16464-2fdd-4aaa-bb4b-1065c5692b5d" />

---

#### 3. Main Power System

###### **3.1 Battery Pack**

Power comes from an **IFR 18650 4S1P 12.8 V 2000 mAh Li-ion battery pack** (a Lefant/OKP Life replacement pack originally designed for robot vacuums).

Its 4S1P configuration (four cells in series) gives a stable **12.8 V nominal output** that directly matches the operating voltage of our DC motor and DRV8871 motor driver.

Its **2000 mAh (2 Ah)** capacity comfortably powers the motor, Raspberry Pi, sensors, and control electronics for a full run without a significant voltage drop, all in a compact, lightweight form factor.

Normal draw is **1.2 A / 2.0 A peak (15.36 W)**.

<img width="475"  alt="Battery Pack IMAGE" src="https://github.com/user-attachments/assets/a7c0bf8d-32ce-4ca9-b66c-57b634085a05" />

---

###### **3.2 5 V DC-DC Buck Converter**

Since our components run at different voltages, a **switching buck converter** steps the 12.8 V battery voltage down to **5 V** for the Arduino Nano, Raspberry Pi, sensors, and other 5 V electronics.

We originally used a linear 7805 regulator for this conversion, but it dissipated roughly **15.6 W** while stepping 12.8 V down to 5 V at ~2 A, driving its temperature to **150–175 °C** and triggering thermal shutdown after only a few corner turns.

The switching buck converter performs the same conversion far more efficiently, protecting components from damage and keeping performance consistent throughout a run.

Output is **0.8 A normal / 1.5 A peak (4.0 W)**.

<img width="475" alt="5V dc to dc buck converter IMAGE" src="https://github.com/user-attachments/assets/902e4a4d-658e-41b0-8106-f455152bf21d" />

---

#### 4. Vision System

###### **4.1 Raspberry Pi Camera Module 3 Wide**

The **Raspberry Pi Camera Module 3 Wide** was chosen for its wider field of view, giving the robot better line and object detection coverage during autonomous navigation.

It is also our **only sensor**. With the PiCam alone, our processing cycle takes ~150 ms, but adding Time-of-Flight or ultrasonic sensors increased this to ~600 ms, a roughly **4× slowdown**.

Since the robot needs to continuously process camera data and issue movement corrections while driving, that added latency would make the robot react more slowly and reduce navigation accuracy.

Because the PiCam already provides the visual information our computer vision algorithm needs from a single image, we prioritized processing speed and responsiveness over adding redundant distance sensors.

<img width="215" alt="picamimg" src="IMAGE">

---

#### 5. Control & Processing Electronics

###### **5.1 Main Controller — Raspberry Pi 4B**

The **Raspberry Pi 4B** is our main controller, handling camera input, object and line detection, navigation calculations, and communication with the motor controller.

At 5 V, it draws **0.70 A normal / 1.20 A peak (3.50 W)** together with the camera module.

<img width="215" alt="raspberrypi4bimg" src="https://github.com/user-attachments/assets/65d65b6f-2e5f-429d-ac70-4b5c2403fa05" />

---

###### **5.2 Motor Controller — Arduino Nano**

The **Arduino Nano** acts as a dedicated motor controller, handling DC motor speed and servo steering, and receiving commands from the Pi over serial communication.

We initially used an **ESP32** in this role, but its 3.3 V PWM logic did not reliably trigger the DRV8871. The Nano outputs a **5 V PWM signal**, matching what the DRV8871 needs for reliable operation.

Separating motor control from the Raspberry Pi also prevents delays caused by image processing from affecting real-time motor and steering control.

Its compact **45 × 18 mm** size and **1–3 second code upload time** also suited our board and testing needs.

At 5 V, it draws **0.05 A normal / 0.10 A peak (0.25 W)**.

<img width="215" alt="arduinonano" src="https://github.com/user-attachments/assets/12157369-6e84-4ef4-8d9e-b78c3604fbd9" />

---

#### 6. Custom PCB & Electrical Organization

###### **6.1 Custom PCB**

A custom-designed PCB organizes wiring between components, giving cleaner cable management, reliable connections, a compact fit inside the chassis, and easier debugging.

It includes a dedicated **servo port** (power, ground, PWM), isolated from the main power rail after servo current spikes were found to cause shutdowns elsewhere.

It also includes a dedicated **motor encoder port** for wheel encoder feedback, enabling closed-loop control of distance and speed.

<img width="215" alt="pcb" src="IMAGE">

---



#### 7. Final Electrical Integration

All components are integrated into the final chassis as a compact, reliable system. The Raspberry Pi handles high-level decision-making from the camera feed, while the Arduino Nano manages real-time motor and steering control.

The systems are separated through dedicated logic and power paths after earlier testing showed shared power rails caused shutdowns under load.

<img width="250" alt="elec" src="IMAGE">
