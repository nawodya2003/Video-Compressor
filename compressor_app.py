import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os
import threading

def compress_video():
    # වීඩියෝ එක තෝරන්න Window එකක් විවෘත කිරීම 📂
    input_file = filedialog.askopenfilename(
        title="Select Video to Compress 🎬",
        filetypes=(("Video Files", "*.mp4 *.avi *.mov *.mkv"), ("All Files", "*.*"))
    )
    
    if not input_file:
        return

    # UI එකේ තත්වය වෙනස් කිරීම ⏳
    status_label.config(text="⏳ Compress වෙමින් පවතී... කරුණාකර රැඳී සිටින්න!", fg="blue")
    compress_btn.config(state=tk.DISABLED)

    # App එක Freeze නොවී තියෙන්න Thread එකක් මගින් Run කිරීම 🚀
    threading.Thread(target=run_ffmpeg, args=(input_file,)).start()

def run_ffmpeg(input_file):
    # අලුත් වීඩියෝ එකට නමක් සෑදීම (උදා: video_compressed.mp4) 🏷️
    filename, ext = os.path.splitext(input_file)
    output_file = f"{filename}_compressed{ext}"

    # FFmpeg විධානය ⚙️
    command = [
        'ffmpeg', '-i', input_file,
        '-vcodec', 'libx264', '-preset', 'faster',
        '-crf', '24', '-acodec', 'aac', '-b:a', '128k',
        '-y', output_file
    ]

    try:
        # Window එකක් නැතිව Background එකේ Run කිරීම
        subprocess.run(command, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        
        # සාර්ථකව අවසන් වූ විට 🟢
        status_label.config(text="✅ සාර්ථකව Compress කර අවසන්!", fg="green")
        messagebox.showinfo("Success 🎉", f"වීඩියෝ එක සුපිරියට Compress වුණා!\n\nSave වුණ ස්ථානය:\n{output_file}")
    except Exception as e:
        # දෝෂයක් ආවොත් 🔴
        status_label.config(text="❌ දෝෂයක් මතු විය!", fg="red")
        messagebox.showerror("Error ⚠️", "FFmpeg ක්‍රියාත්මක වීමේදී දෝෂයක්! FFmpeg Install කර Path එකට ලබා දී ඇත්දැයි පරීක්ෂා කරන්න.")
    finally:
        # බොත්තම නැවත සක්‍රිය කිරීම 🔄
        compress_btn.config(state=tk.NORMAL)

# ප්‍රධාන UI Window එක සෑදීම 🖥️
root = tk.Tk()
root.title("FB Video Compressor Pro 🚀")
root.geometry("450x250")
root.eval('tk::PlaceWindow . center') # මැදට ගන්න

# මාතෘකාව 📌
title_label = tk.Label(root, text="Facebook Video Compressor 🎬", font=("Helvetica", 14, "bold"))
title_label.pack(pady=20)

# බොත්තම 🔘
compress_btn = tk.Button(root, text="📁 වීඩියෝව තෝරන්න (Select Video)", font=("Helvetica", 12), bg="#4CAF50", fg="white", command=compress_video)
compress_btn.pack(pady=10)

# තත්වය පෙන්වන ස්ථානය ℹ️
status_label = tk.Label(root, text="ඉහත බොත්තම ඔබා වීඩියෝවක් තෝරාගන්න 👆", font=("Helvetica", 10))
status_label.pack(pady=20)

# App එක Run කිරීම 🏃‍♂️
root.mainloop()