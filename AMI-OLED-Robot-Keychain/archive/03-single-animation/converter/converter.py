"""ERINX MP4/GIF-to-OLED converter for 128x64 SSD1306 + Seeed XIAO ESP32C3.

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


def write_header(dest: Path, frames: list[Image.Image], settings: Settings) -> None:
    if not frames:
        raise ValueError("No animation frames to export")
    dest.parent.mkdir(parents=True, exist_ok=True)
    frame_bytes = WIDTH * settings.content_height // 8
    raw = b"".join(pack_frame(f) for f in frames)
    safe_label = re.sub(r"[^\x20-\x7E]", "", settings.label).replace('\\', '').replace('"', '')[:18].strip() or "AMI"
    # Adafruit's default 5x7 font uses ASCII glyphs; unaccented label only
    lines = [
        "// Generated by ERINX MP4-to-OLED Converter. DO NOT EDIT BY HAND.",
        "// Format: 1 bit/pixel, black=0, on=1, MSB-first, row-major.",
        "#pragma once",
        "#include <Arduino.h>",
        "#include <pgmspace.h>",
        f"constexpr uint16_t ANIM_WIDTH = {WIDTH};",
        f"constexpr uint16_t ANIM_FRAME_HEIGHT = {settings.content_height};",
        f"constexpr uint16_t ANIM_Y_OFFSET = {settings.offset_y};",
        f"constexpr uint16_t ANIM_FRAME_BYTES = {frame_bytes};",
        f"constexpr uint16_t ANIM_FRAME_COUNT = {len(frames)};",
        f"constexpr uint8_t ANIM_FPS = {settings.fps};",
        f"constexpr bool ANIM_SHOW_HEADER = {'true' if settings.layout == 'ami' else 'false'};",
        f'constexpr char ANIM_HEADER_TEXT[] = "{safe_label}";',
        "const uint8_t ANIM_FRAMES[] PROGMEM = {",
    ]
    for idx in range(0, len(raw), 16):
        portion = raw[idx:idx+16]
        lines.append("  " + ", ".join(f"0x{b:02X}" for b in portion) + ",")
    lines += ["};", "static_assert(sizeof(ANIM_FRAMES) == (size_t)ANIM_FRAME_BYTES * ANIM_FRAME_COUNT, \"Animation byte count mismatch\");", ""]
    dest.write_text("\n".join(lines), encoding="utf-8")


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


def cmdline() -> bool:
    import sys
    if "--input" not in sys.argv:
        return False
    p = argparse.ArgumentParser(description="Export MP4/GIF as SSD1306 C header for ERINX Hair Clip")
    p.add_argument("--input", required=True)
    p.add_argument("--output", default="animation.h")
    p.add_argument("--fps", type=int, default=12)
    p.add_argument("--seconds", type=float, default=10)
    p.add_argument("--start", type=float, default=0)
    p.add_argument("--layout", choices=["ami", "full"], default="ami")
    p.add_argument("--name", default="AMI")
    p.add_argument("--threshold", type=int, default=128)
    p.add_argument("--contrast", type=float, default=1.4)
    p.add_argument("--dither", action="store_true")
    p.add_argument("--invert", action="store_true")
    p.add_argument("--crop", action="store_true")
    args = p.parse_args()
    config = Settings(args.fps, args.seconds, args.start, args.layout, args.name,
                      args.threshold, args.contrast, args.dither, args.invert,
                      "crop" if args.crop else "contain")
    frames = load_frames(Path(args.input), config,
                         lambda a,b: print(f"\rConverting {a}/{b} frames", end="", flush=True))
    write_header(Path(args.output), frames, config)
    size = sum(len(pack_frame(f)) for f in frames)
    print(f"\nSaved {args.output}: {len(frames)} frames, {size/1024:.1f} KiB raw flash.")
    return True


def run_gui() -> None:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    from PIL import ImageTk

    root = tk.Tk()
    root.title("ERINX  •  MP4 to OLED Converter v1.1 (Scrollable)")
    # Compact window by default; scrollable content handles shorter laptop screens.
    root.geometry("880x620")
    root.minsize(620, 390)
    root.configure(bg="#101724")
    style = ttk.Style(root)
    try: style.theme_use("clam")
    except tk.TclError: pass
    style.configure("TFrame", background="#101724")
    style.configure("TLabel", background="#101724", foreground="#e8edf6", font=("Segoe UI", 10))
    style.configure("TButton", padding=7, font=("Segoe UI", 10, "bold"))
    style.configure("TEntry", padding=5)
    style.configure("TCombobox", padding=5)
    style.configure("TCheckbutton", background="#101724", foreground="#e8edf6")
    style.configure("Horizontal.TProgressbar", background="#00baff", troughcolor="#253348")
    # Scrollable page (all fields and preview), plus always-visible action footer.
    # On a 1366x768 laptop at Windows display scaling, no buttons get cut off.
    body = ttk.Frame(root)
    body.pack(side="top", fill="both", expand=True)
    canvas = tk.Canvas(body, bg="#101724", highlightthickness=0, bd=0)
    scroll = ttk.Scrollbar(body, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scroll.set)
    scroll.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    wrapper = ttk.Frame(canvas, padding=18)
    content_id = canvas.create_window((0, 0), window=wrapper, anchor="nw")

    def update_scrollregion(_event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def resize_scrolling_content(event):
        canvas.itemconfigure(content_id, width=event.width)
        update_scrollregion()

    wrapper.bind("<Configure>", update_scrollregion)
    canvas.bind("<Configure>", resize_scrolling_content)

    def is_child_of(widget, ancestor):
        while widget is not None:
            if widget is ancestor:
                return True
            widget = getattr(widget, "master", None)
        return False

    def on_mousewheel(event):
        # Only scroll the page while pointer is over its content. Keep scrolling
        # the settings panel from accidentally changing combobox selections.
        if not is_child_of(event.widget, canvas) and not is_child_of(event.widget, wrapper):
            return
        if isinstance(event.widget, ttk.Combobox):
            return "break"
        if canvas.bbox("all") and canvas.bbox("all")[3] > canvas.winfo_height():
            if getattr(event, "num", None) == 4:  # Linux
                delta = -2
            elif getattr(event, "num", None) == 5:
                delta = 2
            else:  # Windows wheel/trackpad, macOS
                wheel = getattr(event, "delta", 0)
                delta = -max(1, round(abs(wheel) / 120)) if wheel > 0 else max(1, round(abs(wheel) / 120)) if wheel < 0 else 0
            if delta:
                canvas.yview_scroll(delta, "units")
                return "break"

    root.bind_all("<MouseWheel>", on_mousewheel, add="+")
    root.bind_all("<Button-4>", on_mousewheel, add="+")
    root.bind_all("<Button-5>", on_mousewheel, add="+")

    # Sticky actions: the user can ALWAYS Convert/Export, even without scrolling.
    footer = ttk.Frame(root, padding=(18, 9, 18, 12))
    footer.pack(side="bottom", fill="x")
    tk.Label(wrapper, text="ERINX  /  MP4 → OLED", bg="#101724", fg="#eaf4ff", font=("Segoe UI", 22, "bold")).pack(anchor="w")
    ttk.Label(wrapper, text='128×64 SSD1306  •  XIAO ESP32C3  •  Yellow AMI Header or Full Screen').pack(anchor="w", pady=(2, 14))
    file_var = tk.StringVar(value="No video selected")
    file_path: Path | None = None
    controls = ttk.Frame(wrapper)
    controls.pack(fill="x", pady=(0, 8))
    ttk.Label(controls, textvariable=file_var, width=65).pack(side="left", fill="x", expand=True)
    def browse():
        nonlocal file_path
        result = filedialog.askopenfilename(filetypes=[("Video / GIF", "*.mp4 *.mov *.avi *.mkv *.webm *.gif"), ("All files", "*.*")])
        if result:
            file_path = Path(result)
            file_var.set(file_path.name)
            status.set("Ready. Click Convert + Preview.")
    ttk.Button(controls, text="Choose MP4 / GIF", command=browse).pack(side="right")

    grid = ttk.Frame(wrapper)
    grid.pack(fill="x", pady=(8, 8))
    for i in range(4): grid.columnconfigure(i, weight=1)
    fps_var = tk.StringVar(value="12")
    seconds_var = tk.StringVar(value="10")
    start_var = tk.StringVar(value="0")
    layout_var = tk.StringVar(value="ami")
    name_var = tk.StringVar(value="AMI")
    framing_var = tk.StringVar(value="contain")
    threshold_var = tk.IntVar(value=128)
    contrast_var = tk.StringVar(value="1.4")
    dither_var = tk.BooleanVar(value=False)
    invert_var = tk.BooleanVar(value=False)

    def field(r,c,name,value,options=None):
        frame = ttk.Frame(grid)
        frame.grid(row=r,column=c,sticky="ew",padx=6,pady=6)
        ttk.Label(frame,text=name).pack(anchor="w")
        if options:
            ttk.Combobox(frame,textvariable=value,values=options,state="readonly",width=16).pack(fill="x")
        else:
            ttk.Entry(frame,textvariable=value,width=16).pack(fill="x")
    field(0,0,"FPS", fps_var,["8","10","12","15","20"])
    field(0,1,"Max seconds",seconds_var)
    field(0,2,"Start at (sec)",start_var)
    field(0,3,"Framing",framing_var,["contain","crop"])
    field(1,0,"Screen layout",layout_var,["ami","full"])
    field(1,1,"Yellow label",name_var)
    field(1,2,"Threshold 0–255",threshold_var)
    field(1,3,"Contrast (1.0–3.0)",contrast_var)
    opts = ttk.Frame(wrapper)
    opts.pack(anchor="w",pady=(1,10))
    ttk.Checkbutton(opts,text="Floyd–Steinberg dithering",variable=dither_var).pack(side="left",padx=(6,30))
    ttk.Checkbutton(opts,text="Invert black/white",variable=invert_var).pack(side="left")
    ttk.Label(wrapper,text="Yellow band = rows 0–15; blue band = rows 16–63. Hardware decides colors.").pack(anchor="w",pady=3)
    screen_border = tk.Frame(wrapper,bg="#293f5b",padx=11,pady=11)
    screen_border.pack(pady=10)
    placeholder = ImageTk.PhotoImage(Image.new("RGB", (512, 256), "#030812"))
    screen = tk.Label(screen_border, bg="#030812", image=placeholder, width=512, height=256)
    screen.image = placeholder
    screen.pack()
    info = tk.StringVar(value="OLED preview  •  import a clip, then Convert + Preview")
    ttk.Label(wrapper,textvariable=info).pack(anchor="center")
    ttk.Label(wrapper, text="Scroll with mouse wheel or right scrollbar. Convert and Export stay below.").pack(anchor="center", pady=(9, 0))
    # Footer stays at the bottom, independent of the canvas scrolling.
    progress = ttk.Progressbar(footer, mode="determinate", maximum=100)
    progress.pack(fill="x", pady=(0, 5))
    status = tk.StringVar(value="Choose your MP4 or GIF to begin.")
    ttk.Label(footer, textvariable=status, wraplength=700).pack(anchor="w")
    buttons = ttk.Frame(footer)
    buttons.pack(fill="x", pady=(8, 0))

    items: list[Image.Image] = []
    current_config: Settings | None = None
    screen_frame_id = 0
    export_button: ttk.Button
    convert_button: ttk.Button
    tasks: queue.Queue = queue.Queue()
    running = False

    def read_settings() -> Settings:
        s=Settings(
            fps=int(fps_var.get()), seconds=float(seconds_var.get()),
            start=float(start_var.get()), layout=layout_var.get(),
            label=name_var.get().strip(), threshold=int(threshold_var.get()),
            contrast=float(contrast_var.get()), dither=dither_var.get(),
            invert=invert_var.get(), framing=framing_var.get()
        )
        if not 1 <= s.fps <= 30 or not 0 < s.seconds <= 120 or not 0 <= s.threshold <= 255 or not 0.1 <= s.contrast <= 5 or s.start < 0:
            raise ValueError("FPS 1–30, seconds 0–120, threshold 0–255, contrast 0.1–5, start >= 0.")
        return s

    def paint(image: Image.Image, config: Settings):
        preview = ImageTk.PhotoImage(mockup(image,config,scale=4))
        screen.configure(image=preview)
        screen.image=preview

    def cycle():
        nonlocal screen_frame_id
        if items and current_config is not None:
            paint(items[screen_frame_id % len(items)], current_config)
            screen_frame_id += 1
            root.after(max(30,int(1000/current_config.fps)), cycle)
        else:
            root.after(250, cycle)
    root.after(200, cycle)

    def convert():
        nonlocal running
        if running: return
        if file_path is None:
            messagebox.showwarning("Choose a video", "Select an MP4 or GIF first.")
            return
        try:
            chosen = read_settings()
        except (ValueError, TypeError) as exc:
            messagebox.showerror("Invalid settings",str(exc))
            return
        running = True
        convert_button.configure(state="disabled")
        export_button.configure(state="disabled")
        progress.configure(value=0)
        status.set("Processing video frames...")
        def job():
            try:
                value=load_frames(file_path,chosen,lambda a,b: tasks.put(("progress",a,b)))
                tasks.put(("success",value,chosen))
            except Exception as exc:
                tasks.put(("error",str(exc)))
        threading.Thread(target=job,daemon=True).start()

    def poll():
        nonlocal running, items, current_config, screen_frame_id
        try:
            while True:
                msg=tasks.get_nowait()
                if msg[0]=="progress":
                    _,i,n=msg
                    progress.configure(value=100*i/max(1,n))
                    status.set(f"Processing {i}/{n} frames...")
                elif msg[0]=="success":
                    _,items,current_config=msg
                    running=False
                    screen_frame_id=0
                    convert_button.configure(state="normal")
                    export_button.configure(state="normal")
                    kbytes=len(items)*WIDTH*current_config.content_height//8/1024
                    info.set(f"{len(items)} frames  •  {current_config.fps} FPS  •  {kbytes:.1f} KiB raw flash  •  {current_config.layout.upper()}")
                    status.set("Ready! Export animation.h and copy it into the Arduino sketch folder.")
                    progress.configure(value=100)
                    if kbytes > 450:
                        messagebox.showwarning("Flash size",f"Frames use {kbytes:.0f} KiB. Reduce seconds/FPS if your sketch is too large.")
                elif msg[0]=="error":
                    running=False
                    convert_button.configure(state="normal")
                    status.set("Conversion failed.")
                    messagebox.showerror("Conversion error", msg[1])
        except queue.Empty:
            pass
        root.after(100,poll)
    root.after(100,poll)

    def export():
        if not items or current_config is None:
            messagebox.showwarning("Convert first","Press Convert + Preview before exporting.")
            return
        try:
            if read_settings() != current_config:
                messagebox.showwarning("Preview needs updating", "You changed a setting after converting. Please click Convert + Preview again before exporting.")
                return
        except (ValueError, TypeError) as exc:
            messagebox.showerror("Invalid settings", str(exc))
            return
        file=filedialog.asksaveasfilename(title="Export animation.h",defaultextension=".h",initialfile="animation.h",filetypes=[("Arduino C header","*.h")])
        if not file: return
        try:
            write_header(Path(file), items, current_config)
        except Exception as exc:
            messagebox.showerror("Export failed",str(exc))
            return
        status.set(f"Saved: {file}")
        messagebox.showinfo("Export successful","Saved animation.h!\n\nCopy it into arduino/ERINX_HairClip_Player/ and overwrite the old animation.h. Then upload ERINX_HairClip_Player.ino")

    convert_button=ttk.Button(buttons,text="▶  Convert + Preview",command=convert)
    convert_button.pack(side="left",fill="x",expand=True,padx=(0,8))
    export_button=ttk.Button(buttons,text="Export animation.h",command=export,state="disabled")
    export_button.pack(side="left",fill="x",expand=True,padx=(8,0))
    root.mainloop()

if __name__=="__main__":
    if not cmdline():
        run_gui()
