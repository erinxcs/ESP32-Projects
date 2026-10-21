// Auto-generated ERINX Multi Animation Catalog. Do not edit by hand.
#pragma once
#include <Arduino.h>
#include <pgmspace.h>
#include "animation_01.h"
#include "animation_02.h"
#include "animation_03.h"

struct AnimationClip {
  const uint8_t* data;
  uint16_t frameCount;
  uint8_t fps;
  uint8_t frameHeight;
  uint16_t frameBytes;
  uint8_t yOffset;
  bool showHeader;
  const char* headerText;
  const char* title;
};
constexpr uint8_t ANIMATION_COUNT = 3;
const AnimationClip ANIMATIONS[ANIMATION_COUNT] = {
  {ERINX_CLIP_01, 30, 12, 48, 768, 16, true, "AMI", "01_Blinking_Eyes"},
  {ERINX_CLIP_02, 30, 12, 48, 768, 16, true, "AMI", "02_Pixel_Heart"},
  {ERINX_CLIP_03, 30, 12, 48, 768, 16, true, "AMI", "03_Starfield"},
};
