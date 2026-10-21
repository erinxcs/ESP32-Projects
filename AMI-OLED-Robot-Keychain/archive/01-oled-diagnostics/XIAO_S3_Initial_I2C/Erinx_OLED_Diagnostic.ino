// ERINX SMART HAIR CLIP — OLED DIAGNOSTIC
// Target: Seeed Studio XIAO ESP32S3 + 0.96-inch 128x64 I2C SSD1306 OLED
// Wiring: OLED VCC -> 3V3, GND -> GND, SDA -> D4 (GPIO5), SCL -> D5 (GPIO6)
// Install via Arduino Library Manager: Adafruit SSD1306 and Adafruit GFX Library.

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

constexpr uint8_t OLED_SDA = 5;
constexpr uint8_t OLED_SCL = 6;
constexpr uint8_t OLED_WIDTH = 128;
constexpr uint8_t OLED_HEIGHT = 64;
constexpr int OLED_RESET = -1;

Adafruit_SSD1306 display(OLED_WIDTH, OLED_HEIGHT, &Wire, OLED_RESET);
bool oledReady = false;
uint8_t oledAddress = 0;
unsigned long lastScan = 0;
unsigned long lastDraw = 0;
unsigned long lastStatus = 0;
bool whiteFrame = false;

uint8_t scanForOled() {
  uint8_t firstOledAddress = 0;
  int deviceCount = 0;
  Serial.println("\nScanning I2C bus: SDA=GPIO5, SCL=GPIO6 ...");

  for (uint8_t address = 0x08; address <= 0x77; ++address) {
    Wire.beginTransmission(address);
    uint8_t result = Wire.endTransmission();
    if (result == 0) {
      ++deviceCount;
      Serial.printf("I2C device found at 0x%02X\n", address);
      if ((address == 0x3C || address == 0x3D) && firstOledAddress == 0) {
        firstOledAddress = address;
      }
    }
  }

  if (deviceCount == 0) {
    Serial.println("NO I2C DEVICES FOUND. Check VCC/GND/SDA/SCL and board model.");
  } else if (firstOledAddress == 0) {
    Serial.println("I2C found device(s), but not the expected OLED address 0x3C/0x3D.");
    Serial.println("Check OLED module type, pin labels, and controller.");
  }
  return firstOledAddress;
}

void drawMessage() {
  display.clearDisplay();
  display.drawRect(0, 0, 128, 64, SSD1306_WHITE);
  display.setTextColor(SSD1306_WHITE);
  display.setTextSize(1);
  display.setCursor(18, 10);
  display.print("ERINX OLED TEST");
  display.drawLine(8, 26, 119, 26, SSD1306_WHITE);
  display.setCursor(21, 35);
  display.print("SSD1306 128x64");
  display.setCursor(25, 49);
  display.print("I2C: 0x");
  display.print(oledAddress, HEX);
  display.display();
}

void tryStartOled() {
  oledAddress = scanForOled();
  if (oledAddress == 0) return;

  // 'false' prevents the display library from reinitializing I2C on default pins.
  oledReady = display.begin(SSD1306_SWITCHCAPVCC, oledAddress, true, false);
  if (!oledReady) {
    Serial.println("SSD1306 display.begin() FAILED (allocation/initialization).");
    return;
  }

  Serial.printf("SSD1306 init returned OK at 0x%02X\n", oledAddress);
  Serial.println("You should see a WHITE/BLUE full-screen flash, then ERINX OLED TEST.");
  Serial.println("If blank despite 0x3C/0x3D, the OLED may use an SH1106 driver.");
  display.clearDisplay();
  display.fillScreen(SSD1306_WHITE);
  display.display();
  delay(800);
  drawMessage();
  lastDraw = millis();
}

void setup() {
  Serial.begin(115200);
  delay(1200);
  Serial.println("=== ERINX OLED DIAGNOSTIC ===");
  Serial.println("Board: XIAO ESP32S3 (assumed)");
  Wire.begin(OLED_SDA, OLED_SCL);
  Wire.setClock(100000);  // Slower than 400 kHz, easier for initial wiring tests.
  delay(200);
  tryStartOled();
  lastScan = millis();
}

void loop() {
  unsigned long now = millis();

  if (!oledReady) {
    if (now - lastScan >= 3000) {
      lastScan = now;
      tryStartOled();
    }
    return;
  }

  if (now - lastDraw >= 2000) {
    lastDraw = now;
    whiteFrame = !whiteFrame;
    if (whiteFrame) {
      display.fillScreen(SSD1306_WHITE);
      display.display();
    } else {
      drawMessage();
    }
  }

  if (now - lastStatus >= 5000) {
    lastStatus = now;
    Serial.printf("Running. I2C OLED address: 0x%02X (expected visual flash/text)\n", oledAddress);
  }
}
