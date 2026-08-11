from uuid import uuid4

import pytest

from app.models.common import Conversation, Ticket, WorkflowRun, WorkflowStatus
from app.services.workflow_service import WorkflowService


class FakeSession:
    def __init__(self):
        self.items = []

    def add(self, item):
        self.items.append(item)

    async def flush(self):
        return None


@pytest.mark.asyncio
async def test_start_workflow_persists_waiting_input_state():
    session = FakeSession()
    service = WorkflowService(session)
    conversation = Conversation(id=uuid4())

    result = await service.start_workflow(conversation, "software_request", {})

    assert result.tool_calls[0]["tool"] == "workflow_start"
    assert "What software do you need?" in result.content
    assert conversation.active_workflow_status == WorkflowStatus.waiting_input.value
    assert any(isinstance(item, WorkflowRun) for item in session.items)


@pytest.mark.asyncio
async def test_continue_workflow_collects_the_answer(offline_intent_classifier, monkeypatch):
    session = FakeSession()
    service = WorkflowService(session)
    conversation_id = uuid4()
    conversation = Conversation(id=conversation_id)
    workflow = WorkflowRun(
        id=uuid4(),
        conversation_id=conversation_id,
        workflow_type="ticket",
        status=WorkflowStatus.waiting_input,
        state={
            "ticket_type": "incident_ticket",
            "collected_fields": {},
            "asked_fields": ["issue_summary"],
            "confirmation_pending": False,
            "summary": None,
        },
    )
    monkeypatch.setattr(service, "get_active_workflow", lambda _: _async_value(workflow))

    result = await service.respond(conversation, "The printer is offline")

    assert result.tool_calls[0]["tool"] == "collect_workflow_field"
    assert workflow.state["collected_fields"]["issue_summary"] == "The printer is offline"


@pytest.mark.asyncio
async def test_ticket_status_returns_ticket_details(offline_intent_classifier, monkeypatch):
    session = FakeSession()
    service = WorkflowService(session)
    conversation = Conversation(id=uuid4())
    ticket = Ticket(
        id=uuid4(),
        ticket_number="REQ-000001",
        request_type="hardware_request",
        status="open",
        priority="high",
        description="New monitor requested",
    )

    class TicketLookup:
        async def get_ticket(self, ticket_id):
            return ticket if ticket_id in {ticket.id, ticket.ticket_number} else None

    service.ticket_service = TicketLookup()
    monkeypatch.setattr(service, "get_active_workflow", lambda _: _async_value(None))

    result = await service.respond(conversation, f"Check my ticket status: {ticket.ticket_number}")

    assert result.tool_calls == [{"tool": "get_ticket_status", "ticket_id": ticket.ticket_number, "found": True}]
    assert f"Ticket {ticket.ticket_number}" in result.content
    assert f"Status: {ticket.status}" in result.content
    assert "New monitor requested" in result.content


async def _async_value(value):
    return value
