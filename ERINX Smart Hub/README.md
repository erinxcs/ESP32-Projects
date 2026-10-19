# ERINX Smart Hub

**Embedded Systems Mini Project — Carl Jayson Eli B. Bonaobra, CPE4A**

A compact, ESP32-S3-powered interactive smart display that brings together a live clock, online weather, indoor climate sensing, a JPEG photo gallery, and silent EVM video playback on a **3.5-inch 320 × 480 touchscreen**.

![ERINX Smart Hub interface preview](assets/mockups/erinx_smart_hub_dashboard.png)

> **Official final release:** **V5.1.3 — UI Controls**  
> **Target board:** ESP32-S3 CAM N16R8 (16 MB flash / 8 MB PSRAM)  
> **TFT:** 3.5-inch ILI9488, portrait (320 × 480); XPT2046-compatible touch  
> **Release scope:** Weather, clock, DHT11, Gallery, silent Video, Settings, Wi-Fi selection  
> **Verification:** Repository files and media formats checked; full Arduino build and on-device regression test are still needed for the user's hardware

## Features

- Open-Meteo weather and selectable Batangas locations.
- Philippine standard time through Wi-Fi/NTP, with a fallback while offline.
- DHT11 indoor temperature and relative humidity.
- Touch-based dashboard, animated eyes, and saved touch calibration.
- JPEG gallery, digital photo frame, and timed slideshow.
- Silent `.evm` video player using JPEG frames on microSD.
- On-screen 2.4 GHz Wi-Fi scanner and password keyboard with SHOW/HIDE.
- Preferences/NVS persistence for previously saved Wi-Fi credentials and settings.

**Scope note:** V5.1.3 does **not** have the browser-based file manager. The later V5.2 prototype is preserved separately in [`firmware/experimental/`](firmware/experimental/), but it is **not the official final build**.

## Getting started

1. Install the ESP32 board package in Arduino IDE. Select **ESP32S3 Dev Module**, **16 MB Flash**, and **OPI PSRAM**.
2. Install **TFT_eSPI**, **TJpg_Decoder**, **ArduinoJson v7**, **Adafruit DHT sensor library**, and **Adafruit Unified Sensor**.
3. Configure TFT_eSPI for your actual ILI9488/touch wiring. See [ESP32-S3 pin reference](docs/HARDWARE_AND_SETUP.md) and [config notes](hardware/configs/README.md). **Do not use the older ESP32D pin config for this board.**
4. Open [`firmware/final/ERINX_Smart_Hub_V5_1_3_UI_Controls/ERINX_Smart_Hub_V5_1_3_UI_Controls.ino`](firmware/final/ERINX_Smart_Hub_V5_1_3_UI_Controls/ERINX_Smart_Hub_V5_1_3_UI_Controls.ino). Keep `PageTypes.h` in the same folder.
5. Copy the **contents** of [`sd_card/COPY_TO_SD_ROOT/`](sd_card/COPY_TO_SD_ROOT/) to the root of a FAT32 microSD card (`/icons`, `/photos`, `/videos`).
6. Select the correct USB serial port, **Verify**, and **Upload**. Use Serial Monitor at **115200 baud** if you encounter an error.
7. Calibrate touch when prompted, select a Wi-Fi network from Settings, and test each page.

See [hardware + software setup](docs/HARDWARE_AND_SETUP.md) and [test checklist](docs/TESTING_CHECKLIST.md) for detail.

## Repository structure

```text
ERINX_Smart_Hub/
├── firmware/
│   ├── final/                 # Official V5.1.3 Arduino sketch + PageTypes.h
│   ├── experimental/          # Archived V5.2 browser file manager
│   ├── development/           # Previous version milestones
│   └── diagnostics/           # Display, touch, SDMMC, FPS tests
├── hardware/configs/         # TFT_eSPI pin setup references
├── sd_card/COPY_TO_SD_ROOT/   # RGB565 icons + sample photos/EVM
├── tools/
│   ├── photo_converter/      # JPG converter
│   └── video_converter/      # MP4/MOV/etc. to custom .evm
├── assets/                    # UI previews / editable SVG icons
└── docs/                      # Documentation, testing, history
```

## Media formats

| Media | Supported format | Suggested dimensions |
|---|---|---|
| Icons | Raw RGB565 | 40 × 40 pixels |
| Photos | **Baseline JPEG** (not progressive) | 320 × 480 pixels |
| Video | Custom silent **ERXV `.evm`** container | 240 × 360 at 7 fps default |

An ordinary `.mp4` cannot be played directly. Use the [media converter guide](tools/README.md) for photo/video formats, dependencies, commands, and output behavior. The scripts are in [`tools/video_converter/`](tools/video_converter/) and [`tools/photo_converter/`](tools/photo_converter/).

## Technical notes

- The board's built-in microSD uses SDMMC 1-bit mode, not an external SPI SD card module.
- Camera capture and Bluetooth audio are **not implemented** in V5.1.3.
- The touchscreen UI can visibly flicker on some transitions. Sprite/differential rendering improvements are possible, but not included in the final release.
- The existing weather HTTPS client uses `setInsecure()`, which disables certificate verification; use this as a learning prototype, not a hardened production appliance.
- Wi-Fi password input defaults to visible until the user toggles HIDE. Credentials are stored on-device in Preferences/NVS, not in GitHub source files.

## Documentation

- [Hardware setup and wiring](docs/HARDWARE_AND_SETUP.md)
- [Version history](docs/DEVELOPMENT_VERSIONS.md)
- [Testing checklist](docs/TESTING_CHECKLIST.md)
- [Embedded Systems paper (DOCX)](docs/ERINX_Smart_Hub_Embedded_Systems_Documentation.docx)
- [GitHub preparation audit](docs/GITHUB_RELEASE_REVIEW.md)
- [Changelog](CHANGELOG.md)

## Author

**Carl Jayson Eli B. Bonaobra** — CPE4A  
Embedded Systems Mini Project

**License:** Not assigned. If you intend to allow others to reuse the code, choose and add a license before publishing under those terms.
