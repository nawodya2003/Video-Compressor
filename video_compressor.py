#!/usr/bin/env python3
"""
🎬 VideoPress - Facebook-Optimized Video Compressor
Fast, high-quality compression with a sleek GUI
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import subprocess
import threading
import os
import time
import json
import re
import shutil
from pathlib import Path

# ─── Theme ────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Simple Presets
SIMPLE_PRESETS = {
    "🌟 Optimal (Recommended - High Quality, Small Size)": {"codec": "libx265", "crf": 28, "preset": "medium"},
    "💎 High Quality (Larger File Size)": {"codec": "libx265", "crf": 23, "preset": "slow"},
    "📱 Smallest File (For sharing on mobile)": {"codec": "libx265", "crf": 34, "preset": "fast"},
    "📺 Max Compatibility (Old devices - H.264)": {"codec": "libx264", "crf": 23, "preset": "medium"},
}


def get_video_info(path: str) -> dict:
    """Get video metadata via ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_streams", "-show_format",
        path
    ]
    info = {"duration": 0, "size_mb": 0, "width": 0, "height": 0, "fps": 0, "codec": ""}
    if not shutil.which("ffprobe"):
        return info
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        fmt = data.get("format", {})
        info["duration"] = float(fmt.get("duration", 0))
        info["size_mb"] = os.path.getsize(path) / (1024 * 1024)
        for s in data.get("streams", []):
            if s.get("codec_type") == "video":
                info["width"]  = s.get("width", 0)
                info["height"] = s.get("height", 0)
                info["codec"]  = s.get("codec_name", "")
                fps_str = s.get("r_frame_rate", "30/1")
                num, den = fps_str.split("/")
                info["fps"] = round(int(num) / int(den), 2)
                break
    except Exception:
        pass
    return info


class VideoCompressorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🎬 VideoPress — Facebook Optimizer")
        self.geometry("780x720")
        self.resizable(False, False)
        self.configure(fg_color="#181611")

        self.input_path  = tk.StringVar()
        self.output_path = tk.StringVar()
        self.preset_var  = tk.StringVar(value=list(SIMPLE_PRESETS.keys())[0])
        self._proc       = None
        self._start_time = 0
        self._duration   = 0

        self._build_ui()
        self.after(500, self._check_dependencies)

    def _check_dependencies(self):
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            messagebox.showerror(
                "Missing Dependencies",
                "FFmpeg is not installed or not found in your system PATH.\n\n"
                "This application requires FFmpeg and FFprobe to compress videos.\n\n"
                "Please install FFmpeg and restart the application."
            )
            self._compress_btn.configure(state="disabled")

    # ── UI Construction ────────────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="#241e12", corner_radius=0, height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header,
            text="🎬  VideoPress",
            font=ctk.CTkFont("Courier", 26, "bold"),
            text_color="#ffd700"
        ).place(x=24, y=10)
        ctk.CTkLabel(
            header,
            text="Facebook-Optimized Video Compressor",
            font=ctk.CTkFont("Courier", 11),
            text_color="#d4af37"
        ).place(x=26, y=44)

        # Body
        body = ctk.CTkScrollableFrame(self, fg_color="#181611", scrollbar_button_color="#2d2516")
        body.pack(fill="both", expand=True, padx=16, pady=(10, 0))

        self._section(body, "📂  INPUT FILE")
        row = ctk.CTkFrame(body, fg_color="transparent")
        row.pack(fill="x", pady=(0, 6))
        self._input_entry = ctk.CTkEntry(
            row, textvariable=self.input_path,
            placeholder_text="Select a video file…",
            height=40, font=ctk.CTkFont("Courier", 12),
            fg_color="#2d2516", border_color="#8c6f2d"
        )
        self._input_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            row, text="Browse", width=90, height=40,
            fg_color="#8c6f2d", hover_color="#b38e3a",
            font=ctk.CTkFont("Courier", 12, "bold"),
            command=self._browse_input
        ).pack(side="right")

        self._info_frame = ctk.CTkFrame(body, fg_color="#241e12", corner_radius=8)
        self._info_frame.pack(fill="x", pady=(0, 12))
        self._info_label = ctk.CTkLabel(
            self._info_frame, text="  No file selected",
            font=ctk.CTkFont("Courier", 11), text_color="#8f805b", anchor="w"
        )
        self._info_label.pack(fill="x", padx=12, pady=8)

        self._section(body, "🎯  COMPRESSION QUALITY")
        self._preset_menu = ctk.CTkOptionMenu(
            body, values=list(SIMPLE_PRESETS.keys()),
            variable=self.preset_var,
            height=40, font=ctk.CTkFont("Courier", 12),
            fg_color="#2d2516", button_color="#8c6f2d", button_hover_color="#b38e3a",
            dropdown_fg_color="#2d2516",
        )
        self._preset_menu.pack(fill="x", pady=(0, 12))

        self._section(body, "💾  OUTPUT FILE")
        out_row = ctk.CTkFrame(body, fg_color="transparent")
        out_row.pack(fill="x", pady=(0, 16))
        self._output_entry = ctk.CTkEntry(
            out_row, textvariable=self.output_path,
            placeholder_text="Output path (auto-set when input is selected)…",
            height=40, font=ctk.CTkFont("Courier", 12),
            fg_color="#2d2516", border_color="#8c6f2d"
        )
        self._output_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            out_row, text="Browse", width=90, height=40,
            fg_color="#8c6f2d", hover_color="#b38e3a",
            font=ctk.CTkFont("Courier", 12, "bold"),
            command=self._browse_output
        ).pack(side="right")

        # Bottom bar (fixed)
        bottom = ctk.CTkFrame(self, fg_color="#14120e", corner_radius=0, height=180)
        bottom.pack(fill="x", side="bottom")
        bottom.pack_propagate(False)

        # Progress
        prog_frame = ctk.CTkFrame(bottom, fg_color="transparent")
        prog_frame.pack(fill="x", padx=16, pady=(12, 4))
        self._progress = ctk.CTkProgressBar(
            prog_frame, height=14,
            progress_color="#ffd700", fg_color="#2d2516", corner_radius=6
        )
        self._progress.pack(fill="x")
        self._progress.set(0)

        stats_row = ctk.CTkFrame(bottom, fg_color="transparent")
        stats_row.pack(fill="x", padx=16, pady=(0, 6))
        self._pct_label   = ctk.CTkLabel(stats_row, text="0%",   font=ctk.CTkFont("Courier", 11, "bold"), text_color="#ffd700")
        self._pct_label.pack(side="left")
        self._time_label  = ctk.CTkLabel(stats_row, text="",     font=ctk.CTkFont("Courier", 11), text_color="#d4af37")
        self._time_label.pack(side="left", padx=(12, 0))
        self._eta_label   = ctk.CTkLabel(stats_row, text="",     font=ctk.CTkFont("Courier", 11), text_color="#d4af37")
        self._eta_label.pack(side="right")

        self._status_label = ctk.CTkLabel(
            bottom, text="Ready to compress",
            font=ctk.CTkFont("Courier", 12), text_color="#8f805b"
        )
        self._status_label.pack(pady=(0, 8))

        btn_row = ctk.CTkFrame(bottom, fg_color="transparent")
        btn_row.pack(pady=(0, 12))
        self._compress_btn = ctk.CTkButton(
            btn_row, text="▶  COMPRESS VIDEO", width=220, height=46,
            fg_color="#b8860b", hover_color="#daa520",
            font=ctk.CTkFont("Courier", 15, "bold"),
            command=self._start_compression
        )
        self._compress_btn.pack(side="left", padx=8)
        self._cancel_btn = ctk.CTkButton(
            btn_row, text="✕  Cancel", width=100, height=46,
            fg_color="#4a4131", hover_color="#c62828",
            font=ctk.CTkFont("Courier", 13, "bold"),
            command=self._cancel,
            state="disabled"
        )
        self._cancel_btn.pack(side="left", padx=8)

    # ── Helpers ────────────────────────────────────────────────────────────────
    def _section(self, parent, title):
        ctk.CTkLabel(
            parent, text=title,
            font=ctk.CTkFont("Courier", 11, "bold"),
            text_color="#8f805b", anchor="w"
        ).pack(fill="x", pady=(8, 4))

    def _browse_input(self):
        path = filedialog.askopenfilename(
            title="Select Video",
            filetypes=[("Video files", "*.mp4 *.mov *.avi *.mkv *.webm *.flv *.wmv *.m4v *.ts"), ("All", "*.*")]
        )
        if not path:
            return
        self.input_path.set(path)
        stem = Path(path).stem
        out  = str(Path(path).parent / f"{stem}_compressed_fb.mp4")
        self.output_path.set(out)
        self._load_info(path)

    def _browse_output(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".mp4",
            filetypes=[("MP4", "*.mp4")]
        )
        if path:
            self.output_path.set(path)

    def _load_info(self, path):
        info = get_video_info(path)
        self._duration = info["duration"]
        mins, secs = divmod(int(self._duration), 60)
        txt = (
            f"  📹 {info['width']}×{info['height']}  |  "
            f"⏱ {mins}m {secs:02d}s  |  "
            f"📦 {info['size_mb']:.1f} MB  |  "
            f"🎞 {info['fps']} fps  |  "
            f"🔤 {info['codec'].upper()}"
        )
        self._info_label.configure(text=txt, text_color="#b0bec5")

    # ── Compression ────────────────────────────────────────────────────────────
    def _build_ffmpeg_cmd(self, inp, out, cfg):
        codec = cfg["codec"]
        crf = cfg["crf"]
        preset = cfg["preset"]

        cmd = [
            "ffmpeg", "-y",
            "-i", inp,
            "-c:v", codec,
            "-preset", preset,
            "-crf", str(crf),
            "-movflags", "+faststart",
            "-pix_fmt", "yuv420p",
        ]
        
        if codec == "libx265":
            cmd += ["-tag:v", "hvc1"]
        else:
            cmd += ["-profile:v", "high", "-level", "4.0"]
            
        cmd += ["-c:a", "aac", "-b:a", "128k", "-ar", "44100"]
        cmd += [out]
        return cmd

    def _start_compression(self):
        inp = self.input_path.get().strip()
        out = self.output_path.get().strip()
        if not inp or not os.path.isfile(inp):
            messagebox.showerror("Error", "Please select a valid input video.")
            return
        if not out:
            messagebox.showerror("Error", "Please set an output path.")
            return

        cfg = SIMPLE_PRESETS[self.preset_var.get()]
        cmd = self._build_ffmpeg_cmd(inp, out, cfg)

        self._compress_btn.configure(state="disabled")
        self._cancel_btn.configure(state="normal")
        self._progress.set(0)
        self._start_time = time.time()

        threading.Thread(target=self._run_ffmpeg, args=(cmd, out), daemon=True).start()

    def _run_ffmpeg(self, cmd, out):
        self._set_status("🔄  Compressing…", "#4fc3f7")
        try:
            self._proc = subprocess.Popen(
                cmd,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                encoding="utf-8",
                errors="replace"
            )
            for line in self._proc.stderr:
                self._parse_progress(line)
            self._proc.wait()
            if self._proc.returncode == 0:
                self._on_done(out)
            elif self._proc.returncode != -9:
                self._set_status("❌  Compression failed.", "#ef5350")
        except Exception as e:
            self._set_status(f"❌  Error: {e}", "#ef5350")
        finally:
            self._reset_buttons()



    def _parse_progress(self, line, offset=0.0, scale=1.0):
        # Parse ffmpeg's time= output
        m = re.search(r"time=(\d+):(\d+):([\d.]+)", line)
        if m and self._duration > 0:
            elapsed_vid = int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3))
            frac = min(offset + scale * (elapsed_vid / self._duration), 1.0)
            pct  = int(frac * 100)
            wall = time.time() - self._start_time
            speed_str = ""
            eta_str   = ""
            if frac > 0.01:
                total_est = wall / frac
                eta       = max(0, total_est - wall)
                m2, s2    = divmod(int(eta), 60)
                eta_str   = f"ETA {m2}m {s2:02d}s"
                spd_match = re.search(r"speed=([\d.]+)x", line)
                if spd_match:
                    speed_str = f"  {spd_match.group(1)}×speed"
            wm, ws = divmod(int(wall), 60)
            self.after(0, lambda p=frac, pc=pct, t=f"Elapsed {wm}m {ws:02d}s{speed_str}", e=eta_str: (
                self._progress.set(p),
                self._pct_label.configure(text=f"{pc}%"),
                self._time_label.configure(text=t),
                self._eta_label.configure(text=e),
            ))

    def _on_done(self, out):
        dur  = time.time() - self._start_time
        mins, secs = divmod(int(dur), 60)
        size = os.path.getsize(out) / (1024*1024) if os.path.exists(out) else 0
        self.after(0, lambda: (
            self._progress.set(1.0),
            self._pct_label.configure(text="100%"),
            self._eta_label.configure(text="Done!"),
            self._set_status(
                f"✅  Done in {mins}m {secs:02d}s  —  Output: {size:.1f} MB  →  {out}",
                "#66bb6a"
            )
        ))
        self.after(0, lambda: messagebox.showinfo(
            "✅ Compression Complete",
            f"Video compressed successfully!\n\n"
            f"⏱  Time taken : {mins}m {secs:02d}s\n"
            f"📦  Output size: {size:.1f} MB\n"
            f"📂  Saved to   : {out}"
        ))

    def _cancel(self):
        if self._proc:
            self._proc.kill()
        self._set_status("⛔  Cancelled.", "#ffa726")
        self._reset_buttons()
        self._progress.set(0)
        self._pct_label.configure(text="0%")

    def _set_status(self, msg, color="#546e7a"):
        self.after(0, lambda: self._status_label.configure(text=msg, text_color=color))

    def _reset_buttons(self):
        self.after(0, lambda: (
            self._compress_btn.configure(state="normal"),
            self._cancel_btn.configure(state="disabled"),
        ))


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = VideoCompressorApp()
    app.mainloop()
