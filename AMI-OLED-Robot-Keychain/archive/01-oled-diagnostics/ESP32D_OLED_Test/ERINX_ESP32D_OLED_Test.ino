/*
  ERINX SMART HAIR CLIP - ESP32D OLED DIAGNOSTIC
  Board: ESP32 Dev Module / ESP32D DevKit (classic ESP32)
  Display: 0.96-inch 128x64 I2C SSD1306 OLED

  Wiring:
    OLED VCC -> ESP32 3V3
    OLED GND -> ESP32 GND
    OLED SDA -> ESP32 GPIO21
    OLED SCL -> ESP32 GPIO22

  Install in Arduino Library Manager:
    Adafruit SSD1306
    Adafruit GFX Library

  Serial Monitor: 115200 baud
*/

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define OLED_SDA 21
#define OLED_SCL 22
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

bool oledReady = false;
uint8_t oledAddress = 0;
unsigned long lastScan = 0;
unsigned long lastFrame = 0;
uint32_t frameNumber = 0;

void scanAndStart() {
  Serial.println();
  Serial.println("--- Scanning I2C: SDA=GPIO21, SCL=GPIO22 ---");

  bool anyFound = false;
  uint8_t possibleAddress = 0;

  for (uint8_t address = 1; address < 127; address++) {
    Wire.beginTransmission(address);
    uint8_t error = Wire.endTransmission();
    if (error == 0) {
      anyFound = true;
      Serial.printf("I2C device found at 0x%02X\n", address);
      if (address == 0x3C || address == 0x3D) {
        possibleAddress = address;
      }
    }
  }

  if (!anyFound) {
    Serial.println("NO I2C DEVICES FOUND!");
    Serial.println("Check OLED VCC/GND/SDA/SCL, then reset ESP32.");
    return;
  }

  if (possibleAddress == 0) {
    Serial.println("I2C device present, but not at 0x3C or 0x3D.");
    Serial.println("Check that the module is a 4-pin I2C OLED.");
    return;
  }

  oledAddress = possibleAddress;
  Serial.printf("Trying SSD1306 init at 0x%02X...\n", oledAddress);

  if (!display.begin(SSD1306_SWITCHCAPVCC, oledAddress)) {
    Serial.println("SSD1306 initialization FAILED.");
    return;
  }

  oledReady = true;
  display.clearDisplay();
  display.display();
  Serial.println("SSD1306 init returned OK. Check the OLED screen!");
  Serial.println("NOTE: I2C detection does not guarantee SSD1306 driver type.");
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("ERINX ESP32D OLED TEST");
  Wire.begin(OLED_SDA, OLED_SCL);
  Wire.setClock(100000); // Sa first test, use slower 100kHz
  scanAndStart();
  lastScan = millis();
}

void loop() {
  if (!oledReady) {
    // Repeat scan periodically so the Serial Monitor can show the result.
    if (millis() - lastScan >= 3000) {
      lastScan = millis();
      scanAndStart();
    }
    delay(20);
    return;
  }

  if (millis() - lastFrame < 500) return;
  lastFrame = millis();
  frameNumber++;

  display.clearDisplay();
  display.drawRect(0, 0, 128, 64, SSD1306_WHITE);
  display.setTextColor(SSD1306_WHITE);
  display.setTextSize(1);
  display.setCursor(25, 7);
  display.println("ERINX OLED TEST");
  display.drawLine(8, 21, 119, 21, SSD1306_WHITE);
  display.setCursor(12, 27);
  display.print("Address: 0x");
  display.println(oledAddress, HEX);
  display.setCursor(12, 40);
  display.print("Counter: ");
  display.println(frameNumber);
  // Blinking indicator proves frames are updating.
  if (frameNumber % 2 == 0) {
    display.fillCircle(113, 48, 5, SSD1306_WHITE);
  } else {
    display.drawCircle(113, 48, 5, SSD1306_WHITE);
  }
  display.display();
}
