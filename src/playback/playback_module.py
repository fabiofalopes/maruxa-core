import sounddevice as sd
import soundfile as sf
import threading
import time
import platform
from pynput import keyboard
from rich.console import Console
from rich.progress import Progress
from typing import Optional
import numpy as np

class AudioController:
    def __init__(self):
        self.console = Console()
        self.is_playing = False
        self.is_paused = False
        self.stream = None
        self.current_frame = 0
        self.total_frames = 0
        self.data = None
        self.samplerate = None
        self.paused = False
        self.should_stop = False
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()

    def play_audio(self, audio_file: str):
        """Start playing audio with controls"""
        try:
            # Load the audio file
            self.data, self.samplerate = sf.read(audio_file)
            self.total_frames = len(self.data)
            self.current_frame = 0
            self.is_playing = True
            self.is_paused = False

            # Ensure data is in the correct shape (convert mono to stereo if needed)
            if len(self.data.shape) == 1:
                self.data = self.data.reshape(-1, 1)

            total_duration = len(self.data) / self.samplerate
            
            # Print controls before progress bar
            self.console.print("\nPlaying Audio Response")
            self.console.print("\nControls:")
            self.console.print("p: Pause/Resume | s: Stop | q: Quit")
            self.console.print("←/→: Skip 1s | ⇧←/⇧→: Skip 10s\n")
            
            with Progress() as progress:
                task = progress.add_task("", total=100)
                
                def callback(outdata, frames, time, status):
                    if status:
                        self.console.print(f"[red]Status: {status}[/red]")
                    
                    if self.is_paused:
                        outdata.fill(0)
                        return
                    
                    if self.current_frame + frames > len(self.data):
                        remaining = len(self.data) - self.current_frame
                        outdata[:remaining] = self.data[self.current_frame:len(self.data)]
                        outdata[remaining:] = 0
                        self.is_playing = False
                        raise sd.CallbackStop()
                    else:
                        outdata[:] = self.data[self.current_frame:self.current_frame + frames]
                        self.current_frame += frames
                        # Update progress
                        progress.update(task, completed=(self.current_frame / len(self.data)) * 100)

                # Create and start the stream
                channels = self.data.shape[1]
                self.stream = sd.OutputStream(
                    samplerate=self.samplerate,
                    channels=channels,
                    callback=callback
                )

                def check_input():
                    while self.is_playing:
                        if self.paused:
                            time.sleep(0.2)  # Debounce
                        elif self.should_stop:
                            self.is_playing = False
                            break
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

    def _skip_frames(self, frames):
        """Skip forward or backward in the audio"""
        new_position = self.current_frame + frames
        if 0 <= new_position < self.total_frames:
            self.current_frame = new_position
            skip_seconds = frames / self.samplerate
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

    def on_press(self, key):
        try:
            if hasattr(key, 'char'):  # Regular keys
                if key.char == 'p':
                    self.paused = not self.paused
                elif key.char == 's':
                    self.should_stop = True
                elif key.char == 'q':
                    self.should_stop = True
                    return False  # Stop listener
            elif key == keyboard.Key.left:
                self._skip_frames(-int(self.samplerate))
            elif key == keyboard.Key.right:
                self._skip_frames(int(self.samplerate))
        except AttributeError:
            pass

    def __del__(self):
        if hasattr(self, 'listener'):
            self.listener.stop()

# Create a singleton instance
audio_controller = AudioController()

# Function to maintain backward compatibility
def play_audio(audio_file: str):
    """Backward compatible function for playing audio"""
    audio_controller.play_audio(audio_file)

# Export both the class and the function
__all__ = ['AudioController', 'audio_controller', 'play_audio']
