"""Tests for network-aware Groq to Ollama fallback provider."""

import pytest
from unittest.mock import AsyncMock

from ..engine import Suggestion, ImprovementType
from ..groq_provider import GroqWithOllamaFallbackProvider
from ...prompt_analyzer.analyzer import VaguePhrase, VagueType


def _sample_phrase() -> VaguePhrase:
    return VaguePhrase.create(0, 9, "something", VagueType.GENERIC_TERM)


def _sample_suggestions():
    return [
        Suggestion.create(
            improved_text="a specific task",
            rationale="More precise",
            improvement_type=ImprovementType.SPECIFICITY,
            original_phrase="something",
            confidence=0.9,
        )
    ]


@pytest.mark.asyncio
async def test_uses_groq_when_available_and_successful():
    provider = GroqWithOllamaFallbackProvider(api_key="test-key")
    expected = _sample_suggestions()

    provider._groq.is_available = AsyncMock(return_value=True)
    provider._groq.generate_suggestions = AsyncMock(return_value=expected)
    provider._ollama.is_available = AsyncMock(return_value=True)
    provider._ollama.generate_suggestions = AsyncMock(return_value=_sample_suggestions())

    result = await provider.generate_suggestions(_sample_phrase(), "Write something")

    assert result == expected
    provider._groq.generate_suggestions.assert_awaited_once()
    provider._ollama.generate_suggestions.assert_not_called()


@pytest.mark.asyncio
async def test_falls_back_to_ollama_only_on_network_error():
    provider = GroqWithOllamaFallbackProvider(api_key="test-key")
    expected = _sample_suggestions()

    provider._groq.is_available = AsyncMock(return_value=True)
    provider._groq.generate_suggestions = AsyncMock(side_effect=Exception("connection timeout"))
    provider._ollama.is_available = AsyncMock(return_value=True)
    provider._ollama.generate_suggestions = AsyncMock(return_value=expected)

    result = await provider.generate_suggestions(_sample_phrase(), "Write something")

    assert result == expected
    provider._groq.generate_suggestions.assert_awaited_once()
    provider._ollama.generate_suggestions.assert_awaited_once()


@pytest.mark.asyncio
async def test_does_not_use_ollama_on_non_network_groq_error():
    provider = GroqWithOllamaFallbackProvider(api_key="test-key")

    provider._groq.is_available = AsyncMock(return_value=True)
    provider._groq.generate_suggestions = AsyncMock(side_effect=Exception("invalid request payload"))
    provider._ollama.is_available = AsyncMock(return_value=True)
    provider._ollama.generate_suggestions = AsyncMock(return_value=_sample_suggestions())

    with pytest.raises(Exception):
        await provider.generate_suggestions(_sample_phrase(), "Write something")

    provider._groq.generate_suggestions.assert_awaited_once()
    provider._ollama.generate_suggestions.assert_not_called()


@pytest.mark.asyncio
async def test_does_not_use_ollama_when_groq_not_configured():
    provider = GroqWithOllamaFallbackProvider(api_key="")

    provider._groq.is_available = AsyncMock(return_value=False)
    provider._ollama.is_available = AsyncMock(return_value=True)
    provider._ollama.generate_suggestions = AsyncMock(return_value=_sample_suggestions())

    with pytest.raises(RuntimeError, match="Groq provider is not configured"):
        await provider.generate_suggestions(_sample_phrase(), "Write something")

    provider._ollama.generate_suggestions.assert_not_called()
