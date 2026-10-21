"""AMI MP4/GIF-to-OLED converter for 128x64 SSD1306 + Seeed XIAO ESP32C3.

Python 3.10+. OpenCV + Pillow, tkinter-based GUI or CLI via --input.
Output animation.h fits Arduino Adafruit_SSD1306::drawBitmap (MSB-first rows).
"""
from __future__ import annotations

import argparse
import os
import queue
import re
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageOps, ImageSequence

WIDTH = 128
HEIGHT = 64
HEADER_H = 16    # Typical dual-color SSD1306: y=0..15 yellow, y=16..63 blue
SUPPORTED = (".mp4", ".mov", ".avi", ".mkv", ".webm", ".gif")


@dataclass(frozen=True)
class Settings:
    fps: int = 12
    seconds: float = 10.0
    start: float = 0.0
    layout: str = "ami"    # ami: reserved yellow header; full: full-screen movie
    label: str = "AMI"
    threshold: int = 128
    contrast: float = 1.4
    dither: bool = False
    invert: bool = False
    framing: str = "contain"  # contain or crop

    @property
    def content_height(self) -> int:
        return HEIGHT - HEADER_H if self.layout == "ami" else HEIGHT

    @property
    def offset_y(self) -> int:
        return HEADER_H if self.layout == "ami" else 0


def load_frames(file: Path, settings: Settings, progress: Callable[[int, int], None] | None = None) -> list[Image.Image]:
    """Sample by presentation time at settings.fps, preserving original clip rate."""
    if not file.is_file():
        raise FileNotFoundError(f"Video not found: {file}")
    if file.suffix.lower() not in SUPPORTED:
        raise ValueError("Unsupported format. Use MP4, MOV, AVI, MKV, WEBM or GIF.")
    if settings.fps < 1 or settings.fps > 30 or not (0 < settings.seconds <= 120):
        raise ValueError("FPS must be 1..30; maximum duration 0..120 seconds.")
    if settings.start < 0:
        raise ValueError("Start must be 0 or greater.")
    total = max(1, int(settings.seconds * settings.fps))
    out: list[Image.Image] = []
    if file.suffix.lower() == ".gif":
        with Image.open(file) as im:
            # Honor per-frame GIF delays and transparency via seek/convert("RGBA")
            gif_images: list[Image.Image] = []
            times: list[float] = []
            elapsed = 0.0
            for frame in ImageSequence.Iterator(im):
                gif_images.append(frame.convert("RGB"))
                times.append(elapsed)
                elapsed += max(20, int(frame.info.get("duration", 100))) / 1000.0
            if not gif_images or settings.start >= elapsed:
                raise ValueError("GIF has no frames after chosen start time.")
            k = 0
            for i in range(total):
                t = settings.start + i / settings.fps
                if t >= elapsed - 1e-6:
                    break
                while k+1 < len(times) and times[k+1] <= t:
                    k += 1
                out.append(process_image(gif_images[k], settings))
                if progress and i % 5 == 0:
                    progress(i+1, total)
    else:
        capture = cv2.VideoCapture(str(file))
        try:
            if not capture.isOpened():
                raise RuntimeError("Cannot open video. Try converting to H.264 MP4 or install a codec.")
            src_fps = float(capture.get(cv2.CAP_PROP_FPS))
            if not 0.1 < src_fps < 1000:
                src_fps = 30.0
            frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
            if frame_count > 0 and settings.start >= frame_count / src_fps:
                raise ValueError("Start time exceeds video duration.")
            start_frame = int(round(settings.start * src_fps))
            if start_frame:
                capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            current_idx = start_frame - 1
            last_rgb: Image.Image | None = None
            for i in range(total):
                # Video frame nearest to target playback timestamp
                target_idx = max(start_frame, int(round((settings.start + i / settings.fps) * src_fps)))
                while current_idx < target_idx:
                    ok, frame = capture.read()
                    if not ok:
                        break
                    current_idx += 1
                    if current_idx == target_idx:
                        last_rgb = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                if current_idx < target_idx:
                    break
                if last_rgb is None:
                    break
                out.append(process_image(last_rgb, settings))
                if progress and i % 5 == 0:
                    progress(i+1, total)
        finally:
            capture.release()
    if not out:
        raise ValueError("No frames extracted. Check video format/start time.")
    if progress:
        progress(len(out), len(out))
    return out


def process_image(img: Image.Image, settings: Settings) -> Image.Image:
    target_h = settings.content_height
    image = img.convert("RGB")
    if settings.framing == "crop":
        image = ImageOps.fit(image, (WIDTH, target_h), method=Image.Resampling.LANCZOS)
    else:
        image = ImageOps.contain(image, (WIDTH, target_h), method=Image.Resampling.LANCZOS)
        composed = Image.new("RGB", (WIDTH, target_h), "black")
        composed.paste(image, ((WIDTH-image.width)//2, (target_h-image.height)//2))
        image = composed
    gray = ImageEnhance.Contrast(image.convert("L")).enhance(settings.contrast)
    if settings.dither:
        if settings.invert:
            gray = ImageOps.invert(gray)
        bw = gray.convert("1", dither=Image.Dither.FLOYDSTEINBERG)
    else:
        array = np.asarray(gray, dtype=np.uint8)
        binary = (array >= settings.threshold).astype(np.uint8) * 255
        if settings.invert:
            binary = 255 - binary
        bw = Image.fromarray(binary, "L").convert("1", dither=Image.Dither.NONE)
    return bw


def pack_frame(bw: Image.Image) -> bytes:
    """Pillow '1' bytes: 8 pixels/byte, bit 7=leftmost; same as Adafruit drawBitmap."""
    if bw.mode != "1" or bw.width != WIDTH or bw.height not in (HEIGHT, HEIGHT-HEADER_H):
        raise ValueError("Invalid frame size or pixel mode.")
    data = bw.tobytes()
    assert len(data) == WIDTH * bw.height // 8
    return data


def mockup(frame: Image.Image, settings: Settings, scale: int = 4) -> Image.Image:
    """Make realistic simulated yellow/blue OLED preview using actual 1-bit bits."""
    on = np.array(frame, dtype=np.uint8) > 0
    preview = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    if settings.layout == "ami":
        y_offset = HEADER_H
        preview[y_offset:, :, :] = np.where(on[:, :, None], (18, 170, 255), (2, 8, 20))
        # Header text drawn with PIL default, a visual approximation of GFX builtin font
        header = Image.new("RGB", (WIDTH, HEADER_H), (2, 8, 20))
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(header)
        name = settings.label.strip()[:18] or "AMI"
        try:
            fpath = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
            font = ImageFont.truetype(fpath, 13) if os.path.exists(fpath) else ImageFont.load_default()
        except Exception:
            font = ImageFont.load_default()
        b = draw.textbbox((0, 0), name, font=font)
        draw.text(((WIDTH-(b[2]-b[0]))/2, (HEADER_H-(b[3]-b[1]))/2-b[1]), name, font=font, fill=(255, 218, 0))
        preview[:HEADER_H, :, :] = np.asarray(header)
    else:
        colors = np.where(on[:, :, None], (18, 170, 255), (2, 8, 20))
        preview[:, :, :] = colors
        # fixed hardware color band for top 16 rows
        preview[:HEADER_H, :, :] = np.where(on[:HEADER_H, :, None], (255, 218, 0), (2, 8, 20))
    return Image.fromarray(preview, "RGB").resize((WIDTH*scale, HEIGHT*scale), Image.Resampling.NEAREST)



# ------------------------------ V2 MULTI-CLIP ------------------------------
# This intentionally keeps the proven load_frames/process_image engine above.
from dataclasses import field
import shutil

MAX_SLOTS = 10
# Caution threshold only: actual sketch/app partition size depends on Arduino IDE.
CAUTION_BYTES = 950 * 1024

@dataclass
class ClipEntry:
    path: Path
    frames: list[Image.Image] = field(default_factory=list)
    settings: Settings | None = None

    @property
    def bytes_used(self) -> int:
        if self.settings is None:
            return 0
        return len(self.frames) * WIDTH * self.settings.content_height // 8


def estimate_total(entries: list[ClipEntry]) -> int:
    return sum(x.bytes_used for x in entries)


def sanitize_label(value: str, length: int = 18) -> str:
    """Restrict to printable ASCII for builtin Adafruit font / C++ literal."""
    value = re.sub(r"[^\x20-\x7E]", "", value)
    return value.replace('"', "").replace("\\", "")[:length].strip() or "AMI"


def write_catalog_header(dest: Path, entries: list[ClipEntry]) -> None:
    """One generated .h file: no mismatched slots or repeated ANIM_WIDTH symbols.

    The data format stays MSB-first/row-major to match SSD1306 drawBitmap.
    """
    if not entries or any(not e.frames or e.settings is None for e in entries):
        raise ValueError("Convert all clips before export")
    lines = [
        "// AMI OLED Robot Keychain V2.2 - generated animation catalog.",
        "// Keep this file next to AMI_OLED_Robot_Keychain.ino.",
        "#pragma once",
        "#include <Arduino.h>",
        "#include <pgmspace.h>",
        "",
        "struct AnimationClip {",
        "  const uint8_t* data;",
        "  uint16_t frameCount;",
        "  uint8_t fps;",
        "  uint8_t frameHeight;",
        "  uint16_t frameBytes;",
        "  uint8_t yOffset;",
        "  bool showHeader;",
        "  const char* headerText;",
        "  const char* title;",
        "};",
        "",
    ]
    for i, entry in enumerate(entries, 1):
        raw = b"".join(pack_frame(f) for f in entry.frames)
        symbol = f"ERINX_V22_CLIP_{i:02d}"
        lines.extend([
            f"// Slot {i}: {sanitize_label(entry.path.name, 36)}",
            f"static const uint8_t {symbol}[] PROGMEM = {{",
        ])
        for j in range(0, len(raw), 24):
            lines.append("  " + ", ".join(f"0x{v:02X}" for v in raw[j:j+24]) + ",")
        lines += [
            "};",
            f"static_assert(sizeof({symbol}) == {len(raw)}U, \"Unexpected clip data size\");",
            "",
        ]
    lines += [
        f"static constexpr uint8_t ANIMATION_COUNT = {len(entries)};",
        "static const AnimationClip ANIMATIONS[ANIMATION_COUNT] = {",
    ]
    for i, entry in enumerate(entries, 1):
        cfg = entry.settings
        assert cfg is not None
        label = sanitize_label(cfg.label)
        title = sanitize_label(entry.path.stem, 24)
        size = WIDTH * cfg.content_height // 8
        lines.append(
            f"  {{ERINX_V22_CLIP_{i:02d}, {len(entry.frames)}, {cfg.fps}, "
            f"{cfg.content_height}, {size}, {cfg.offset_y}, "
            f"{'true' if cfg.layout == 'ami' else 'false'}, \"{label}\", \"{title}\"}},"
        )
    lines.extend(["};", ""])
    dest.write_text("\n".join(lines), encoding="utf-8")


def export_project(target: Path, entries: list[ClipEntry]) -> Path:
    """Export one .ino + one .h in an isolated Arduino sketch folder."""
    if not entries or any(not e.frames or e.settings is None for e in entries):
        raise ValueError("Add and convert at least one clip before exporting")
    # Prevent mixing the old V1/V2 individual animation headers into this sketch.
    if target.is_dir():
        existing = {p.name for p in target.iterdir() if p.is_file()}
        allowed = {"AMI_OLED_Robot_Keychain.ino", "erinxc3_animation_catalog.h"}
        conflicts = sorted(existing - allowed)
        if conflicts:
            raise FileExistsError(
                "Old files detected in target folder: " + ", ".join(conflicts[:8])
                + ". Export into a DIFFERENT/empty folder instead of mixing versions."
            )
    target.mkdir(parents=True, exist_ok=True)
    firmware = Path(__file__).resolve().parents[2] / "firmware" / "AMI_OLED_Robot_Keychain" / "AMI_OLED_Robot_Keychain.ino"
    if not firmware.exists():
        raise FileNotFoundError(f"Bundled firmware not found: {firmware}")
    shutil.copyfile(firmware, target / firmware.name)
    write_catalog_header(target / "erinxc3_animation_catalog.h", entries)
    return target


def run_cli(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(description="Batch convert up to 10 MP4/GIF clips into a XIAO ESP32C3 Arduino sketch")
    parser.add_argument("--clips", nargs="+", required=True, help="List of MP4/GIF files")
    parser.add_argument("--output", required=True, help="Arduino sketch folder destination")
    parser.add_argument("--fps", type=int, default=12)
    parser.add_argument("--seconds", type=float, default=5.0)
    parser.add_argument("--start", type=float, default=0.0)
    parser.add_argument("--layout", choices=["ami", "full"], default="ami")
    parser.add_argument("--label", default="AMI")
    parser.add_argument("--threshold", type=int, default=128)
    parser.add_argument("--contrast", type=float, default=1.4)
    parser.add_argument("--dither", action="store_true")
    parser.add_argument("--invert", action="store_true")
    parser.add_argument("--framing", choices=["contain", "crop"], default="crop")
    args = parser.parse_args(argv)
    if not (1 <= len(args.clips) <= MAX_SLOTS):
        parser.error(f"Choose 1 to {MAX_SLOTS} clips")
    config = Settings(args.fps, args.seconds, args.start, args.layout, args.label,
                      args.threshold, args.contrast, args.dither, args.invert, args.framing)
    entries = []
    for i,path in enumerate(args.clips,1):
        print(f"[{i}/{len(args.clips)}] Processing {path} ...", flush=True)
        entry = ClipEntry(Path(path))
        entry.frames = load_frames(entry.path, config)
        entry.settings = config
        entries.append(entry)
    result = export_project(Path(args.output), entries)
    print(f"Exported {len(entries)} slots / {estimate_total(entries)/1024:.1f} KiB raw frames to {result}")
    if estimate_total(entries) > CAUTION_BYTES:
        print("WARNING: Data is large; check board app partition size before uploading.")


def run_gui() -> None:
    """Scrollable content with permanently visible conversion/export footer."""
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    from PIL import ImageTk

    root = tk.Tk()
    root.title("ERINX  /  Multi-Animation OLED Converter V2.2 FIXED")
    # Adapt startup size to actual logical Windows desktop (including display scaling).
    # Otherwise a 960x660 window can hide its footer below the taskbar.
    screen_w, screen_h = root.winfo_screenwidth(), root.winfo_screenheight()
    initial_w = min(960, max(660, screen_w - 45))
    initial_h = min(660, max(400, screen_h - 60))
    root.geometry(f"{initial_w}x{initial_h}+15+15")
    root.minsize(660, 380)
    root.configure(bg="#101724")
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure("TFrame", background="#101724")
    style.configure("TLabel", background="#101724", foreground="#e8edf6", font=("Segoe UI", 10))
    style.configure("TButton", padding=5, font=("Segoe UI", 9, "bold"))
    style.configure("TEntry", padding=4)
    style.configure("TCombobox", padding=4)
    style.configure("TCheckbutton", background="#101724", foreground="#e8edf6")
    style.configure("Horizontal.TProgressbar", background="#00baff", troughcolor="#253348")

    # Fixed action footer: ALWAYS within view, independently of scroll position.
    footer = ttk.Frame(root, padding=(13, 8, 13, 12))
    footer.pack(side="bottom", fill="x")
    body = ttk.Frame(root)
    body.pack(side="top", fill="both", expand=True)
    canvas = tk.Canvas(body, bg="#101724", highlightthickness=0, bd=0)
    scrollbar = ttk.Scrollbar(body, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    page = ttk.Frame(canvas, padding=(18, 10, 18, 14))
    canvas_id = canvas.create_window((0, 0), window=page, anchor="nw")
    page.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda e: (canvas.itemconfig(canvas_id, width=e.width), canvas.configure(scrollregion=canvas.bbox("all"))))

    def mousewheel(event):
        # Windows positive wheel means scroll upward. Restrict to UI contents.
        if event.widget.winfo_toplevel() != root:
            return
        if isinstance(event.widget, (ttk.Combobox, tk.Listbox)):
            return
        if getattr(event, "num", None) == 4:
            amount = -2
        elif getattr(event, "num", None) == 5:
            amount = 2
        else:
            ticks = max(1, round(abs(getattr(event, "delta", 0)) / 120))
            amount = -ticks if event.delta > 0 else ticks
        if amount:
            canvas.yview_scroll(amount, "units")
            return "break"
    root.bind_all("<MouseWheel>", mousewheel, add="+")
    root.bind_all("<Button-4>", mousewheel, add="+")
    root.bind_all("<Button-5>", mousewheel, add="+")

    tk.Label(page, text="ERINX / MULTI-ANIMATION", font=("Segoe UI", 22, "bold"),
             bg="#101724", fg="#eaf4ff").pack(anchor="w")
    ttk.Label(page, text="XIAO ESP32C3 + SSD1306 128×64  •  Short tap NEXT  •  Hold 1.2s OLED OFF/ON").pack(anchor="w", pady=(0, 13))
    ttk.Label(page, text=f"STEP 1   Add up to {MAX_SLOTS} MP4/GIF clips and arrange their playback order.").pack(anchor="w")

    clips: list[ClipEntry] = []
    queue_events: queue.Queue = queue.Queue()
    active = False
    preview_idx = 0
    preview_frame = 0
    working_settings: Settings | None = None

    filearea = ttk.Frame(page)
    filearea.pack(fill="x", pady=(7, 8))
    listbox = tk.Listbox(filearea, height=7, bg="#192537", fg="#eaf1fc", font=("Consolas", 10),
                         selectbackground="#266696", selectforeground="white", activestyle="none",
                         exportselection=False, bd=0)
    listbox.pack(side="left", fill="both", expand=True, padx=(0, 12))
    listbuttons = ttk.Frame(filearea)
    listbuttons.pack(side="right", fill="y")

    def selected_index() -> int:
        selection = listbox.curselection()
        return selection[0] if selection else -1

    def fmt(entry: ClipEntry, i: int) -> str:
        status = f"{len(entry.frames)}fr / {entry.bytes_used/1024:.0f}KB READY" if entry.frames else "not converted"
        return f"{i+1:02d} | {entry.path.name[:36]:36s} | {status}"

    def repaint_list(index: int | None = None):
        listbox.delete(0, "end")
        for j, entry in enumerate(clips):
            listbox.insert("end", fmt(entry, j))
        if clips:
            new = min(max(0, index if index is not None else selected_index()), len(clips)-1)
            listbox.selection_set(new)
            listbox.see(new)
        refresh_stats()

    def add_clips():
        if active: return
        paths = filedialog.askopenfilenames(title="Add MP4 or GIF files",
                filetypes=[("MP4 / GIF / Videos", "*.mp4 *.gif *.mov *.mkv *.avi *.webm"), ("All files", "*.*")])
        for p in paths:
            if len(clips) >= MAX_SLOTS:
                messagebox.showwarning("Slot limit", f"V2 supports up to {MAX_SLOTS} clips per project.")
                break
            if Path(p).suffix.lower() not in SUPPORTED: continue
            clips.append(ClipEntry(Path(p)))
        repaint_list(len(clips)-1)
        if paths: status.set("Clips added. Click Convert ALL Clips when ready.")

    def remove_selected():
        if active: return
        index = selected_index()
        if index < 0: return
        del clips[index]
        repaint_list(min(index, len(clips)-1))

    def move_selected(step: int):
        if active: return
        index = selected_index()
        other = index + step
        if index >= 0 and 0 <= other < len(clips):
            clips[index], clips[other] = clips[other], clips[index]
            repaint_list(other)

    ttk.Button(listbuttons, text="+ Add MP4 / GIF", command=add_clips).pack(fill="x", pady=(0, 5))
    ttk.Button(listbuttons, text="Remove selected", command=remove_selected).pack(fill="x", pady=5)
    ttk.Button(listbuttons, text="↑ Move up", command=lambda: move_selected(-1)).pack(fill="x", pady=5)
    ttk.Button(listbuttons, text="↓ Move down", command=lambda: move_selected(1)).pack(fill="x", pady=5)

    ttk.Label(page, text="STEP 2   Choose conversion settings (applied to all clips)").pack(anchor="w", pady=(8, 4))
    settings_grid = ttk.Frame(page)
    settings_grid.pack(fill="x", pady=(0, 6))
    for col in range(4): settings_grid.columnconfigure(col, weight=1)
    fps_var = tk.StringVar(value="12")
    seconds_var = tk.StringVar(value="5")
    start_var = tk.StringVar(value="0")
    framing_var = tk.StringVar(value="crop")
    layout_var = tk.StringVar(value="ami")
    label_var = tk.StringVar(value="AMI")
    threshold_var = tk.StringVar(value="128")
    contrast_var = tk.StringVar(value="1.4")
    dither_var = tk.BooleanVar(value=False)
    invert_var = tk.BooleanVar(value=False)

    def make_field(row, col, label, variable, values=None):
        frame = ttk.Frame(settings_grid)
        frame.grid(row=row, column=col, sticky="ew", padx=4, pady=4)
        ttk.Label(frame, text=label).pack(anchor="w")
        if values:
            ttk.Combobox(frame, textvariable=variable, values=values, state="readonly", width=14).pack(fill="x")
        else:
            ttk.Entry(frame, textvariable=variable, width=14).pack(fill="x")
    make_field(0, 0, "FPS", fps_var, ["8", "10", "12", "15", "20"])
    make_field(0, 1, "Max seconds / clip", seconds_var)
    make_field(0, 2, "Start at seconds", start_var)
    make_field(0, 3, "Framing", framing_var, ["crop", "contain"])
    make_field(1, 0, "Screen layout", layout_var, ["ami", "full"])
    make_field(1, 1, "Yellow header name", label_var)
    make_field(1, 2, "Threshold 0–255", threshold_var)
    make_field(1, 3, "Contrast (0.1–5)", contrast_var)
    checks = ttk.Frame(page)
    checks.pack(anchor="w", pady=(0, 9))
    ttk.Checkbutton(checks, text="Floyd–Steinberg dithering", variable=dither_var).pack(side="left", padx=(0, 15))
    ttk.Checkbutton(checks, text="Invert black/white", variable=invert_var).pack(side="left")

    ttk.Label(page, text="STEP 3   Select a READY clip to preview on the simulated two-color OLED.").pack(anchor="w")
    frame_border = tk.Frame(page, bg="#2a405d", padx=9, pady=9)
    frame_border.pack(pady=(8, 7))
    preview_label = tk.Label(frame_border, bg="#030812", width=512, height=256)
    preview_label.pack()
    empty_img = ImageTk.PhotoImage(Image.new("RGB", (512,256), "#030812"))
    preview_label.configure(image=empty_img)
    preview_label.image = empty_img
    preview_text = tk.StringVar(value="No clip preview yet — use Convert ALL Clips")
    ttk.Label(page, textvariable=preview_text).pack(anchor="center")
    ttk.Label(page, text="Rows 0–15 = yellow, 16–63 = blue. Color is fixed by OLED hardware.").pack(anchor="center")

    # Permanent bottom bar for compact 1366x768/125%-scaled Windows screens.
    status = tk.StringVar(value="Add video clips to start.")
    storage = tk.StringVar(value="0 clips  •  0 KiB raw animation data")
    ttk.Label(footer, textvariable=storage).pack(anchor="w")
    bar = ttk.Progressbar(footer, orient="horizontal", mode="determinate", maximum=100)
    bar.pack(fill="x", pady=(3, 4))
    ttk.Label(footer, textvariable=status, wraplength=800).pack(anchor="w")
    actions = ttk.Frame(footer)
    actions.pack(fill="x", pady=(5,0))

    def refresh_stats():
        total = estimate_total(clips)
        ready = sum(bool(c.frames) for c in clips)
        storage.set(f"{len(clips)} clips ({ready} ready)  •  {total/1024:.1f} KiB frames  •  Check IDE flash partition limits")

    def get_settings() -> Settings:
        cfg = Settings(fps=int(fps_var.get()), seconds=float(seconds_var.get()),
                       start=float(start_var.get()), layout=layout_var.get(),
                       label=sanitize_label(label_var.get()), threshold=int(threshold_var.get()),
                       contrast=float(contrast_var.get()), dither=dither_var.get(),
                       invert=invert_var.get(), framing=framing_var.get())
        if not (1 <= cfg.fps <= 30 and 0 < cfg.seconds <= 120 and cfg.start >= 0
                and 0 <= cfg.threshold <= 255 and 0.1 <= cfg.contrast <= 5.0):
            raise ValueError("FPS 1..30; seconds 0..120; start >= 0; threshold 0..255; contrast 0.1..5")
        return cfg

    def set_busy(value: bool):
        nonlocal active
        active = value
        for btn in (convert_btn, export_btn):
            btn.configure(state="disabled" if value else "normal")

    def convert_all():
        nonlocal working_settings
        if active: return
        if not clips:
            messagebox.showwarning("No clips", "Click + Add MP4 / GIF first.")
            return
        try:
            cfg = get_settings()
        except Exception as exc:
            messagebox.showerror("Invalid settings", str(exc))
            return
        working_settings = cfg
        set_busy(True)
        bar.configure(value=0)
        status.set(f"Converting {len(clips)} clips. Please wait...")
        copies = [entry.path for entry in clips]
        # Never touch tkinter widgets or shared entry objects from worker thread.
        def worker():
            try:
                results=[]
                for j,path in enumerate(copies):
                    def progress(done, total, idx=j):
                        queue_events.put(("progress", idx, done, total, len(copies)))
                    frames = load_frames(path, cfg, progress)
                    results.append(frames)
                    queue_events.put(("progress", j+1, 0, 0, len(copies)))
                queue_events.put(("done", results, cfg))
            except Exception as exc:
                queue_events.put(("failed", str(exc)))
        threading.Thread(target=worker, daemon=True).start()

    def export_all():
        if active: return
        if not clips or any(not e.frames for e in clips):
            messagebox.showwarning("Not ready", "Convert ALL clips first.")
            return
        try:
            cfg = get_settings()
        except Exception as exc:
            messagebox.showerror("Invalid settings", str(exc))
            return
        if any(e.settings != cfg for e in clips):
            messagebox.showwarning("Settings changed", "Settings changed after conversion. Convert ALL Clips again first.")
            return
        total = estimate_total(clips)
        if total > CAUTION_BYTES:
            if not messagebox.askyesno("Flash capacity warning",
                f"Frames alone use {total/1024:.0f} KiB. The available app partition also needs firmware.\n"
                "Export anyway? You may have to shorten clips or choose a larger app partition."):
                return
        destination = filedialog.askdirectory(title="Choose where to save Arduino project")
        if not destination: return
        try:
            folder = export_project(Path(destination) / "AMI_OLED_Robot_Keychain", clips)
        except Exception as exc:
            messagebox.showerror("Export failed", str(exc))
            return
        status.set(f"Exported Arduino sketch: {folder}")
        messagebox.showinfo("Arduino project ready",
            f"Saved {len(clips)} animations in:\n{folder}\n\n"
            "Open AMI_OLED_Robot_Keychain.ino with Arduino IDE.\n"
            "Board: XIAO_ESP32C3. Tap D1 button = next; hold 2s and release = deep sleep; press to wake.")

    convert_btn = ttk.Button(actions, text="1 ▶ Convert ALL Clips", command=convert_all)
    convert_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))
    export_btn = ttk.Button(actions, text="2 ⇩ Export Arduino Project", command=export_all)
    export_btn.pack(side="left", fill="x", expand=True, padx=(6,0))

    def update_preview():
        nonlocal preview_frame, preview_idx
        index=selected_index()
        if index != preview_idx:
            preview_idx=index
            preview_frame=0
        if 0 <= index < len(clips):
            entry=clips[index]
            if entry.frames and entry.settings:
                frame=entry.frames[preview_frame % len(entry.frames)]
                image=ImageTk.PhotoImage(mockup(frame,entry.settings,scale=4))
                preview_label.configure(image=image)
                preview_label.image=image
                preview_frame+=1
                preview_text.set(f"Slot {index+1}: {entry.path.name} | {len(entry.frames)} frames | {entry.settings.fps} FPS")
                delay=max(30, int(1000/entry.settings.fps))
            else:
                preview_label.configure(image=empty_img)
                preview_label.image=empty_img
                preview_text.set(f"Slot {index+1}: {entry.path.name}  •  not converted")
                delay=250
        else:
            preview_label.configure(image=empty_img)
            preview_label.image=empty_img
            preview_text.set("No clip preview yet — use Convert ALL Clips")
            delay=250
        root.after(delay, update_preview)

    def poll_events():
        nonlocal preview_frame
        try:
            while True:
                msg=queue_events.get_nowait()
                if msg[0] == "progress":
                    _, idx, done, count, num=msg
                    fraction=(idx+done/max(1,count))/num if count else 0
                    bar.configure(value=100 * min(1.0, fraction))
                    if count:
                        status.set(f"Converting clip {idx+1}/{num}, frame {done}/{count}...")
                elif msg[0] == "done":
                    _, frame_lists, cfg=msg
                    for entry, frames in zip(clips, frame_lists):
                        entry.frames=frames
                        entry.settings=cfg
                    set_busy(False)
                    bar.configure(value=100)
                    preview_frame=0
                    repaint_list(0)
                    total=estimate_total(clips)
                    status.set(f"Ready: {len(clips)} clips, {total/1024:.1f} KiB raw frames. Click Export Arduino Project.")
                    if total > CAUTION_BYTES:
                        messagebox.showwarning("Storage caution", "Animation data is large. Shorten clips or check Arduino IDE app partition size before upload.")
                elif msg[0] == "failed":
                    set_busy(False)
                    status.set("Conversion failed. Fix the source clip or settings and retry.")
                    messagebox.showerror("Conversion failed", msg[1])
        except queue.Empty:
            pass
        root.after(100, poll_events)

    repaint_list()
    root.after(200, poll_events)
    root.after(250, update_preview)
    root.mainloop()


if __name__ == "__main__":
    import sys
    if "--clips" in sys.argv:
        run_cli(sys.argv[1:])
    else:
        run_gui()
