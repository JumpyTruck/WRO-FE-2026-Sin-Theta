# Raspberry Pi 4B ↔ Arduino Nano Serial Communication Test

This guide demonstrates how to verify serial communication between a **Raspberry Pi 4B** and an **Arduino Nano** over USB.

## Requirements

### Hardware

- Raspberry Pi 4B
- Arduino Nano
- USB cable (USB-C to USB or USB-A to Mini-USB/Micro-USB depending on your Nano)
- Arduino IDE installed on your computer
- Raspberry Pi OS

### Software

- Python 3
- `pyserial`

---

## Step 1 - Upload the Arduino Test Sketch

1. Open the Arduino IDE.
2. Connect the Arduino Nano to your computer.
3. Download the [test sketch](Serial_Test_Nano.ino)
4. Select the correct board and COM port.
5. Upload the sketch.

---

## Step 2 - Connect the Arduino to the Raspberry Pi

Disconnect the Arduino from your computer and connect it to the Raspberry Pi using the USB cable.

The Arduino should automatically appear as a serial device.

---

## Step 3 - Install PySerial

On the Raspberry Pi, install the required Python library.

```bash
pip3 install pyserial
```

---

## Step 4 - Identify the Serial Port

Run:

```bash
ls /dev/tty*
```

or

```bash
dmesg | grep tty
```

Look for one of the following devices:

```
/dev/ttyUSB0
```

or

```
/dev/ttyACM0
```

If unsure, unplug the Arduino, run the command, plug it back in, and run the command again. The new device is your Arduino.

---

## Step 5 - Create the Python Test Script

Create a new file:

```bash
nano serial_test.py
```

Paste the test code for the [Raspberry Pi](Serial_Test_Pi.py)

Save the file.

---

## Step 6 - Run the Test

Execute the script.

```bash
python3 serial_test.py
```

---

## Expected Output

If everything is working correctly, you should see output similar to:

```
Connected
Arduino: Arduino Ready
Arduino: Received: PING
Arduino: PONG
Arduino: Heartbeat
Arduino: Received: PING
Arduino: PONG
Arduino: Heartbeat
```

---

## Troubleshooting

### Permission Denied

If you receive a permission error:

```bash
Permission denied: '/dev/ttyUSB0'
```

Add your user to the `dialout` group:

```bash
sudo usermod -a -G dialout $USER
```

Then reboot:

```bash
sudo reboot
```

---

### Port Not Found

Verify the Arduino is detected:

```bash
ls /dev/ttyUSB*
```

or

```bash
ls /dev/ttyACM*
```

---

### No Output

Check that:

- The Arduino sketch uploaded successfully.
- The baud rate matches (`115200`).
- The correct serial port is selected.
- The USB cable supports data transfer (some cables are power-only).

---

## Success Criteria

The test is successful when:

- Raspberry Pi sends `PING`
- Arduino receives `PING`
- Arduino replies with `PONG`
- Raspberry Pi receives `PONG`
- Heartbeat messages are received every 2 seconds

This confirms reliable bidirectional serial communication between the Raspberry Pi and Arduino Nano.
