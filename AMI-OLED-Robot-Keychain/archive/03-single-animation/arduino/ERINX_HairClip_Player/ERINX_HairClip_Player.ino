/*
  ERINX SMART HAIR CLIP | MP4-to-OLED player | XIAO ESP32C3
  OLED: 128x64 SSD1306 (dual-color yellow/blue or monochrome)

  Wiring:
  SSD1306 VCC -> 3V3, GND -> GND
  SSD1306 SDA -> XIAO C3 D4 / GPIO6
  SSD1306 SCL -> XIAO C3 D5 / GPIO7

  Install libraries: Adafruit SSD1306 + Adafruit GFX
  The MP4 converter generates animation.h in THIS sketch folder.
*/
#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <pgmspace.h>
#include "animation.h"

constexpr int OLED_SDA = 6; // XIAO ESP32C3 D4
constexpr int OLED_SCL = 7; // XIAO ESP32C3 D5
constexpr int OLED_RESET = -1;
constexpr uint8_t SCREEN_WIDTH = 128;
constexpr uint8_t SCREEN_HEIGHT = 64;

Adafruit_SSD1306 oled(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
uint16_t frameIndex = 0;
uint32_t nextFrameMs = 0;

void drawHeader() {
  if (!ANIM_SHOW_HEADER) return;
  // The physical display panel automatically makes the first 16px yellow.
  oled.setTextColor(SSD1306_WHITE);
  oled.setTextWrap(false);
  const size_t length = strlen(ANIM_HEADER_TEXT);
  const uint8_t scale = (length <= 10) ? 2 : 1;
  const int textW = length * 6 * scale;
  const int x = max(0, (SCREEN_WIDTH - textW) / 2);
  oled.setTextSize(scale);
  oled.setCursor(x, scale == 2 ? 0 : 4);
  oled.print(ANIM_HEADER_TEXT);
  // Yellow accent lines, only if there's room beside the name
  if (x >= 17) {
    oled.drawLine(5, 8, x-8, 8, SSD1306_WHITE);
    oled.drawLine(SCREEN_WIDTH-x+7, 8, SCREEN_WIDTH-6, 8, SSD1306_WHITE);
  }
}

uint8_t detectDisplayAddress() {
  const uint8_t addresses[] = {0x3C, 0x3D};
  for (uint8_t addr : addresses) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() == 0) return addr;
  }
  return 0;
}

void setup() {
  Serial.begin(115200);
  delay(300);
  Serial.println("\nERINX Hair Clip animation player");
  Wire.begin(OLED_SDA, OLED_SCL);
  Wire.setClock(400000);
  uint8_t address = detectDisplayAddress();
  if (!address) {
    Serial.println("OLED NOT FOUND. Check SDA=D4 GPIO6, SCL=D5 GPIO7.");
    while (true) delay(1000);
  }
  if (!oled.begin(SSD1306_SWITCHCAPVCC, address)) {
    Serial.println("OLED initialization failed");
    while (true) delay(1000);
  }
  oled.setRotation(0);
  oled.clearDisplay();
  oled.setTextSize(1);
  oled.setTextColor(SSD1306_WHITE);
  oled.setCursor(4, 24);
  oled.print("ERINX LOADING...");
  oled.display();
  delay(400);
  Serial.printf("OLED 0x%02X | %u frames | %u FPS | %u bytes/frame\n",
                address, ANIM_FRAME_COUNT, ANIM_FPS, ANIM_FRAME_BYTES);
  Serial.println(ANIM_SHOW_HEADER ? "AMI HEADER mode" : "FULL SCREEN mode");
  nextFrameMs = millis();
}

void loop() {
  const uint32_t now = millis();
  const uint32_t intervalMs = max(1U, 1000U / ANIM_FPS);
  if ((int32_t)(now - nextFrameMs) < 0) return;
  nextFrameMs = now + intervalMs;

  oled.clearDisplay();
  drawHeader();
  // drawBitmap expects 1-bit MSB-first bytes: exactly what converter.py creates
  const size_t offset = static_cast<size_t>(frameIndex) * ANIM_FRAME_BYTES;
  oled.drawBitmap(0, ANIM_Y_OFFSET, ANIM_FRAMES + offset,
                  ANIM_WIDTH, ANIM_FRAME_HEIGHT, SSD1306_WHITE);
  oled.display();

  frameIndex++;
  if (frameIndex >= ANIM_FRAME_COUNT) frameIndex = 0;
}
