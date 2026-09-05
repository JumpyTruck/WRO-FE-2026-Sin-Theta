import serial
import time

# Change this if needed:
PORT = "/dev/ttyUSB0"     # or /dev/ttyACM0
BAUD = 115200

ser = serial.Serial(PORT, BAUD, timeout=1)

# Give Arduino time to reset after opening the port
time.sleep(2)

print("Connected")

while True:
    # Send ping
    ser.write(b"PING\n")

    # Read all available lines
    start = time.time()
    while time.time() - start < 1:
        if ser.in_waiting:
            line = ser.readline().decode(errors="ignore").strip()
            print("Arduino:", line)

    time.sleep(2)
