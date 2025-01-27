import os
import hashlib
import json
from typing import Optional, List, Dict
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
    Settings,
    Document
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

class IndexManager:
    def __init__(
        self,
        persist_dir: str = "./.index_store",
        notes_dir: str = "./notes",
        embedding_model_name: str = "BAAI/bge-small-en-v1.5"
    ):
        self.persist_dir = persist_dir
        self.notes_dir = notes_dir
        self.console = Console()
        self.notes_state_file = os.path.join(persist_dir, "notes_state.json")
        self.notes_state: Dict[str, str] = {}  # filename -> hash
        self.documents = []
        self.index = None
        
        # Set global settings for LlamaIndex
        Settings.embed_model = HuggingFaceEmbedding(
            model_name=embedding_model_name
        )
        
        # Load previous state if exists
        self._load_notes_state()
        
        # Initialize index
        self._load_or_create_index()

    def display_documents_info(self):
        """Display information about currently indexed documents."""
        if not self.documents:
            self.console.print("[yellow]No documents currently indexed[/yellow]")
            return

        table = Table(title="Indexed Documents")
        table.add_column("Filename", style="cyan")
        table.add_column("Size", justify="right")
        table.add_column("Preview", style="green")

        for doc in self.documents:
            # Access text and metadata from the node
            text = doc.text if hasattr(doc, 'text') else str(doc)
            filename = doc.metadata.get('file_name', 'Unknown') if hasattr(doc, 'metadata') else 'Unknown'
            
            # Calculate size in characters
            size = f"{len(text)} chars"
            
            # Get preview (first 100 characters)
            preview = text[:100] + "..." if len(text) > 100 else text
            
            table.add_row(filename, size, preview)

        self.console.print(table)

    def get_document_quotes(self, query: str, llm, num_quotes: int = 3) -> List[Dict]:
        """Get relevant quotes from documents based on a query."""
        if not self.index:
            return []

        # Create a retriever instead of using query engine
        retriever = self.index.as_retriever(similarity_top_k=num_quotes)
        nodes = retriever.retrieve(query)
        
        quotes = []
        for node in nodes:
            quotes.append({
                'text': node.text,
                'file': node.metadata.get('file_name', 'Unknown'),
                'score': node.score if hasattr(node, 'score') else 0.0
            })
            
        return quotes

    def _get_file_hash(self, filepath: str) -> str:
        """Calculate MD5 hash of a file."""
        hasher = hashlib.md5()
        with open(filepath, 'rb') as f:
            buf = f.read(65536)  # Read in 64kb chunks
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(65536)
        return hasher.hexdigest()

    def _load_notes_state(self):
        """Load the previous state of notes."""
        if os.path.exists(self.notes_state_file):
            with open(self.notes_state_file, 'r') as f:
                self.notes_state = json.load(f)

    def _save_notes_state(self):
        """Save the current state of notes."""
        os.makedirs(self.persist_dir, exist_ok=True)
        with open(self.notes_state_file, 'w') as f:
            json.dump(self.notes_state, f)

    def _should_update_index(self) -> bool:
        """Check if index needs to be updated based on notes directory."""
        if not os.path.exists(self.notes_dir):
            return False

        # Get current files and their hashes
        current_files = {}
        changes = {
            'new': [],
            'modified': [],
            'deleted': []
        }
        
        # Check for new or modified files
        for filename in os.listdir(self.notes_dir):
            if filename.startswith('.'):
                continue
                
            filepath = os.path.join(self.notes_dir, filename)
            if os.path.isfile(filepath):
                current_hash = self._get_file_hash(filepath)
                current_files[filename] = current_hash
                
                if filename not in self.notes_state:
                    changes['new'].append(filename)
                    self.console.print(f"[yellow]New file detected: {filename}[/yellow]")
                elif self.notes_state[filename] != current_hash:
                    changes['modified'].append(filename)
                    self.console.print(f"[yellow]Modified file detected: {filename}[/yellow]")
        
        # Check for deleted files
        for filename in self.notes_state:
            if filename not in current_files:
                changes['deleted'].append(filename)
                self.console.print(f"[yellow]Deleted file detected: {filename}[/yellow]")
        
        needs_update = any(changes.values())
        
        if needs_update:
            self.notes_state = current_files
            self._save_notes_state()
            return True
            
        self.console.print("[dim]No changes detected in notes. Using existing index.[/dim]")
        return False

    def _load_or_create_index(self) -> Optional[VectorStoreIndex]:
        """Load existing index or create a new one if needed."""
        try:
            if not os.path.exists(self.notes_dir):
                os.makedirs(self.notes_dir)
                self.console.print("[dim]Created empty notes directory[/dim]")
                return None
                
            if self._should_update_index():
                return self.create_index_from_directory(self.notes_dir)
                
            if os.path.exists(self.persist_dir):
                storage_context = StorageContext.from_defaults(
                    persist_dir=self.persist_dir
                )
                self.index = load_index_from_storage(storage_context)
                # Store the nodes directly instead of just their text
                self.documents = list(self.index.docstore.docs.values())
                self.console.print("[green]Successfully loaded existing index[/green]")
                self.display_documents_info()
                return self.index
                
            return None
                
        except Exception as e:
            self.console.print(f"[red]Error loading/creating index: {str(e)}[/red]")
            return None

    def create_index_from_directory(
        self,
        directory_path: str,
        exclude_hidden: bool = True
    ) -> VectorStoreIndex:
        """Create a new index from documents in a directory."""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TimeElapsedColumn(),
                console=self.console
            ) as progress:
                # Load documents
                task1 = progress.add_task("Loading documents...", total=None)
                self.documents = SimpleDirectoryReader(
                    directory_path,
                    exclude_hidden=exclude_hidden
                ).load_data()
                progress.update(task1, completed=True)
                
                # Display loaded documents
                self.display_documents_info()
                
                # Create index
                task2 = progress.add_task("Creating index...", total=None)
                self.index = VectorStoreIndex.from_documents(self.documents)
                progress.update(task2, completed=True)
                
                # Persist index
                task3 = progress.add_task("Persisting index...", total=None)
                os.makedirs(self.persist_dir, exist_ok=True)
                self.index.storage_context.persist(persist_dir=self.persist_dir)
                progress.update(task3, completed=True)
                
            self.console.print("[green]Successfully created and persisted new index[/green]")
            return self.index
            
        except Exception as e:
            self.console.print(f"[red]Error creating index: {str(e)}[/red]")
            raise

    def get_query_engine(self, llm):
        """Get query engine from the current index."""
        if not self.index:
            self.console.print("[yellow]No index available. Please check if there are documents in the notes directory.[/yellow]")
            return None
        return self.index.as_query_engine(llm=llm)

    def refresh_index(self, directory_path: str) -> None:
        """Refresh the index with new documents."""
        # Remove existing index
        if os.path.exists(self.persist_dir):
            import shutil
            shutil.rmtree(self.persist_dir)
        
        # Create new index
        self.create_index_from_directory(directory_path)
