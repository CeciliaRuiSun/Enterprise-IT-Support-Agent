from app.agent.intent import classify_intent


def test_vpn_question_uses_knowledge_search(offline_intent_classifier):
    result = classify_intent("How do I connect to the enterprise VPN?")

    assert result.intent == "search_knowledge"
    assert result.extracted_fields["query"] == "How do I connect to the enterprise VPN?"
