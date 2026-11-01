// EXP 3.2 - Activity #3
// BT Master-Slave: SLAVE (Peripheral)

#include "BluetoothSerial.h"
#include "esp_bt_device.h"

BluetoothSerial SerialBT;
const int LED_PIN = 5;  // D5 - external LED

void setup() {
  Serial.begin(115200);
  SerialBT.begin("ESP32_SLAVE");  // slave device name

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  const uint8_t* mac = esp_bt_dev_get_address();
  Serial.print("Slave BT MAC: ");
  for (int i = 0; i < 6; i++) {
    Serial.printf("%02X", mac[  i]);
    if (i < 5) Serial.print(":");
  }
  Serial.println("\nWaiting for master to connect...");
}

void loop() {
  if (SerialBT.available() > 0) {
    char c = SerialBT.read();
    if (c == '1') {
      digitalWrite(LED_PIN, HIGH);
      Serial.println("LED ON (command from master)");
    } else if (c == '0') {
      digitalWrite(LED_PIN, LOW);
      Serial.println("LED OFF (command from master)");
    }
  }
}