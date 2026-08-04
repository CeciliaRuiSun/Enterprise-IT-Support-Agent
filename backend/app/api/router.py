from fastapi import APIRouter

from app.api.endpoints.conversations import router as conversations_router
from app.api.endpoints.knowledge import router as knowledge_router
from app.api.endpoints.tickets import router as tickets_router

api_router = APIRouter()
api_router.include_router(conversations_router)
api_router.include_router(knowledge_router)
api_router.include_router(tickets_router)

