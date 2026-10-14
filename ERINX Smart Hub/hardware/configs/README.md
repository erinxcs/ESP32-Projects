# TFT_eSPI configuration references

**Final hardware: ESP32-S3 CAM N16R8 + separate 3.5-inch ILI9488 SPI TFT**

Use **[`ERINX_V4_User_Setup.h`](ERINX_V4_User_Setup.h)** as the matching ESP32-S3 pin reference (TFT_MOSI=21, TFT_SCLK=47, TFT_CS=42, TFT_DC=41, TFT_RST=48, TOUCH_CS=2, touch MISO=1). It was created for an earlier S3 milestone, so prefer your already-verified active `TFT_eSPI/User_Setup.h` when uploading final V5.1.3. In some setups `USE_HSPI_PORT` is also needed. Ensure only one ILI9488 driver configuration is active.

`User_Setup_ESP32_ILI9488.h` is an **OLD ESP32D/DevKit example**, with MOSI=23, SCLK=18 etc. **DO NOT USE for ESP32-S3 CAM N16R8.** Kept only as a historical reference.

TFT_eSPI takes pin configuration from the library's active User_Setup. Copying a sketch alone does not configure those display pins automatically. Back up your already-working setup before making changes.
