from __future__ import annotations

import asyncio
import sys

# Allow direct execution from backend/scripts/ without needing PYTHONPATH tweaks.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.init_db import create_tables
from app.db.session import async_session_maker
from app.services.document_ingestion import DocumentIngestionService


async def main() -> None:
    await create_tables()

    async with async_session_maker() as session:
        service = DocumentIngestionService(session)
        ingested = await service.sync_knowledge_base()
        await session.commit()
        print(f"Indexed {len(ingested)} new knowledge-base document(s).")


if __name__ == "__main__":
    asyncio.run(main())
