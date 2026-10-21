/*
  ERINX Smart Hair Clip V2.1 - XIAO ESP32C3 + SSD1306 128x64

  Wiring (board GPIO, NOT XIAO ESP32S3):
    OLED VCC -> 3V3       GND -> GND
    OLED SDA -> D4/GPIO6  SCL -> D5/GPIO7
    BUTTON -> D1/GPIO3 and GND (normally-open pushbutton)

  SHORT press/release: next animation
  LONG  press (2s): turn OLED off; wait for release; deep sleep
  NEXT  press: wake from deep sleep (ESP reboots; resumes saved slot)

  Deep sleep does NOT physically disconnect the battery.
  Recommmended for reliable button wake: 10k pull-up from GPIO3 to 3V3.

  Libraries: Adafruit SSD1306, Adafruit GFX, ESP32 by Espressif.
  Keep animation_index.h and all animation_XX.h in this sketch folder.
*/

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <pgmspace.h>
#include <esp_sleep.h>
#include "animation_index.h"

constexpr uint8_t SCREEN_W = 128;
constexpr uint8_t SCREEN_H = 64;
constexpr int SDA_PIN = 6;       // XIAO C3 D4
constexpr int SCL_PIN = 7;       // XIAO C3 D5
constexpr int BUTTON_PIN = 3;    // XIAO C3 D1; RTC-capable wake pin
constexpr uint32_t DEBOUNCE_MS = 40;
constexpr uint32_t LONG_PRESS_MS = 2000;
constexpr uint32_t SLEEP_RELEASE_MS = 70;
constexpr uint32_t RTC_MAGIC = 0xE21C2026;

// RTC retention survives deep sleep, but NOT complete power removal.
RTC_DATA_ATTR uint32_t savedMagic = 0;
RTC_DATA_ATTR uint32_t savedClip = 0;

Adafruit_SSD1306 oled(SCREEN_W, SCREEN_H, &Wire, -1);
uint8_t currentClip = 0;
uint16_t currentFrame = 0;
uint32_t nextFrameMs = 0;

bool lastRaw = HIGH;
bool stableLevel = HIGH;
bool longHandled = false;
bool sleepPending = false;
bool ignoreWakeButton = false;
uint32_t rawChangedMs = 0;
uint32_t pressStartMs = 0;
uint32_t wakeReleasedMs = 0;

uint8_t detectOLED() {
  const uint8_t addresses[] = {0x3C, 0x3D};
  for (uint8_t address : addresses) {
    Wire.beginTransmission(address);
    if (Wire.endTransmission() == 0) return address;
  }
  return 0;
}

void drawHeader(const AnimationClip &clip) {
  if (!clip.showHeader) return;
  oled.setTextColor(SSD1306_WHITE);
  oled.setTextWrap(false);
  const size_t n = strlen(clip.headerText);
  const uint8_t fontSize = n <= 10 ? 2 : 1;
  const int16_t textWidth = (int16_t)(n * 6 * fontSize);
  oled.setTextSize(fontSize);
  oled.setCursor(textWidth <= SCREEN_W ? (SCREEN_W - textWidth) / 2 : 0,
                 fontSize == 2 ? 0 : 4);
  oled.print(clip.headerText);
}

void chooseClip(uint8_t index) {
  if (ANIMATION_COUNT == 0) return;
  currentClip = index % ANIMATION_COUNT;
  savedMagic = RTC_MAGIC;
  savedClip = currentClip;
  currentFrame = 0;
  nextFrameMs = millis();
  Serial.printf("Animation %u/%u: %s (%u frames at %u fps)\n",
                currentClip + 1, ANIMATION_COUNT, ANIMATIONS[currentClip].title,
                ANIMATIONS[currentClip].frameCount, ANIMATIONS[currentClip].fps);
}

void enterDeepSleep() {
  // Clear the OLED before sleeping: panel stays powered but display goes off.
  oled.clearDisplay();
  oled.display();
  oled.ssd1306_command(SSD1306_DISPLAYOFF);

  // Only enter after RELEASE. A LOW-level wake pressed during sleep
  // would otherwise wake the chip immediately.
  uint32_t releasedAt = 0;
  while (true) {
    if (digitalRead(BUTTON_PIN) == HIGH) {
      if (!releasedAt) releasedAt = millis();
      if ((uint32_t)(millis() - releasedAt) >= SLEEP_RELEASE_MS) break;
    } else {
      releasedAt = 0; // restart debounce after any bounce
    }
    delay(5);
  }

  savedMagic = RTC_MAGIC;
  savedClip = currentClip;
  const esp_err_t result = esp_deep_sleep_enable_gpio_wakeup(
      (1ULL << BUTTON_PIN), ESP_GPIO_WAKEUP_GPIO_LOW);

  if (result != ESP_OK) {
    Serial.printf("GPIO deep-sleep wake setup FAILED: %d\n", (int)result);
    oled.ssd1306_command(SSD1306_DISPLAYON);
    nextFrameMs = millis();
    sleepPending = false;
    return;
  }

  Serial.println("DEEP SLEEP. Tap D1/GPIO3 button to wake.");
  Serial.flush();
  delay(20);
  esp_deep_sleep_start();
}

void pollButton() {
  const uint32_t now = millis();
  const bool raw = digitalRead(BUTTON_PIN);

  // On wake, a press is already held LOW. Ignore it, including its release,
  // so the wake tap won't accidentally switch to the next animation.
  if (ignoreWakeButton) {
    if (raw == HIGH) {
      if (wakeReleasedMs == 0) wakeReleasedMs = now;
      if ((uint32_t)(now - wakeReleasedMs) >= DEBOUNCE_MS) {
        ignoreWakeButton = false;
        lastRaw = HIGH;
        stableLevel = HIGH;
        rawChangedMs = now;
        longHandled = false;
      }
    } else {
      wakeReleasedMs = 0;
    }
    return;
  }

  if (raw != lastRaw) {
    lastRaw = raw;
    rawChangedMs = now;
  }
  if (raw != stableLevel &&
      (uint32_t)(now - rawChangedMs) >= DEBOUNCE_MS) {
    stableLevel = raw;
    if (stableLevel == LOW) {
      pressStartMs = now;
      longHandled = false;
    } else {  // Stable release
      if (sleepPending) {
        enterDeepSleep();
      } else if (!longHandled) {
        if (ANIMATION_COUNT > 0)
          chooseClip((currentClip + 1) % ANIMATION_COUNT);
      }
    }
  }
  if (!sleepPending && stableLevel == LOW && !longHandled &&
      (uint32_t)(now - pressStartMs) >= LONG_PRESS_MS) {
    longHandled = true;
    sleepPending = true;
    Serial.println("Long press detected. RELEASE button to sleep...");
    // Show immediate power-off visual feedback; deep sleep after release.
    oled.ssd1306_command(SSD1306_DISPLAYOFF);
  }
}

void drawFrame() {
  if (sleepPending || ANIMATION_COUNT == 0) return;
  const AnimationClip &clip = ANIMATIONS[currentClip];
  if (clip.frameCount == 0 || clip.fps == 0) return;
  const uint32_t now = millis();
  if ((int32_t)(now - nextFrameMs) < 0) return;
  nextFrameMs = now + max(1UL, 1000UL / clip.fps);

  oled.clearDisplay();
  drawHeader(clip);
  const size_t byteOffset = (size_t)currentFrame * clip.frameBytes;
  oled.drawBitmap(0, clip.yOffset, clip.data + byteOffset,
                  SCREEN_W, clip.frameHeight, SSD1306_WHITE);
  oled.display();

  if (++currentFrame >= clip.frameCount) currentFrame = 0;
}

void setup() {
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  Serial.begin(115200);
  delay(150);   // NEVER wait for Serial; battery-powered wake must boot too.

  const bool wokeFromButton =
      esp_sleep_get_wakeup_cause() == ESP_SLEEP_WAKEUP_GPIO;
  ignoreWakeButton = wokeFromButton && digitalRead(BUTTON_PIN) == LOW;
  lastRaw = digitalRead(BUTTON_PIN);
  stableLevel = lastRaw;
  rawChangedMs = millis();

  Serial.println("\nERINX Hair Clip V2.1 | XIAO ESP32C3");
  Serial.println(wokeFromButton ? "WAKE: GPIO button" : "COLD BOOT / RESET");
  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(400000);
  uint8_t address = detectOLED();
  if (!address) {
    Serial.println("OLED NOT FOUND. SDA=D4/GPIO6, SCL=D5/GPIO7");
    while (true) delay(1000);
  }
  if (!oled.begin(SSD1306_SWITCHCAPVCC, address)) {
    Serial.println("OLED init failed");
    while (true) delay(1000);
  }

  oled.clearDisplay();
  oled.setTextColor(SSD1306_WHITE);
  oled.setTextSize(1);
  oled.setCursor(13, 20);
  oled.println("ERINX HAIR CLIP");
  oled.setCursor(11, 36);
  oled.println("V2.1  POWER SAVE");
  oled.display();
  delay(450);

  if (wokeFromButton && savedMagic == RTC_MAGIC &&
      savedClip < ANIMATION_COUNT) {
    chooseClip((uint8_t)savedClip);
  } else {
    chooseClip(0);
  }
  Serial.println("Tap = NEXT | Hold 2 sec + RELEASE = SLEEP | Tap = WAKE");
}

void loop() {
  pollButton();
  drawFrame();
  delay(1);
}
