# ERINX Smart Hub V5.1.3 — Hardware & Functional Testing Checklist

**Official final firmware:** [`firmware/final/ERINX_Smart_Hub_V5_1_3_UI_Controls/`](../firmware/final/ERINX_Smart_Hub_V5_1_3_UI_Controls/).

Record an actual **PASS / FAIL / NOT TESTED** and optionally photos/serial output. These rows are intentionally unfilled; this repository check did not run the hardware.

| ID | Test case | Expected outcome | Status |
|---|---|---|---|
| T01 | Boot on ESP32-S3 N16R8, ILI9488, XPT2046 | Home screen in portrait | NOT RECORDED |
| T02 | Calibrate and reboot | Touch calibration persists | NOT RECORDED |
| T03 | Open every home-screen page | Navigation and BACK work | NOT RECORDED |
| T04 | Read DHT11 on GPIO14 | Valid indoor temperature/humidity | NOT RECORDED |
| T05 | Scan Wi-Fi / SHOW-HIDE keyboard | Can connect to 2.4 GHz network | NOT RECORDED |
| T06 | Reboot with saved credentials | Wi-Fi reconnects automatically | NOT RECORDED |
| T07 | Choose each weather city | Appropriate city data is displayed | NOT RECORDED |
| T08 | Disconnect Wi-Fi | Offline handling visible, no crash | NOT RECORDED |
| T09 | Insert/remove microSD safely when powered off | SD status and icons reflect presence | NOT RECORDED |
| T10 | Open JPEG gallery and slideshow | Media loads and navigation works | NOT RECORDED |
| T11 | Play a valid `.evm` clip | Silent video frames render | NOT RECORDED |
| T12 | Clock and animated eyes | Time refreshes and eye movement is visible | NOT RECORDED |
| T13 | Compile V5.1.3 `.ino` with PageTypes.h | Successful Arduino IDE Verify | NOT RECORDED |
| T14 | Upload V5.1.3 | Board boots into working firmware | NOT RECORDED |

## Static checks completed for this GitHub preparation

- ZIP archive integrity: **PASS**.
- Official `.ino` and `PageTypes.h` present together: **PASS**.
- Original V5.1.3 source files preserved byte-for-byte: **PASS**.
- Sample RGB565 icon file sizes (40 × 40 × 2 = 3,200 bytes): **PASS**.
- Sample JPEG resolution and baseline encoding: **PASS**.
- Sample `.evm` ERXV header and embedded JPEG frames: **PASS**.
- Search for obvious hardcoded network credentials in code: placeholders only; **no actual credentials detected**.

**Not performed:** Full Arduino/ESP32 compilation in this environment, live device upload and a repeat of all touch/media tests. Previous V5.2 build verification does not establish that V5.1.3 was verified in this review.

## Optional V5.2 experiment

The Wi-Fi web file manager is stored under [`firmware/experimental/`](../firmware/experimental/). If you choose to test it, additionally check the local IP/PIN login, JPG/EVM upload, SD file deletion and interrupted upload recovery. These features are **not** part of official V5.1.3.
