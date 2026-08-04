from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.document_ingestion import DocumentIngestionService
from app.schemas.knowledge import KnowledgeSearchResponse
from app.services.knowledge_service import KnowledgeService

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(q: str, top_k: int = 5, db: AsyncSession = Depends(get_db)) -> KnowledgeSearchResponse:
    service = KnowledgeService(db)
    result = await service.search(q, top_k=top_k)
    return KnowledgeSearchResponse(query=result.query, chunks=result.chunks)


@router.post("/documents")
async def ingest_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    service = DocumentIngestionService(db)
    content = await file.read()
    document = await service.ingest_bytes(content, file.filename or "document.txt", title=None)
    await db.commit()
    return {"document_id": str(document.id), "title": document.title}
