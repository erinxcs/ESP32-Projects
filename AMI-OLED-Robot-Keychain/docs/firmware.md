# Firmware

**Active sketch:** `firmware/AMI_OLED_Robot_Keychain/AMI_OLED_Robot_Keychain.ino`

The player uses a generated animation catalog compiled into flash. Each catalog entry contains a bitmap pointer, frame count, frame rate, bytes per frame, display offset, header visibility, and a clip label. Bitmaps use one bit per pixel, MSB-first row packing, compatible with `Adafruit_SSD1306::drawBitmap()`.

## Controls

| Action | Response |
| --- | --- |
| Tap and release | Advance to the next animation; wrap to the first after the final slot |
| Press and hold 2 s, then release | Turn OLED off and request ESP32-C3 GPIO-wake deep sleep |
| Tap while sleeping | Wake and restart the player on the previously selected slot |

The selected clip index is stored in RTC-retained memory and survives supported deep-sleep wake cycles, not a full battery disconnect. Deep sleep significantly reduces MCU consumption but does not disconnect the battery from peripheral circuitry.

## Timing and storage

Playback uses `millis()`-based frame scheduling. The bundled demo runs 12 FPS, with 30 frames per clip. OLED frame transport over I2C and library overhead may limit practical playback at higher frame rates.

The sketch auto-detects OLED addresses `0x3C` and `0x3D`. The selected board must be an ESP32-C3 with a compatible Arduino-ESP32 API for GPIO deep-sleep wake. Confirm compilation using the installed Espressif core version; stub-based C++ syntax checks do not establish board-toolchain compatibility.

## Updating animations

Use the converter export to produce the **two-file** Arduino sketch in a separate directory. The previous per-clip `animation_01.h`, `animation_index.h` layout is obsolete and must not be mixed into the current sketch folder.
