from __future__ import annotations

from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.common import Conversation, ConversationStatus, Message, MessageRole, User
from app.schemas.conversation import (
    ConversationCreateResponse,
    ConversationHistoryResponse,
    ConversationListItem,
    ConversationListResponse,
    MessageItem,
    SendMessageResponse,
)
from app.services.workflow_service import WorkflowService


class ConversationService:
    def __init__(self, db: AsyncSession, user: User) -> None:
        self.db = db
        self.user = user
        self.workflow_service = WorkflowService(db)

    async def list_conversations(self, limit: int = 20, offset: int = 0) -> ConversationListResponse:
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == self.user.id)
            .order_by(desc(Conversation.created_at))
            .offset(offset)
            .limit(limit)
        )
        conversations = (await self.db.scalars(stmt)).all()
        return ConversationListResponse(
            conversations=[
                ConversationListItem(
                    conversation_id=item.id,
                    title=item.title,
                    status=item.status,
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                )
                for item in conversations
            ]
        )

    async def get_conversation(self, conversation_id: UUID) -> ConversationHistoryResponse | None:
        stmt = (
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == conversation_id)
            .where(Conversation.user_id == self.user.id)
        )
        conversation = (await self.db.scalars(stmt)).first()
        if not conversation:
            return None
        messages = list(conversation.messages)
        return ConversationHistoryResponse(
            conversation_id=conversation.id,
            title=conversation.title,
            status=conversation.status,
            messages=[
                MessageItem(
                    message_id=message.id,
                    role=message.role,
                    content=message.content,
                    created_at=message.created_at,
                    citations=message.citations,
                    tool_calls=message.tool_calls,
                )
                for message in messages
            ],
        )

    async def create_conversation(self, message_content: str) -> ConversationCreateResponse:
        conversation = Conversation(user_id=self.user.id, status=ConversationStatus.active)
        self.db.add(conversation)
        await self.db.flush()

        user_message = Message(
            conversation_id=conversation.id,
            role=MessageRole.user,
            content=message_content,
        )
        self.db.add(user_message)
        await self.db.flush()

        if not conversation.title:
            conversation.title = message_content[:80]

        agent_result = await self.workflow_service.respond(conversation, message_content)
        assistant_message = Message(
            conversation_id=conversation.id,
            role=MessageRole.assistant,
            content=agent_result.content,
            citations=agent_result.citations or None,
            tool_calls=agent_result.tool_calls or None,
        )
        self.db.add(assistant_message)
        await self.db.flush()

        return ConversationCreateResponse(
            conversation_id=conversation.id,
            status=conversation.status,
            created_at=conversation.created_at,
            message=MessageItem(
                message_id=assistant_message.id,
                role=assistant_message.role,
                content=assistant_message.content,
                created_at=assistant_message.created_at,
                citations=assistant_message.citations,
                tool_calls=assistant_message.tool_calls,
            ),
        )

    async def send_message(self, conversation_id: UUID, message_content: str) -> SendMessageResponse | None:
        conversation = await self.db.get(Conversation, conversation_id)
        if not conversation or conversation.user_id != self.user.id:
            return None

        user_message = Message(
            conversation_id=conversation.id,
            role=MessageRole.user,
            content=message_content,
        )
        self.db.add(user_message)
        await self.db.flush()

        agent_result = await self.workflow_service.respond(conversation, message_content)

        assistant_message = Message(
            conversation_id=conversation.id,
            role=MessageRole.assistant,
            content=agent_result.content,
            citations=agent_result.citations or None,
            tool_calls=agent_result.tool_calls or None,
        )
        self.db.add(assistant_message)
        await self.db.flush()

        return SendMessageResponse(
            message_id=assistant_message.id,
            content=assistant_message.content,
            conversation_id=conversation.id,
            created_at=assistant_message.created_at,
            citations=assistant_message.citations,
            tool_calls=assistant_message.tool_calls,
        )
