import asyncio
import edge_tts
from datetime import datetime
import os
from config.config import VOICE_OUTPUTS_DIR

SELECT_VOICE = ["pt-PT-RaquelNeural", "pt-PT-DuarteNeural"]

async def generate_speech(text, output_file, voice="pt-PT-DuarteNeural"):
    """
    Generate speech from text using edge-tts

    Args:
        text (str): Text to convert to speech
        output_file (str): Output audio file path
        voice (str): Voice to use (default: Portuguese male voice)
    """
    communicate = edge_tts.Communicate(
        text,
        voice,
        rate="+25%",    # Speed up by 25%
        volume="+0%",   # Default volume
        pitch="+10Hz"   # Default pitch
    )
    await communicate.save(output_file)

def create_audio(text):
    """
    Synchronously generate audio from text.

    Args:
        text (str): Text to convert to speech

    Returns:
        str: Path to the generated audio file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    audio_file = f"tts_output_{timestamp}.mp3"
    audio_file_path = os.path.join(VOICE_OUTPUTS_DIR, audio_file)
    
    try:
        asyncio.run(generate_speech(
            text=text,
            output_file=audio_file_path,
            voice=SELECT_VOICE[0]
        ))
        print(f"Audio file generated: {audio_file_path}")
        return audio_file_path
    except Exception as e:
        print(f"Error generating speech: {str(e)}")
        return None
