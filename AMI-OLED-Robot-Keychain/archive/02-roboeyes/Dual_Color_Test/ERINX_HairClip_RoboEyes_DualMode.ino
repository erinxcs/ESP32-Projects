/*
  ERINX SMART HAIR CLIP - ROBOEYES DUAL MODE TEST
  Hardware: Seeed XIAO ESP32C3 + SSD1306 128x64 I2C OLED
  Panel: two-color yellow (top ~16 rows) / blue (bottom ~48 rows)

  Mode A: Yellow status strip + BLUE RoboEyes
  Mode B: Blue-only RoboEyes (yellow rows forced OFF)
  Automatically switches A <-> B every 12 seconds.

  Serial Monitor (115200):
    A = show accent mode
    B = show blue-only mode
    N = switch to next mood

  Libraries from Arduino Library Manager:
  - Adafruit GFX Library
  - Adafruit SSD1306
  - FluxGarage RoboEyes (v1.1+)

  Wiring XIAO ESP32C3 -> OLED:
  3V3 -> VCC; GND -> GND; D4/GPIO6 -> SDA; D5/GPIO7 -> SCL
*/

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <FluxGarage_RoboEyes.h>

constexpr uint8_t PIN_SDA = 6;          // XIAO ESP32C3 D4
constexpr uint8_t PIN_SCL = 7;          // XIAO ESP32C3 D5
constexpr uint8_t OLED_WIDTH = 128;
constexpr uint8_t OLED_HEIGHT = 64;
constexpr int8_t OLED_RESET = -1;
constexpr uint8_t YELLOW_ROWS = 16;     // Adjust if your panel split differs

constexpr unsigned long MODE_INTERVAL = 12000UL;
constexpr unsigned long MOOD_INTERVAL = 3000UL;
constexpr unsigned long GAZE_INTERVAL = 2500UL;

enum ViewMode : uint8_t { ACCENT = 0, BLUE_ONLY = 1 };
ViewMode viewMode = ACCENT;
uint8_t moodIndex = 0;
const char* moodLabel = "IDLE";

// The RoboEyes library calls display.display() itself.
// By passing this subclass as the display type, our display() adds the
// two-color layout to the framebuffer BEFORE the SINGLE OLED transfer.
// This avoids flashing yellow pixels during blue-only mode.
class HairClipOLED : public Adafruit_SSD1306 {
public:
  HairClipOLED(uint8_t w, uint8_t h, TwoWire* bus, int8_t rst)
    : Adafruit_SSD1306(w, h, bus, rst) {}

  void display() {
    // Clear the fixed yellow part, even if the eyes happened to reach it.
    fillRect(0, 0, OLED_WIDTH, YELLOW_ROWS, SSD1306_BLACK);

    if (viewMode == ACCENT) {
      setTextSize(1);
      setTextColor(SSD1306_WHITE);
      setTextWrap(false);
      setCursor(3, 3);
      print(F("ERINX"));

      // Animated yellow status dot
      if (((millis() / 550UL) % 2UL) == 0UL) {
        fillCircle(67, 7, 2, SSD1306_WHITE);
      }

      setCursor(88, 3);
      print(moodLabel);
      drawFastHLine(0, YELLOW_ROWS - 1, OLED_WIDTH, SSD1306_WHITE);
    }

    Adafruit_SSD1306::display();  // Only ONE actual I2C screen refresh
  }
};

HairClipOLED oled(OLED_WIDTH, OLED_HEIGHT, &Wire, OLED_RESET);
RoboEyes<HairClipOLED> roboEyes(oled);

unsigned long lastMode = 0;
unsigned long lastMood = 0;
unsigned long lastGaze = 0;
uint8_t gazeStep = 0;

void selectMood(uint8_t index) {
  moodIndex = index % 5;

  switch (moodIndex) {
    case 0:
      moodLabel = "IDLE";
      roboEyes.setMood(DEFAULT);
      break;
    case 1:
      moodLabel = "HAPPY";
      roboEyes.setMood(HAPPY);
      roboEyes.anim_laugh();
      break;
    case 2:
      moodLabel = "ANGRY";
      roboEyes.setMood(ANGRY);
      break;
    case 3:
      moodLabel = "TIRED";
      roboEyes.setMood(TIRED);
      break;
    default:
      moodLabel = "CONF";
      roboEyes.setMood(DEFAULT);
      roboEyes.anim_confused();
      break;
  }
  Serial.print(F("Mood: "));
  Serial.println(moodLabel);
}

void chooseMode(ViewMode nextMode) {
  viewMode = nextMode;
  lastMode = millis();
  Serial.print(F("View: "));
  Serial.println(viewMode == ACCENT ? F("A - YELLOW HEADER + BLUE EYES")
                                    : F("B - BLUE EYES ONLY"));
}

uint8_t findOLED() {
  const uint8_t addresses[] = {0x3C, 0x3D};
  for (uint8_t i = 0; i < 2; ++i) {
    Wire.beginTransmission(addresses[i]);
    if (Wire.endTransmission() == 0) return addresses[i];
  }
  return 0;
}

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println(F("\n=== ERINX HAIR CLIP | ROBOEYES DUAL MODE ==="));
  Serial.println(F("XIAO ESP32C3: SDA=GPIO6, SCL=GPIO7"));

  Wire.begin(PIN_SDA, PIN_SCL);
  Wire.setClock(400000);

  const uint8_t address = findOLED();
  if (!address) {
    Serial.println(F("OLED NOT FOUND. Check power, D4/SDA, D5/SCL."));
    while (true) delay(1000);
  }
  Serial.print(F("OLED I2C address: 0x"));
  Serial.println(address, HEX);

  if (!oled.begin(SSD1306_SWITCHCAPVCC, address)) {
    Serial.println(F("OLED initialization FAILED."));
    while (true) delay(1000);
  }

  oled.setRotation(0);         // Top strip yellow, bottom blue

  // Keep the 28px-tall eyes vertically centered; their top is normally
  // at y~18, just below the yellow strip. Horizontal gaze only.
  roboEyes.begin(OLED_WIDTH, OLED_HEIGHT, 20); // 20 fps stable I2C target
  roboEyes.setWidth(36, 36);
  roboEyes.setHeight(28, 28);
  roboEyes.setBorderradius(9, 9);
  roboEyes.setSpacebetween(12);
  roboEyes.setAutoblinker(ON, 3, 1);
  roboEyes.setIdleMode(OFF);     // Prevent random eyes entering yellow zone
  roboEyes.setCuriosity(OFF);    // Prevent 8-pixel vertical eye expansion
  roboEyes.setPosition(DEFAULT);

  selectMood(0);
  chooseMode(ACCENT);
  lastMood = millis();
  lastGaze = millis();

  Serial.println(F("Serial commands: A = accent, B = blue-only, N = next mood"));
  Serial.println(F("Auto A/B switch: every 12 seconds"));
}

void loop() {
  const unsigned long now = millis();

  // Serial commands allow quick manual A/B testing.
  while (Serial.available()) {
    const char cmd = (char)Serial.read();
    if (cmd == 'a' || cmd == 'A') chooseMode(ACCENT);
    if (cmd == 'b' || cmd == 'B') chooseMode(BLUE_ONLY);
    if (cmd == 'n' || cmd == 'N') {
      selectMood(moodIndex + 1);
      lastMood = millis();
    }
  }

  if (now - lastMode >= MODE_INTERVAL) {
    chooseMode(viewMode == ACCENT ? BLUE_ONLY : ACCENT);
  }

  if (now - lastMood >= MOOD_INTERVAL) {
    lastMood = now;
    selectMood(moodIndex + 1);
  }

  // Smooth horizontal gaze, avoiding the yellow upper strip.
  if (now - lastGaze >= GAZE_INTERVAL) {
    lastGaze = now;
    gazeStep = (gazeStep + 1) % 4;
    switch (gazeStep) {
      case 0: roboEyes.setPosition(DEFAULT); break;
      case 1: roboEyes.setPosition(W);       break;
      case 2: roboEyes.setPosition(DEFAULT); break;
      case 3: roboEyes.setPosition(E);       break;
    }
  }

  roboEyes.update();  // This calls our HairClipOLED::display() when due
}
