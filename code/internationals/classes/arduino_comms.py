import time

import serial

from utils.constants import (
    BAUD_RATE,
    SERIAL_PORT,
    SERIAL_TIMEOUT,
    SERIAL_WARMUP_TIME,
    STEER_CENTER,
    STEER_SIGN,
)


class ArduinoComms:
    # everything we say to the motor/servo board goes through here
    def __init__(self, port=SERIAL_PORT, baud_rate=BAUD_RATE, timeout=SERIAL_TIMEOUT):
        self.serial_port = serial.Serial(port, baud_rate, timeout=timeout)
        time.sleep(SERIAL_WARMUP_TIME)  # give the board time to boot
        self.profile = None  # steering limits, set once we know which challenge it is
        self._last_servo_angle = None

    def use_profile(self, profile):
        # has to be called before any steering, the limits come from the challenge
        self.profile = profile

    def _to_servo_angle(self, angle):
        # servo expects the opposite direction
        if STEER_SIGN == -1:
            return int(round(2 * STEER_CENTER - angle))
        return int(round(angle))

    def set_steering_angle(self, angle, min_angle=None, max_angle=None):
        low = self.profile.steer_min if min_angle is None else min_angle
        high = self.profile.steer_max if max_angle is None else max_angle
        angle = max(low, min(high, angle))
        servo_angle = self._to_servo_angle(angle)

        # no point resending the angle the servo is already at
        if servo_angle == self._last_servo_angle:
            return
        self._last_servo_angle = servo_angle
        self.serial_port.write(f"SERVO,{servo_angle}\n".encode())

    def set_park_steering(self, angle):
        self.set_steering_angle(angle, self.profile.park_steer_min, self.profile.park_steer_max)

    def drive(self, motor_direction, speed, ticks=None):
        motor_direction = max(0, min(2, int(motor_direction)))
        speed = max(0, min(255, int(speed)))

        if ticks is not None:
            # reset the ticks first so distance is relative to now
            self.reset_tick_counter()
            return self.drive_ticks(motor_direction, speed, int(ticks))

        self.serial_port.write(f"MOTOR,{motor_direction},{speed}\n".encode())
        return None

    def drive_ticks(self, motor_direction, speed, ticks, timeout=11.0):
        self.serial_port.reset_input_buffer()
        self.serial_port.write(f"MOVE,{motor_direction},{speed},{abs(ticks)}\n".encode())

        # wait for the board to say it's done
        deadline = time.time() + timeout
        while time.time() < deadline:
            line = self.serial_port.readline().decode(errors="ignore").strip()
            if line.startswith("DONE"):
                parts = line.split(",")
                return int(parts[1]) if len(parts) > 1 else None
        return None

    def stop(self, immediate=False):
        self.serial_port.write(b"STOP,1\n" if immediate else b"STOP\n")

    def reset_tick_counter(self):
        self.serial_port.reset_input_buffer()
        self.serial_port.write(b"RESET\n")
        self.serial_port.readline()

    def close(self):
        self.serial_port.close()
