import subprocess
import os

def run_ffmpeg_auto_encode(input_path, temp_path):
    """Run FFmpeg to re-encode input_path to temp_path with smear-friendly settings."""
    ffmpeg_cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-c:v", "libxvid",
        "-bf", "2",
        "-g", "150",
        "-keyint_min", "150",
        "-sc_threshold", "0",
        "-an",
        temp_path
    ]
    subprocess.run(ffmpeg_cmd, check=True)

def cleanup_temp_file(path):
    """Delete a file if it exists."""
    if os.path.exists(path):
        try:
            os.remove(path)
            return True
        except Exception:
            return False
    return False 