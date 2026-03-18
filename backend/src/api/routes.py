"""
API routes for prompt analysis.

This module implements the FastAPI endpoints for analyzing AI prompts,
getting suggestions, and managing user preferences.
"""

import time
from typing import Dict, List, Optional
from uuid import UUID
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Path
from fastapi.responses import JSONResponse

from ..libs.prompt_analyzer.analyzer import PromptAnalyzer
from ..libs.suggestion_engine.engine import SuggestionEngine, SuggestionRequest as LibSuggestionRequest, AIProvider
from ..libs.suggestion_engine import GroqWithOllamaFallbackProvider, RuleBasedProvider
from ..config import settings
from ..models import (
    AnalysisRequest,
    AnalysisResponse,
    SuggestionRequest,
    SuggestionResponse,
    SuggestionFeedbackRequest,
    SuggestionFeedbackResponse,
    UserPreferences,
    ModelConverter,
    ErrorResponse,
    ErrorDetail
)

router = APIRouter(prefix="/api", tags=["analysis"])

# Initialize our libraries
prompt_analyzer = PromptAnalyzer()

# Initialize suggestion engine with providers

# Try Groq first, fallback to rule-based
providers: List[AIProvider] = [
    GroqWithOllamaFallbackProvider(
        api_key=settings.GROQ_API_KEY,
        groq_model=settings.GROQ_MODEL,
        ollama_model=settings.OLLAMA_MODEL,
        ollama_host=settings.OLLAMA_HOST,
    ),
    RuleBasedProvider()     # Fallback if Groq unavailable
]
suggestion_engine = SuggestionEngine(providers)

# Model discovery (Mocked/Static for Groq)
# model_discovery = ModelDiscovery()

# In-memory storage for phrases from recent analyses (for suggestions endpoint)
# In production, this would be a proper database or cache
recent_phrases: Dict[str, tuple] = {}  # phrase_id -> (phrase, context)
suggestion_feedback: List[dict] = []


@router.post("/prompts/analyze", response_model=AnalysisResponse)
async def analyze_prompt(request: AnalysisRequest) -> AnalysisResponse:
    """
    Analyze a prompt for vague phrases and optionally generate suggestions.
    
    This endpoint detects vague phrases in the provided prompt text and can
    optionally generate improvement suggestions for each detected phrase.
    """
    try:
        start_time = time.perf_counter()

        if not request.content:
            return AnalysisResponse(
                content="",
                vague_phrases=[],
                analysis_time_ms=0.0,
            )
        
        # Extract options with defaults
        options = request.options
        include_suggestions = options.include_suggestions if options else False
        max_suggestions = options.max_suggestions_per_phrase if options else 3
        min_confidence = options.min_confidence if options else 0.5
        
        # Analyze the prompt for vague phrases
        analysis_result = prompt_analyzer.analyze(request.content)
        
        # Filter by confidence threshold
        filtered_phrases = [
            phrase for phrase in analysis_result.vague_phrases 
            if phrase.confidence_score >= min_confidence
        ]
        
        # Store phrases for later suggestions requests
        for phrase in filtered_phrases:
            recent_phrases[str(phrase.id)] = (phrase, request.content)
        
        # Generate suggestions if requested
        suggestions_dict = {}
        if include_suggestions and filtered_phrases:
            for phrase in filtered_phrases:
                try:
                    # Create suggestion request for this phrase
                    lib_request = LibSuggestionRequest(
                        vague_phrase=phrase,
                        full_context=request.content,
                        max_suggestions=max_suggestions
                    )
                    
                    # Get suggestions for this phrase
                    suggestion_response = await suggestion_engine.generate_suggestions(lib_request)
                    
                    if suggestion_response.suggestions:
                        suggestions_dict[phrase.id] = suggestion_response.suggestions
                
                except Exception as e:
                    # Log error but continue with other phrases
                    print(f"Error generating suggestions for phrase '{phrase.original_text}': {e}")
                    continue
        
        # Convert to API models
        api_phrases = ModelConverter.vague_phrases_with_suggestions_to_models(
            filtered_phrases, suggestions_dict if include_suggestions else None
        )
        
        end_time = time.perf_counter()
        analysis_time_ms = (end_time - start_time) * 1000
        
        return AnalysisResponse(
            content=request.content,
            vague_phrases=api_phrases,
            analysis_time_ms=analysis_time_ms
        )
        
    except Exception as e:
        error_detail = ErrorDetail(
            type="analysis_error",
            message=f"Failed to analyze prompt: {str(e)}",
            code="ANALYSIS_FAILED"
        )
        
        error_response = ErrorResponse(
            detail="Prompt analysis failed",
            errors=[error_detail]
        )
        
        raise HTTPException(
            status_code=500,
            detail=error_response.model_dump()
        )


@router.get("/suggestions/{phrase_id}", response_model=SuggestionResponse)
async def get_suggestions_for_phrase(
    phrase_id: str = Path(..., description="ID of the vague phrase"),
    max_suggestions: int = Query(3, ge=1, le=10, description="Maximum number of suggestions"),
    min_confidence: float = Query(0.5, ge=0.0, le=1.0, description="Minimum confidence threshold"),
    preferred_style: Optional[str] = Query(None, description="Preferred writing style")
) -> SuggestionResponse:
    """
    Get improvement suggestions for a specific vague phrase.
    
    This endpoint generates suggestions for a previously detected vague phrase
    using the phrase ID from an analysis response.
    """
    try:
        start_time = time.perf_counter()
        
        # Validate UUID format first
        try:
            uuid_obj = UUID(phrase_id)
        except ValueError:
            # Invalid UUID format should return 404, not 422
            raise HTTPException(
                status_code=404,
                detail={
                    "detail": "Phrase not found",
                    "errors": [
                        {
                            "type": "not_found",
                            "message": f"No phrase found with ID {phrase_id}",
                            "field": "phrase_id", 
                            "code": "PHRASE_NOT_FOUND"
                        }
                    ]
                }
            )
        
        # Look up the phrase in our recent storage
        phrase_key = str(uuid_obj)  # Use the validated UUID
        if phrase_key not in recent_phrases:
            raise HTTPException(
                status_code=404,
                detail={
                    "detail": "Phrase not found",
                    "errors": [
                        {
                            "type": "not_found",
                            "message": f"No phrase found with ID {phrase_id}",
                            "field": "phrase_id",
                            "code": "PHRASE_NOT_FOUND"
                        }
                    ]
                }
            )
        
        # Get the stored phrase and context
        phrase, context = recent_phrases[phrase_key]
        
        # Create suggestion request for this phrase
        lib_request = LibSuggestionRequest(
            vague_phrase=phrase,
            full_context=context,
            max_suggestions=max_suggestions
        )
        
        # Generate suggestions
        suggestion_response_lib = await suggestion_engine.generate_suggestions(lib_request)
        
        # Filter by confidence if needed
        filtered_suggestions = [
            suggestion for suggestion in suggestion_response_lib.suggestions
            if suggestion.confidence_score >= min_confidence
        ]
        
        # Convert to API models
        api_suggestions = ModelConverter.suggestions_to_models(filtered_suggestions)
        
        end_time = time.perf_counter()
        generation_time_ms = (end_time - start_time) * 1000
        
        return SuggestionResponse(
            phrase_id=uuid_obj,  # Use the validated UUID object
            suggestions=api_suggestions,
            generation_time_ms=generation_time_ms,
            provider_used=suggestion_response_lib.provider_used,
            fallback_mode=suggestion_response_lib.fallback_mode
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_detail = ErrorDetail(
            type="suggestion_error",
            message=f"Failed to generate suggestions: {str(e)}",
            code="SUGGESTION_FAILED"
        )
        
        error_response = ErrorResponse(
            detail="Suggestion generation failed",
            errors=[error_detail]
        )
        
        raise HTTPException(
            status_code=500,
            detail=error_response.model_dump()
        )


@router.post("/suggestions/feedback", response_model=SuggestionFeedbackResponse)
async def submit_suggestion_feedback(feedback: SuggestionFeedbackRequest) -> SuggestionFeedbackResponse:
    """Record user feedback for a suggestion (thumbs up/down)."""
    try:
        feedback_id = uuid4()
        suggestion_feedback.append(
            {
                "feedback_id": str(feedback_id),
                "suggestion_id": str(feedback.suggestion_id),
                "phrase_text": feedback.phrase_text,
                "improved_text": feedback.improved_text,
                "rating": feedback.rating.value,
                "context": feedback.context,
                "provider_used": feedback.provider_used,
                "created_at": time.time(),
            }
        )

        # Keep in-memory storage bounded.
        if len(suggestion_feedback) > 1000:
            suggestion_feedback.pop(0)

        return SuggestionFeedbackResponse(
            feedback_id=feedback_id,
            received=True,
            rating=feedback.rating,
            message="Feedback recorded",
        )
    except Exception as e:
        error_detail = ErrorDetail(
            type="feedback_error",
            message=f"Failed to store feedback: {str(e)}",
            code="FEEDBACK_STORE_FAILED"
        )
        error_response = ErrorResponse(
            detail="Failed to store suggestion feedback",
            errors=[error_detail]
        )
        raise HTTPException(
            status_code=500,
            detail=error_response.model_dump()
        )


@router.get("/preferences", response_model=UserPreferences)
async def get_preferences() -> UserPreferences:
    """
    Get current user preferences.
    
    Returns the user's current analysis, suggestion, and UI preferences.
    For now, this returns default preferences since we don't have persistence.
    """
    try:
        # Return default preferences
        # In a real implementation, this would load from user storage
        return UserPreferences()
        
    except Exception as e:
        error_detail = ErrorDetail(
            type="preferences_error",
            message=f"Failed to load preferences: {str(e)}",
            code="PREFERENCES_LOAD_FAILED"
        )
        
        error_response = ErrorResponse(
            detail="Failed to load user preferences",
            errors=[error_detail]
        )
        
        raise HTTPException(
            status_code=500,
            detail=error_response.model_dump()
        )


@router.put("/preferences", response_model=UserPreferences)
async def update_preferences(preferences: UserPreferences) -> UserPreferences:
    """
    Update user preferences.
    
    Updates the user's analysis, suggestion, and UI preferences.
    For now, this just returns the provided preferences since we don't have persistence.
    """
    try:
        # In a real implementation, this would save to user storage
        # For now, just return the preferences as confirmation
        return preferences
        
    except Exception as e:
        error_detail = ErrorDetail(
            type="preferences_error", 
            message=f"Failed to save preferences: {str(e)}",
            code="PREFERENCES_SAVE_FAILED"
        )
        
        error_response = ErrorResponse(
            detail="Failed to save user preferences",
            errors=[error_detail]
        )
        
        raise HTTPException(
            status_code=500,
            detail=error_response.model_dump()
        )


@router.get("/models/discover")
async def discover_models():
    """
    Discover locally available models and provide recommendations.
    
    Updated to support Groq API.
    """
    try:
        # Static response for Groq
        groq_model = settings.GROQ_MODEL
        
        return JSONResponse(content={
            'available_models': [{
                'name': groq_model,
                'size': 'N/A', 
                'size_gb': 0,
                'modified': 'Remote'
            }],
            'recommendations': [{
                'model_name': groq_model,
                'suitable_for': ['analysis', 'rewriting', 'inline_checks'],
                'warnings': [],
                'score': 1.0
            }],
            'status': 'ok',
            'best_models': {
                'analysis': groq_model,
                'rewriting': groq_model,
                'inline_checks': groq_model
            }
        })
    except Exception as e:
        error_detail = ErrorDetail(
            type="model_discovery_error",
            message=f"Failed to discover models: {str(e)}",
            code="MODEL_DISCOVERY_FAILED"
        )
        
        error_response = ErrorResponse(
            detail="Failed to discover Ollama models",
            errors=[error_detail]
        )
        
        raise HTTPException(
            status_code=500,
            detail=error_response.model_dump()
        )