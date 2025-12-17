"""
Tests for Pydantic data models and validation.

These tests ensure that our API models validate correctly,
provide proper error messages, and serialize/deserialize properly.
"""

import json
import pytest
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import ValidationError

from src.models.schemas import (
    VagueTypeModel,
    ImprovementTypeModel,
    VaguePhraseModel,
    SuggestionModel,
    VaguePhraseWithSuggestionsModel,
    AnalysisRequest,
    AnalysisResponse,
    AnalysisOptionsModel,
    SuggestionRequest,
    SuggestionResponse,
    UserPreferences,
    AnalysisPreferences,
    SuggestionPreferences,
    UIPreferences,
    HealthResponse,
    HealthStatus,
    DependencyHealth,
    ErrorResponse,
    ErrorDetail,
    WebSocketAnalysisRequest,
    WebSocketAnalysisResponse,
    WebSocketMessageType,
)


class TestVaguePhraseModel:
    """Test VaguePhraseModel validation and serialization."""
    
    def test_valid_vague_phrase(self):
        """Test creating a valid vague phrase model."""
        phrase_id = uuid4()
        phrase = VaguePhraseModel(
            id=phrase_id,
            start_position=5,
            end_position=14,
            text="something",
            type=VagueTypeModel.GENERIC_TERM,
            confidence=0.9
        )
        
        assert phrase.id == phrase_id
        assert phrase.start_position == 5
        assert phrase.end_position == 14
        assert phrase.text == "something"
        assert phrase.type == VagueTypeModel.GENERIC_TERM
        assert phrase.confidence == 0.9
    
    def test_end_position_validation(self):
        """Test that end_position must be greater than start_position."""
        with pytest.raises(ValidationError) as exc_info:
            VaguePhraseModel(
                id=uuid4(),
                start_position=10,
                end_position=5,  # Invalid: end before start
                text="something",
                type=VagueTypeModel.GENERIC_TERM,
                confidence=0.9
            )
        
        errors = exc_info.value.errors()
        assert any("end_position must be greater than start_position" in str(error) for error in errors)
    
    def test_confidence_range_validation(self):
        """Test that confidence must be between 0.0 and 1.0."""
        # Test confidence too high
        with pytest.raises(ValidationError):
            VaguePhraseModel(
                id=uuid4(),
                start_position=5,
                end_position=14,
                text="something",
                type=VagueTypeModel.GENERIC_TERM,
                confidence=1.5  # Invalid: > 1.0
            )
        
        # Test confidence too low
        with pytest.raises(ValidationError):
            VaguePhraseModel(
                id=uuid4(),
                start_position=5,
                end_position=14,
                text="something",
                type=VagueTypeModel.GENERIC_TERM,
                confidence=-0.1  # Invalid: < 0.0
            )
    
    def test_empty_text_validation(self):
        """Test that text cannot be empty."""
        with pytest.raises(ValidationError):
            VaguePhraseModel(
                id=uuid4(),
                start_position=5,
                end_position=14,
                text="",  # Invalid: empty text
                type=VagueTypeModel.GENERIC_TERM,
                confidence=0.9
            )


class TestSuggestionModel:
    """Test SuggestionModel validation and serialization."""
    
    def test_valid_suggestion(self):
        """Test creating a valid suggestion model."""
        suggestion_id = uuid4()
        suggestion = SuggestionModel(
            id=suggestion_id,
            improved_text="a specific example",
            rationale="Replace vague 'something' with concrete request",
            type=ImprovementTypeModel.SPECIFICITY,
            confidence=0.8,
            original_phrase="something"
        )
        
        assert suggestion.id == suggestion_id
        assert suggestion.improved_text == "a specific example"
        assert suggestion.rationale == "Replace vague 'something' with concrete request"
        assert suggestion.type == ImprovementTypeModel.SPECIFICITY
        assert suggestion.confidence == 0.8
        assert suggestion.original_phrase == "something"
    
    def test_empty_fields_validation(self):
        """Test that required text fields cannot be empty."""
        with pytest.raises(ValidationError):
            SuggestionModel(
                id=uuid4(),
                improved_text="",  # Invalid: empty
                rationale="Some rationale",
                type=ImprovementTypeModel.SPECIFICITY,
                confidence=0.8,
                original_phrase="something"
            )


class TestAnalysisRequest:
    """Test AnalysisRequest validation."""
    
    def test_valid_analysis_request(self):
        """Test creating a valid analysis request."""
        request = AnalysisRequest(
            content="Write something good about AI",
            options=AnalysisOptionsModel(
                include_suggestions=True,
                max_suggestions_per_phrase=3
            )
        )
        
        assert request.content == "Write something good about AI"
        assert request.options is not None
        assert request.options.include_suggestions is True
        assert request.options.max_suggestions_per_phrase == 3
    
    def test_default_options(self):
        """Test that options are optional."""
        request = AnalysisRequest(content="Write something good about AI")
        
        assert request.content == "Write something good about AI"
        assert request.options is None
    
    def test_empty_content_validation(self):
        """Test that content cannot be empty or whitespace only."""
        with pytest.raises(ValidationError) as exc_info:
            AnalysisRequest(content="   ")  # Only whitespace
        
        errors = exc_info.value.errors()
        assert any("Content cannot be empty or whitespace only" in str(error) for error in errors)
    
    def test_content_length_validation(self):
        """Test that content has a maximum length."""
        long_content = "a" * 10001  # Exceeds max_length=10000
        
        with pytest.raises(ValidationError):
            AnalysisRequest(content=long_content)


class TestAnalysisOptionsModel:
    """Test AnalysisOptionsModel validation."""
    
    def test_default_values(self):
        """Test that all options have sensible defaults."""
        options = AnalysisOptionsModel()
        
        assert options.include_suggestions is False
        assert options.max_suggestions_per_phrase == 3
        assert options.min_confidence == 0.5
        assert options.debounce_ms == 300
    
    def test_range_validations(self):
        """Test range validations for numeric fields."""
        # Test max_suggestions_per_phrase range
        with pytest.raises(ValidationError):
            AnalysisOptionsModel(max_suggestions_per_phrase=0)  # Below minimum
        
        with pytest.raises(ValidationError):
            AnalysisOptionsModel(max_suggestions_per_phrase=11)  # Above maximum
        
        # Test debounce_ms range
        with pytest.raises(ValidationError):
            AnalysisOptionsModel(debounce_ms=-1)  # Below minimum
        
        with pytest.raises(ValidationError):
            AnalysisOptionsModel(debounce_ms=5001)  # Above maximum


class TestAnalysisResponse:
    """Test AnalysisResponse model."""
    
    def test_valid_analysis_response(self):
        """Test creating a valid analysis response."""
        phrase_id = uuid4()
        analysis_id = uuid4()
        
        response = AnalysisResponse(
            analysis_id=analysis_id,
            content="Write something good about AI",
            vague_phrases=[
                VaguePhraseWithSuggestionsModel(
                    id=phrase_id,
                    start_position=6,
                    end_position=15,
                    text="something",
                    type=VagueTypeModel.GENERIC_TERM,
                    confidence=0.9
                )
            ],
            analysis_time_ms=125.5
        )
        
        assert response.analysis_id == analysis_id
        assert response.content == "Write something good about AI"
        assert len(response.vague_phrases) == 1
        assert response.vague_phrases[0].id == phrase_id
        assert response.analysis_time_ms == 125.5
        assert isinstance(response.timestamp, datetime)
    
    def test_auto_generated_fields(self):
        """Test that UUID and timestamp are auto-generated."""
        response = AnalysisResponse(
            content="Test content",
            vague_phrases=[],
            analysis_time_ms=50.0
        )
        
        assert isinstance(response.analysis_id, UUID)
        assert isinstance(response.timestamp, datetime)


class TestUserPreferences:
    """Test UserPreferences model."""
    
    def test_default_preferences(self):
        """Test that preferences have sensible defaults."""
        prefs = UserPreferences()
        
        # Analysis preferences
        assert prefs.analysis.auto_analyze is True
        assert prefs.analysis.debounce_ms == 300
        assert prefs.analysis.min_confidence == 0.6
        
        # Suggestion preferences
        assert prefs.suggestions.max_per_phrase == 3
        assert prefs.suggestions.preferred_style == "professional"
        assert prefs.suggestions.include_rationale is True
        assert prefs.suggestions.auto_apply_high_confidence is False
        
        # UI preferences
        assert prefs.ui.theme == "light"
        assert prefs.ui.highlight_style == "underline"
        assert prefs.ui.show_confidence is True
        assert prefs.ui.compact_suggestions is False
    
    def test_nested_model_validation(self):
        """Test that nested models are validated properly."""
        with pytest.raises(ValidationError):
            UserPreferences(
                analysis=AnalysisPreferences(debounce_ms=-1)  # Invalid
            )


class TestHealthResponse:
    """Test HealthResponse model."""
    
    def test_valid_health_response(self):
        """Test creating a valid health response."""
        response = HealthResponse(
            status=HealthStatus.HEALTHY,
            version="0.1.0",
            dependencies={
                "ollama": DependencyHealth(
                    available=True,
                    response_time_ms=45.2,
                    version="mistral:8b"
                ),
                "database": DependencyHealth(
                    available=False,
                    error="Connection timeout"
                )
            }
        )
        
        assert response.status == HealthStatus.HEALTHY
        assert response.version == "0.1.0"
        assert response.dependencies["ollama"].available is True
        assert response.dependencies["ollama"].response_time_ms == 45.2
        assert response.dependencies["database"].available is False
        assert response.dependencies["database"].error == "Connection timeout"


class TestWebSocketModels:
    """Test WebSocket message models."""
    
    def test_websocket_analysis_request(self):
        """Test WebSocket analysis request model."""
        analysis_request = AnalysisRequest(content="Test content")
        
        ws_request = WebSocketAnalysisRequest(data=analysis_request)
        
        assert ws_request.type == WebSocketMessageType.ANALYSIS_REQUEST
        assert ws_request.data.content == "Test content"
        assert isinstance(ws_request.timestamp, datetime)
    
    def test_websocket_analysis_response(self):
        """Test WebSocket analysis response model."""
        analysis_response = AnalysisResponse(
            content="Test content",
            vague_phrases=[],
            analysis_time_ms=50.0
        )
        
        ws_response = WebSocketAnalysisResponse(data=analysis_response)
        
        assert ws_response.type == WebSocketMessageType.ANALYSIS_RESPONSE
        assert ws_response.data.content == "Test content"
        assert isinstance(ws_response.timestamp, datetime)


class TestModelSerialization:
    """Test model JSON serialization/deserialization."""
    
    def test_vague_phrase_serialization(self):
        """Test that VaguePhraseModel serializes to valid JSON."""
        phrase = VaguePhraseModel(
            id=uuid4(),
            start_position=5,
            end_position=14,
            text="something",
            type=VagueTypeModel.GENERIC_TERM,
            confidence=0.9
        )
        
        # Should serialize without errors
        json_str = phrase.model_dump_json()
        parsed = json.loads(json_str)
        
        assert parsed["text"] == "something"
        assert parsed["type"] == "generic_term"
        assert parsed["confidence"] == 0.9
    
    def test_analysis_request_deserialization(self):
        """Test that AnalysisRequest can be created from JSON."""
        json_data = {
            "content": "Write something good",
            "options": {
                "include_suggestions": True,
                "max_suggestions_per_phrase": 5
            }
        }
        
        request = AnalysisRequest.model_validate(json_data)
        
        assert request.content == "Write something good"
        assert request.options is not None
        assert request.options.include_suggestions is True
        assert request.options.max_suggestions_per_phrase == 5


class TestErrorResponse:
    """Test ErrorResponse model."""
    
    def test_error_response_with_details(self):
        """Test error response with detailed error information."""
        error = ErrorResponse(
            detail="Validation error in request data",
            errors=[
                ErrorDetail(
                    type="value_error",
                    message="Content cannot be empty",
                    field="content",
                    code="EMPTY_CONTENT"
                )
            ]
        )
        
        assert error.detail == "Validation error in request data"
        assert error.errors is not None
        assert len(error.errors) == 1
        assert error.errors[0].field == "content"
        assert error.errors[0].code == "EMPTY_CONTENT"
        assert isinstance(error.timestamp, datetime)