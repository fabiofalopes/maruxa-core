import platform
import subprocess
import sys
import os

def check_dependencies():
    system = platform.system()
    
    if system == 'Windows':
        print("Checking Windows dependencies...")
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True)
            print("FFmpeg found!")
        except FileNotFoundError:
            print("""
FFmpeg not found! Please install FFmpeg:
1. Download from https://ffmpeg.org/download.html
2. Add to system PATH
Or use Chocolatey: choco install ffmpeg
            """)
            sys.exit(1)
            
    elif system == 'Linux':
        print("Checking Linux dependencies...")
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True)
            print("FFmpeg found!")
        except FileNotFoundError:
            print("""
FFmpeg not found! Please install FFmpeg:
For Debian/Ubuntu: sudo apt-get install ffmpeg
For other distributions, use your package manager
            """)
            sys.exit(1)

if __name__ == "__main__":
    check_dependencies()