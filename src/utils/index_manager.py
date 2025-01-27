import os
from typing import Optional, List
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
    Settings,
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

class IndexManager:
    def __init__(
        self,
        persist_dir: str = "./.index_store",
        embedding_model_name: str = "BAAI/bge-small-en-v1.5"
    ):
        self.persist_dir = persist_dir
        # Initialize embedding model
        Settings.embed_model = HuggingFaceEmbedding(
            model_name=embedding_model_name
        )
        self.index = self._load_or_create_index()

    def _load_or_create_index(self) -> VectorStoreIndex:
        """Load existing index or create a new one if it doesn't exist."""
        if os.path.exists(self.persist_dir):
            storage_context = StorageContext.from_defaults(
                persist_dir=self.persist_dir
            )
            return load_index_from_storage(storage_context)
        return None

    def create_index_from_directory(
        self,
        directory_path: str,
        exclude_hidden: bool = True
    ) -> VectorStoreIndex:
        """Create a new index from documents in a directory."""
        try:
            documents = SimpleDirectoryReader(
                directory_path,
                exclude_hidden=exclude_hidden
            ).load_data()
            
            self.index = VectorStoreIndex.from_documents(documents)
            
            # Persist the index
            os.makedirs(self.persist_dir, exist_ok=True)
            self.index.storage_context.persist(persist_dir=self.persist_dir)
            
            return self.index
        except Exception as e:
            raise Exception(f"Error creating index: {str(e)}")

    def get_query_engine(self, llm=None):
        """Get a query engine from the index."""
        if self.index is None:
            raise ValueError("No index available. Please create or load an index first.")
        return self.index.as_query_engine(llm=llm)

    def refresh_index(self, directory_path: str) -> None:
        """Refresh the index with new documents."""
        # Remove existing index
        if os.path.exists(self.persist_dir):
            import shutil
            shutil.rmtree(self.persist_dir)
        
        # Create new index
        self.create_index_from_directory(directory_path)