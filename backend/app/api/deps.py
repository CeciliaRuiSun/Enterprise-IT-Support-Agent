from __future__ import annotations

from sqlalchemy import select
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db
from app.models.common import User


async def get_current_user(db: AsyncSession = Depends(get_db)) -> User:
    settings = get_settings()
    stmt = select(User).where(User.email == settings.default_user_email)
    user = (await db.scalars(stmt)).first()
    if user:
        return user

    user = User(email=settings.default_user_email, full_name=settings.default_user_full_name, role="employee")
    db.add(user)
    await db.flush()
    await db.commit()
    await db.refresh(user)
    return user
