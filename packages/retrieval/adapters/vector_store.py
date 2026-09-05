from abc import ABC, abstractmethod
from typing import Any

from retrieval.document_models import Chunk


class VectorStoreAdapter(ABC):
    """
    Abstract interface for vector stores (e.g., Qdrant, Pinecone, Redis).
    """

    @abstractmethod
    def search(
        self, query_embedding: list[float], top_k: int, filters: dict[str, Any] = None
    ) -> list[Chunk]:
        pass

    @abstractmethod
    def insert(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        pass


class InMemoryVectorStore(VectorStoreAdapter):
    """
    Dummy implementation for local testing without a DB.
    """

    def __init__(self):
        self.chunks = []

    def search(
        self, query_embedding: list[float], top_k: int, filters: dict[str, Any] = None
    ) -> list[Chunk]:
        return self.chunks[:top_k]

    def insert(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        self.chunks.extend(chunks)
