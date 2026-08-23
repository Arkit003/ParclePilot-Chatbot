import pytest

from src.llm.client import get_llm_client
from src.llm.config import settings


def test_provider_is_supported():
    assert settings.llm_provider.lower() in {
        "groq",
        "openrouter",
    }


def test_invalid_provider(monkeypatch):
    monkeypatch.setattr(
        "src.llm.client.settings.llm_provider",
        "invalid-provider",
    )

    with pytest.raises(
        ValueError,
        match="Unsupported LLM provider",
    ):
        get_llm_client()