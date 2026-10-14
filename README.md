# ESP32 Projects Workspace

This workspace contains three related ESP32 and embedded systems experiments:

## 1) ERINX Smart Hub

Location: `ERINX Smart Hub/`

This is the main project in the workspace. It is an ESP32-S3 smart display project with a touchscreen UI, weather data, clock, DHT11 sensor handling, gallery support, SD card media, and a silent EVM video player.

Key areas:
- `firmware/` — final and experimental Arduino source files
- `hardware/` — configuration and wiring references
- `sd_card/` — media files to copy onto the SD card
- `tools/` — photo and video conversion utilities
- `docs/` — setup, testing, and release documentation

See the project README in [ERINX Smart Hub/README.md](ERINX%20Smart%20Hub/README.md).

## 2) Face Follower Robot

Location: `Face Follower Robot/`

This project explores ESP32-CAM computer vision and face-following concepts. It includes experiments for a live camera stream and several iterations of a face-following client setup.

Key areas:
- `test.cpp` — ESP32-CAM live stream server example
- `V1/` — early face follower implementation
- `V2 new/` — newer media pipe-based client versions
- `V3/` — later experimental version

See the project README in [Face Follower Robot/README.md](Face%20Follower%20Robot/README.md).

## 3) TFT project

Location: `TFT project/`

This is a development archive and historical progression of the ERINX Smart Hub experiments. It contains early display and touch tests, weather examples, and multiple V4/V5 prototype folders.

Key areas:
- `01_` to `06_` test folders — early learning and prototype builds
- `ERINX_Smart_Hub_V5_*` folders — development releases and diagnostics
- `assets/`, `config/`, `docs/` — supporting resources

See the project README in [TFT project/README.md](TFT%20project/README.md).

## Quick start

- For the current main project: open [ERINX Smart Hub/README.md](ERINX%20Smart%20Hub/README.md)
- For the camera and vision experiments: open [Face Follower Robot/README.md](Face%20Follower%20Robot/README.md)
- For historical firmware/tests: open [TFT project/README.md](TFT%20project/README.md)

## Notes

These folders are related but represent different stages of development:
- the Smart Hub project is the most polished and documented
- the Face Follower Robot is a computer-vision experimental branch
- the TFT project is a historical archive of earlier firmware and testing iterations
