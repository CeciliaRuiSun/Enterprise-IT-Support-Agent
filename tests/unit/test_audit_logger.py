from uuid import uuid4

import pytest

from app.core.request_context import request_id_context
from app.models.common import AuditEvent
from app.services.audit_logger import AuditLogger
from app.services.workflow_service import WorkflowService


class FakeSession:
    def __init__(self):
        self.added = []
        self.commits = 0

    def add(self, value):
        self.added.append(value)

    async def commit(self):
        self.commits += 1


def test_logger_is_transaction_neutral_and_redacts_unallowlisted_values():
    session = FakeSession()
    request_token = request_id_context.set(str(uuid4()))
    try:
        event = AuditLogger(session).log(
            event_type="tool_execution",
            action="execute",
            status="success",
            metadata={
                "tool_name": "search_knowledge",
                "query": "secret conversation content",
                "raw_result": {"content": "should not persist"},
                "result_count": 2,
            },
        )
    finally:
        request_id_context.reset(request_token)

    assert session.commits == 0
    assert session.added == [event]
    assert event.request_id is not None
    assert event.event_metadata == {"tool_name": "search_knowledge", "result_count": 2}


def test_audit_event_has_no_mutation_api():
    assert not hasattr(AuditEvent, "update")
    assert not hasattr(AuditEvent, "delete")


@pytest.mark.asyncio
async def test_tool_success_and_failure_are_audited_with_request_id():
    session = FakeSession()
    service = WorkflowService(session)
    request_token = request_id_context.set(str(uuid4()))
    try:
        assert await service._run_tool("existing_tool", uuid4(), lambda: _value("ok")) == "ok"

        async def fail():
            raise RuntimeError("secret conversation content must not be logged")

        with pytest.raises(RuntimeError):
            await service._run_tool("existing_tool", uuid4(), fail)
    finally:
        request_id_context.reset(request_token)

    assert [event.status for event in session.added] == ["success", "failure"]
    assert session.added[0].request_id == session.added[1].request_id
    assert "secret conversation content" not in repr(session.added[1].event_metadata)
    assert session.added[1].event_metadata["error_type"] == "RuntimeError"


async def _value(value):
    return value
