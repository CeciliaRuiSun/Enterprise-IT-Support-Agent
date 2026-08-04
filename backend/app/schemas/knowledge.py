from uuid import UUID

from pydantic import BaseModel, Field


class KnowledgeSearchRequest(BaseModel):
    q: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=10)


class KnowledgeChunk(BaseModel):
    chunk_id: UUID
    document_id: UUID
    title: str
    content: str
    chunk_index: int
    page_number: int | None = None
    score: float | None = None
    metadata: dict | None = None


class KnowledgeSearchResponse(BaseModel):
    query: str
    chunks: list[KnowledgeChunk]

