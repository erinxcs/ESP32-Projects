# Media converters

These PC tools prepare photos and videos for the ERINX Smart Hub's microSD card. They require Python 3 and Pillow; the video converter also requires FFmpeg available on `PATH`.

Install Pillow with:

```powershell
python -m pip install Pillow
```

## Photos

Convert JPG, PNG, WebP, BMP, or TIFF files into 320 × 480 baseline JPEGs. The converter keeps the full image and fills unused space with a dark background.

```powershell
python "ERINX Smart Hub/tools/photo_converter/convert_photos.py" "C:\Users\you\Pictures" "E:\photos"
```

The output folder can be a staging folder or the SD card's `/photos` folder. Files are named `PIC_001.jpg`, `PIC_002.jpg`, and so on, in sorted input order. Existing output files are skipped by default. Pass `--overwrite` after the two folder arguments to replace them.

## Videos

Convert MP4, MOV, AVI, MKV, WebM, M4V, or GIF files into the Smart Hub's silent `.evm` format. Install FFmpeg and make sure `ffmpeg` runs from PowerShell. On Windows, one install option is `winget install Gyan.FFmpeg`; restart PowerShell after installing.

```powershell
python "ERINX Smart Hub/tools/video_converter/convert_videos.py" "C:\Users\you\Videos" "E:\videos"
```

The defaults are 240 × 360 pixels, 7 frames per second, and at most 12 seconds per clip. For example, add `--seconds 20 --fps 8` after the folder arguments to change the duration and frame rate. Existing `.evm` files are skipped by default; add `--overwrite` to replace them. The converter writes to a temporary file and replaces the destination only after a successful conversion. If two input videos have the same filename stem, convert them in separate runs to avoid an output name collision.

Copy the resulting files to the SD card's `/photos` and `/videos` folders. Safely power off the ESP32-S3 before inserting or removing the card, then restart it so the firmware detects the card.
