from app.workflows.ticket.engine import TicketWorkflowEngine


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
