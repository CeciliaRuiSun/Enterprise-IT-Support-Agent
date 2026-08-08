from app.agent.intent import classify_intent


def test_incident_message_starts_incident_workflow(offline_intent_classifier):
    message = "My printer is broken and shows an error"

    result = classify_intent(message)

    assert result.intent == "create_ticket"
    assert result.ticket_type == "incident_ticket"
    assert result.extracted_fields["issue_summary"] == message
