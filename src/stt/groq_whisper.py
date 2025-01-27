import os
from typing import Optional, Union, List
from groq import Groq
from config.config import GROQ_API_KEY  # Changed to absolute import
import traceback
from pydub import AudioSegment

#from post_processing.analyzer import TextAnalyzer  # Changed to absolute import

class GroqWhisperAPI:
    models = [
        "distil-whisper-large-v3-en",
        "whisper-large-v3",
        "whisper-large-v3-turbo"
    ]

    SELECTED_MODEL = models[2]

    def __init__(self):
        self.selected_model = self.models[0]
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set in environment variables.")
        
        # Initialize the client directly with the API key
        self.client = Groq(api_key=GROQ_API_KEY)
        #self.analyzer = TextAnalyzer()

    def transcribe_audio(
        self,
        file_path: str,
        model_id: Optional[str] = None,
        prompt: Optional[str] = None,
        response_format: str = 'json',
        language: Optional[str] = None,
        temperature: Optional[float] = None,
        timestamp_granularities: Optional[List[str]] = None,
        product_names: Optional[List[str]] = None
    ) -> Union[dict, str]:
        try:
            model_id = model_id or self.SELECTED_MODEL
            file_size = os.path.getsize(file_path)
            if file_size > 25 * 1024 * 1024:  # 25 MB
                chunks = _split_audio(file_path)
                transcriptions = []
                for chunk in chunks:
                    with open(chunk, "rb") as file:
                        transcription = self.client.audio.transcriptions.create(
                            file=(os.path.basename(chunk), file.read()),
                            model=model_id,
                            prompt=prompt,
                            response_format=response_format,
                            language=language,
                            temperature=temperature,
                            timestamp_granularities=timestamp_granularities
                        )
                    transcriptions.append(transcription.text if response_format != 'json' else transcription.to_dict()['text'])
                full_transcription = " ".join(transcriptions)
            else:
                with open(file_path, "rb") as file:
                    transcription = self.client.audio.transcriptions.create(
                        file=(os.path.basename(file_path), file.read()),
                        model=model_id,
                        prompt=prompt,
                        response_format=response_format,
                        language=language,
                        temperature=temperature,
                        timestamp_granularities=timestamp_granularities
                    )
                #full_transcription = transcription.text if response_format != 'json' else transcription.to_dict()['text']
            return transcription.text

        except Exception as e:
            print(f"An error occurred during transcription: {e}")
            traceback.print_exc()
            return {"error": str(e)}

    def translate_audio(
        self,
        file_path: str,
        model_id: str = SELECTED_MODEL,
        prompt: Optional[str] = None,
        response_format: str = 'json',
        language: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> Union[dict, str]:
        try:
            with open(file_path, "rb") as file:
                translation = self.client.audio.translations.create(
                    file=(os.path.basename(file_path), file.read()),
                    model=model_id,
                    prompt=prompt,
                    response_format=response_format,
                    language=language,
                    temperature=temperature
                )
            if response_format == 'json':
                return translation.to_dict()
            else:
                return translation.text
        except Exception as e:
            print(f"An error occurred during translation: {e}")
            traceback.print_exc()  # Print the full traceback for detailed debugging
            return {"error": str(e)}

def _split_audio(file_path: str, chunk_duration: int = 10 * 60 * 1000) -> List[str]:
    """
    Split a large audio file into smaller chunks.
    
    :param file_path: Path to the audio file
    :param chunk_duration: Duration of each chunk in milliseconds (default: 10 minutes)
    :return: List of paths to the split audio files
    """
    audio = AudioSegment.from_file(file_path)
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    chunks = []

    for i, chunk in enumerate(audio[::chunk_duration]):
        chunk_name = f"{base_name}_chunk_{i}.mp3"
        chunk.export(chunk_name, format="mp3")
        chunks.append(chunk_name)

    return chunks
