import time

import serial

from utils.constants import (
    BAUD_RATE,
    MOTOR_REVERSE,
    SERIAL_PORT,
    SERIAL_TIMEOUT,
    SERIAL_WARMUP_TIME,
    STEER_CENTER,
    STEER_SIGN,
)


class ArduinoComms:
    # Everything sent to the Arduino Nano (motor driver, steering servo, encoder) goes through here.
    # Commands are plain text lines: SERVO,<angle>  MOTOR,<dir>,<speed>  MOVE,<dir>,<speed>,<ticks>
    # STOP / STOP,1  RESET
    def __init__(self, port=SERIAL_PORT, baud_rate=BAUD_RATE, timeout=SERIAL_TIMEOUT):
        self.serial_port = serial.Serial(port, baud_rate, timeout=timeout)
        time.sleep(SERIAL_WARMUP_TIME)  # the Nano resets when the port opens

        self.profile = None   # steering limits, set once the challenge is known
        self.speed = 0        # last commanded motor speed, read by the video overlay
        self.reversing = False
        self._last_servo_angle = None

    def use_profile(self, profile):
        # must be called before any steering because the limits come from the challenge profile
        self.profile = profile

    def _to_servo_angle(self, angle):
        # the servo is mounted reversed, so the logical angle is mirrored around the centre
        if STEER_SIGN == -1:
            return int(round(2 * STEER_CENTER - angle))
        return int(round(angle))

    def _write_servo(self, servo_angle):
        self._last_servo_angle = servo_angle
        self.serial_port.write(f"SERVO,{servo_angle}\n".encode())

    def set_steering_angle(self, angle, min_angle=None, max_angle=None,
                           duration=0.0, resend_interval=0.03):
        # clamps the angle to the allowed range and sends it.
        # with a duration the angle is re-sent repeatedly, which also holds the servo in place
        low = self.profile.steer_min if min_angle is None else min_angle
        high = self.profile.steer_max if max_angle is None else max_angle
        servo_angle = self._to_servo_angle(max(low, min(high, angle)))

        if duration > 0:
            end_time = time.time() + duration
            while time.time() < end_time:
                self._write_servo(servo_angle)
                time.sleep(resend_interval)
            return

        # no point re-sending the angle the servo is already at
        if servo_angle != self._last_servo_angle:
            self._write_servo(servo_angle)

    def set_park_steering(self, angle):
        # same as set_steering_angle but with the wider parking limits
        self.set_steering_angle(angle, self.profile.park_steer_min, self.profile.park_steer_max)

    def drive(self, motor_direction, speed, ticks=None):
        # without ticks the motor runs until told otherwise.
        # with ticks the call blocks until the encoder has counted that many ticks
        motor_direction = max(0, min(2, int(motor_direction)))
        speed = max(0, min(255, int(speed)))

        moving = motor_direction != 0 and speed > 0
        self.speed = speed if moving else 0
        self.reversing = moving and motor_direction == MOTOR_REVERSE

        if ticks is not None:
            self.reset_tick_counter()  # distance is measured from now
            moved = self.drive_ticks(motor_direction, speed, int(ticks))
            self.speed = 0  # the board stops by itself once the ticks are done
            self.reversing = False
            return moved

        self.serial_port.write(f"MOTOR,{motor_direction},{speed}\n".encode())
        return None

    def drive_ticks(self, motor_direction, speed, ticks, timeout=11.0):
        self.serial_port.reset_input_buffer()
        self.serial_port.write(f"MOVE,{motor_direction},{speed},{abs(ticks)}\n".encode())

        # the board answers DONE,<ticks moved> when the move is finished
        deadline = time.time() + timeout
        while time.time() < deadline:
            line = self.serial_port.readline().decode(errors="ignore").strip()
            if line.startswith("DONE"):
                parts = line.split(",")
                return int(parts[1]) if len(parts) > 1 else None
        return None

    def stop(self, immediate=False):
        # immediate brakes (hard stop), otherwise the motor coasts
        self.speed = 0
        self.reversing = False
        self.serial_port.write(b"STOP,1\n" if immediate else b"STOP\n")

    def reset_tick_counter(self):
        self.serial_port.reset_input_buffer()
        self.serial_port.write(b"RESET\n")
        self.serial_port.readline()

    def close(self):
        self.serial_port.close()
