import pytest

from app.workflows.ticket.engine import TicketWorkflowEngine


@pytest.mark.parametrize(
    ("ticket_type", "first_field"),
    [
        ("software_request", "software_name"),
        ("hardware_request", "requested_item"),
        ("incident_ticket", "issue_summary"),
    ],
)
def test_each_ticket_questionnaire_has_a_first_question(ticket_type, first_field):
    engine = TicketWorkflowEngine()
    state = engine.create_state(ticket_type)

    assert engine.next_question(state)
    assert state.asked_fields == [first_field]
