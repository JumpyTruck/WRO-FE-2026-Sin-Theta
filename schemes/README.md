### Electrical Design Process

#### 1\. Motorization & Power System

###### **1.1 DC Motor Selection**
We use a **12V 37D metal gearmotor with an 11PPR encoder**, running at **510RPM**. The metal gearbox provides enough torque for reliable acceleration, while the built-in encoder allows precise speed and distance feedback for accurate autonomous control. Its compact 37D size fits neatly within the chassis while still delivering the power and durability needed for consistent performance.

<img width="215" alt="motorimg" src="https://github.com/user-attachments/assets/7b737ab7-3e7a-44c5-87d2-d31869414b0c" />

---

###### **1.2 Motor Driver: Adafruit DRV8871**
The **Adafruit DRV8871** drives the DC motor with the current the Arduino Nano can't supply directly. It gives PWM-based speed control, forward/reverse direction control, and built-in overcurrent and thermal protection, all in a small enough package for our limited space.

<img width="200" alt="motordruiv" src="https://github.com/user-attachments/assets/2a387b91-c8b5-48e4-8d71-ee1e7a48a98d" />

---

###### **1.3 Steering Servo: Coreless Black Servo**
The **Coreless Black Servo** metal-gear servo handles our Ackermann steering. It offers precise angle control, fast response, and enough torque for the steering mechanism, and its compact size fit our chassis without issue. We'd also used it in past projects, which sped up integration and tuning.

<img width="215" alt="newservo" src="https://github.com/user-attachments/assets/9455e3b6-741a-4784-834f-df74e1c16b89" />

---

###### **1.4 Battery Pack**
Power comes from an **IFR 18650 4S1P 12.8V 2000mAh battery pack** (a Lefant/OKP Life replacement pack originally designed for robot vacuums). Its 4S1P configuration gives a stable 12.8V output, and the 2000mAh capacity comfortably powers all electrical components for a full run without a significant voltage drop.

<img width="220" alt="batteryimg" src="https://github.com/user-attachments/assets/c675d81f-2ac3-4ca7-b616-fff872ef0a64" />

---

###### **1.5 Buck Converter**
Since our components run at different voltages, a **buck converter** steps the 12.8V battery voltage down to the level each part needs. This protects components from damage and keeps performance consistent throughout operation.

<img width="350" alt="buck_converter" src="IMAGE">

---

#### 2\. Electrical Components

###### **2.1 Main Controller: Raspberry Pi**
The **Raspberry Pi** is our main controller, handling camera input, object and line detection, navigation calculations, and communication with the motor controller.

<img width="220" alt="raspberrypi4bimg" src="https://github.com/user-attachments/assets/0de325c4-8aff-4621-ba53-301a315b03ae">

---

###### **2.2 Motor Controller: ESP32**
An **Arduino Nano** acts as a dedicated motor controller, handling DC motor speed and servo steering, and receiving commands from the Pi over serial communication, keeping motor control isolated from delays caused by image processing.

<img width="220" alt="arduinonano" src="https://github.com/user-attachments/assets/e42be539-4e3a-4a02-aaf5-1eb4dc3bbcfe" />

---

###### **2.3 Camera: Raspberry Pi Camera Module 3 Wide**
The **Raspberry Pi Camera Module 3 Wide** was chosen for its wider field of view, giving the robot better line and object detection coverage during autonomous navigation.

<img width="215" alt="picamimg" src="https://github.com/user-attachments/assets/eea5814d-47b6-4ad2-9bd3-d7ed7dbc0355" />

---

###### **2.4 Custom PCB**
A custom-designed PCB organizes wiring between components, giving cleaner cable management, reliable connections, a compact fit inside the chassis, and easier debugging.

<img width="215" alt="pcb" src="https://github.com/user-attachments/assets/8928a744-2e74-4a87-bdf1-33e05931037d" />

---

#### 3\. Electrical Integration
All components are integrated into the final chassis as a compact, reliable system: the Raspberry Pi handles high-level decision-making, while the ESP32 manages real-time motor and steering control.

<img width="250" alt="elec" src="https://github.com/user-attachments/assets/ce538aed-06b1-4c1c-95ff-e8c79c9cbd87" />
