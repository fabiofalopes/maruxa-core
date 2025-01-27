from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
    Settings,
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import os
from typing import Optional

class RAGEngine:
    def __init__(
        self,
        persist_dir: str = "./.index_store",
        embedding_model_name: str = "BAAI/bge-small-en-v1.5"
    ):
        self.persist_dir = persist_dir
        Settings.embed_model = HuggingFaceEmbedding(
            model_name=embedding_model_name
        )
        self.index = self._load_or_create_index()

    def _load_or_create_index(self) -> Optional[VectorStoreIndex]:
        if os.path.exists(self.persist_dir):
            storage_context = StorageContext.from_defaults(
                persist_dir=self.persist_dir
            )
            return load_index_from_storage(storage_context)
        return None

    def create_index_from_directory(self, directory_path: str) -> VectorStoreIndex:
        documents = SimpleDirectoryReader(directory_path).load_data()
        self.index = VectorStoreIndex.from_documents(documents)
        os.makedirs(self.persist_dir, exist_ok=True)
        self.index.storage_context.persist(persist_dir=self.persist_dir)
        return self.index

    def get_query_engine(self, llm):
        if not self.index:
            raise ValueError("No index available. Please create an index first.")
        return self.index.as_query_engine(llm=llm)
