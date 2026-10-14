# Official final Arduino firmware — V5.1.3

Open **[`ERINX_Smart_Hub_V5_1_3_UI_Controls.ino`](ERINX_Smart_Hub_V5_1_3_UI_Controls/ERINX_Smart_Hub_V5_1_3_UI_Controls.ino)** in Arduino IDE, keeping `PageTypes.h` in the **same** sketch directory.

Board: ESP32S3 Dev Module (N16R8); 16 MB flash; OPI PSRAM. TFT_eSPI setup must match the connected ILI9488 TFT touchscreen. See [hardware setup](../../docs/HARDWARE_AND_SETUP.md) and [configuration notes](../../hardware/configs/README.md).

**V5.1.3 is the author's chosen final submission.** The optional Wi-Fi File Manager (V5.2) has been retained under [`firmware/experimental/`](../experimental/) so it is not mistaken for the final version.

The original V5.1.3 `.ino` and `PageTypes.h` are byte-for-byte unchanged in this repository preparation. No hardware upload or full ESP32 compiler test was performed during this GitHub review.
