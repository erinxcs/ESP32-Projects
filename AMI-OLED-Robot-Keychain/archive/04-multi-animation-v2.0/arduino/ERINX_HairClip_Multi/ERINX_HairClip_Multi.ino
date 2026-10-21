/*
  ERINX Smart Hair Clip V2.0 — MULTI-ANIMATION PLAYER
  Board: Seeed Studio XIAO ESP32C3 (NOT XIAO ESP32S3)
  OLED: 128x64 SSD1306 I2C; yellow top rows are the OLED panel's fixed colors.

  CONNECTIONS:
    OLED VCC -> XIAO 3V3,  OLED GND -> GND
    OLED SDA -> XIAO D4/GPIO6, OLED SCL -> XIAO D5/GPIO7
    Push-button -> XIAO D1/GPIO3 and GND (INPUT_PULLUP)

  Short press: next animation (wraps to first).
  Hold 1.2 seconds: toggle OLED sleep/wake (CPU stays running).
  Arduino libraries: Adafruit SSD1306 + Adafruit GFX Library.
  Data: animation_index.h and animation_XX.h from ERINX converter (stored in flash).

  SAFETY: USB power first. Battery connection only after cell safety checks.
*/
#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <pgmspace.h>
#include "animation_index.h"

constexpr uint8_t SCREEN_W = 128;
constexpr uint8_t SCREEN_H = 64;
constexpr int SDA_PIN = 6;             // D4 XIAO ESP32C3
constexpr int SCL_PIN = 7;             // D5 XIAO ESP32C3
constexpr int BUTTON_PIN = 3;          // D1 XIAO ESP32C3
constexpr unsigned long DEBOUNCE_MS = 35;
constexpr unsigned long LONG_PRESS_MS = 1200;

Adafruit_SSD1306 oled(SCREEN_W, SCREEN_H, &Wire, -1);
uint8_t currentClip = 0;
uint16_t currentFrame = 0;
uint32_t nextFrameMs = 0;
bool oledSleeping = false;

bool lastRawButton = HIGH;
bool stableButton = HIGH;
bool longHandled = false;
uint32_t lastBounceMs = 0;
uint32_t pressedAtMs = 0;

uint8_t detectOLED() {
  const uint8_t addresses[] = {0x3C, 0x3D};
  for (uint8_t address : addresses) {
    Wire.beginTransmission(address);
    if (Wire.endTransmission() == 0) return address;
  }
  return 0;
}

void drawHeader(const AnimationClip& clip) {
  if (!clip.showHeader) return;
  oled.setTextColor(SSD1306_WHITE);
  oled.setTextWrap(false);
  const size_t length = strlen(clip.headerText);
  // Built-in Adafruit font uses 6x8 cells; 2x size fits exactly in 16px header.
  const uint8_t size = length <= 10 ? 2 : 1;
  const int16_t width = length * 6 * size;
  const int16_t x = width <= SCREEN_W ? (SCREEN_W - width) / 2 : 0;
  oled.setTextSize(size);
  oled.setCursor(x, size == 2 ? 0 : 4);
  oled.print(clip.headerText);
}

void chooseClip(uint8_t index) {
  if (ANIMATION_COUNT == 0) return;
  currentClip = index % ANIMATION_COUNT;
  currentFrame = 0;
  nextFrameMs = millis();
  Serial.printf("Slot %u/%u: %s (%u frames @ %u FPS)\n",
     currentClip + 1, ANIMATION_COUNT, ANIMATIONS[currentClip].title,
     ANIMATIONS[currentClip].frameCount, ANIMATIONS[currentClip].fps);
}

void wakeOrSleep() {
  oledSleeping = !oledSleeping;
  oled.ssd1306_command(oledSleeping ? SSD1306_DISPLAYOFF : SSD1306_DISPLAYON);
  if (!oledSleeping) {
    nextFrameMs = millis();
    currentFrame = 0;
  }
  Serial.println(oledSleeping ? "DISPLAY OFF (hold to wake)" : "DISPLAY ON");
}

void pollButton() {
  const uint32_t now = millis();
  const bool raw = digitalRead(BUTTON_PIN);

  if (raw != lastRawButton) {
    lastBounceMs = now;
    lastRawButton = raw;
  }
  if ((uint32_t)(now - lastBounceMs) >= DEBOUNCE_MS && raw != stableButton) {
    stableButton = raw;
    if (stableButton == LOW) {
      pressedAtMs = now;
      longHandled = false;
    } else if (!longHandled) {
      // A short tap advances a slot. If sleeping, a tap does not turn on the OLED.
      if (!oledSleeping) chooseClip((currentClip + 1) % ANIMATION_COUNT);
    }
  }
  if (stableButton == LOW && !longHandled &&
      (uint32_t)(now - pressedAtMs) >= LONG_PRESS_MS) {
    longHandled = true;
    wakeOrSleep();
  }
}

void drawFrame() {
  if (oledSleeping || ANIMATION_COUNT == 0) return;
  const AnimationClip& clip = ANIMATIONS[currentClip];
  if (clip.frameCount == 0 || clip.fps == 0) return;
  const uint32_t now = millis();
  if ((int32_t)(now - nextFrameMs) < 0) return;
  // Schedule against the current time to recover cleanly if serial/Wire is slow.
  nextFrameMs = now + max(1UL, 1000UL / clip.fps);

  oled.clearDisplay();
  drawHeader(clip);
  const size_t byteOffset = static_cast<size_t>(currentFrame) * clip.frameBytes;
  // Adafruit drawBitmap() reads 1-bit MSB-first pixels, bytewise from PROGMEM.
  oled.drawBitmap(0, clip.yOffset, clip.data + byteOffset,
                  SCREEN_W, clip.frameHeight, SSD1306_WHITE);
  oled.display();
  ++currentFrame;
  if (currentFrame >= clip.frameCount) currentFrame = 0;
}

void setup() {
  Serial.begin(115200);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  delay(200);
  Serial.println("\nERINX Smart Hair Clip V2 | XIAO ESP32C3");
  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(400000);
  const uint8_t address = detectOLED();
  if (address == 0) {
    Serial.println("OLED NOT DETECTED: check SDA=D4/GPIO6, SCL=D5/GPIO7");
    while (true) delay(1000);
  }
  if (!oled.begin(SSD1306_SWITCHCAPVCC, address)) {
    Serial.println("OLED initialization failed");
    while (true) delay(1000);
  }
  oled.clearDisplay();
  oled.setTextSize(1);
  oled.setTextColor(SSD1306_WHITE);
  oled.setCursor(8, 22);
  oled.println("ERINX MULTI PLAYER");
  oled.setCursor(25, 36);
  oled.print(ANIMATION_COUNT);
  oled.print(" SLOTS");
  oled.display();
  delay(600);
  chooseClip(0);
  Serial.println("Button D1/GPIO3 to GND | tap=NEXT | hold=DISPLAY OFF/ON");
}

void loop() {
  pollButton();
  drawFrame();
  delay(1);
}
