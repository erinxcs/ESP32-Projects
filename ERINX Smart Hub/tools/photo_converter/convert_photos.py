r"""ERINX V4.9 - Convert your images to 320x480 baseline JPEG for ESP32-S3.
Requires: python -m pip install pillow
Run: python convert_photos.py "C:\Users\you\Pictures" "E:\photos"
The destination must be your SD card's /photos folder or a staging folder.
"""
from pathlib import Path
from PIL import Image, ImageOps
import argparse

IMAGE_TYPES = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'}


def main() -> int:
    parser = argparse.ArgumentParser(description='Convert images to 320x480 baseline JPEG for ERINX Smart Hub')
    parser.add_argument('input_folder', help='folder containing source images')
    parser.add_argument('output_folder', help='destination folder, such as the SD card /photos folder')
    parser.add_argument('--overwrite', action='store_true',
                        help='replace existing PIC_NNN.jpg files (default: skip them)')
    args = parser.parse_args()

    source = Path(args.input_folder).expanduser().resolve()
    target = Path(args.output_folder).expanduser().resolve()
    if not source.is_dir():
        parser.error(f'input folder does not exist or is not a directory: {source}')
    if source == target:
        parser.error('input and output folders must be different')

    inputs = [path for path in sorted(source.iterdir())
              if path.is_file() and path.suffix.lower() in IMAGE_TYPES]
    if not inputs:
        print(f'No supported images found in {source}')
        return 1

    target.mkdir(parents=True, exist_ok=True)
    count = skipped = failures = 0
    for index, input_file in enumerate(inputs, start=1):
        filename = f'PIC_{index:03d}.jpg'
        output_file = target / filename
        if output_file.exists() and not args.overwrite:
            print(f'SKIPPED existing output (use --overwrite to replace): {filename}')
            skipped += 1
            continue
        temporary_file = output_file.with_name(output_file.name + '.tmp')
        try:
            with Image.open(input_file) as raw:
                image = ImageOps.exif_transpose(raw).convert('RGB')
                # Keep whole photo and letterbox it; don't crop faces/important areas.
                fitted = ImageOps.contain(image, (320, 480), Image.Resampling.LANCZOS)
                canvas = Image.new('RGB', (320, 480), (7, 18, 39))
                canvas.paste(fitted, ((320 - fitted.width) // 2, (480 - fitted.height) // 2))
                canvas.save(temporary_file, format='JPEG', quality=88, optimize=True,
                            progressive=False, subsampling=0)
            temporary_file.replace(output_file)
            print(input_file.name, '->', filename)
            count += 1
        except Exception as exc:
            temporary_file.unlink(missing_ok=True)
            print('SKIPPED', input_file, exc)
            failures += 1

    print(f'Conversion complete. {count} converted, {skipped} skipped, {failures} failed.')
    print('Reinsert microSD in ESP32-S3 when power is OFF.')
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
