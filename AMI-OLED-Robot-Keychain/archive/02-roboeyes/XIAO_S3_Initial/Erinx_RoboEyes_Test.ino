/*
  ERINX SMART HAIR CLIP V1.0 - ROBOEYES TEST
  Board: Seeed Studio XIAO ESP32S3
  Display: 0.96-inch SSD1306 I2C, 128 x 64 pixels

  OLED VCC -> XIAO 3V3
  OLED GND -> XIAO GND
  OLED SDA -> XIAO D4 / GPIO5
  OLED SCL -> XIAO D5 / GPIO6

  Libraries (Arduino Library Manager):
    - FluxGarage RoboEyes
    - Adafruit SSD1306
    - Adafruit GFX Library

  The sketch cycles automatically through moods every 5 seconds.
*/

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <FluxGarage_RoboEyes.h>

// XIAO ESP32S3 I2C GPIO numbers (change if using a different board)
#define OLED_SDA 5
#define OLED_SCL 6
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
RoboEyes<Adafruit_SSD1306> roboEyes(display);

const unsigned long MOOD_DURATION_MS = 5000;
unsigned long lastMoodChange = 0;
uint8_t currentMood = 0;

void selectMood(uint8_t mood) {
  switch (mood) {
    case 0:
      roboEyes.setMood(DEFAULT);
      Serial.println("[RoboEyes] NORMAL / IDLE");
      break;
    case 1:
      roboEyes.setMood(HAPPY);
      roboEyes.anim_laugh();
      Serial.println("[RoboEyes] HAPPY / LAUGH");
      break;
    case 2:
      roboEyes.setMood(ANGRY);
      Serial.println("[RoboEyes] ANGRY");
      break;
    case 3:
      roboEyes.setMood(TIRED);
      Serial.println("[RoboEyes] TIRED");
      break;
    case 4:
      roboEyes.setMood(DEFAULT);
      roboEyes.anim_confused();
      Serial.println("[RoboEyes] CONFUSED");
      break;
  }
}

void setup() {
  Serial.begin(115200);
  Wire.begin(OLED_SDA, OLED_SCL);
  Wire.setClock(400000);

  // The usual SSD1306 I2C address is 0x3C; some modules use 0x3D.
  uint8_t address = 0x3C;
  Wire.beginTransmission(address);
  if (Wire.endTransmission() != 0) {
    address = 0x3D;
    Wire.beginTransmission(address);
    if (Wire.endTransmission() != 0) {
      Serial.println("OLED not detected at 0x3C or 0x3D.");
      Serial.println("Check VCC/GND/SDA/SCL and the display driver.");
      while (true) { delay(1000); }
    }
  }

  if (!display.begin(SSD1306_SWITCHCAPVCC, address)) {
    Serial.println("SSD1306 initialization failed.");
    while (true) { delay(1000); }
  }

  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(10, 20);
  display.println("ERINX HAIR CLIP");
  display.setCursor(22, 36);
  display.println("ROBOEYES V1");
  display.display();
  delay(850); // Only during startup; no delay in loop.

  roboEyes.begin(SCREEN_WIDTH, SCREEN_HEIGHT, 30); // 30 FPS target for I2C OLED
  roboEyes.setWidth(36, 36);
  roboEyes.setHeight(38, 38);
  roboEyes.setBorderradius(9, 9);
  roboEyes.setSpacebetween(10);
  roboEyes.setAutoblinker(ON, 3, 2); // Auto blink every 3 sec +/- variation
  roboEyes.setIdleMode(ON, 2, 2);    // Randomly look around
  roboEyes.setCuriosity(ON);
  selectMood(currentMood);
  lastMoodChange = millis();
  Serial.println("ERINX RoboEyes test running.");
}

void loop() {
  roboEyes.update(); // Keep running continuously for smooth eye animations.

  if (millis() - lastMoodChange >= MOOD_DURATION_MS) {
    lastMoodChange = millis();
    currentMood = (currentMood + 1) % 5;
    selectMood(currentMood);
  }
}
