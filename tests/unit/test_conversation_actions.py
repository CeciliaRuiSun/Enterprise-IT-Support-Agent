from uuid import uuid4

import pytest

from app.models.common import Conversation, ConversationStatus, User
from app.services.conversation_service import ConversationService


class FakeSession:
    def __init__(self, conversation: Conversation):
        self.conversation = conversation

    async def get(self, model, conversation_id):
        return self.conversation if self.conversation.id == conversation_id else None

    async def flush(self):
        return None


@pytest.mark.asyncio
async def test_close_conversation_sets_closed_status_without_reactivation():
    user_id = uuid4()
    conversation = Conversation(
        id=uuid4(),
        user_id=user_id,
        status=ConversationStatus.active,
        is_archived=False,
        is_deleted=False,
    )
    service = ConversationService(FakeSession(conversation), User(id=user_id))

    closed = await service.close_conversation(conversation.id)

    assert closed is conversation
    assert conversation.status == ConversationStatus.closed
    assert conversation.active_workflow_type is None


@pytest.mark.asyncio
async def test_delete_conversation_marks_row_deleted_instead_of_removing_it():
    user_id = uuid4()
    conversation = Conversation(
        id=uuid4(),
        user_id=user_id,
        status=ConversationStatus.active,
        is_archived=False,
        is_deleted=False,
    )
    service = ConversationService(FakeSession(conversation), User(id=user_id))

    deleted = await service.delete_conversation(conversation.id)

    assert deleted is True
    assert conversation.is_deleted is True
