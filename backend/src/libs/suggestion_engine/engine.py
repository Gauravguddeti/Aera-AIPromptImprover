"""
Core suggestion engine for generating AI-powered prompt improvements.

This module provides the main SuggestionEngine class and supporting abstractions.
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from enum import Enum
from typing import List, Dict, Any, Optional, Protocol
from uuid import uuid4, UUID

# Import the VaguePhrase from prompt_analyzer
try:
    from ..prompt_analyzer.analyzer import VaguePhrase, VagueType
except ImportError:
    # Fallback for standalone usage
    from prompt_analyzer.analyzer import VaguePhrase, VagueType


class ImprovementType(Enum):
    """Types of improvements that can be suggested."""
    SPECIFICITY = "specificity"
    CLARITY = "clarity"
    CONTEXT = "context"
    PRECISION = "precision"
    STRENGTH = "strength"


@dataclass
class Suggestion:
    """Represents an improvement suggestion for a vague phrase."""
    id: UUID
    improved_text: str
    rationale: str
    improvement_type: ImprovementType
    confidence_score: float
    original_phrase: str
    
    @classmethod
    def create(cls, improved_text: str, rationale: str, improvement_type: ImprovementType, 
               original_phrase: str, confidence: float = 1.0):
        """Create a new Suggestion with generated UUID."""
        return cls(
            id=uuid4(),
            improved_text=improved_text,
            rationale=rationale,
            improvement_type=improvement_type,
            confidence_score=confidence,
            original_phrase=original_phrase
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": str(self.id),
            "improved_text": self.improved_text,
            "rationale": self.rationale,
            "type": self.improvement_type.value,
            "confidence": self.confidence_score,
            "original_phrase": self.original_phrase
        }


class AIProvider(ABC):
    """Abstract base class for AI suggestion providers."""
    
    @abstractmethod
    async def generate_suggestions(self, vague_phrase: VaguePhrase, context: str) -> List[Suggestion]:
        """Generate suggestions for a vague phrase in context."""
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the AI provider is available."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the provider."""
        pass


@dataclass
class SuggestionRequest:
    """Request for suggestion generation."""
    vague_phrase: VaguePhrase
    full_context: str
    max_suggestions: int = 3
    preferred_style: Optional[str] = None


@dataclass
class SuggestionResponse:
    """Response containing generated suggestions."""
    request: SuggestionRequest
    suggestions: List[Suggestion]
    provider_used: str
    generation_time_ms: float
    error: Optional[str] = None
    fallback_mode: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "vague_phrase": self.request.vague_phrase.to_dict(),
            "full_context": self.request.full_context,
            "suggestions": [s.to_dict() for s in self.suggestions],
            "provider_used": self.provider_used,
            "generation_time_ms": self.generation_time_ms,
            "error": self.error,
            "fallback_mode": self.fallback_mode
        }


class SuggestionEngine:
    """Main engine for generating improvement suggestions."""
    
    def __init__(self, providers: List[AIProvider]):
        """
        Initialize the suggestion engine.
        
        Args:
            providers: List of AI providers to use, in order of preference
        """
        self.providers = providers
        self._fallback_suggestions = self._load_fallback_suggestions()
    
    async def generate_suggestions(self, request: SuggestionRequest) -> SuggestionResponse:
        """
        Generate suggestions for a vague phrase.
        
        Args:
            request: SuggestionRequest containing phrase and context
            
        Returns:
            SuggestionResponse with generated suggestions
        """
        import time
        start_time = time.perf_counter()
        
        try:
            # Try each provider in order
            for provider in self.providers:
                if await provider.is_available():
                    try:
                        suggestions = await provider.generate_suggestions(
                            request.vague_phrase, 
                            request.full_context
                        )
                        
                        # Limit to requested number
                        suggestions = suggestions[:request.max_suggestions]
                        
                        generation_time = (time.perf_counter() - start_time) * 1000
                        return SuggestionResponse(
                            request=request,
                            suggestions=suggestions,
                            provider_used=provider.name,
                            generation_time_ms=generation_time
                        )
                    except Exception as e:
                        # Try next provider
                        continue
            
            # All providers failed, use fallback
            suggestions = self._generate_fallback_suggestions(request)
            generation_time = (time.perf_counter() - start_time) * 1000
            
            return SuggestionResponse(
                request=request,
                suggestions=suggestions,
                provider_used="fallback",
                generation_time_ms=generation_time,
                fallback_mode=True
            )
            
        except Exception as e:
            generation_time = (time.perf_counter() - start_time) * 1000
            return SuggestionResponse(
                request=request,
                suggestions=[],
                provider_used="error",
                generation_time_ms=generation_time,
                error=str(e),
                fallback_mode=True
            )
    
    def _generate_fallback_suggestions(self, request: SuggestionRequest) -> List[Suggestion]:
        """Generate rule-based fallback suggestions."""
        vague_phrase = request.vague_phrase
        suggestions = []
        
        # Get fallback suggestions for this vague type
        fallback_options = self._fallback_suggestions.get(vague_phrase.vague_type, [])
        
        for option in fallback_options[:request.max_suggestions]:
            suggestion = Suggestion.create(
                improved_text=option["replacement"],
                rationale=option["rationale"],
                improvement_type=ImprovementType(option["type"]),
                original_phrase=vague_phrase.original_text,
                confidence=option.get("confidence", 0.5)
            )
            suggestions.append(suggestion)
        
        return suggestions
    
    def _load_fallback_suggestions(self) -> Dict[VagueType, List[Dict[str, Any]]]:
        """Load rule-based fallback suggestions."""
        return {
            VagueType.GENERIC_TERM: [
                {
                    "replacement": "a specific task",
                    "rationale": "Replace 'something' with a specific action or object",
                    "type": "specificity",
                    "confidence": 0.7
                },
                {
                    "replacement": "the following",
                    "rationale": "Replace 'something' with more precise reference",
                    "type": "clarity",
                    "confidence": 0.6
                },
                {
                    "replacement": "a detailed example",
                    "rationale": "Replace 'something' with specific type of content",
                    "type": "specificity",
                    "confidence": 0.8
                }
            ],
            VagueType.SUBJECTIVE_QUALIFIER: [
                {
                    "replacement": "well-structured",
                    "rationale": "Replace 'good' with specific quality description",
                    "type": "specificity",
                    "confidence": 0.7
                },
                {
                    "replacement": "comprehensive",
                    "rationale": "Replace 'good' with measurable quality",
                    "type": "precision",
                    "confidence": 0.8
                },
                {
                    "replacement": "professional",
                    "rationale": "Replace 'good' with specific standard",
                    "type": "clarity",
                    "confidence": 0.7
                }
            ],
            VagueType.IMPRECISE_QUANTITY: [
                {
                    "replacement": "5-10",
                    "rationale": "Replace 'some' with specific range",
                    "type": "precision",
                    "confidence": 0.8
                },
                {
                    "replacement": "3",
                    "rationale": "Replace 'few' with exact number",
                    "type": "precision", 
                    "confidence": 0.9
                },
                {
                    "replacement": "at least 10",
                    "rationale": "Replace 'many' with minimum threshold",
                    "type": "precision",
                    "confidence": 0.7
                }
            ],
            VagueType.WEAK_INSTRUCTION: [
                {
                    "replacement": "Create",
                    "rationale": "Replace 'try to' with direct command",
                    "type": "strength",
                    "confidence": 0.8
                },
                {
                    "replacement": "Generate",
                    "rationale": "Replace weak instruction with action verb",
                    "type": "strength",
                    "confidence": 0.8
                },
                {
                    "replacement": "Write",
                    "rationale": "Replace 'maybe write' with direct instruction",
                    "type": "strength",
                    "confidence": 0.9
                }
            ],
            VagueType.MISSING_CONTEXT: [
                {
                    "replacement": "the document",
                    "rationale": "Replace 'it' with specific reference",
                    "type": "context",
                    "confidence": 0.6
                },
                {
                    "replacement": "this feature",
                    "rationale": "Replace 'this' with specific subject",
                    "type": "context",
                    "confidence": 0.7
                },
                {
                    "replacement": "the API response",
                    "rationale": "Replace vague reference with specific object",
                    "type": "context",
                    "confidence": 0.6
                }
            ]
        }
    
    async def batch_generate_suggestions(self, requests: List[SuggestionRequest]) -> List[SuggestionResponse]:
        """Generate suggestions for multiple vague phrases concurrently."""
        tasks = [self.generate_suggestions(request) for request in requests]
        return await asyncio.gather(*tasks)
    
    def sync_generate_suggestions(self, request: SuggestionRequest) -> SuggestionResponse:
        """Synchronous wrapper for generate_suggestions."""
        return asyncio.run(self.generate_suggestions(request))