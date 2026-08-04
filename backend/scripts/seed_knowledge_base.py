from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Allow direct execution from backend/scripts/ without needing PYTHONPATH tweaks.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.init_db import create_tables
from app.db.session import async_session_maker
from app.services.document_ingestion import DocumentIngestionService


async def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    knowledge_dir = repo_root / "Knowledge Base"
    if not knowledge_dir.exists():
        raise FileNotFoundError(f"Knowledge Base directory not found: {knowledge_dir}")

    await create_tables()

    async with async_session_maker() as session:
        service = DocumentIngestionService(session)
        for path in sorted(knowledge_dir.iterdir()):
            if path.suffix.lower() not in {".txt", ".docx", ".pdf"}:
                continue
            content = path.read_bytes()
            await service.ingest_bytes(content, path.name, title=path.stem)
        await session.commit()


if __name__ == "__main__":
    asyncio.run(main())
