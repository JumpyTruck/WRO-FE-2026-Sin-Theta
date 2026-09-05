#include <Servo.h>

// motor driver (DRV8871)
int m1 = 10; // IN1
int m2 = 11; // IN2

// servo
Servo myservo;
int servoPin = 5;

// encoder
const int ENC_C1 = 2;  // interrupt pin (Nano INT0)
const int ENC_C2 = 7;  // no longer read in the ISR -- see encoderISR() below
volatile long encoderTicks = 0;

// Serial commands, one per line, terminated with '\n':
//   SERVO,<angle>               angle = 0-180
//   MOTOR,<dir>,<speed>         dir = 0 stop / 1 forward / 2 backward, speed = 0-255
//   MOVE,<dir>,<speed>,<ticks>  blocking: drives until |ticks moved| >= <ticks>, replies "DONE,<ticks_moved>"
//   STOP / STOP,1               STOP coasts, STOP,1 brakes
//   TICKS?                      replies "TICKS,<count>"
//   RESET                       zeroes the encoder count, replies "TICKS,0"
// anything else is ignored

void setup() {
  Serial.begin(115200);

  pinMode(m1, OUTPUT);
  pinMode(m2, OUTPUT);
  pinMode(ENC_C1, INPUT_PULLUP);
  pinMode(ENC_C2, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(ENC_C1), encoderISR, CHANGE);

  myservo.attach(servoPin);

  // make sure motor is physically off until the Pi explicitly says go
  move_motor(0, 0);

  Serial.println("Nano ready");
}

void encoderISR() {
  // Direction via C2 wasn't reliable on this wiring. handleMove() (and
  // therefore set_motor(..., ticks=...) on the Pi side) only ever cares
  // about abs(encoderTicks - startTicks), i.e. magnitude of movement, not
  // sign -- so a monotonically-increasing counter is all that's actually
  // needed. This matches the standalone encoder-test sketch that was
  // confirmed working by hand.
  encoderTicks++;
}

void loop() {

  if (Serial.available() > 0) {

    String input = Serial.readStringUntil('\n');
    input.trim();

    if (input.length() == 0) return;

    // ---- STOP command ----
    if (input == "STOP") {
      move_motor(0, 0);
      return;
    }

    // ---- report current encoder count ----
    if (input == "TICKS?") {
      Serial.print("TICKS,");
      Serial.println(encoderTicks);
      return;
    }

    // ---- zero the encoder count ----
    if (input == "RESET") {
      noInterrupts();
      encoderTicks = 0;
      interrupts();
      Serial.println("TICKS,0");
      return;
    }

    // ---- blocking move by tick count ----
    if (input.startsWith("MOVE,")) {
      handleMove(input);
      return;
    }

    // ---- MOTOR command: "MOTOR,<dir>,<speed>" ----
    if (input.startsWith("MOTOR,")) {
      int firstComma = input.indexOf(',');
      int secondComma = input.indexOf(',', firstComma + 1);
      if (secondComma == -1) return; // malformed, ignore

      int dir   = input.substring(firstComma + 1, secondComma).toInt();
      int speed = input.substring(secondComma + 1).toInt();

      dir = constrain(dir, 0, 2);
      speed = constrain(speed, 0, 255);

      move_motor(speed, dir);
      return;
    }

    // ---- SERVO command: "SERVO,<angle>" ----
    // ---- STOP command: "STOP" (coast) or "STOP,1" (immediate/brake) ----
  if (input == "STOP" || input.startsWith("STOP,")) {
    int mode = 0;
    if (input.startsWith("STOP,")) {
    mode = input.substring(5).toInt(); // mode 1 = brake, else coast
  }
  move_motor(0, mode == 1 ? 3 : 0);
  return;
}

    // unrecognized input -- ignore
  }
}

// handles "MOVE,<dir>,<speed>,<ticks>" -- blocks until target ticks are
// reached, or a STOP/STOP,1 command comes in early
void handleMove(String input) {
  int c1 = input.indexOf(',');
  int c2 = input.indexOf(',', c1 + 1);
  int c3 = input.indexOf(',', c2 + 1);
  if (c2 == -1 || c3 == -1) return;

  int dir          = constrain(input.substring(c1 + 1, c2).toInt(), 0, 2);
  int speed        = constrain(input.substring(c2 + 1, c3).toInt(), 0, 255);
  long targetTicks = abs(input.substring(c3 + 1).toInt());

  noInterrupts();
  long startTicks = encoderTicks;
  interrupts();

  move_motor(speed, dir);

  int stopMode = 0;  // default: coast, unless a STOP,1 arrives below

  while (true) {
    noInterrupts();
    long moved = abs(encoderTicks - startTicks);
    interrupts();

    if (moved >= targetTicks) break;

    if (Serial.available() > 0) {
      String cmd = Serial.readStringUntil('\n');
      cmd.trim();
      if (cmd == "STOP" || cmd.startsWith("STOP,")) {
        if (cmd.startsWith("STOP,")) stopMode = cmd.substring(5).toInt();
        break;
      }
    }
  }

  move_motor(0, 3); // brake once target ticks are hit (or STOP arrives)

  noInterrupts();
  long finalMoved = abs(encoderTicks - startTicks);
  interrupts();

  Serial.print("DONE,");
  Serial.println(finalMoved);
}

// DRV8871 motor control
// direction: 0 = coast, 1 = forward, 2 = backward, 3 = immediate stop/brake
// speed: 0-255 PWM duty cycle
void move_motor(int speed, int direction) {

  speed = constrain(speed, 0, 255);

  if (direction == 0) {
    // coast stop
    digitalWrite(m1, LOW);
    digitalWrite(m2, LOW);
  }
  else if (direction == 1) { // forward
    analogWrite(m2, (255 - speed));
    digitalWrite(m1, HIGH);
  }
  else if (direction == 2) { // backward
    analogWrite(m2, speed);
    digitalWrite(m1, LOW);
  }
  else if (direction == 3) {
    // immediate stop
    digitalWrite(m1, HIGH);
    digitalWrite(m2, HIGH);
  }
}
