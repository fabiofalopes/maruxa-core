import ffmpeg
import os
import platform
import subprocess
from pathlib import Path
from config.config import VOICE_OUTPUTS_DIR

def check_ffmpeg():
    """Check if FFmpeg is available in the system."""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True)
        return True
    except FileNotFoundError:
        return False

def get_ffmpeg_path():
    """Get the FFmpeg path based on the platform."""
    system = platform.system()
    if system == 'Windows':
        # Check common Windows installation paths
        possible_paths = [
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
            os.path.join(os.environ.get('PROGRAMFILES', ''), 'ffmpeg', 'bin', 'ffmpeg.exe'),
            os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), 'ffmpeg', 'bin', 'ffmpeg.exe')
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
    return 'ffmpeg'  # Default to system PATH

def preprocess_audio(input_path: str, output_path: str) -> bool:
    """
    Preprocess the audio file to downsample to 16,000 Hz mono.
    """
    try:
        # Convert paths to absolute paths
        input_path = os.path.abspath(input_path)
        output_path = os.path.abspath(output_path)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Check if FFmpeg is available
        if not check_ffmpeg():
            print("FFmpeg not found. Please ensure FFmpeg is installed and in your system PATH.")
            return False

        ffmpeg_path = get_ffmpeg_path()
        
        # Use subprocess directly for better cross-platform compatibility
        command = [
            ffmpeg_path,
            '-i', input_path,
            '-ar', '16000',
            '-ac', '1',
            '-y',  # Overwrite output file if it exists
            output_path
        ]
        
        subprocess.run(command, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error preprocessing audio: {e}")
        print(f"FFmpeg stderr: {e.stderr.decode()}")
        return False
    except Exception as e:
        print(f"Error preprocessing audio: {e}")
        return False
