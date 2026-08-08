from __future__ import annotations

import logging

from openai import OpenAI
from openai import OpenAIError

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = (
            OpenAI(api_key=self.settings.openai_api_key, max_retries=0)
            if self.settings.openai_api_key
            else None
        )

    def embed_query(self, text: str) -> list[float] | None:
        if not self.client:
            return None
        try:
            response = self.client.embeddings.create(model=self.settings.openai_embeddings_model, input=text)
        except OpenAIError as exc:
            logger.warning("OpenAI embeddings unavailable; using lexical knowledge search: %s", exc)
            return None

        return list(response.data[0].embedding)
