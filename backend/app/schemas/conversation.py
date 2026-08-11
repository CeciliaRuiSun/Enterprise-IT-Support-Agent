from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.common import ConversationStatus, MessageRole
from app.schemas.common import ORMBaseModel


class ConversationCreateRequest(BaseModel):
    message_content: str = Field(min_length=1)


class MessageItem(ORMBaseModel):
    message_id: UUID
    role: MessageRole
    content: str
    created_at: datetime
    citations: list[dict] | None = None
    tool_calls: list[dict] | None = None


class ConversationListItem(ORMBaseModel):
    conversation_id: UUID
    title: str | None = None
    status: ConversationStatus
    is_pinned: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime


class ConversationCreateResponse(ORMBaseModel):
    conversation_id: UUID
    status: ConversationStatus
    created_at: datetime
    message: MessageItem


class ConversationHistoryResponse(ORMBaseModel):
    conversation_id: UUID
    title: str | None = None
    status: ConversationStatus
    messages: list[MessageItem]


class ConversationListResponse(BaseModel):
    conversations: list[ConversationListItem]


class SendMessageRequest(BaseModel):
    role: MessageRole = MessageRole.user
    message_content: str = Field(min_length=1)


class SendMessageResponse(ORMBaseModel):
    message_id: UUID
    content: str
    conversation_id: UUID
    created_at: datetime
    citations: list[dict] | None = None
    tool_calls: list[dict] | None = None
