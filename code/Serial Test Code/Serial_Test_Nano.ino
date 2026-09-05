void setup() {
  Serial.begin(115200);
  while (!Serial) {
    ; // Wait for serial (ignored on Nano but harmless)
  }

  Serial.println("Arduino Ready");
}

void loop() {
  // If data comes from Raspberry Pi
  if (Serial.available()) {
    String msg = Serial.readStringUntil('\n');

    Serial.print("Received: ");
    Serial.println(msg);

    if (msg == "PING") {
      Serial.println("PONG");
    }
  }

  // Periodic heartbeat every 2 seconds
  static unsigned long last = 0;
  if (millis() - last > 2000) {
    last = millis();
    Serial.println("Heartbeat");
  }
}
