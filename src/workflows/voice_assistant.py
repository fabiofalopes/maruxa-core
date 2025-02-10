from typing import Optional
from rich.console import Console
from rich.progress import Progress
from llama_index.core.llms import ChatMessage
from stt.groq_whisper import GroqWhisperAPI
from tts.edge_tts_integration import create_audio
from llm.groq_llm import GroqLLMWrapper  # Groq LLM via API
from llm.local_llm import LocalLLMWrapper  # Local LLM
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
        self.index_manager = index_manager
        self.audio_controller = audio_controller
        
        # Add conversation history
        self.conversation_history = []
        
        # Load prompts
        #self.system_prompt = self._load_prompt("system_prompt.md")
        self.system_prompt = self._load_prompt("system_prompt_lus.md")

        self.speech_prompt = self._load_prompt("speech_prompt.md")
        

        '''
        Change the LLM instances between Groq and Local
        '''
        
        # Create specialized LLM instances (Groq LLM)
        ## ------------ 
        self.thinking_llm = GroqLLMWrapper.create_thinking_llm(self.system_prompt)
        self.speech_llm = GroqLLMWrapper.create_speech_llm(self.speech_prompt)
        ## ------------ 

        # Create specialized LLM instances (Local LLM)
        ## ------------ 
        ###self.thinking_llm = LocalLLMWrapper.create_thinking_llm(self.system_prompt)
        ###self.speech_llm = LocalLLMWrapper.create_speech_llm(self.speech_prompt)
        ## ------------ 

        '''
        Above - Change the LLM instances between Groq and Local 
        '''



    def process_voice_input(self):

        try:
            # Recording and transcription
            self.console.print("[bold green]Recording...[/bold green] (Press Ctrl+C to stop)")
            audio_path = self.recorder.record_until_q("input.wav")
            
            text = self.stt.transcribe_audio(audio_path)
            self.console.print(f"\n[blue]Transcribed:[/blue] {text}")
            
            # Query and LLM processing
            with Progress() as progress:
                task = progress.add_task("[yellow]Processing query...", total=None)
                try:
                    # Add user input to history
                    self.conversation_history.append(
                        ChatMessage(role="user", content=text)
                    )
                    
                    # First stage: Get relevant documents and detailed thinking with context
                    query_engine = self.index_manager.get_query_engine(self.thinking_llm.get_llm())
                    if query_engine is None:
                        raise ValueError("No index available")
                    
                    # Get and display relevant documents concisely
                    quotes = self.index_manager.get_document_quotes(text, self.thinking_llm.get_llm(), num_quotes=2)
                    if quotes:
                        self.console.print("\n[dim]Referencing documents:[/dim]")
                        for quote in quotes:
                            self.console.print(f"[dim]• {quote['file']} (relevance: {quote['score']:.2f})[/dim]")
                    
                    detailed_response = query_engine.query(text)
                    
                    # Second stage: Convert to natural speech
                    speech_messages = [
                        *self.conversation_history[-4:],  # Include last 2 exchanges (4 messages)
                        ChatMessage(role="user", content=f"Convert this response to natural speech: {detailed_response}")
                    ]
                    natural_response = self.speech_llm.chat(speech_messages)
                    
                    # Add assistant's response to history
                    self.conversation_history.append(
                        ChatMessage(role="assistant", content=natural_response)
                    )
                    
                    progress.update(task, completed=True)
                    
                    # Display both responses for debugging
                    self.console.print(f"\n[cyan]Detailed Response:[/cyan] {detailed_response}")
                    self.console.print(f"\n[green]Natural Speech Response:[/green] {natural_response}")
                    
                    # Convert to speech using the natural response
                    audio_file = create_audio(natural_response)
                    if audio_file:
                        progress.stop()
                        self.audio_controller.play_audio(audio_file)
                        
                except Exception as e:
                    progress.update(task, completed=True)
                    self.console.print(f"[red]Error processing query: {str(e)}[/red]")
                    raise ValueError("Não foi possível processar a consulta. Verifique se existem documentos na pasta 'notes'.")
                    
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Recording cancelled[/yellow]")
        except Exception as e:
            self.console.print(f"\n[red]Error in workflow: {str(e)}[/red]")
            
        self.console.print("\n[dim]Press Enter for new interaction, or 'q' to quit[/dim]")

    def _load_prompt(self, filename: str) -> str:
        prompt_path = os.path.join("src", "prompts", filename)
        try:
            # Explicitly specify UTF-8 encoding
            with open(prompt_path, "r", encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            self.console.print(f"[yellow]Warning: {filename} not found[/yellow]")
            return ""
