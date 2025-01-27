import pygame
import threading

def play_audio(file_path):
    """
    Play audio file using pygame.

    Args:
        file_path (str): Path to the audio file
    """
    def _play():
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        except Exception as e:
            print(f"Error playing audio: {e}")

    playback_thread = threading.Thread(target=_play)
    playback_thread.start()
