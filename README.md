# Audio Recording and Transcription Tool

A Python-based tool for recording audio and performing transcription.

## System Requirements

### Windows Setup

1. Install Chocolatey package manager
   - Visit https://chocolatey.org/install#individual
   - Follow the installation instructions for individual use

2. Install FFmpeg using Chocolatey
   ```powershell
   choco install ffmpeg
   ```

3. Verify FFmpeg installation
   ```powershell
   ffmpeg -version
   ```

4. Audio Device Configuration
   - Ensure your microphone is properly connected and set as default input device
   - Check Windows Sound Settings to confirm microphone permissions are enabled
   - The application will list available audio input devices on startup

### Linux Setup

1. Install required audio and FFmpeg packages:

   For Ubuntu/Debian:
   ```bash
   sudo apt-get update
   sudo apt-get install python3-pyaudio portaudio19-dev
   sudo apt-get install ffmpeg
   sudo apt-get install alsa-utils
   ```

   For Fedora:
   ```bash
   sudo dnf install python3-pyaudio portaudio-devel
   sudo dnf install ffmpeg
   sudo dnf install alsa-utils
   ```

2. Configure ALSA:
   ```bash
   sudo alsactl init
   ```

3. Add your user to the audio group:
   ```bash
   sudo usermod -a -G audio $USER
   ```
   Note: You'll need to log out and back in for this change to take effect.

4. Verify audio device detection:
   ```bash
   arecord -l
   ```

## Common Issues

### Windows
- If FFmpeg is not found: Restart your terminal/IDE after installing FFmpeg
- Audio device not found: Check Windows Sound Settings and ensure microphone permissions are enabled

### Linux
- ALSA device errors: Run `alsamixer` to check if your input device is muted
- Permission denied: Ensure you're part of the `audio` group
- Device busy: Check if another application is using the audio device

## Virtual Environment Setup

It's recommended to run this application in a virtual environment:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

1. Run the application:
```bash
python src/main.py
```

2. The application will:
   - List available audio input devices
   - Start recording (press 'q' to stop)
   - Process the audio
   - Perform transcription

## Notes

- The application requires proper audio input device configuration on your system
- FFmpeg must be available in your system PATH
- Audio files are temporarily stored in the 'recordings' directory
