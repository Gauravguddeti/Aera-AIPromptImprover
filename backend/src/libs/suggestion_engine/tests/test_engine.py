"""
Tests for the SuggestionEngine core functionality.

Following TDD principles with comprehensive test coverage.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from ..engine import (
    SuggestionEngine, 
    Suggestion, 
    SuggestionRequest,
    SuggestionResponse,
    ImprovementType,
    AIProvider
)
from ..providers import RuleBasedProvider
from ...prompt_analyzer.analyzer import VaguePhrase, VagueType


class MockAIProvider(AIProvider):
    """Mock AI provider for testing."""
    
    def __init__(self, name: str = "mock", available: bool = True, should_fail: bool = False):
        self._name = name
        self._available = available
        self._should_fail = should_fail
    
    @property
    def name(self) -> str:
        return self._name
    
    async def is_available(self) -> bool:
        return self._available
    
    async def generate_suggestions(self, vague_phrase: VaguePhrase, context: str) -> list[Suggestion]:
        if self._should_fail:
            raise Exception("Mock provider failure")
        
        return [
            Suggestion.create(
                improved_text="mock improvement",
                rationale="mock rationale",
                improvement_type=ImprovementType.SPECIFICITY,
                original_phrase=vague_phrase.original_text,
                confidence=0.9
            )
        ]


class TestSuggestion:
    """Test Suggestion data class functionality."""
    
    def test_create_suggestion(self):
        """Test creating a Suggestion with proper defaults."""
        suggestion = Suggestion.create(
            improved_text="specific task",
            rationale="More specific than 'something'",
            improvement_type=ImprovementType.SPECIFICITY,
            original_phrase="something"
        )
        
        assert suggestion.improved_text == "specific task"
        assert suggestion.rationale == "More specific than 'something'"
        assert suggestion.improvement_type == ImprovementType.SPECIFICITY
        assert suggestion.original_phrase == "something"
        assert suggestion.confidence_score == 1.0
        assert suggestion.id is not None
    
    def test_suggestion_to_dict(self):
        """Test Suggestion serialization."""
        suggestion = Suggestion.create(
            improved_text="clear instructions",
            rationale="Replace vague request",
            improvement_type=ImprovementType.CLARITY,
            original_phrase="something",
            confidence=0.8
        )
        
        result = suggestion.to_dict()
        
        assert result["improved_text"] == "clear instructions"
        assert result["rationale"] == "Replace vague request"
        assert result["type"] == "clarity"
        assert result["original_phrase"] == "something"
        assert result["confidence"] == 0.8
        assert "id" in result


class TestSuggestionRequest:
    """Test SuggestionRequest data class."""
    
    def test_create_request(self):
        """Test creating a suggestion request."""
        vague_phrase = VaguePhrase.create(0, 9, "something", VagueType.GENERIC_TERM)
        
        request = SuggestionRequest(
            vague_phrase=vague_phrase,
            full_context="Write something good",
            max_suggestions=3
        )
        
        assert request.vague_phrase == vague_phrase
        assert request.full_context == "Write something good"
        assert request.max_suggestions == 3
        assert request.preferred_style is None


class TestSuggestionResponse:
    """Test SuggestionResponse data class."""
    
    def test_response_to_dict(self):
        """Test SuggestionResponse serialization."""
        vague_phrase = VaguePhrase.create(0, 9, "something", VagueType.GENERIC_TERM)
        request = SuggestionRequest(vague_phrase=vague_phrase, full_context="test context")
        suggestion = Suggestion.create("improved", "rationale", ImprovementType.CLARITY, "something")
        
        response = SuggestionResponse(
            request=request,
            suggestions=[suggestion],
            provider_used="test",
            generation_time_ms=100.5
        )
        
        result = response.to_dict()
        
        assert result["full_context"] == "test context"
        assert len(result["suggestions"]) == 1
        assert result["provider_used"] == "test"
        assert result["generation_time_ms"] == 100.5
        assert result["error"] is None
        assert result["fallback_mode"] is False


class TestSuggestionEngine:
    """Test SuggestionEngine core functionality."""
    
    def test_engine_initialization(self):
        """Test that engine initializes properly."""
        provider = RuleBasedProvider()
        engine = SuggestionEngine([provider])
        
        assert len(engine.providers) == 1
        assert engine.providers[0] == provider
        assert engine._fallback_suggestions is not None
    
    @pytest.mark.asyncio
    async def test_generate_suggestions_with_available_provider(self):
        """Test suggestion generation with available provider."""
        mock_provider = MockAIProvider()
        engine = SuggestionEngine([mock_provider])
        
        vague_phrase = VaguePhrase.create(0, 9, "something", VagueType.GENERIC_TERM)
        request = SuggestionRequest(vague_phrase=vague_phrase, full_context="Write something")
        
        response = await engine.generate_suggestions(request)
        
        assert response.provider_used == "mock"
        assert len(response.suggestions) == 1
        assert response.suggestions[0].improved_text == "mock improvement"
        assert response.error is None
        assert response.fallback_mode is False
    
    @pytest.mark.asyncio
    async def test_generate_suggestions_with_unavailable_provider(self):
        """Test suggestion generation falls back when provider unavailable."""
        mock_provider = MockAIProvider(available=False)
        engine = SuggestionEngine([mock_provider])
        
        vague_phrase = VaguePhrase.create(0, 9, "something", VagueType.GENERIC_TERM)
        request = SuggestionRequest(vague_phrase=vague_phrase, full_context="Write something")
        
        response = await engine.generate_suggestions(request)
        
        assert response.provider_used == "fallback"
        assert response.fallback_mode is True
        assert len(response.suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_generate_suggestions_with_failing_provider(self):
        """Test suggestion generation handles provider failures."""
        mock_provider = MockAIProvider(should_fail=True)
        engine = SuggestionEngine([mock_provider])
        
        vague_phrase = VaguePhrase.create(0, 9, "something", VagueType.GENERIC_TERM)
        request = SuggestionRequest(vague_phrase=vague_phrase, full_context="Write something")
        
        response = await engine.generate_suggestions(request)
        
        assert response.provider_used == "fallback"
        assert response.fallback_mode is True
        assert len(response.suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_provider_priority_order(self):
        """Test that providers are tried in order of preference."""
        # First provider unavailable, second available
        provider1 = MockAIProvider("first", available=False)
        provider2 = MockAIProvider("second", available=True)
        engine = SuggestionEngine([provider1, provider2])
        
        vague_phrase = VaguePhrase.create(0, 9, "something", VagueType.GENERIC_TERM)
        request = SuggestionRequest(vague_phrase=vague_phrase, full_context="Write something")
        
        response = await engine.generate_suggestions(request)
        
        assert response.provider_used == "second"
        assert response.fallback_mode is False
    
    @pytest.mark.asyncio
    async def test_max_suggestions_limit(self):
        """Test that max_suggestions limit is respected."""
        # Create provider that returns many suggestions
        class MultiSuggestionProvider(AIProvider):
            @property
            def name(self) -> str:
                return "multi"
            
            async def is_available(self) -> bool:
                return True
            
            async def generate_suggestions(self, vague_phrase: VaguePhrase, context: str) -> list[Suggestion]:
                # Return 5 suggestions
                return [
                    Suggestion.create(f"suggestion {i}", "rationale", ImprovementType.CLARITY, "something")
                    for i in range(5)
                ]
        
        engine = SuggestionEngine([MultiSuggestionProvider()])
        vague_phrase = VaguePhrase.create(0, 9, "something", VagueType.GENERIC_TERM)
        request = SuggestionRequest(vague_phrase=vague_phrase, full_context="test", max_suggestions=2)
        
        response = await engine.generate_suggestions(request)
        
        assert len(response.suggestions) == 2
    
    @pytest.mark.asyncio
    async def test_batch_generate_suggestions(self):
        """Test batch suggestion generation."""
        engine = SuggestionEngine([MockAIProvider()])
        
        requests = [
            SuggestionRequest(
                VaguePhrase.create(0, 9, "something", VagueType.GENERIC_TERM),
                "Write something"
            ),
            SuggestionRequest(
                VaguePhrase.create(10, 14, "good", VagueType.SUBJECTIVE_QUALIFIER),
                "Write good code"
            )
        ]
        
        responses = await engine.batch_generate_suggestions(requests)
        
        assert len(responses) == 2
        assert all(r.provider_used == "mock" for r in responses)
    
    def test_sync_generate_suggestions(self):
        """Test synchronous wrapper for suggestion generation."""
        engine = SuggestionEngine([MockAIProvider()])
        vague_phrase = VaguePhrase.create(0, 9, "something", VagueType.GENERIC_TERM)
        request = SuggestionRequest(vague_phrase=vague_phrase, full_context="Write something")
        
        response = engine.sync_generate_suggestions(request)
        
        assert response.provider_used == "mock"
        assert len(response.suggestions) == 1


class TestFallbackSuggestions:
    """Test fallback suggestion generation."""
    
    def test_fallback_suggestions_for_generic_terms(self):
        """Test fallback suggestions for generic terms."""
        engine = SuggestionEngine([])  # No providers
        vague_phrase = VaguePhrase.create(0, 9, "something", VagueType.GENERIC_TERM)
        request = SuggestionRequest(vague_phrase=vague_phrase, full_context="Write something")
        
        suggestions = engine._generate_fallback_suggestions(request)
        
        assert len(suggestions) > 0
        assert all(s.original_phrase == "something" for s in suggestions)
        assert all(s.confidence_score > 0 for s in suggestions)
    
    def test_fallback_suggestions_for_subjective_qualifiers(self):
        """Test fallback suggestions for subjective qualifiers."""
        engine = SuggestionEngine([])  # No providers
        vague_phrase = VaguePhrase.create(0, 4, "good", VagueType.SUBJECTIVE_QUALIFIER)
        request = SuggestionRequest(vague_phrase=vague_phrase, full_context="Write good code")
        
        suggestions = engine._generate_fallback_suggestions(request)
        
        assert len(suggestions) > 0
        assert all(s.original_phrase == "good" for s in suggestions)
        quality_words = ["well-structured", "comprehensive", "professional"]
        suggestion_texts = [s.improved_text for s in suggestions]
        assert any(word in suggestion_texts for word in quality_words)
    
    def test_fallback_suggestions_respect_max_limit(self):
        """Test that fallback suggestions respect max limit."""
        engine = SuggestionEngine([])  # No providers
        vague_phrase = VaguePhrase.create(0, 9, "something", VagueType.GENERIC_TERM)
        request = SuggestionRequest(vague_phrase=vague_phrase, full_context="test", max_suggestions=1)
        
        suggestions = engine._generate_fallback_suggestions(request)
        
        assert len(suggestions) <= 1


class TestErrorHandling:
    """Test error handling in suggestion engine."""
    
    @pytest.mark.asyncio
    async def test_engine_handles_all_providers_failing(self):
        """Test engine handles when all providers fail."""
        failing_provider = MockAIProvider(should_fail=True)
        engine = SuggestionEngine([failing_provider])
        
        vague_phrase = VaguePhrase.create(0, 9, "something", VagueType.GENERIC_TERM)
        request = SuggestionRequest(vague_phrase=vague_phrase, full_context="Write something")
        
        response = await engine.generate_suggestions(request)
        
        # Should fall back to rule-based suggestions
        assert response.fallback_mode is True
        assert response.provider_used == "fallback"
        assert len(response.suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_timing_measurement(self):
        """Test that timing is measured correctly."""
        engine = SuggestionEngine([MockAIProvider()])
        vague_phrase = VaguePhrase.create(0, 9, "something", VagueType.GENERIC_TERM)
        request = SuggestionRequest(vague_phrase=vague_phrase, full_context="Write something")
        
        response = await engine.generate_suggestions(request)
        
        assert response.generation_time_ms >= 0
        assert response.generation_time_ms < 1000  # Should be very fast for mock