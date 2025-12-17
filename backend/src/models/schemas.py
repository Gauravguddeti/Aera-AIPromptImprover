"""
Data Models for Aera Backend API

These Pydantic models define the request/response schemas for the API endpoints.
They provide validation, serialization, and documentation for the API.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, ConfigDict


class VagueTypeModel(str, Enum):
    """Types of vague phrases that can be detected."""
    GENERIC_TERM = "generic_term"
    SUBJECTIVE_QUALIFIER = "subjective_qualifier"
    MISSING_CONTEXT = "missing_context"
    IMPRECISE_QUANTITY = "imprecise_quantity"
    WEAK_INSTRUCTION = "weak_instruction"
    MISSING_EXAMPLES = "missing_examples"         # Zero-shot when few-shot would help
    MISSING_REASONING = "missing_reasoning"       # Missing CoT/step-by-step
    MISSING_STRUCTURE = "missing_structure"       # Could use ReAct/ToT format
    AMBIGUOUS_TASK = "ambiguous_task"            # Task definition unclear


class ImprovementTypeModel(str, Enum):
    """Types of improvements that can be suggested."""
    SPECIFICITY = "specificity"
    CLARITY = "clarity"
    CONTEXT = "context"
    PRECISION = "precision"
    STRENGTH = "strength"


class VaguePhraseModel(BaseModel):
    """Model for a detected vague phrase."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "start_position": 6,
                "end_position": 15,
                "text": "something",
                "type": "generic_term",
                "confidence": 0.9
            }
        }
    )
    
    id: UUID = Field(description="Unique identifier for the vague phrase")
    start_position: int = Field(ge=0, description="Start position in the text")
    end_position: int = Field(ge=0, description="End position in the text")
    text: str = Field(min_length=1, description="The actual vague phrase text")
    type: VagueTypeModel = Field(description="Type of vague phrase")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score for the detection")
    
    @field_validator('end_position')
    @classmethod
    def end_after_start(cls, v, info):
        if info.data and 'start_position' in info.data and v <= info.data['start_position']:
            raise ValueError('end_position must be greater than start_position')
        return v


class SuggestionModel(BaseModel):
    """Model for an improvement suggestion."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174001",
                "improved_text": "a specific example",
                "rationale": "Replace vague 'something' with concrete request",
                "type": "specificity",
                "confidence": 0.8,
                "original_phrase": "something"
            }
        }
    )
    
    id: UUID = Field(description="Unique identifier for the suggestion")
    improved_text: str = Field(min_length=1, description="The suggested replacement text")
    rationale: str = Field(min_length=1, description="Explanation of why this is better")
    type: ImprovementTypeModel = Field(description="Type of improvement")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score for the suggestion")
    original_phrase: str = Field(min_length=1, description="The original vague phrase")


class AnalysisOptionsModel(BaseModel):
    """Options for prompt analysis."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "include_suggestions": True,
                "max_suggestions_per_phrase": 3,
                "min_confidence": 0.5,
                "debounce_ms": 300
            }
        }
    )
    
    include_suggestions: bool = Field(default=False, description="Whether to include suggestions in the response")
    max_suggestions_per_phrase: int = Field(default=3, ge=1, le=10, description="Maximum suggestions per vague phrase")
    min_confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Minimum confidence threshold for detection")
    debounce_ms: int = Field(default=300, ge=0, le=5000, description="Debounce delay in milliseconds")


class AnalysisRequest(BaseModel):
    """Request model for prompt analysis."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "Write something good about AI technology",
                "options": {
                    "include_suggestions": True,
                    "max_suggestions_per_phrase": 3
                }
            }
        }
    )
    
    content: str = Field(description="The prompt text to analyze", max_length=50000)
    options: Optional[AnalysisOptionsModel] = Field(default=None, description="Analysis options")
    
    @field_validator('content')
    @classmethod
    def content_not_empty_after_strip(cls, v):
        # Allow empty content - just return an empty analysis
        if v is None:
            raise ValueError('Content cannot be None')
        return v


class VaguePhraseWithSuggestionsModel(VaguePhraseModel):
    """Vague phrase model that may include suggestions."""
    suggestions: Optional[List[SuggestionModel]] = Field(default=None, description="Improvement suggestions for this phrase")


class AnalysisResponse(BaseModel):
    """Response model for prompt analysis."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "analysis_id": "123e4567-e89b-12d3-a456-426614174002",
                "content": "Write something good about AI technology",
                "vague_phrases": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "start_position": 6,
                        "end_position": 15,
                        "text": "something",
                        "type": "generic_term",
                        "confidence": 0.9,
                        "suggestions": [
                            {
                                "id": "123e4567-e89b-12d3-a456-426614174001",
                                "improved_text": "a specific example",
                                "rationale": "Replace vague 'something' with concrete request",
                                "type": "specificity",
                                "confidence": 0.8,
                                "original_phrase": "something"
                            }
                        ]
                    }
                ],
                "analysis_time_ms": 125.5,
                "timestamp": "2025-09-16T10:30:00Z"
            }
        }
    )
    
    analysis_id: UUID = Field(default_factory=uuid4, description="Unique identifier for this analysis")
    content: str = Field(description="The analyzed prompt text")
    vague_phrases: List[VaguePhraseWithSuggestionsModel] = Field(description="Detected vague phrases")
    analysis_time_ms: float = Field(ge=0, description="Time taken for analysis in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the analysis was performed")


class SuggestionRequest(BaseModel):
    """Request model for getting suggestions for a specific phrase."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "max_suggestions": 5,
                "min_confidence": 0.7,
                "preferred_style": "formal"
            }
        }
    )
    
    max_suggestions: Optional[int] = Field(default=3, ge=1, le=10, description="Maximum number of suggestions")
    min_confidence: Optional[float] = Field(default=0.5, ge=0.0, le=1.0, description="Minimum confidence threshold")
    preferred_style: Optional[str] = Field(default=None, description="Preferred writing style (formal, casual, technical)")


class SuggestionResponse(BaseModel):
    """Response model for suggestions."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "phrase_id": "123e4567-e89b-12d3-a456-426614174000",
                "suggestions": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174001",
                        "improved_text": "a specific example",
                        "rationale": "Replace vague 'something' with concrete request",
                        "type": "specificity",
                        "confidence": 0.8,
                        "original_phrase": "something"
                    }
                ],
                "generation_time_ms": 45.2,
                "provider_used": "ollama-mistral:8b",
                "timestamp": "2025-09-16T10:30:00Z"
            }
        }
    )
    
    phrase_id: UUID = Field(description="ID of the vague phrase these suggestions are for")
    suggestions: List[SuggestionModel] = Field(description="Generated suggestions")
    generation_time_ms: float = Field(ge=0, description="Time taken to generate suggestions")
    provider_used: str = Field(description="AI provider that generated the suggestions")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When suggestions were generated")
    fallback_mode: bool = Field(default=False, description="Whether fallback suggestions were used")


class AnalysisPreferences(BaseModel):
    """User preferences for analysis behavior."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "auto_analyze": True,
                "debounce_ms": 300,
                "min_confidence": 0.6
            }
        }
    )
    
    auto_analyze: bool = Field(default=True, description="Whether to automatically analyze as user types")
    debounce_ms: int = Field(default=300, ge=0, le=5000, description="Debounce delay for auto-analysis")
    min_confidence: float = Field(default=0.6, ge=0.0, le=1.0, description="Minimum confidence for phrase detection")


class SuggestionPreferences(BaseModel):
    """User preferences for suggestion generation."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "max_per_phrase": 3,
                "preferred_style": "professional",
                "include_rationale": True,
                "auto_apply_high_confidence": False
            }
        }
    )
    
    max_per_phrase: int = Field(default=3, ge=1, le=10, description="Maximum suggestions per vague phrase")
    preferred_style: str = Field(default="professional", description="Preferred writing style")
    include_rationale: bool = Field(default=True, description="Whether to include rationale for suggestions")
    auto_apply_high_confidence: bool = Field(default=False, description="Auto-apply suggestions with >90% confidence")


class UIPreferences(BaseModel):
    """User preferences for UI behavior."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "theme": "light",
                "highlight_style": "underline",
                "show_confidence": True,
                "compact_suggestions": False
            }
        }
    )
    
    theme: str = Field(default="light", description="UI theme (light, dark, auto)")
    highlight_style: str = Field(default="underline", description="Style for highlighting vague phrases")
    show_confidence: bool = Field(default=True, description="Whether to show confidence scores")
    compact_suggestions: bool = Field(default=False, description="Whether to use compact suggestion display")


class UserPreferences(BaseModel):
    """Complete user preferences model."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "analysis": {
                    "auto_analyze": True,
                    "debounce_ms": 300,
                    "min_confidence": 0.6
                },
                "suggestions": {
                    "max_per_phrase": 3,
                    "preferred_style": "professional",
                    "include_rationale": True
                },
                "ui": {
                    "theme": "light",
                    "highlight_style": "underline",
                    "show_confidence": True
                }
            }
        }
    )
    
    analysis: AnalysisPreferences = Field(default_factory=AnalysisPreferences)
    suggestions: SuggestionPreferences = Field(default_factory=SuggestionPreferences)
    ui: UIPreferences = Field(default_factory=UIPreferences)


class HealthStatus(str, Enum):
    """Health check status values."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class DependencyHealth(BaseModel):
    """Health status of a dependency."""
    available: bool = Field(description="Whether the dependency is available")
    response_time_ms: Optional[float] = Field(default=None, description="Response time in milliseconds")
    version: Optional[str] = Field(default=None, description="Version information")
    model: Optional[str] = Field(default=None, description="Model information (for AI services)")
    error: Optional[str] = Field(default=None, description="Error message if unavailable")


class HealthResponse(BaseModel):
    """Health check response model."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "timestamp": "2025-09-16T10:30:00Z",
                "version": "0.1.0",
                "dependencies": {
                    "ollama": {
                        "available": True,
                        "response_time_ms": 45.2,
                        "version": "mistral:8b"
                    },
                    "database": {
                        "available": True,
                        "response_time_ms": 2.1
                    }
                }
            }
        }
    )
    
    status: HealthStatus = Field(description="Overall health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    version: str = Field(description="Application version")
    dependencies: Dict[str, DependencyHealth] = Field(description="Status of external dependencies")


class ErrorDetail(BaseModel):
    """Detailed error information."""
    type: str = Field(description="Error type")
    message: str = Field(description="Human-readable error message")
    field: Optional[str] = Field(default=None, description="Field that caused the error (for validation errors)")
    code: Optional[str] = Field(default=None, description="Machine-readable error code")


class ErrorResponse(BaseModel):
    """Standard error response model."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": "Validation error in request data",
                "errors": [
                    {
                        "type": "value_error",
                        "message": "Content cannot be empty",
                        "field": "content",
                        "code": "EMPTY_CONTENT"
                    }
                ],
                "timestamp": "2025-09-16T10:30:00Z"
            }
        }
    )
    
    detail: str = Field(description="General error description")
    errors: Optional[List[ErrorDetail]] = Field(default=None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


# Extended analysis schema matching requirements
class IssueSeverity(str, Enum):
    """Severity levels for detected issues."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class IssueType(str, Enum):
    """Types of issues in prompts."""
    AMBIGUITY = "ambiguity"
    MISSING_CONSTRAINT = "missing_constraint"
    CONTRADICTION = "contradiction"
    VERBOSITY = "verbosity"


class PromptIssue(BaseModel):
    """Individual issue detected in prompt analysis."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "start": 6,
                "end": 15,
                "type": "ambiguity",
                "severity": "medium",
                "explanation": "Vague term 'something' weakens the prompt",
                "suggestion": "Specify exactly what you want"
            }
        }
    )
    
    start: int = Field(ge=0, description="Start position of issue")
    end: int = Field(ge=0, description="End position of issue")
    type: IssueType = Field(description="Type of issue")
    severity: IssueSeverity = Field(description="Severity level")
    explanation: str = Field(description="Why this weakens the prompt")
    suggestion: str = Field(description="What to add or change")


class ExtendedAnalysisResponse(BaseModel):
    """Extended analysis response with scoring and model info."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "issues": [
                    {
                        "start": 6,
                        "end": 15,
                        "type": "ambiguity",
                        "severity": "medium",
                        "explanation": "Vague term 'something' weakens the prompt",
                        "suggestion": "Specify exactly what you want"
                    }
                ],
                "overall_score": 0.65,
                "ai_model": "llama3:8b",
                "confidence": 0.85
            }
        }
    )
    
    issues: List[PromptIssue] = Field(description="Detected issues in the prompt")
    overall_score: float = Field(ge=0.0, le=1.0, description="Overall prompt quality score (0-1)")
    ai_model: str = Field(description="AI model used for analysis")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in the analysis")


# WebSocket message models for real-time communication
class WebSocketMessageType(str, Enum):
    """Types of WebSocket messages."""
    ANALYSIS_REQUEST = "analysis_request"
    ANALYSIS_RESPONSE = "analysis_response"
    SUGGESTION_REQUEST = "suggestion_request"
    SUGGESTION_RESPONSE = "suggestion_response"
    ERROR = "error"
    PING = "ping"
    PONG = "pong"


class WebSocketMessage(BaseModel):
    """Base WebSocket message model."""
    type: WebSocketMessageType = Field(description="Message type")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Message payload")


class WebSocketAnalysisRequest(BaseModel):
    """WebSocket message for real-time analysis."""
    type: WebSocketMessageType = Field(default=WebSocketMessageType.ANALYSIS_REQUEST)
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    data: AnalysisRequest = Field(description="Analysis request data")


class WebSocketAnalysisResponse(BaseModel):
    """WebSocket message for analysis results."""
    type: WebSocketMessageType = Field(default=WebSocketMessageType.ANALYSIS_RESPONSE)
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    data: AnalysisResponse = Field(description="Analysis response data")


class WebSocketError(BaseModel):
    """WebSocket error message."""
    type: WebSocketMessageType = Field(default=WebSocketMessageType.ERROR)
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    data: ErrorResponse = Field(description="Error details")