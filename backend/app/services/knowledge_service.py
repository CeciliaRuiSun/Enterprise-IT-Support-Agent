from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.common import DocumentChunk
from app.schemas.knowledge import KnowledgeChunk
from app.services.embeddings import EmbeddingService


@dataclass
class KnowledgeSearchResult:
    query: str
    chunks: list[KnowledgeChunk]


class KnowledgeService:
    def __init__(self, db: AsyncSession, embedding_service: EmbeddingService | None = None) -> None:
        self.db = db
        self.embedding_service = embedding_service or EmbeddingService()

    async def search(self, query: str, top_k: int = 5) -> KnowledgeSearchResult:
        embedding = self.embedding_service.embed_query(query)
        if embedding:
            stmt = (
                select(
                    DocumentChunk.id,
                    DocumentChunk.document_id,
                    DocumentChunk.content,
                    DocumentChunk.chunk_index,
                    DocumentChunk.page_number,
                    DocumentChunk.chunk_metadata,
                    func.coalesce(DocumentChunk.chunk_metadata["title"].astext, "").label("title"),
                    func.coalesce(DocumentChunk.chunk_metadata["source_path"].astext, "").label("source_path"),
                    DocumentChunk.embedding.cosine_distance(embedding).label("score"),
                )
                .order_by(DocumentChunk.embedding.cosine_distance(embedding))
                .limit(top_k)
            )
            rows = (await self.db.execute(stmt)).all()
            chunks = [
                KnowledgeChunk(
                    chunk_id=row.id,
                    document_id=row.document_id,
                    title=row.title or row.chunk_metadata.get("title", "Knowledge Chunk") if row.chunk_metadata else "Knowledge Chunk",
                    content=row.content,
                    chunk_index=row.chunk_index,
                    page_number=row.page_number,
                    score=float(row.score) if row.score is not None else None,
                    metadata=row.chunk_metadata,
                )
                for row in rows
            ]
            return KnowledgeSearchResult(query=query, chunks=chunks)

        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.content.ilike(f"%{query}%"))
            .order_by(DocumentChunk.created_at.desc())
            .limit(top_k)
        )
        rows = (await self.db.scalars(stmt)).all()
        chunks = [
            KnowledgeChunk(
                chunk_id=row.id,
                document_id=row.document_id,
                title=row.chunk_metadata.get("title", "Knowledge Chunk") if row.chunk_metadata else "Knowledge Chunk",
                content=row.content,
                chunk_index=row.chunk_index,
                page_number=row.page_number,
                score=None,
                metadata=row.chunk_metadata,
            )
            for row in rows
        ]
        return KnowledgeSearchResult(query=query, chunks=chunks)
