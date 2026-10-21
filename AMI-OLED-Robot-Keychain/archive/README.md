# Archived prototypes

These source files document the firmware's development and are **not** part of the active Arduino build. Each version should be opened separately. Do not copy archival animation headers into the current `firmware/AMI_OLED_Robot_Keychain/` directory.

| Folder | Content | Notes |
| --- | --- | --- |
| `01-oled-diagnostics/` | First SSD1306 scanner and ESP32 DevKit display tests | The initial XIAO diagnostic targets S3 pins, not C3 pins |
| `02-roboeyes/` | RoboEyes library sketches and dual-color experiments | Some initial examples target XIAO ESP32S3; check board before uploading |
| `03-single-animation/` | Original single-clip converter and playback firmware | Uses a standalone `animation.h` |
| `04-multi-animation-v2.0/` | First multi-clip exporter, individual headers, button input | Superseded by combined catalog; may produce symbol/constant collisions if mixed |
| `05-deep-sleep-v2.1/` | Pre-consolidation deep-sleep firmware and converter | Kept for code history; known legacy header layout |

See [`docs/development-history.md`](../docs/development-history.md) for the feature progression.
