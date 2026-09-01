from abc import ABC, abstractmethod
from typing import Any, Dict, List

from retrieval.document_models import Chunk


class VectorStoreAdapter(ABC):
    """
    Abstract interface for vector stores (e.g., Qdrant, Pinecone, Redis).
    """
    @abstractmethod
    def search(self, query_embedding: List[float], top_k: int, filters: Dict[str, Any] = None) -> List[Chunk]:
        pass
    
    @abstractmethod
    def insert(self, chunks: List[Chunk], embeddings: List[List[float]]) -> None:
        pass

class InMemoryVectorStore(VectorStoreAdapter):
    """
    Dummy implementation for local testing without a DB.
    """
    def __init__(self):
        self.chunks = []
        
    def search(self, query_embedding: List[float], top_k: int, filters: Dict[str, Any] = None) -> List[Chunk]:
        return self.chunks[:top_k]
        
    def insert(self, chunks: List[Chunk], embeddings: List[List[float]]) -> None:
        self.chunks.extend(chunks)
