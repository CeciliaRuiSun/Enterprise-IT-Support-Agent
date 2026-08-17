from contextlib import asynccontextmanager
import logging
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import async_session_maker
from app.services.document_ingestion import DocumentIngestionService
from app.core.request_context import request_id_context

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    if settings.enable_demo_seed:
        try:
            async with async_session_maker() as session:
                service = DocumentIngestionService(session)
                ingested = await service.sync_knowledge_base()
                await session.commit()
                logger.info("Knowledge base ready; indexed %d new document(s).", len(ingested))
        except Exception:
            logger.exception("Knowledge-base sync failed; continuing without new local documents.")
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)


@app.middleware("http")
async def request_id_middleware(request, call_next):
    request_id = str(uuid4())
    token = request_id_context.set(request_id)
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        request_id_context.reset(token)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=(
        r"https?://(?:localhost|127\.0\.0\.1|\[::1\]|0\.0\.0\.0|"
        r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|"
        r"172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})(:\d+)?$"
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
