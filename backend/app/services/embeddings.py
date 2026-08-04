from __future__ import annotations

from openai import OpenAI

from app.core.config import get_settings


class EmbeddingService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key) if self.settings.openai_api_key else None

    def embed_query(self, text: str) -> list[float] | None:
        if not self.client:
            return None
        response = self.client.embeddings.create(model=self.settings.openai_embeddings_model, input=text)
        return list(response.data[0].embedding)

