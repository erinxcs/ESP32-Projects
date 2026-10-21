# Development history

| Stage | Milestone | Result |
| --- | --- | --- |
| Initial display validation | SSD1306 text, shapes and I2C scan on ESP32 DevKit | OLED communication and panel operation verified |
| Board migration | XIAO ESP32C3 GPIO correction | Changed SDA/SCL to GPIO6/GPIO7 after initial XIAO ESP32S3-oriented diagnostic mappings failed on the C3 |
| RoboEyes experiments | Dynamic expressions, blinking and two-color region handling | Confirmed 128 × 64 eye animations on XIAO C3 |
| V1 | Single MP4/GIF-to-bitmap conversion and looping playback | Initial Python converter, preview and Arduino `animation.h` player |
| V1.1 | Scrollable Python GUI | Improved usability on lower-resolution Windows displays |
| V2.0 | Multi-clip playback | Ten-slot UI, button-controlled switching, generated per-animation headers |
| V2.1 | Power management | Two-second long press, OLED blanking, deep-sleep wake via GPIO3, selected-slot retention |
| V2.2 | Catalog consolidation | Single `erinxc3_animation_catalog.h`; avoids undefined animation symbols and duplicate size constants |
| Current enclosure iteration | OLED cyber-ninja keychain | 3 mm Sintra-board box, right-side USB-C, underside button, printable skins and panel templates |

Older sketches and converters are kept in `archive/` as development references. The V2.2 sketch under `firmware/` is the active version.
