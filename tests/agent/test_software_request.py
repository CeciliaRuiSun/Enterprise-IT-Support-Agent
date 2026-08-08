from app.agent.intent import classify_intent


def test_software_request_starts_software_workflow(offline_intent_classifier):
    message = "I need the accounting software installed"

    result = classify_intent(message)

    assert result.intent == "create_ticket"
    assert result.ticket_type == "software_request"
    assert result.extracted_fields["software_name"] == message
