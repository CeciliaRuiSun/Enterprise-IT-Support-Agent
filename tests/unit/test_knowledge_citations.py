from uuid import uuid4

import pytest

from app.models.common import Conversation
from app.schemas.knowledge import KnowledgeChunk
from app.services.knowledge_service import KnowledgeSearchResult
from app.services import workflow_service as workflow_service_module
from app.services.workflow_service import WorkflowService


class FakeKnowledgeService:
    async def search(self, query: str):
        document_id = uuid4()
        return KnowledgeSearchResult(
            query=query,
            chunks=[
                KnowledgeChunk(
                    chunk_id=uuid4(),
                    document_id=document_id,
                    title="ServiceNow_User_Guide_Submitting_and_Tracking_Tickets",
                    content="First relevant section",
                    chunk_index=0,
                ),
                KnowledgeChunk(
                    chunk_id=uuid4(),
                    document_id=document_id,
                    title=" ServiceNow_User_Guide_Submitting_and_Tracking_Tickets ",
                    content="Another section from the same guide",
                    chunk_index=1,
                ),
                KnowledgeChunk(
                    chunk_id=uuid4(),
                    document_id=uuid4(),
                    title="Enterprise_Printer_Troubleshooting_Guide",
                    content="Printer troubleshooting section",
                    chunk_index=0,
                ),
            ],
        )


async def no_active_workflow(conversation_id):
    return None


@pytest.mark.asyncio
async def test_search_results_show_each_source_once(offline_intent_classifier, monkeypatch):
    service = WorkflowService(object())
    service.knowledge_service = FakeKnowledgeService()
    monkeypatch.setattr(service, "get_active_workflow", no_active_workflow)

    class NoAnswerLLM:
        def responses_text(self, prompt):
            return None

    monkeypatch.setattr(workflow_service_module, "LLMService", NoAnswerLLM)

    result = await service.respond(Conversation(id=uuid4()), "How do I submit a ticket?")

    assert [citation["source"] for citation in result.citations] == [
        "ServiceNow_User_Guide_Submitting_and_Tracking_Tickets",
        "Enterprise_Printer_Troubleshooting_Guide",
    ]
    assert result.tool_calls[0]["result_count"] == 2
    assert "ServiceNow_User_Guide_Submitting_and_Tracking_Tickets" not in result.content


@pytest.mark.asyncio
async def test_knowledge_chunks_are_summarized_by_the_llm(offline_intent_classifier, monkeypatch):
    service = WorkflowService(object())
    service.knowledge_service = FakeKnowledgeService()
    monkeypatch.setattr(service, "get_active_workflow", no_active_workflow)

    class AnsweringLLM:
        def responses_text(self, prompt):
            assert "First relevant section" in prompt
            assert "Another section from the same guide" not in prompt
            return "Use the ServiceNow guide to submit and track the ticket."

    monkeypatch.setattr(workflow_service_module, "LLMService", AnsweringLLM)

    result = await service.respond(Conversation(id=uuid4()), "How do I submit a ticket?")

    assert result.content == "Use the ServiceNow guide to submit and track the ticket."
    assert len(result.citations) == 2


@pytest.mark.asyncio
async def test_knowledge_answer_removes_parenthetical_source_artifacts(offline_intent_classifier, monkeypatch):
    service = WorkflowService(object())
    service.knowledge_service = FakeKnowledgeService()
    monkeypatch.setattr(service, "get_active_workflow", no_active_workflow)

    class ArtifactProducingLLM:
        def responses_text(self, prompt):
            return "(ServiceNow_User_Guide_Submitting_and_Tracking_Tickets: ticket)\nUse the helpdesk."

    monkeypatch.setattr(workflow_service_module, "LLMService", ArtifactProducingLLM)

    result = await service.respond(Conversation(id=uuid4()), "How do I submit a ticket?")

    assert result.content == "Use the helpdesk."
