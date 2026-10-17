# ESP32 Projects

A collection of ESP32 and embedded systems projects, from a touchscreen smart display to ESP32-CAM experiments.

## Projects

### ERINX Smart Hub

The organized project for an ESP32-S3 touchscreen display with weather, clock, indoor climate sensing, photo gallery, and silent video playback.

- **Recommended starting point:** [Project guide](ERINX%20Smart%20Hub/README.md)
- **Official final release:** V5.1.3 UI Controls
- **Firmware:** [`firmware/final/`](ERINX%20Smart%20Hub/firmware/final/)
- **Setup and testing:** [Hardware and software setup](ERINX%20Smart%20Hub/docs/HARDWARE_AND_SETUP.md) · [Testing checklist](ERINX%20Smart%20Hub/docs/TESTING_CHECKLIST.md)
- **V5.2 browser file manager:** preserved as an experimental build; it is not the official final release.

### Face Follower Robot

ESP32-CAM streaming and face-tracking prototypes, with several firmware and client iterations.

- **Recommended starting point:** [Project guide](Face%20Follower%20Robot/README.md)
- Browse `V1/`, `V2 new/`, and `V3/` for the different experiments.
- These versions are prototypes and may need hardware, network, or dependency setup.

### TFT Project Archive

Historical display tests and packaged ERINX Smart Hub V4/V5 development builds. Use this archive to compare earlier versions; use the organized Smart Hub project for the documented V5.1.3 release.

- **Recommended starting point:** [Archive guide](TFT%20project/README.md)
- Find early tests, versioned firmware packages, diagnostics, and historical assets here.

## Quick start

1. Choose a project above and open its guide.
2. Check its hardware, library, and setup requirements before building or uploading firmware.
3. Keep Wi-Fi credentials and other personal secrets out of committed source files.

Each project has its own setup and maturity level. The Smart Hub is the most fully documented; the Face Follower and TFT archive contain experimental and historical work.
