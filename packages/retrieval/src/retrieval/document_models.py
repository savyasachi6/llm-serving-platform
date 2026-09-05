from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    tenant: str
    auth_scope: str
    corpus_version: str
    source: str
    timestamp: str | None = None
    custom: dict[str, str] = Field(default_factory=dict)


class Chunk(BaseModel):
    id: str
    document_id: str
    content: str
    metadata: ChunkMetadata
    score: float | None = None
