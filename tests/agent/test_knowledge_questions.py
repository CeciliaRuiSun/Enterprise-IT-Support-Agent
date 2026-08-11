from app.agent.intent import classify_intent


def test_ticket_submission_question_searches_the_knowledge_base(offline_intent_classifier):
    result = classify_intent("How do I submit a ticket?")

    assert result.intent == "search_knowledge"
    assert result.extracted_fields["query"] == "How do I submit a ticket?"
