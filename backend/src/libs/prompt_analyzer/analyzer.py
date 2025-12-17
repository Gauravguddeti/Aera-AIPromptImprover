"""
Core analyzer module for detecting vague phrases in AI prompts.

This module provides the main PromptAnalyzer class and supporting data structures.
"""

import re
from dataclasses import dataclass, asdict
from enum import Enum
from typing import List, Dict, Any, Optional
from uuid import uuid4, UUID


class VagueType(Enum):
    """Types of vague phrases that can be detected."""
    GENERIC_TERM = "generic_term"  # "something", "stuff", "things"
    SUBJECTIVE_QUALIFIER = "subjective_qualifier"  # "good", "better", "nice"
    MISSING_CONTEXT = "missing_context"  # "it", "this", "that" without clear reference
    IMPRECISE_QUANTITY = "imprecise_quantity"  # "some", "many", "few"
    WEAK_INSTRUCTION = "weak_instruction"  # "try to", "maybe", "kind of"
    MISSING_EXAMPLES = "missing_examples"  # Zero-shot when few-shot would help
    MISSING_REASONING = "missing_reasoning"  # Missing CoT/step-by-step
    MISSING_STRUCTURE = "missing_structure"  # Could use ReAct/ToT format
    AMBIGUOUS_TASK = "ambiguous_task"  # Task definition unclear


class ImprovementType(Enum):
    """Types of improvements that can be suggested."""
    SPECIFICITY = "specificity"
    CLARITY = "clarity"
    CONTEXT = "context"
    PRECISION = "precision"
    STRENGTH = "strength"


@dataclass
class VaguePhrase:
    """Represents a vague phrase detected in a prompt."""
    id: UUID
    start_position: int
    end_position: int
    original_text: str
    vague_type: VagueType
    confidence_score: float
    
    @classmethod
    def create(cls, start: int, end: int, text: str, vague_type: VagueType, confidence: float = 1.0):
        """Create a new VaguePhrase with generated UUID."""
        return cls(
            id=uuid4(),
            start_position=start,
            end_position=end,
            original_text=text,
            vague_type=vague_type,
            confidence_score=confidence
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": str(self.id),
            "start": self.start_position,
            "end": self.end_position,
            "text": self.original_text,
            "type": self.vague_type.value,
            "confidence": self.confidence_score
        }


@dataclass
class Suggestion:
    """Represents an improvement suggestion for a vague phrase."""
    id: UUID
    improved_text: str
    rationale: str
    improvement_type: ImprovementType
    confidence_score: float
    
    @classmethod
    def create(cls, improved_text: str, rationale: str, improvement_type: ImprovementType, confidence: float = 1.0):
        """Create a new Suggestion with generated UUID."""
        return cls(
            id=uuid4(),
            improved_text=improved_text,
            rationale=rationale,
            improvement_type=improvement_type,
            confidence_score=confidence
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": str(self.id),
            "improved_text": self.improved_text,
            "rationale": self.rationale,
            "type": self.improvement_type.value,
            "confidence": self.confidence_score
        }


@dataclass
class AnalysisResult:
    """Complete analysis result for a prompt."""
    original_text: str
    vague_phrases: List[VaguePhrase]
    analysis_time_ms: float
    error: Optional[str] = None
    fallback_mode: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "original_text": self.original_text,
            "vague_phrases": [phrase.to_dict() for phrase in self.vague_phrases],
            "analysis_time_ms": self.analysis_time_ms,
            "error": self.error,
            "fallback_mode": self.fallback_mode
        }


class PromptAnalyzer:
    """Main analyzer class for detecting vague phrases in prompts."""
    
    # Pattern definitions for vague phrase detection
    VAGUE_PATTERNS = {
        VagueType.GENERIC_TERM: [
            r'\b(something|stuff|things?|item|matter|element)\b',
            r'\b(anything|everything|nothing)\b',
            r'\b(someone|somebody|anyone|everybody)\b',
            r'\ba\s+(new|basic|simple|quick|small)\s+(feature|function|component|module|tool|system|method)\b',  # "a new feature"
            r'\bthe\s+(feature|function|component|module|bot|agent|system|code|app)\b',  # "the feature", "the bot"
            r'\bsome\s+(code|logic|functionality|feature)\b',  # "some code"
            r'\b(my|the)\s+(code|project|app|application|system|program)\b',  # "my code" without specifics
        ],
        VagueType.SUBJECTIVE_QUALIFIER: [
            r'\b(good|better|best|bad|worse|worst)\b',
            r'\b(nice|great|awesome|amazing|terrible)\b',
            r'\b(cool|neat|interesting|boring)\b',
            r'\b(easy|simple|hard|difficult|complex)\b',
            r'\b(clean|elegant|efficient|optimized)\b(?!\s+(algorithm|solution|implementation))',  # "clean" without specifics
        ],
        VagueType.MISSING_CONTEXT: [
            r'\b(it|this|that|these|those)\b(?!\s+\w+)',  # Pronouns without clear reference
            r'\b(here|there)\b(?!\s+(is|are|was|were))',  # Location without context
            r'\bto\s+(add|integrate|implement|create|build|make)\b(?!\s+(a|an|the)\s+\w+\s+\w+)',  # "to add" without object
        ],
        VagueType.IMPRECISE_QUANTITY: [
            r'\b(some|many|few|several|various|multiple)\b',
            r'\b(a lot|lots|tons|loads|plenty)\b',
            r'\b(little|bit|piece|part)\b',
        ],
        VagueType.WEAK_INSTRUCTION: [
            r'\b(try to|attempt to|maybe|perhaps|possibly)\b',
            r'\b(kind of|sort of|somewhat|rather)\b',
            r'\b(please|could you|would you mind)\b',
            r'\b(want to|need to|should)\s+(add|create|make|build|implement|integrate)\b',  # "want to add" is weak
        ],
        VagueType.MISSING_EXAMPLES: [
            # Detect task requests without examples that would benefit from few-shot
            r'\b(classify|categorize|label|tag|identify|extract|parse|format|convert)\b(?!.*example)',
            r'\b(write|generate|create)\s+(a|an|the)\s+\w+(?!.*example|.*like|.*such as)',
            r'\b(analyze|evaluate|assess|judge|rate|score)\b(?!.*example|.*for instance)',
        ],
        VagueType.MISSING_REASONING: [
            # Detect complex tasks that need step-by-step reasoning (CoT)
            r'\b(explain|analyze|solve|calculate|determine|figure out|reason|deduce)\b(?!.*step|.*first|.*then)',
            r'\b(why|how does|what causes|what leads to)\b(?!.*because|.*step)',
            r'\b(complex|difficult|multi-step|intricate)\s+(problem|task|question)\b',
        ],
        VagueType.MISSING_STRUCTURE: [
            # Detect tasks that could use ReAct or ToT patterns
            r'\b(plan|strategy|approach|method)\b(?!.*1\.|.*first|.*step)',
            r'\b(debug|troubleshoot|fix|resolve)\b(?!.*check|.*verify|.*step)',
            r'\b(multiple (solutions|approaches|ways|options|alternatives))\b',
        ],
        VagueType.AMBIGUOUS_TASK: [
            # Detect unclear task definitions
            r'^(?!.*\b(create|write|generate|list|explain|analyze|classify)\b).{0,30}$',  # Very short prompts
            r'\b(do|make|handle|process)\s+(this|that|it)\b',  # Vague task verbs
        ]
    }
    
    def __init__(self):
        """Initialize the analyzer."""
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for efficiency."""
        self._compiled_patterns = {}
        for vague_type, patterns in self.VAGUE_PATTERNS.items():
            self._compiled_patterns[vague_type] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
    
    def analyze(self, text: str) -> AnalysisResult:
        """
        Analyze text for vague phrases.
        
        Args:
            text: The prompt text to analyze
            
        Returns:
            AnalysisResult containing detected vague phrases
        """
        import time
        
        try:
            start_time = time.perf_counter()
            vague_phrases = self._detect_vague_phrases(text)
            analysis_time = (time.perf_counter() - start_time) * 1000
            
            return AnalysisResult(
                original_text=text,
                vague_phrases=vague_phrases,
                analysis_time_ms=analysis_time
            )
        except Exception as e:
            # Fallback error handling - return basic result with error info
            return AnalysisResult(
                original_text=text,
                vague_phrases=[],
                analysis_time_ms=0.0,
                error=str(e),
                fallback_mode=True
            )
    
    def _detect_vague_phrases(self, text: str) -> List[VaguePhrase]:
        """Detect vague phrases using pattern matching."""
        vague_phrases = []
        
        for vague_type, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                for match in pattern.finditer(text):
                    phrase = VaguePhrase.create(
                        start=match.start(),
                        end=match.end(),
                        text=match.group(),
                        vague_type=vague_type,
                        confidence=self._calculate_confidence(match.group(), vague_type)
                    )
                    vague_phrases.append(phrase)
        
        # Sort by position in text
        vague_phrases.sort(key=lambda p: p.start_position)
        
        # Remove overlapping matches (keep highest confidence)
        return self._remove_overlaps(vague_phrases)
    
    def _calculate_confidence(self, text: str, vague_type: VagueType) -> float:
        """Calculate confidence score for a detected phrase."""
        # Simple confidence calculation based on phrase type
        confidence_map = {
            VagueType.GENERIC_TERM: 0.9,
            VagueType.SUBJECTIVE_QUALIFIER: 0.8,
            VagueType.MISSING_CONTEXT: 0.7,
            VagueType.IMPRECISE_QUANTITY: 0.8,
            VagueType.WEAK_INSTRUCTION: 0.6,
        }
        return confidence_map.get(vague_type, 0.5)
    
    def _remove_overlaps(self, phrases: List[VaguePhrase]) -> List[VaguePhrase]:
        """Remove overlapping vague phrases, keeping the one with highest confidence."""
        if not phrases:
            return phrases
        
        non_overlapping = []
        phrases_sorted = sorted(phrases, key=lambda p: (p.start_position, -p.confidence_score))
        
        for phrase in phrases_sorted:
            # Check if this phrase overlaps with any accepted phrase
            overlaps = False
            for accepted in non_overlapping:
                if (phrase.start_position < accepted.end_position and 
                    phrase.end_position > accepted.start_position):
                    overlaps = True
                    break
            
            if not overlaps:
                non_overlapping.append(phrase)
        
        return sorted(non_overlapping, key=lambda p: p.start_position)