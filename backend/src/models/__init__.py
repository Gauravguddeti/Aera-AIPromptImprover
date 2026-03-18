"""
Models package for Aera Backend

This package contains Pydantic models for API request/response validation,
and converters to bridge between library models and API models.
"""

from .schemas import (
    # Core models
    VagueTypeModel,
    ImprovementTypeModel,
    VaguePhraseModel,
    SuggestionModel,
    VaguePhraseWithSuggestionsModel,
    
    # Request/Response models
    AnalysisRequest,
    AnalysisResponse,
    AnalysisOptionsModel,
    SuggestionRequest,
    SuggestionResponse,
    SuggestionFeedbackRating,
    SuggestionFeedbackRequest,
    SuggestionFeedbackResponse,
    
    # Preference models
    UserPreferences,
    AnalysisPreferences,
    SuggestionPreferences,
    UIPreferences,
    
    # Health and error models
    HealthResponse,
    HealthStatus,
    DependencyHealth,
    ErrorResponse,
    ErrorDetail,
    
    # WebSocket models
    WebSocketMessage,
    WebSocketMessageType,
    WebSocketAnalysisRequest,
    WebSocketAnalysisResponse,
    WebSocketError,
)

from .converters import ModelConverter

__all__ = [
    # Core models
    'VagueTypeModel',
    'ImprovementTypeModel',
    'VaguePhraseModel',
    'SuggestionModel',
    'VaguePhraseWithSuggestionsModel',
    
    # Request/Response models
    'AnalysisRequest',
    'AnalysisResponse',
    'AnalysisOptionsModel',
    'SuggestionRequest',
    'SuggestionResponse',
    'SuggestionFeedbackRating',
    'SuggestionFeedbackRequest',
    'SuggestionFeedbackResponse',
    
    # Preference models
    'UserPreferences',
    'AnalysisPreferences',
    'SuggestionPreferences',
    'UIPreferences',
    
    # Health and error models
    'HealthResponse',
    'HealthStatus',
    'DependencyHealth',
    'ErrorResponse',
    'ErrorDetail',
    
    # WebSocket models
    'WebSocketMessage',
    'WebSocketMessageType',
    'WebSocketAnalysisRequest',
    'WebSocketAnalysisResponse',
    'WebSocketError',
    
    # Converters
    'ModelConverter',
]