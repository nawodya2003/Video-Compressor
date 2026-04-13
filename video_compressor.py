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
from pathlib import Path

# ─── Theme ────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Facebook recommended settings
FB_PRESETS = {
    "Facebook Feed (1080p)"  : {"width": 1920, "height": 1080, "bitrate": "4000k",  "audio": "192k", "fps": 30},
    "Facebook Reel (9:16)"   : {"width": 1080, "height": 1920, "bitrate": "5000k",  "audio": "192k", "fps": 30},
    "Facebook Story (1080p)" : {"width": 1080, "height": 1920, "bitrate": "3500k",  "audio": "128k", "fps": 30},
    "Facebook Lite (720p)"   : {"width": 1280, "height": 720,  "bitrate": "2500k",  "audio": "128k", "fps": 30},
    "Max Quality (4K ready)" : {"width": 3840, "height": 2160, "bitrate": "8000k",  "audio": "256k", "fps": 60},
}

SPEED_PRESETS = {
    "⚡ Ultra Fast": "ultrafast",
    "🚀 Very Fast" : "veryfast",
    "⚖️  Balanced"  : "medium",
    "🎯 Best Quality": "slow",
}


def get_video_info(path: str) -> dict:
    """Get video metadata via ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_streams", "-show_format",
        path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)
    info = {"duration": 0, "size_mb": 0, "width": 0, "height": 0, "fps": 0, "codec": ""}
    try:
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
        self.configure(fg_color="#0f0f13")

        self.input_path  = tk.StringVar()
        self.output_path = tk.StringVar()
        self.preset_var  = tk.StringVar(value=list(FB_PRESETS.keys())[0])
        self.speed_var   = tk.StringVar(value=list(SPEED_PRESETS.keys())[1])
        self.crf_var     = tk.IntVar(value=23)
        self.two_pass    = tk.BooleanVar(value=False)
        self.remove_audio = tk.BooleanVar(value=False)
        self._proc       = None
        self._start_time = 0
        self._duration   = 0

        self._build_ui()

    # ── UI Construction ────────────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="#1a1a2e", corner_radius=0, height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header,
            text="🎬  VideoPress",
            font=ctk.CTkFont("Courier", 26, "bold"),
            text_color="#4fc3f7"
        ).place(x=24, y=10)
        ctk.CTkLabel(
            header,
            text="Facebook-Optimized Video Compressor",
            font=ctk.CTkFont("Courier", 11),
            text_color="#607d8b"
        ).place(x=26, y=44)

        # Body
        body = ctk.CTkScrollableFrame(self, fg_color="#0f0f13", scrollbar_button_color="#1e1e2e")
        body.pack(fill="both", expand=True, padx=16, pady=(10, 0))

        self._section(body, "📂  INPUT FILE")
        row = ctk.CTkFrame(body, fg_color="transparent")
        row.pack(fill="x", pady=(0, 6))
        self._input_entry = ctk.CTkEntry(
            row, textvariable=self.input_path,
            placeholder_text="Select a video file…",
            height=40, font=ctk.CTkFont("Courier", 12),
            fg_color="#1e1e2e", border_color="#2d3561"
        )
        self._input_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            row, text="Browse", width=90, height=40,
            fg_color="#2d3561", hover_color="#3d4a8a",
            font=ctk.CTkFont("Courier", 12, "bold"),
            command=self._browse_input
        ).pack(side="right")

        self._info_frame = ctk.CTkFrame(body, fg_color="#1a1a2e", corner_radius=8)
        self._info_frame.pack(fill="x", pady=(0, 12))
        self._info_label = ctk.CTkLabel(
            self._info_frame, text="  No file selected",
            font=ctk.CTkFont("Courier", 11), text_color="#546e7a", anchor="w"
        )
        self._info_label.pack(fill="x", padx=12, pady=8)

        self._section(body, "🎯  FACEBOOK PRESET")
        self._preset_menu = ctk.CTkOptionMenu(
            body, values=list(FB_PRESETS.keys()),
            variable=self.preset_var,
            height=40, font=ctk.CTkFont("Courier", 12),
            fg_color="#1e1e2e", button_color="#2d3561", button_hover_color="#3d4a8a",
            dropdown_fg_color="#1e1e2e",
        )
        self._preset_menu.pack(fill="x", pady=(0, 12))

        self._section(body, "⚡  COMPRESSION SPEED")
        speed_row = ctk.CTkFrame(body, fg_color="transparent")
        speed_row.pack(fill="x", pady=(0, 12))
        for label in SPEED_PRESETS:
            ctk.CTkRadioButton(
                speed_row, text=label, variable=self.speed_var, value=label,
                font=ctk.CTkFont("Courier", 11),
                fg_color="#4fc3f7", hover_color="#0288d1"
            ).pack(side="left", padx=(0, 18))

        self._section(body, "🎚️  QUALITY (CRF)  — lower = better quality, larger file")
        crf_row = ctk.CTkFrame(body, fg_color="transparent")
        crf_row.pack(fill="x", pady=(0, 2))
        self._crf_label = ctk.CTkLabel(
            crf_row, text=f"CRF: {self.crf_var.get()}",
            font=ctk.CTkFont("Courier", 13, "bold"), text_color="#4fc3f7", width=70
        )
        self._crf_label.pack(side="left")
        ctk.CTkSlider(
            crf_row, from_=0, to=51, number_of_steps=51,
            variable=self.crf_var,
            progress_color="#2d3561", button_color="#4fc3f7", button_hover_color="#81d4fa",
            command=lambda v: self._crf_label.configure(text=f"CRF: {int(v)}")
        ).pack(side="left", fill="x", expand=True, padx=(8, 0))

        hint_row = ctk.CTkFrame(body, fg_color="transparent")
        hint_row.pack(fill="x", pady=(2, 12))
        for val, lbl, col in [(18, "Excellent", "#66bb6a"), (23, "Good (default)", "#4fc3f7"),
                               (28, "Acceptable", "#ffa726"), (35, "Small file", "#ef5350")]:
            ctk.CTkLabel(
                hint_row, text=f"{val}={lbl}",
                font=ctk.CTkFont("Courier", 10), text_color=col
            ).pack(side="left", padx=(0, 16))

        # Extra options
        self._section(body, "🔧  OPTIONS")
        opts_row = ctk.CTkFrame(body, fg_color="transparent")
        opts_row.pack(fill="x", pady=(0, 12))
        ctk.CTkCheckBox(
            opts_row, text="Two-Pass Encoding (best bitrate accuracy)",
            variable=self.two_pass,
            font=ctk.CTkFont("Courier", 11),
            fg_color="#4fc3f7", hover_color="#0288d1"
        ).pack(side="left", padx=(0, 24))
        ctk.CTkCheckBox(
            opts_row, text="Remove Audio",
            variable=self.remove_audio,
            font=ctk.CTkFont("Courier", 11),
            fg_color="#4fc3f7", hover_color="#0288d1"
        ).pack(side="left")

        self._section(body, "💾  OUTPUT FILE")
        out_row = ctk.CTkFrame(body, fg_color="transparent")
        out_row.pack(fill="x", pady=(0, 16))
        self._output_entry = ctk.CTkEntry(
            out_row, textvariable=self.output_path,
            placeholder_text="Output path (auto-set when input is selected)…",
            height=40, font=ctk.CTkFont("Courier", 12),
            fg_color="#1e1e2e", border_color="#2d3561"
        )
        self._output_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            out_row, text="Browse", width=90, height=40,
            fg_color="#2d3561", hover_color="#3d4a8a",
            font=ctk.CTkFont("Courier", 12, "bold"),
            command=self._browse_output
        ).pack(side="right")

        # Bottom bar (fixed)
        bottom = ctk.CTkFrame(self, fg_color="#12121a", corner_radius=0, height=180)
        bottom.pack(fill="x", side="bottom")
        bottom.pack_propagate(False)

        # Progress
        prog_frame = ctk.CTkFrame(bottom, fg_color="transparent")
        prog_frame.pack(fill="x", padx=16, pady=(12, 4))
        self._progress = ctk.CTkProgressBar(
            prog_frame, height=14,
            progress_color="#4fc3f7", fg_color="#1e1e2e", corner_radius=6
        )
        self._progress.pack(fill="x")
        self._progress.set(0)

        stats_row = ctk.CTkFrame(bottom, fg_color="transparent")
        stats_row.pack(fill="x", padx=16, pady=(0, 6))
        self._pct_label   = ctk.CTkLabel(stats_row, text="0%",   font=ctk.CTkFont("Courier", 11, "bold"), text_color="#4fc3f7")
        self._pct_label.pack(side="left")
        self._time_label  = ctk.CTkLabel(stats_row, text="",     font=ctk.CTkFont("Courier", 11), text_color="#607d8b")
        self._time_label.pack(side="left", padx=(12, 0))
        self._eta_label   = ctk.CTkLabel(stats_row, text="",     font=ctk.CTkFont("Courier", 11), text_color="#607d8b")
        self._eta_label.pack(side="right")

        self._status_label = ctk.CTkLabel(
            bottom, text="Ready to compress",
            font=ctk.CTkFont("Courier", 12), text_color="#546e7a"
        )
        self._status_label.pack(pady=(0, 8))

        btn_row = ctk.CTkFrame(bottom, fg_color="transparent")
        btn_row.pack(pady=(0, 12))
        self._compress_btn = ctk.CTkButton(
            btn_row, text="▶  COMPRESS VIDEO", width=220, height=46,
            fg_color="#1565c0", hover_color="#1976d2",
            font=ctk.CTkFont("Courier", 15, "bold"),
            command=self._start_compression
        )
        self._compress_btn.pack(side="left", padx=8)
        self._cancel_btn = ctk.CTkButton(
            btn_row, text="✕  Cancel", width=100, height=46,
            fg_color="#37474f", hover_color="#c62828",
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
            text_color="#37474f", anchor="w"
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
    def _build_ffmpeg_cmd(self, inp, out, preset_cfg, speed, crf):
        w, h      = preset_cfg["width"],   preset_cfg["height"]
        vb        = preset_cfg["bitrate"]
        ab        = preset_cfg["audio"]
        fps       = preset_cfg["fps"]
        enc_speed = SPEED_PRESETS[speed]

        # Scale filter: fit within preset dims while keeping aspect ratio
        vf = (
            f"scale='if(gt(iw/ih,{w}/{h}),{w},-2)':"
            f"'if(gt(iw/ih,{w}/{h}),-2,{h})',"
            f"fps={fps}"
        )

        cmd = [
            "ffmpeg", "-y",
            "-i", inp,
            "-vf", vf,
            "-c:v", "libx264",
            "-preset", enc_speed,
            "-crf", str(crf),
            "-b:v", vb,
            "-maxrate", vb,
            "-bufsize", f"{int(vb[:-1])*2}k",
            "-movflags", "+faststart",   # web-optimised (fb likes this)
            "-pix_fmt", "yuv420p",
        ]
        if self.remove_audio.get():
            cmd += ["-an"]
        else:
            cmd += ["-c:a", "aac", "-b:a", ab, "-ar", "44100"]
        cmd += ["-profile:v", "high", "-level", "4.0", out]
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

        preset_cfg = FB_PRESETS[self.preset_var.get()]
        speed      = self.speed_var.get()
        crf        = self.crf_var.get()
        cmd        = self._build_ffmpeg_cmd(inp, out, preset_cfg, speed, crf)

        self._compress_btn.configure(state="disabled")
        self._cancel_btn.configure(state="normal")
        self._progress.set(0)
        self._start_time = time.time()

        if self.two_pass.get():
            threading.Thread(target=self._run_two_pass, args=(inp, out, preset_cfg, speed, crf), daemon=True).start()
        else:
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

    def _run_two_pass(self, inp, out, preset_cfg, speed, crf):
        self._set_status("🔄  Pass 1/2…", "#ffa726")
        tmp_log = "/tmp/ffmpeg2pass"
        vb      = preset_cfg["bitrate"]
        fps     = preset_cfg["fps"]
        w, h    = preset_cfg["width"], preset_cfg["height"]
        enc_speed = SPEED_PRESETS[speed]
        vf = f"scale='if(gt(iw/ih,{w}/{h}),{w},-2)':'if(gt(iw/ih,{w}/{h}),-2,{h})',fps={fps}"

        pass1 = [
            "ffmpeg", "-y", "-i", inp,
            "-vf", vf,
            "-c:v", "libx264", "-preset", enc_speed,
            "-b:v", vb, "-pass", "1", "-passlogfile", tmp_log,
            "-an", "-f", "null", "/dev/null"
        ]
        pass2 = [
            "ffmpeg", "-y", "-i", inp,
            "-vf", vf,
            "-c:v", "libx264", "-preset", enc_speed,
            "-crf", str(crf), "-b:v", vb,
            "-maxrate", vb, "-bufsize", f"{int(vb[:-1])*2}k",
            "-pass", "2", "-passlogfile", tmp_log,
            "-movflags", "+faststart", "-pix_fmt", "yuv420p",
        ]
        if self.remove_audio.get():
            pass2 += ["-an"]
        else:
            pass2 += ["-c:a", "aac", "-b:a", preset_cfg["audio"], "-ar", "44100"]
        pass2 += ["-profile:v", "high", "-level", "4.0", out]

        try:
            self._proc = subprocess.Popen(pass1, stderr=subprocess.PIPE, universal_newlines=True, encoding="utf-8", errors="replace")
            for line in self._proc.stderr:
                self._parse_progress(line, scale=0.5)
            self._proc.wait()

            self._set_status("🔄  Pass 2/2…", "#4fc3f7")
            self._proc = subprocess.Popen(pass2, stderr=subprocess.PIPE, universal_newlines=True, encoding="utf-8", errors="replace")
            for line in self._proc.stderr:
                self._parse_progress(line, offset=0.5, scale=0.5)
            self._proc.wait()

            if self._proc.returncode == 0:
                self._on_done(out)
            else:
                self._set_status("❌  Compression failed.", "#ef5350")
        except Exception as e:
            self._set_status(f"❌  Error: {e}", "#ef5350")
        finally:
            self._reset_buttons()
            for f in Path("/tmp").glob("ffmpeg2pass*"):
                try: f.unlink()
                except: pass

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
