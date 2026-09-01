from typing import Dict, Optional

from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    tenant: str
    auth_scope: str
    corpus_version: str
    source: str
    timestamp: Optional[str] = None
    custom: Dict[str, str] = Field(default_factory=dict)

class Chunk(BaseModel):
    id: str
    document_id: str
    content: str
    metadata: ChunkMetadata
    score: Optional[float] = None
