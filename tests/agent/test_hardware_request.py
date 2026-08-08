from app.agent.intent import classify_intent


def test_hardware_request_starts_hardware_workflow(offline_intent_classifier):
    message = "I need a new laptop for my role"

    result = classify_intent(message)

    assert result.intent == "create_ticket"
    assert result.ticket_type == "hardware_request"
    assert result.extracted_fields["requested_item"] == message
