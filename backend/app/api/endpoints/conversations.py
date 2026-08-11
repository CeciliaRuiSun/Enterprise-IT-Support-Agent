from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.conversation import (
    ConversationCreateRequest,
    ConversationCreateResponse,
    ConversationHistoryResponse,
    ConversationListItem,
    ConversationListResponse,
    SendMessageRequest,
    SendMessageResponse,
)
from app.services.conversation_service import ConversationService
from app.models.common import User

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=ConversationCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    request: ConversationCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ConversationCreateResponse:
    service = ConversationService(db, user)
    try:
        response = await service.create_conversation(request.message_content)
    except ProgrammingError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database schema is out of date. Run 'python -m alembic upgrade head' from backend and try again.",
        ) from exc
    await db.commit()
    return response


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ConversationListResponse:
    service = ConversationService(db, user)
    response = await service.list_conversations(limit=limit, offset=offset)
    return response


@router.post("/{conversation_id}/pin", response_model=ConversationListItem)
async def pin_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ConversationListItem:
    service = ConversationService(db, user)
    conversation = await service.set_pinned(conversation_id, True)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    await db.commit()
    return service._to_list_item(conversation)


@router.delete("/{conversation_id}/pin", response_model=ConversationListItem)
async def unpin_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ConversationListItem:
    service = ConversationService(db, user)
    conversation = await service.set_pinned(conversation_id, False)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    await db.commit()
    return service._to_list_item(conversation)


@router.post("/{conversation_id}/close", response_model=ConversationListItem)
async def close_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ConversationListItem:
    service = ConversationService(db, user)
    conversation = await service.close_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    await db.commit()
    return service._to_list_item(conversation)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    service = ConversationService(db, user)
    deleted = await service.delete_conversation(conversation_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    await db.commit()


@router.get("/{conversation_id}", response_model=ConversationHistoryResponse)
async def get_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ConversationHistoryResponse:
    service = ConversationService(db, user)
    response = await service.get_conversation(conversation_id)
    if response is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return response


@router.post("/{conversation_id}/messages", response_model=SendMessageResponse)
async def send_message(
    conversation_id: UUID,
    request: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SendMessageResponse:
    service = ConversationService(db, user)
    try:
        response = await service.send_message(conversation_id, request.message_content)
    except ProgrammingError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database schema is out of date. Run 'python -m alembic upgrade head' from backend and try again.",
        ) from exc
    if response is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    await db.commit()
    return response
