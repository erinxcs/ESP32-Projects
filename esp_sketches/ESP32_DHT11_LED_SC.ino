// EXP 3.2 - Activity #2: Serial Communication
// Part A: LED Control via Serial
// Part B: DHT11 Monitoring via Serial Monitor

#include <DHT.h>

#define DHTPIN 2        // DHT11 data pin connected to pin 2
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);

const int LED_PIN = 13;
char incomingByte;

unsigned long previousMillis = 0;
const long interval = 2000;  // read DHT11 every 2 seconds

void setup() {
  Serial.begin(9600);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  dht.begin();

  Serial.println("=== Activity 2: Serial Communication ===");
  Serial.println("Send '1' = LED ON, '0' = LED OFF");
  Serial.println("DHT11 readings will print automatically...");
  Serial.println();
}

void loop() {
  // ----- Part A: LED Control -----
  if (Serial.available() > 0) {
    incomingByte = Serial.read();

    if (incomingByte == '1') {
      digitalWrite(LED_PIN, HIGH);
      Serial.println(">> LED ON");
    } 
    else if (incomingByte == '0') {
      digitalWrite(LED_PIN, LOW);
      Serial.println(">> LED OFF");
    }
  }

  // ----- Part B: DHT11 Monitoring -----
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;

    float humidity = dht.readHumidity();
    float temperature = dht.readTemperature();  // Celsius

    if (isnan(humidity) || isnan(temperature)) {
      Serial.println("Failed to read from DHT sensor!");
      return;
    }

    Serial.print("Temperature: ");
    Serial.print(temperature);
    Serial.print(" °C   Humidity: ");
    Serial.print(humidity);
    Serial.println(" %");
  }
}