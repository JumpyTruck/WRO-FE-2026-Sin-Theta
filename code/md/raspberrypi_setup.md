# Raspberry Pi Setup Guide

This guide covers everything needed to get a fresh Raspberry Pi ready to run the robot's code — OS setup, enabling the camera, installing dependencies, pulling the code, and running the program.

The robot runs the **International version** of our code (`code/internationals/main.py`). It is one program for **both** challenges: at the start it checks for the pink parking walls in front of the camera and picks the Open or Obstacle Challenge by itself.

## 1) What You Need

- Raspberry Pi (4 or 5 recommended) with Raspberry Pi OS
- Raspberry Pi Camera Module 3 Wide, connected to the CSI port
- Arduino Nano connected via USB (flashed with `Arduino_Serial.ino`)
- Push button + status LED wired to GPIO (pins 26 and 16 by default)

## 2) Update the System

```bash
sudo apt update && sudo apt full-upgrade -y
sudo reboot
```

## 3) Enable the Camera

```bash
sudo raspi-config
```

Go to **Interface Options → Camera → Enable**, then reboot when prompted.

## 4) Find the Arduino's Serial Port

The Nano usually shows up as `/dev/ttyUSB0` or `/dev/ttyACM0`. Check which one:

```bash
ls /dev/tty*
```

Plug/unplug the Nano and re-run the command — whichever entry appears/disappears is the right port. If it's different from `/dev/ttyUSB0`, update `SERIAL_PORT` in `code/internationals/utils/constants.py`.

Give your user permission to use serial ports, then reboot:

```bash
sudo usermod -a -G dialout $USER
sudo reboot
```

## 5) Install System Dependencies

```bash
sudo apt install -y python3-pip python3-venv python3-opencv python3-picamera2 git
```

`opencv` and `picamera2` are installed as system packages here since they rely on hardware libraries that pip struggles to install cleanly on a Pi.

## 6) Create a Virtual Environment

```bash
python3 -m venv --system-site-packages venv
source venv/bin/activate
```

Run `source venv/bin/activate` again anytime you open a new terminal.

## 7) Install Python Dependencies

```bash
pip install pyserial numpy gpiozero RPi.GPIO
```

| Package | What it's for |
|---|---|
| opencv (system) | Vision pipeline — colour masks, contours, steering math |
| picamera2 (system) | Reading frames from the Pi camera |
| numpy | Array math used throughout the vision pipeline |
| pyserial | Talking to the Arduino Nano over USB |
| RPi.GPIO | Reading the start button |
| gpiozero | Controlling the status LED |

## 8) Get the Code onto the Pi

Clone the repo:

```bash
git clone https://github.com/JumpyTruck/WRO-FE-2026-Sin-Theta.git
cd WRO-FE-2026-Sin-Theta/code/internationals
```

The International code is split into modules:

| File / Folder | What it does |
|---|---|
| `main.py` | Entry point — the state machine for the whole run |
| `classes/` | Pillar navigation, lap counting, Arduino serial link, video recording |
| `utils/constants.py` | Shared settings (serial port, GPIO pins, LAB colour ranges, gains) |
| `utils/challenge_profile.py` | Values that differ between the Open and Obstacle Challenge |
| `utils/park_profile.py` | Parking values for left and right runs |

## 9) Wiring Check

| Component | GPIO Pin (BCM) |
|---|---|
| Start button | 26 |
| Status LED | 16 |

## 10) Running the Code

```bash
source venv/bin/activate
cd WRO-FE-2026-Sin-Theta/code/internationals   # if not already there
python3 main.py
```

The status LED turns on, and the program waits for the start button to be pressed. After the button is pressed the robot:

1. Warms up the camera
2. Detects the challenge (pink parking walls in view → Obstacle Challenge, no pink → Open Challenge)
3. Detects the driving direction
4. Drives the 3 laps (and parks, in the Obstacle Challenge)

The same command runs both challenges — there is no separate Open or Obstacle script to choose. Each run is recorded to the `recordings/` folder (with lap count, timer and speed drawn on the video) for debugging.

**Next step:** once this guide is complete, continue with Phase 3, Step 2 (Load Arduino Firmware) in the main setup instructions.
