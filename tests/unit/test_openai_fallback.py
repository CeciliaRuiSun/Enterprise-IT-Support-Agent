from types import SimpleNamespace

from app.services.embeddings import EmbeddingService
from app.services.llm import LLMJsonResult, LLMService


class FailingResponses:
    def create(self, **kwargs):
        from openai import OpenAIError

        raise OpenAIError("quota exhausted")


class FailingEmbeddings:
    def create(self, **kwargs):
        from openai import OpenAIError

        raise OpenAIError("quota exhausted")


class FailingClient:
    responses = FailingResponses()
    embeddings = FailingEmbeddings()


class TextResponses:
    def create(self, **kwargs):
        return type("Response", (), {"output_text": "Generated answer"})()


class TextClient:
    responses = TextResponses()


def test_llm_service_returns_empty_result_when_provider_is_unavailable():
    service = LLMService.__new__(LLMService)
    service.model = "test-model"
    service.client = FailingClient()

    result = service.responses_json("classify this")

    assert result == LLMJsonResult(raw_text="", payload=None)


def test_llm_service_returns_plain_text_response():
    service = LLMService.__new__(LLMService)
    service.model = "test-model"
    service.client = TextClient()

    assert service.responses_text("answer this") == "Generated answer"


def test_embedding_service_returns_none_when_provider_is_unavailable():
    service = EmbeddingService.__new__(EmbeddingService)
    service.settings = SimpleNamespace(openai_embeddings_model="test-embeddings")
    service.client = FailingClient()

    assert service.embed_query("vpn help") is None
