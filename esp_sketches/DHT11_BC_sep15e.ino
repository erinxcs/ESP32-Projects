// EXP 3.2 - Activity #3
// DHT11 Monitoring Using BT Serial App (ESP32)

#include "BluetoothSerial.h"
#include <DHT.h>

#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error Bluetooth is not enabled! Enable it in "Tools -> Partition Scheme"
#endif

BluetoothSerial SerialBT;

#define DHTPIN 4        // D4 - DHT11 data pin
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(115200);
  SerialBT.begin("ESP32_DHT_Monitor");  // Bluetooth device name shown in app
  dht.begin();

  Serial.println("Bluetooth started. Pair with 'ESP32_DHT_Monitor'");
}

void loop() {
  delay(2000);  // DHT11 needs ~2s between reads

  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();

  if (isnan(humidity) || isnan(temperature)) {
    SerialBT.println("Failed to read from DHT sensor!");
    Serial.println("Failed to read from DHT sensor!");
    return;
  }

  String reading = "Temp: " + String(temperature) + " C   Humidity: " + String(humidity) + " %";
  SerialBT.println(reading);
  Serial.println(reading);
}