from pathlib import Path
import sys

import pytest


BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


@pytest.fixture
def offline_intent_classifier(monkeypatch):
    """Keep intent tests deterministic and independent of OpenAI credits/network."""

    from app.agent import intent

    class OfflineLLM:
        client = None

    monkeypatch.setattr(intent, "LLMService", OfflineLLM)
