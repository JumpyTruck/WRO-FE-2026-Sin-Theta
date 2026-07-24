#include <Servo.h>

// ========== MOTOR PINS (DRV8871) ==========
int m1 = 10; // IN1
int m2 = 11; // IN2

// ========== SERVO ==========
Servo myservo;
int servoPin = 5;

// ========== SERIAL COMMAND SENTINELS ==========
// These are out-of-range for a servo angle (0-180), so they can't collide
// with a real angle value.
const int CMD_MOTOR_STOP  = 999;
const int CMD_MOTOR_START = 888;

bool motorRunning = false;

void setup() {
  Serial.begin(115200);

  pinMode(m1, OUTPUT);
  pinMode(m2, OUTPUT);

  myservo.attach(servoPin);

  // make sure motor is physically off until the Pi explicitly says go
  move_motor(0, 0);
  motorRunning = false;

  Serial.println("Nano ready");
}

void loop() {

  if (Serial.available() > 0) {

    String input = Serial.readStringUntil('\n');
    input.trim();

    int value = input.toInt();

    // ---- STOP command ----
    if (value == CMD_MOTOR_STOP) {
      motorRunning = false;
      move_motor(0, 0);
      return;
    }

    // ---- START command ----
    if (value == CMD_MOTOR_START) {
      motorRunning = true;
      move_motor(255, 1);
      return;
    }

    // ---- otherwise treat as a servo angle ----
    int angle = constrain(value, 0, 180);
    Serial.print("ANGLE:");
    Serial.println(angle);
    myservo.write(angle);

    // keep driving the motor only if we've been told to start.
    if (motorRunning) {
      move_motor(255, 1);
    }
  }
}

// ========== DRV8871 MOTOR CONTROL ==========
// direction 0 = stop (coast), 1 = counter-clockwise, 2 = clockwise
// speed = 0-255 PWM duty cycle
void move_motor(int speed, int direction) {

  speed = constrain(speed, 0, 255);

  if (direction == 0) {
    // coast / stop
    digitalWrite(m1, LOW);
    digitalWrite(m2, LOW);
  }
  else if (direction == 1) { // counter clockwise
    digitalWrite(m2, LOW);
    analogWrite(m1, speed);
  }
  else if (direction == 2) { // clockwise
    digitalWrite(m1, LOW);
    analogWrite(m2, speed);
  }
}
