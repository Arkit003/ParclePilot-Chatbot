from __future__ import annotations

import logging

from openai import OpenAI

from src.llm.config import settings
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def get_llm_client() -> OpenAI:
    """
    Return an OpenAI-compatible client for the configured provider.
    """

    provider = settings.llm_provider.lower().strip()

    if provider == "groq":

        if not settings.groq_api_key:
            raise ValueError(
                "GROQ_API_KEY is not configured."
            )

        logger.info(
            "Initializing Groq LLM client."
        )

        return OpenAI(
            api_key=settings.groq_api_key,
            base_url="https://api.groq.com/openai/v1",
        )

    if provider == "openrouter":

        if not settings.openrouter_api_key:
            raise ValueError(
                "OPENROUTER_API_KEY is not configured."
            )

        logger.info(
            "Initializing OpenRouter LLM client."
        )

        return OpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )

    raise ValueError(
        f"Unsupported LLM provider: {provider}"
    )


def get_model() -> str:
    """
    Return the model configured for the current provider.
    """

    provider = settings.llm_provider.lower().strip()

    if provider == "groq":
        if not settings.groq_model:
            raise ValueError(
                "GROQ_MODEL is not configured."
            )

        return settings.groq_model

    if provider == "openrouter":
        if not settings.openrouter_model:
            raise ValueError(
                "OPENROUTER_MODEL is not configured."
            )

        return settings.openrouter_model

    raise ValueError(
        f"Unsupported LLM provider: {provider}"
    )