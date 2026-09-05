# Raspberry Pi Setup Guide

This guide covers everything needed to get a fresh Raspberry Pi ready to run the robot's code — OS setup, enabling the camera, installing dependencies, pulling the code, and running the script.

## 1) What You Need

- Raspberry Pi (4 or 5 recommended) with Raspberry Pi OS
- Raspberry Pi Camera Module, connected to the CSI port
- Arduino Nano connected via USB
- Push button + status LED wired to GPIO (pins 26 and 16 by default)

## 2) Update the System

sudo apt update && sudo apt full-upgrade -y
sudo reboot

## 3) Enable the Camera

sudo raspi-config

Go to **Interface Options → Camera → Enable**, then reboot when prompted.

## 4) Find the Arduino's Serial Port

The Nano usually shows up as `/dev/ttyUSB0` or `/dev/ttyACM0`. Check which one:

ls /dev/tty*

Plug/unplug the Nano and re-run the command — whichever entry appears/disappears is the right port. Update `SERIAL_PORT_NAME` in the code if it's different from `/dev/ttyUSB0`.

Give your user permission to use serial ports, then reboot:

sudo usermod -a -G dialout $USER
sudo reboot

## 5) Install System Dependencies

sudo apt install -y python3-pip python3-venv python3-opencv python3-picamera2 git

`opencv` and `picamera2` are installed as system packages here since they rely on hardware libraries that pip struggles to install cleanly on a Pi.

## 6) Create a Virtual Environment

python3 -m venv --system-site-packages venv
source venv/bin/activate

Run `source venv/bin/activate` again anytime you open a new terminal.

## 7) Install Python Dependencies

pip install pyserial numpy gpiozero RPi.GPIO

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

`git clone https://github.com/JumpyTruck/WRO-FE-2026-Sin-Theta.git`

`cd WRO-FE-2026-Sin-Theta`

## 9) Wiring Check

| Component | GPIO Pin (BCM) |
|---|---|
| Start button | 26 |
| Status LED | 16 |

## 10) Running the Code

source venv/bin/activate
cd WRO-FE-2026-Sin-Theta   # if not already there
python3 ObstacleChallenge.py

The status LED turns on, and the program waits for the start button to be pressed.

**Next step:** once this guide is complete, continue with Phase 3, Step 2 (Load Arduino Firmware) in the main setup instructions.
