import os
from audio_processing.recorder import AudioRecorder
from audio_processing.preprocess import preprocess_audio
from stt.groq_whisper import GroqWhisperAPI
from config.config import RECORDINGS_DIR

def main():
    # Initialize components with absolute paths
    recordings_dir = RECORDINGS_DIR
    recorder = AudioRecorder(output_directory=recordings_dir)
    transcriber = GroqWhisperAPI()
    
    raw_audio_path = None
    processed_audio_path = None
    
    try:
        # First list available devices to help with debugging
        print("\nAvailable audio input devices:")
        recorder.list_input_devices()
        print("\n")
        
        # 1. Record audio
        print("Starting recording... Press Ctrl+C to stop.")
        raw_audio_path = recorder.record_until_q("raw_recording.wav")
        
        if not raw_audio_path:
            print("Recording failed.")
            return
            
        # 2. Preprocess audio
        processed_audio_path = os.path.join(recordings_dir, 'processed_recording.wav')
        if preprocess_audio(raw_audio_path, processed_audio_path):
            print("Audio preprocessed successfully.")
        else:
            print("Audio preprocessing failed.")
            return
            
        # 3. Transcribe
        print("Transcribing audio...")
        transcription = transcriber.transcribe_audio(processed_audio_path)
        
        print("\nTranscription:")
        print("-" * 50)
        print(transcription)
        print("-" * 50)
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
