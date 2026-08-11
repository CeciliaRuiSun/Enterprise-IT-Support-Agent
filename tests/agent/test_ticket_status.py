from app.workflows.ticket.engine import TicketWorkflowEngine
from app.agent.intent import classify_intent


def test_ticket_status_request_extracts_ticket_id(offline_intent_classifier):
    ticket_id = "8c503ed5-6a0e-456c-a216-e45fe1209c06"

    result = classify_intent(f"I want to check my ticket status: {ticket_id}")

    assert result.intent == "ticket_status"
    assert result.ticket_id == ticket_id


def test_formatted_ticket_status_request_extracts_ticket_number(offline_intent_classifier):
    result = classify_intent("Check my ticket status: INC-000001")

    assert result.intent == "ticket_status"
    assert result.ticket_id == "INC-000001"


def test_ticket_workflow_reaches_confirmation_state():
    engine = TicketWorkflowEngine()
    state = engine.create_state("incident_ticket")

    first_question = engine.next_question(state)
    assert first_question == "Briefly describe the issue."
    assert state.asked_fields == ["issue_summary"]

    state.collected_fields.update(
        {
            "issue_summary": "The printer is offline.",
            "affected_system": "Finance printer",
            "impact": "The team cannot print invoices.",
            "urgency": "high",
        }
    )

    assert engine.is_complete(state)
    summary = engine.build_summary(state)

    assert state.confirmation_pending is True
    assert "Ticket type: incident_ticket" in summary
    assert "urgency: high" in summary
