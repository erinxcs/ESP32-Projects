# AMI OLED Robot Keychain

A compact ESP32-C3 animation keychain built around a 128 × 64 OLED display. A desktop converter transforms MP4 and GIF clips into monochrome bitmaps stored in the microcontroller's flash memory. A single pushbutton selects animations and controls sleep.

![Cyber Ninja enclosure concept](assets/concept-cyber-ninja.jpg)

> **Enclosure concept.** The artwork illustrates the intended appearance; the actual case uses layered 3 mm Sintra (PVC foam board) panels. Refer to the [print files](enclosure/prints/) for 1:1 patterns and verify each cutout against the assembled hardware.

## Features

- **Multi-animation playback:** up to 10 configurable clip slots; actual storage capacity depends on clip lengths and the selected flash partition.
- **MP4 / GIF converter:** 1-bit bitmap export, dithering, threshold, contrast, cropping, and per-clip preview.
- **Two OLED layouts:** reserved yellow label (`AMI`) with 128 × 48 blue animation area, or full-screen 128 × 64 playback.
- **Single-button interface:** short press for the next animation; hold for 2 seconds and release to sleep; press again to wake.
- **Battery-powered form factor:** Seeed XIAO ESP32C3 with LiPo battery pads and onboard charging circuitry; suitability of a particular cell must be checked separately.
- **DIY enclosure:** layered black Sintra board, front ninja-mask treatment, right-side USB-C opening and bottom-mounted button.

## Hardware

| Part | Specification |
| --- | --- |
| Controller | Seeed Studio XIAO ESP32C3, 4 MB flash |
| Display | 0.96-inch, 128 × 64 I2C SSD1306 OLED (yellow/blue variant) |
| Input | Normally-open momentary pushbutton |
| Power | Compatible protected 3.7 V LiPo; capacity and charge rating must be verified |
| Enclosure | 3 mm Sintra board and reinforced metal keyring attachment |

### Connections

| Peripheral | XIAO ESP32C3 |
| --- | --- |
| OLED VCC | 3V3 |
| OLED GND | GND |
| OLED SDA | D4 / GPIO6 |
| OLED SCL | D5 / GPIO7 |
| Pushbutton | D1 / GPIO3 to GND |

The button uses `INPUT_PULLUP`; an external 10 kΩ pull-up to 3V3 is recommended for reliable GPIO wake-up. Check the actual button's switched contacts before wiring. The OLED I2C address is detected at `0x3C` or `0x3D`.

## Quick start

**Requirements:** Arduino IDE 2.x, Espressif's Arduino-ESP32 board package, **Adafruit SSD1306** and **Adafruit GFX**. Select the **Seeed XIAO ESP32C3** board (or the equivalent supported profile for your installed core).

1. Wire the OLED and pushbutton as shown above. Connect USB-C for the initial test; keep the battery isolated while altering wiring.
2. Open [`firmware/AMI_OLED_Robot_Keychain/AMI_OLED_Robot_Keychain.ino`](firmware/AMI_OLED_Robot_Keychain/AMI_OLED_Robot_Keychain.ino) in Arduino IDE.
3. Compile and upload. The companion `erinxc3_animation_catalog.h` contains three demo clips: **Blinking Eyes**, **Pixel Heart**, and **Starfield**.
4. Tap to change clips. Hold for two seconds, release, and tap again to wake. Open Serial Monitor at **115200 baud** for diagnostics.

### Convert custom videos

Windows: run [`RUN_CONVERTER_WINDOWS.bat`](RUN_CONVERTER_WINDOWS.bat). The launcher locates Python 3 and installs missing dependencies.

Cross-platform:

```bash
python -m pip install -r tools/mp4_to_oled/requirements.txt
python tools/mp4_to_oled/converter.py
```

Add up to ten MP4/GIF clips, select playback settings, **Convert All Clips**, then **Export Arduino Project** to a **new empty directory**. The export creates an isolated `AMI_OLED_Robot_Keychain` sketch containing the `.ino` player and a single combined animation catalog. Do not merge exported files with older firmware folders.

For CLI conversion:

```bash
python tools/mp4_to_oled/converter.py \
  --clips samples/videos/01_Blinking_Eyes.mp4 samples/videos/02_Pixel_Heart.mp4 \
  --output exports/AMI_OLED_Robot_Keychain --fps 12 --seconds 2.5 --layout ami
```

For visual quality and memory sizing, see [Converter and storage](docs/converter.md).

## Repository layout

```text
firmware/   Current V2.2 multi-animation firmware and demo catalog
tools/      MP4/GIF-to-OLED converter (GUI and CLI)
samples/    Three example videos, a sample GIF, and previews
enclosure/  Printable sticker skins, cut templates, and previews
assets/     Prototype photos, measurement reference, and concept art
tests/      Python converter and export checks
docs/       Wiring, converter, enclosure, and troubleshooting notes
archive/    Historical diagnostics, RoboEyes prototypes, and superseded firmware
```

Only `firmware/` is the primary Arduino build. Earlier prototypes are retained for reference under [`archive/`](archive/README.md).

## Verification

- OLED detection and display output were observed on an ESP32 DevKit; the XIAO ESP32C3 was subsequently used for the working prototype.
- MP4/GIF conversion and multi-clip catalog export have automated Python tests.
- The bundled Arduino sketch has not been compiled and validated with the full current Arduino-ESP32 toolchain in this repository build. Verify and upload on the target board before final assembly.

Run the desktop-side tests with:

```bash
python -m unittest discover -s tests -v
```

## Documentation

- [Hardware and wiring](docs/hardware.md)
- [Animation converter and storage](docs/converter.md)
- [Firmware and button behavior](docs/firmware.md)
- [Sintra enclosure and printing](docs/enclosure.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Development history](docs/development-history.md)

## Safety

Deep sleep is **not** a mechanical power disconnect. Verify LiPo protection, polarity, charging current, and physical condition before use. Do not charge or work on the circuit near exposed conductive tools. A damaged or unverified salvaged battery should be replaced with a suitable protected cell. Reinforce the keyring attachment mechanically, and keep the rear panel serviceable.
