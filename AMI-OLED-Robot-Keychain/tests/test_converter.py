"""Converter integration checks using the repository's bundled sample media."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "mp4_to_oled"))
from converter import Settings, ClipEntry, load_frames, pack_frame, mockup, export_project, estimate_total

SAMPLES = ROOT / "samples" / "videos"

class ConverterTests(unittest.TestCase):
    def test_video_frames_and_header_packing(self):
        cfg = Settings(fps=12, seconds=1, layout="ami", label="AMI", framing="crop")
        path = SAMPLES / "01_Blinking_Eyes.mp4"
        frames = load_frames(path, cfg)
        self.assertEqual(len(frames), 12)
        self.assertTrue(all(frame.size == (128, 48) for frame in frames))
        self.assertEqual(len(pack_frame(frames[0])), 768)
        self.assertEqual(mockup(frames[0], cfg, 2).size, (256, 128))

    def test_gif_fullscreen(self):
        cfg = Settings(fps=10, seconds=.3, layout="full")
        frames = load_frames(SAMPLES / "04_Flash_Test.gif", cfg)
        self.assertGreaterEqual(len(frames), 2)
        self.assertEqual(len(pack_frame(frames[0])), 1024)

    def test_multi_clip_export_and_no_legacy_header_collisions(self):
        cfg = Settings(fps=12, seconds=1, layout="ami", label="AMI", framing="crop")
        entries = []
        for name in ("01_Blinking_Eyes.mp4", "02_Pixel_Heart.mp4", "03_Starfield.mp4"):
            path = SAMPLES / name
            entries.append(ClipEntry(path, load_frames(path, cfg), cfg))
        self.assertEqual(estimate_total(entries), 3 * 12 * 768)
        with tempfile.TemporaryDirectory() as directory:
            sketchdir = Path(directory) / "AMI_OLED_Robot_Keychain"
            export_project(sketchdir, entries)
            self.assertEqual(
                {p.name for p in sketchdir.iterdir()},
                {"AMI_OLED_Robot_Keychain.ino", "erinxc3_animation_catalog.h"},
            )
            code = (sketchdir / "AMI_OLED_Robot_Keychain.ino").read_text()
            header = (sketchdir / "erinxc3_animation_catalog.h").read_text()
            self.assertIn('#include "erinxc3_animation_catalog.h"', code)
            self.assertEqual(header.count("struct AnimationClip"), 1)
            self.assertNotIn("ANIM_WIDTH", header)
            self.assertIn("ANIMATION_COUNT = 3", header)
            self.assertIn("ERINX_V22_CLIP_01", header)
            self.assertIn("ERINX_V22_CLIP_03", header)
            (sketchdir / "animation_index.h").write_text("// old version")
            with self.assertRaises(FileExistsError):
                export_project(sketchdir, entries)

if __name__ == "__main__":
    unittest.main()
