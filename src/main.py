from rich.console import Console
from workflows.voice_assistant import VoiceAssistantWorkflow
from utils.index_manager import IndexManager

def main():
    console = Console()
    console.clear()
    
    # Initialize components
    index_manager = IndexManager()
    assistant = VoiceAssistantWorkflow(index_manager)
    
    console.print("[bold blue]Voice Assistant[/bold blue]")
    console.print("[dim]Press Enter to start a new interaction, or 'q' to quit[/dim]")
    
    while True:
        try:
            key = input()
            if key.lower() == 'q':
                console.print("[yellow]Goodbye![/yellow]")
                break
                
            # Start voice interaction
            assistant.process_voice_input()
            console.print("\n[dim]Press Enter for new interaction, or 'q' to quit[/dim]")
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Interaction cancelled[/yellow]")
            console.print("[dim]Press Enter for new interaction, or 'q' to quit[/dim]")
            continue
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            console.print("[dim]Press Enter to try again, or 'q' to quit[/dim]")

if __name__ == "__main__":
    main()
