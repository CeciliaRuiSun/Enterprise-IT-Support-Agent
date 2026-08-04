from __future__ import annotations

from app.schemas.knowledge import KnowledgeSearchResponse
from app.services.knowledge_service import KnowledgeService


class SearchKnowledgeTool:
    name = "search_knowledge"

    def __init__(self, knowledge_service: KnowledgeService) -> None:
        self.knowledge_service = knowledge_service

    async def run(self, query: str, top_k: int = 5) -> KnowledgeSearchResponse:
        result = await self.knowledge_service.search(query, top_k=top_k)
        return KnowledgeSearchResponse(query=result.query, chunks=result.chunks)

