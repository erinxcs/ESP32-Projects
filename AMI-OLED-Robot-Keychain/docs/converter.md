# Animation conversion

The desktop converter is located at `tools/mp4_to_oled/converter.py` and supports MP4, MOV, AVI, MKV, WEBM and GIF input (subject to the installed video codecs). It provides cropping/contain, monochrome threshold, contrast, dithering, inversion, preview, ordering and multi-clip export.

## Suggested defaults

| Setting | Header layout | Full-screen layout |
| --- | --- | --- |
| Frame size | 128 × 48 pixels | 128 × 64 pixels |
| Physical location | OLED rows 16–63 | OLED rows 0–63 |
| Starting FPS | 12 | 12 |
| Duration/clip | 5–8 seconds | 5–8 seconds |
| Framing | Crop for arbitrary video; contain for 8:3 source | Depends on source ratio |
| Label | `AMI` in top 16 rows | No reserved label |

A video edited specifically for the blue zone can use an **8:3** canvas (for example, 1280 × 480). Cropping a 4:3 clip to 8:3 fills the width but removes some image content. For full-screen content, export a 2:1 canvas if preserving aspect ratio is important.

## Estimating program storage

The animation catalog stores uncompressed 1-bit images:

- Header layout: `128 × 48 / 8 = 768 bytes/frame` (0.75 KiB).
- Full-screen layout: `128 × 64 / 8 = 1024 bytes/frame` (1 KiB).

`bytes = frame_count × bytes_per_frame`; `frame_count ≈ seconds × FPS`.

Six 8-second clips at 12 FPS use **432 KiB** in header layout or **576 KiB** full-screen, excluding compiled firmware and padding. The UI's **950 KiB** warning threshold is a *caution threshold*, not the ESP32's guaranteed maximum. Available flash depends on the compiled sketch and configured partition table. Verify Arduino IDE's **Sketch uses ... Maximum is ...** output for the final decision.

## Export layout

Only one source catalog is generated:

```text
AMI_OLED_Robot_Keychain/
├── AMI_OLED_Robot_Keychain.ino
└── erinxc3_animation_catalog.h
```

The converter actively rejects unexpected files when exporting into an existing sketch directory, avoiding duplicate macro and symbol definitions from earlier layouts.

## Tests

```bash
python -m pip install -r tools/mp4_to_oled/requirements.txt
python -m unittest discover -s tests -v
```
