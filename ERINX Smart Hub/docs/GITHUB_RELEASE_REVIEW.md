# GitHub Release Review — ERINX Smart Hub

**Official version:** V5.1.3 (chosen by the project owner).

## Findings and adjustments

1. The original ZIP advertised V5.2 as the recommended release despite the V5.1.3 final project choice. Updated root `README.md` and `firmware/final/README.md` to highlight V5.1.3.
2. Preserved V5.2 without deletion under `firmware/experimental/` and corrected links and manifest paths.
3. Preserved the official V5.1.3 sketch and `PageTypes.h` byte-for-byte without firmware modification.
4. Clarified that an older config file belongs to ESP32D and must **not** be installed for ESP32-S3.
5. Repaired archived Markdown links and removed a link to a non-included parent `TFT project` folder.
6. Replaced a V5.2-only testing checklist with one for the official V5.1.3 submission.
7. Checked the archive integrity, included samples, and for obvious plaintext Wi-Fi credentials; no obvious real credentials or corrupted media found.

## Files required for compiling official V5.1.3

- `firmware/final/ERINX_Smart_Hub_V5_1_3_UI_Controls/ERINX_Smart_Hub_V5_1_3_UI_Controls.ino`
- `firmware/final/ERINX_Smart_Hub_V5_1_3_UI_Controls/PageTypes.h`
- TFT_eSPI correctly configured outside the sketch for the actual board/display.
- Required Arduino libraries as in the root README.

## Known limitations / before submission

- This review did not execute the Arduino compiler or physically test the board: run Arduino IDE Verify / Upload on the project's hardware.
- Sample media files are valid, but correct behavior of the mounted SD card still requires device testing.
- V5.1.3 does not implement the browser File Manager, and does not play raw MP4 files or produce camera photos.
- Wi-Fi password text is visible by default on the touchscreen until the HIDE toggle is used. The firmware weather HTTPS client uses `setInsecure()`.
- There is no explicit license yet.
- Consider attaching actual build / runtime screenshots in `docs/` and marking verified functional tests in the checklist.
