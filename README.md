# 🎬 VideoPress - Video Compressor

A simple and fast desktop application to compress your videos and reduce their file size while maintaining excellent quality.

## Prerequisites

Before running the application, make sure you have the following installed:

1. **Python 3.8+**: [Download Python here](https://www.python.org/downloads/)
2. **FFmpeg**: This application requires FFmpeg to handle the heavy lifting of video compression.
   - **Windows (Recommended - using winget)**: 
     1. Open PowerShell or Command Prompt.
     2. Run the command: `winget install ffmpeg`
     3. Restart your terminal and the application.
   - **Windows (Manual)**: Download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/), extract it, and add the `bin` folder to your system's PATH.

## Installation

1. Open your terminal or command prompt in the project folder.
2. Install the required Python packages using pip:
   ```bash
   pip install customtkinter
   ```

## How to Run

Run the application by executing the Python script in your terminal:

```bash
python video_compressor.py
```

## How to Use

1. **Select a Video**: Click the **Browse** button in the "INPUT FILE" section to select the video you want to compress.
2. **Choose a Quality Preset**: Select how much you want to compress the video from the dropdown menu. (e.g., "Optimal" is a great balance of size and quality).
3. **Compress**: Click the big **▶ COMPRESS VIDEO** button at the bottom.
4. **Done!**: The application will show a progress bar. Once finished, your compressed video will be saved in the same folder as the original file, with `_compressed` added to the filename!
