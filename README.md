# ESP32 Projects

This repository contains ESP32 projects and experiments, including a touchscreen smart display, an ESP32-CAM face-following robot, and earlier display prototypes.

## Projects

### ERINX Smart Hub

An ESP32-S3 touchscreen display project with weather, a clock, DHT11 climate readings, a photo gallery, and silent video playback.

- **Start here:** [Project README](ERINX%20Smart%20Hub/README.md)
- **Documented final release:** V5.1.3 UI Controls
- **Firmware:** [Final firmware folder](ERINX%20Smart%20Hub/firmware/final/)
- **Setup:** [Hardware and software guide](ERINX%20Smart%20Hub/docs/HARDWARE_AND_SETUP.md)
- **Testing:** [Test checklist](ERINX%20Smart%20Hub/docs/TESTING_CHECKLIST.md)

The V5.2 browser-based file manager is an experimental build. See the project README for version details and instructions.

### AMI OLED Robot Keychain

A compact ESP32-C3 keychain project with a 128 × 64 OLED display, a single-button interface, and a desktop converter for custom MP4/GIF animations.

- **Start here:** [Project README](AMI-OLED-Robot-Keychain/README.md)
- **Hardware:** Seeed XIAO ESP32C3, SSD1306 OLED, pushbutton, and compatible LiPo battery
- **Includes:** Arduino firmware, animation converter, sample clips, and printable enclosure files

### Face Follower Robot

ESP32-CAM streaming and face-tracking experiments, with several firmware and client iterations.

- **Start here:** [Project README](Face%20Follower%20Robot/README.md)
- **Versions:** `V1/`, `V2 new/`, and `V3/`

These are prototypes and may require changes for your hardware, Wi-Fi network, and installed dependencies.

### TFT Project Archive

An archive of earlier display tests and ERINX Smart Hub V4/V5 development packages.

- **Start here:** [Archive README](TFT%20project/README.md)
- Browse the archive for historical firmware, diagnostics, wiring notes, and assets.

## Getting started

1. Pick a project and read its README.
2. Check the board, wiring, libraries, and setup instructions before compiling or uploading.
3. Keep personal credentials, such as Wi-Fi passwords, out of source files and commits.

The Smart Hub has the most complete setup documentation. The Face Follower Robot and TFT archive contain experimental or historical work.
