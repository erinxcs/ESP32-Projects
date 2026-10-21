/*
  ERINX Smart Hair Clip — XIAO ESP32C3 RoboEyes Test
  Board: Seeed Studio XIAO ESP32C3
  OLED: 0.96-inch SSD1306 I2C, 128x64

  OLED VCC -> XIAO 3V3
  OLED GND -> XIAO GND
  OLED SDA -> XIAO D4 (GPIO6)
  OLED SCL -> XIAO D5 (GPIO7)

  Libraries (Arduino Library Manager):
  - Adafruit SSD1306
  - Adafruit GFX Library
  - FluxGarage RoboEyes

  Serial Monitor: 115200 baud
*/

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <FluxGarage_RoboEyes.h>

constexpr int OLED_SDA = 6;  // XIAO ESP32C3 D4
constexpr int OLED_SCL = 7;  // XIAO ESP32C3 D5
constexpr int SCREEN_WIDTH = 128;
constexpr int SCREEN_HEIGHT = 64;
constexpr int OLED_RESET = -1;

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
RoboEyes<Adafruit_SSD1306> roboEyes(display);

unsigned long lastMoodChange = 0;
constexpr unsigned long MOOD_INTERVAL_MS = 5000;
uint8_t moodIndex = 0;

uint8_t findOLEDAddress() {
  Serial.println("Scanning I2C bus on GPIO6 (SDA), GPIO7 (SCL)...");
  uint8_t detected = 0;
  for (uint8_t address = 1; address < 127; ++address) {
    Wire.beginTransmission(address);
    if (Wire.endTransmission() == 0) {
      Serial.printf("I2C device found: 0x%02X\n", address);
      if (address == 0x3C || address == 0x3D) {
        detected = address;
      }
    }
  }
  return detected;
}

void selectMood(uint8_t index) {
  switch (index) {
    case 0:
      roboEyes.setMood(DEFAULT);
      Serial.println("Mood: NORMAL");
      break;
    case 1:
      roboEyes.setMood(HAPPY);
      roboEyes.anim_laugh();
      Serial.println("Mood: HAPPY");
      break;
    case 2:
      roboEyes.setMood(ANGRY);
      Serial.println("Mood: ANGRY");
      break;
    case 3:
      roboEyes.setMood(TIRED);
      Serial.println("Mood: TIRED");
      break;
    case 4:
      roboEyes.setMood(DEFAULT);
      roboEyes.anim_confused();
      Serial.println("Mood: CONFUSED");
      break;
  }
}

void setup() {
  Serial.begin(115200);
  delay(1200);
  Serial.println("\n=== ERINX XIAO ESP32C3 ROBOEYES TEST ===");

  Wire.begin(OLED_SDA, OLED_SCL);
  Wire.setClock(100000);  // Conservative I2C speed for first test

  uint8_t address = findOLEDAddress();
  if (!address) {
    Serial.println("ERROR: OLED not detected at 0x3C or 0x3D.");
    Serial.println("Check: VCC=3V3, GND, SDA=D4/GPIO6, SCL=D5/GPIO7.");
    while (true) delay(1000);
  }

  Serial.printf("Starting SSD1306 at 0x%02X...\n", address);
  if (!display.begin(SSD1306_SWITCHCAPVCC, address)) {
    Serial.println("ERROR: SSD1306 initialization failed.");
    while (true) delay(1000);
  }

  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);
  display.setTextSize(1);
  display.setCursor(18, 19);
  display.println("ERINX HAIR CLIP");
  display.setCursor(26, 37);
  display.println("ROBOEYES TEST");
  display.display();
  delay(1000);

  roboEyes.begin(SCREEN_WIDTH, SCREEN_HEIGHT, 30);
  roboEyes.setWidth(36, 36);
  roboEyes.setHeight(38, 38);
  roboEyes.setBorderradius(9, 9);
  roboEyes.setSpacebetween(10);
  roboEyes.setAutoblinker(ON, 3, 2);
  roboEyes.setIdleMode(ON, 2, 2);
  roboEyes.setCuriosity(ON);
  selectMood(moodIndex);
  lastMoodChange = millis();
  Serial.println("RoboEyes running!");
}

void loop() {
  roboEyes.update();
  if (millis() - lastMoodChange >= MOOD_INTERVAL_MS) {
    lastMoodChange = millis();
    moodIndex = (moodIndex + 1) % 5;
    selectMood(moodIndex);
  }
}
