import sounddevice as sd
import soundfile as sf
import threading
import time
import select
import sys
from rich.console import Console
from rich.progress import Progress
from typing import Optional

class AudioController:
    def __init__(self):
        self.console = Console()
        self.is_playing = False
        self.is_paused = False
        self._pause_event = threading.Event()

    def play_audio(self, audio_file: str):
        """Start playing audio with controls"""
        try:
            # Load the audio file
            self.data, samplerate = sf.read(audio_file)
            self.data_pos = 0
            self.is_playing = True
            self.is_paused = False
            total_duration = len(self.data) / samplerate
            
            # Print controls before progress bar
            self.console.print("\n[dim]Controls:[/dim]")
            self.console.print("[dim]p: Pause/Resume | s: Stop | q: Quit[/dim]")
            self.console.print("[dim]←/→: Skip 1s | ⇧←/⇧→: Skip 10s[/dim]\n")
            
            with Progress() as progress:
                task = progress.add_task("", total=100)
                
                def callback(outdata, frames, time, status):
                    if status:
                        self.console.print(f"[red]Status: {status}[/red]")
                    
                    if self.is_paused:
                        outdata.fill(0)
                        return
                    
                    if self.data_pos < len(self.data):
                        if len(self.data.shape) == 1:
                            chunk = self.data[self.data_pos:self.data_pos + frames]
                            outdata[:len(chunk), 0] = chunk
                            outdata[len(chunk):] = 0
                        else:
                            chunk = self.data[self.data_pos:self.data_pos + frames]
                            outdata[:len(chunk)] = chunk
                            outdata[len(chunk):] = 0
                        
                        self.data_pos += frames
                        # Update progress
                        progress.update(task, completed=(self.data_pos / len(self.data)) * 100)
                    else:
                        self.is_playing = False
                        raise sd.CallbackStop()

                # Create and start the stream
                channels = 2 if len(self.data.shape) > 1 else 1
                self.stream = sd.OutputStream(
                    samplerate=samplerate,
                    channels=channels,
                    callback=callback
                )

                def check_input():
                    while self.is_playing:
                        if sys.stdin.isatty():
                            if select.select([sys.stdin], [], [], 0.1)[0]:
                                key = sys.stdin.read(1)
                                if key in ['p', 'P']:
                                    self._toggle_pause()
                                elif key in ['s', 'S', 'q', 'Q']:
                                    self._stop()
                                    break
                                elif key == '\x1b':  # Arrow key prefix
                                    key = sys.stdin.read(2)
                                    if key == '[D':  # Left arrow
                                        self._skip(-1 * samplerate)
                                    elif key == '[C':  # Right arrow
                                        self._skip(1 * samplerate)
                                    elif key == '[1':  # Shift + arrow
                                        next_key = sys.stdin.read(2)
                                        if next_key == ';2':
                                            direction = sys.stdin.read(1)
                                            if direction == 'D':  # Shift + Left
                                                self._skip(-10 * samplerate)
                                            elif direction == 'C':  # Shift + Right
                                                self._skip(10 * samplerate)
                        time.sleep(0.1)

                # Start input checking in a separate thread
                input_thread = threading.Thread(target=check_input)
                input_thread.daemon = True
                input_thread.start()

                # Start audio playback
                with self.stream:
                    while self.is_playing:
                        time.sleep(0.1)

        except Exception as e:
            self.console.print(f"[red]Error playing audio: {str(e)}[/red]")
            self.is_playing = False

    def _skip(self, frames):
        """Skip forward or backward in the audio"""
        new_pos = self.data_pos + int(frames)
        if 0 <= new_pos < len(self.data):
            self.data_pos = new_pos
            skip_seconds = frames / self.stream.samplerate
            direction = "→" if frames > 0 else "←"
            self.console.print(f"[dim]{direction} {abs(skip_seconds)}s[/dim]")

    def _toggle_pause(self):
        """Toggle pause/resume"""
        self.is_paused = not self.is_paused
        status = "⏸ Paused" if self.is_paused else "▶ Resumed"
        self.console.print(f"[dim]{status}[/dim]")

    def _stop(self):
        """Stop playback"""
        self.is_playing = False
        self.console.print("[dim]⏹ Stopped[/dim]")

# Create a singleton instance
audio_controller = AudioController()

# Function to maintain backward compatibility
def play_audio(audio_file: str):
    """Backward compatible function for playing audio"""
    audio_controller.play_audio(audio_file)

# Export both the class and the function
__all__ = ['AudioController', 'audio_controller', 'play_audio']
