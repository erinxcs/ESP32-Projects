// EXP 4 - Activity #3
// LED Control Using BT Serial App (ESP32)

#include "BluetoothSerial.h"

#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error Bluetooth is not enabled! Enable it in "Tools -> Partition Scheme"
#endif

BluetoothSerial SerialBT;

const int LED_PIN = 5;  // D5 - external LED w/ resistor
char incomingByte;

void setup() {
  Serial.begin(115200);
  SerialBT.begin("ESP32_LED_Control");  // Bluetooth device name shown in app

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  Serial.println("Bluetooth started. Pair with 'ESP32_LED_Control'");
  Serial.println("Send '1' = LED ON, '0' = LED OFF");
}

void loop() {
  if (SerialBT.available() > 0) {
    incomingByte = SerialBT.read();

    if (incomingByte == '1') {
      digitalWrite(LED_PIN, HIGH);
      SerialBT.println("LED ON");
      Serial.println("LED ON");
    } 
    else if (incomingByte == '0') {
      digitalWrite(LED_PIN, LOW);
      SerialBT.println("LED OFF");
      Serial.println("LED OFF");
    }
  }
}