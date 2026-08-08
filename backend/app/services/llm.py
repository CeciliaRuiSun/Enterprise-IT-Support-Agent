from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from openai import OpenAI, OpenAIError

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class LLMJsonResult:
    raw_text: str
    payload: dict | None


class LLMService:
    def __init__(self) -> None:
        settings = get_settings()
        self.model = settings.openai_model
        self.client = OpenAI(api_key=settings.openai_api_key, max_retries=0) if settings.openai_api_key else None

    def responses_json(self, prompt: str) -> LLMJsonResult:
        if not self.client:
            return LLMJsonResult(raw_text="", payload=None)

        try:
            response = self.client.responses.create(model=self.model, input=prompt)
        except OpenAIError as exc:
            logger.warning("OpenAI response unavailable; using local fallback: %s", exc)
            return LLMJsonResult(raw_text="", payload=None)

        raw_text = getattr(response, "output_text", "") or ""
        if not raw_text:
            return LLMJsonResult(raw_text="", payload=None)

        try:
            return LLMJsonResult(raw_text=raw_text, payload=json.loads(raw_text))
        except json.JSONDecodeError:
            start = raw_text.find("{")
            end = raw_text.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return LLMJsonResult(raw_text=raw_text, payload=json.loads(raw_text[start : end + 1]))
                except json.JSONDecodeError:
                    return LLMJsonResult(raw_text=raw_text, payload=None)
            return LLMJsonResult(raw_text=raw_text, payload=None)
