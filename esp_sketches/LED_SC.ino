// EXP 3.2 - Activity #2 (ESP32)
// LED Control Using Serial Communication

const int LED_PIN = 2;  // built-in LED on most ESP32 dev boards
char incomingByte;

void setup() {
  Serial.begin(115200);   // ESP32 default baud rate
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  Serial.println("=== LED Control via Serial (ESP32) ===");
  Serial.println("Send '1' = LED ON, '0' = LED OFF");
}

void loop() {
  if (Serial.available() > 0) {
    incomingByte = Serial.read();

    if (incomingByte == '1') {
      digitalWrite(LED_PIN, HIGH);
      Serial.println("LED ON");
    } 
    else if (incomingByte == '0') {
      digitalWrite(LED_PIN, LOW);
      Serial.println("LED OFF");
    }
  }
}