from __future__ import annotations

from app.db.base import Base
from app.db.session import engine
from app.models import common  # noqa: F401


async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

