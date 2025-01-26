import os
from audio_processing.recorder import AudioRecorder
from audio_processing.preprocess import preprocess_audio
from stt.groq_whisper import GroqWhisperAPI

def main():
    # Initialize components
    recorder = AudioRecorder(output_directory='recordings')
    transcriber = GroqWhisperAPI()
    
    raw_audio_path = None
    processed_audio_path = None
    
    try:
        # First list available devices to help with debugging
        print("\nAvailable audio input devices:")
        recorder.list_input_devices()
        print("\n")
        
        # 1. Record audio (press Ctrl+C to stop recording)
        print("Starting recording... Press Ctrl+C to stop.")
        raw_audio_path = recorder.record_until_q("raw_recording.wav")
        
        if not raw_audio_path:
            print("Recording failed.")
            return
            
        # 2. Preprocess audio (downsample to 16kHz mono)
        processed_audio_path = os.path.join('recordings', 'processed_recording.wav')
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
        
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Cleanup temporary files
        try:
            if raw_audio_path and os.path.exists(raw_audio_path):
                os.remove(raw_audio_path)
            if processed_audio_path and os.path.exists(processed_audio_path):
                os.remove(processed_audio_path)
        except Exception as e:
            print(f"Error during cleanup: {e}")

if __name__ == "__main__":
    main()
