from typing import Optional
from rich.console import Console
from rich.progress import Progress
from llama_index.core.llms import ChatMessage
from stt.groq_whisper import GroqWhisperAPI
from tts.edge_tts_integration import create_audio
from llm.groq_llm import GroqLLMWrapper
from utils.index_manager import IndexManager
from audio_processing.recorder import AudioRecorder
from playback.playback_module import audio_controller
from config.config import RECORDINGS_DIR
import os

class VoiceAssistantWorkflow:
    def __init__(self, index_manager: IndexManager):
        self.console = Console()
        self.recorder = AudioRecorder(output_directory=RECORDINGS_DIR)
        self.stt = GroqWhisperAPI()
        self.llm_wrapper = GroqLLMWrapper()
        self.index_manager = index_manager
        self.audio_controller = audio_controller
        
        # Load system prompts
        self.system_prompt = self._load_prompt("system_prompt.md")
        self.speech_prompt = self._load_prompt("speech_prompt.md")

    def process_voice_input(self) -> Optional[str]:
        try:
            # Recording and transcription
            self.console.print("[bold green]Recording...[/bold green] (Press Ctrl+C to stop)")
            audio_path = self.recorder.record_until_q("input.wav")
            
            text = self.stt.transcribe_audio(audio_path)
            self.console.print(f"\n[blue]Transcribed:[/blue] {text}")
            
            # Check if notes directory is empty
            if not os.path.exists("notes") or not os.listdir("notes"):
                response = "Não encontrei nenhuma nota para consultar. Por favor, adicione alguns documentos à pasta 'notes' primeiro."
                self.console.print(f"\n[yellow]{response}[/yellow]")
                return response
            
            # Query and LLM processing
            with Progress() as progress:
                task = progress.add_task("[yellow]Processing query...", total=None)
                try:
                    query_engine = self.index_manager.get_query_engine(self.llm_wrapper.get_llm())
                    if query_engine is None:
                        raise ValueError("No index available")
                    rag_response = query_engine.query(text)
                    progress.update(task, completed=True)
                except Exception as e:
                    progress.update(task, completed=True)
                    raise ValueError("Não foi possível processar a consulta. Verifique se existem documentos na pasta 'notes'.")

            # Process with LLM and show response
            messages = [
                ChatMessage(role="system", content=self.system_prompt),
                ChatMessage(role="user", content=f"User input: {text}\nQuery result: {str(rag_response)}")
            ]
            llm_response = self.llm_wrapper.chat(messages)
            
            self.console.print("\n[green]Assistant Response:[/green]")
            self.console.print(f"[white]{llm_response}[/white]\n")
            
            # Convert to speech-optimized format
            speech_messages = [
                ChatMessage(role="system", content=self.speech_prompt),
                ChatMessage(role="user", content=llm_response)
            ]
            speech_text = self.llm_wrapper.chat(speech_messages)
            
            # Generate and play audio
            self.console.print("[dim]Generating audio response...[/dim]")
            audio_file = create_audio(speech_text)
            if audio_file:
                self.console.print("\n[bold]Playing Audio Response[/bold]")
                self.audio_controller.play_audio(audio_file)
            
            return speech_text
            
        except Exception as e:
            self.console.print(f"[red]Error in workflow: {str(e)}[/red]")
            return None

    def _load_prompt(self, filename: str) -> str:
        prompt_path = os.path.join("src", "prompts", filename)
        try:
            # Explicitly specify UTF-8 encoding
            with open(prompt_path, "r", encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            self.console.print(f"[yellow]Warning: {filename} not found[/yellow]")
            return ""
