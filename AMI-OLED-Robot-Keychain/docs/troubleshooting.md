# Troubleshooting

| Symptom | Check |
| --- | --- |
| I2C scanner reports no devices | Verify OLED 3V3/GND, actual pin labels, solder joints, and the C3 mapping SDA GPIO6 / SCL GPIO7. Try 100 kHz I2C during diagnosis. |
| OLED works on ESP32 DevKit but not XIAO | Do not reuse DevKit GPIO21/22 or XIAO S3 GPIO5/6 on XIAO ESP32C3. |
| I2C address detected, display stays dark | Confirm OLED controller (SSD1306 vs SH1106), correct power and display initialization. |
| Compilation errors: `ERINX_CLIP_01` or `ANIM_WIDTH` redefined | Old V2 per-clip headers mixed with the current combined catalog. Export into a completely new sketch directory. |
| Converted animation appears small | For header mode, use 8:3 source composition, or select Crop to fill 128 × 48. |
| Video image appears negative | Adjust Invert. A white background often appears as a lit rectangle in 1-bit OLED output. |
| Too many frames / program too large | Reduce frame rate, duration, or number of clips. The 950 KiB warning is not a physical memory cap. |
| Button skips multiple clips | Verify switched contacts, GPIO3 wiring and debounce logic. |
| Deep sleep works but wakes unreliably | Verify the pull-up, ESP32 core wake API and that the button is released before entering sleep. |
| Converter window clips buttons | The current Tk interface uses a scrollable body and a persistent bottom action area. |

For board faults, start with `archive/01-oled-diagnostics`. If the panel has a different controller, adapt the firmware display driver before using the animation player.
