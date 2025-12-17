"""
Model Converters for Aera Backend

These utilities convert between the library models (from prompt_analyzer and suggestion_engine)
and the API models (Pydantic schemas) for proper serialization and validation.
"""

from uuid import uuid4
from typing import List, Optional

from ..libs.prompt_analyzer.analyzer import VaguePhrase, VagueType
from ..libs.suggestion_engine.engine import Suggestion, ImprovementType
from .schemas import (
    VaguePhraseModel,
    VagueTypeModel, 
    SuggestionModel,
    ImprovementTypeModel,
    VaguePhraseWithSuggestionsModel
)


class ModelConverter:
    """Converts between library models and API models."""
    
    @staticmethod
    def vague_type_to_model(vague_type: VagueType) -> VagueTypeModel:
        """Convert library VagueType to API VagueTypeModel."""
        mapping = {
            VagueType.GENERIC_TERM: VagueTypeModel.GENERIC_TERM,
            VagueType.SUBJECTIVE_QUALIFIER: VagueTypeModel.SUBJECTIVE_QUALIFIER,
            VagueType.MISSING_CONTEXT: VagueTypeModel.MISSING_CONTEXT,
            VagueType.IMPRECISE_QUANTITY: VagueTypeModel.IMPRECISE_QUANTITY,
            VagueType.WEAK_INSTRUCTION: VagueTypeModel.WEAK_INSTRUCTION,
            VagueType.MISSING_EXAMPLES: VagueTypeModel.MISSING_EXAMPLES,
            VagueType.MISSING_REASONING: VagueTypeModel.MISSING_REASONING,
            VagueType.MISSING_STRUCTURE: VagueTypeModel.MISSING_STRUCTURE,
            VagueType.AMBIGUOUS_TASK: VagueTypeModel.AMBIGUOUS_TASK
        }
        return mapping[vague_type]
    
    @staticmethod
    def improvement_type_to_model(improvement_type: ImprovementType) -> ImprovementTypeModel:
        """Convert library ImprovementType to API ImprovementTypeModel."""
        mapping = {
            ImprovementType.SPECIFICITY: ImprovementTypeModel.SPECIFICITY,
            ImprovementType.CLARITY: ImprovementTypeModel.CLARITY,
            ImprovementType.CONTEXT: ImprovementTypeModel.CONTEXT,
            ImprovementType.PRECISION: ImprovementTypeModel.PRECISION,
            ImprovementType.STRENGTH: ImprovementTypeModel.STRENGTH
        }
        return mapping[improvement_type]
    
    @staticmethod
    def vague_phrase_to_model(vague_phrase: VaguePhrase) -> VaguePhraseModel:
        """Convert library VaguePhrase to API VaguePhraseModel."""
        return VaguePhraseModel(
            id=vague_phrase.id,
            start_position=vague_phrase.start_position,
            end_position=vague_phrase.end_position,
            text=vague_phrase.original_text,
            type=ModelConverter.vague_type_to_model(vague_phrase.vague_type),
            confidence=vague_phrase.confidence_score
        )
    
    @staticmethod
    def suggestion_to_model(suggestion: Suggestion) -> SuggestionModel:
        """Convert library Suggestion to API SuggestionModel."""
        return SuggestionModel(
            id=suggestion.id,
            improved_text=suggestion.improved_text,
            rationale=suggestion.rationale,
            type=ModelConverter.improvement_type_to_model(suggestion.improvement_type),
            confidence=suggestion.confidence_score,
            original_phrase=suggestion.original_phrase
        )
    
    @staticmethod
    def vague_phrase_with_suggestions_to_model(
        vague_phrase: VaguePhrase,
        suggestions: Optional[List[Suggestion]] = None
    ) -> VaguePhraseWithSuggestionsModel:
        """Convert library VaguePhrase with suggestions to API model."""
        base_model = ModelConverter.vague_phrase_to_model(vague_phrase)
        
        # Convert suggestions if provided
        suggestion_models = None
        if suggestions is not None:
            suggestion_models = [
                ModelConverter.suggestion_to_model(suggestion)
                for suggestion in suggestions
            ]
        
        return VaguePhraseWithSuggestionsModel(
            id=base_model.id,
            start_position=base_model.start_position,
            end_position=base_model.end_position,
            text=base_model.text,
            type=base_model.type,
            confidence=base_model.confidence,
            suggestions=suggestion_models
        )
    
    @staticmethod
    def suggestions_to_models(suggestions: List[Suggestion]) -> List[SuggestionModel]:
        """Convert a list of library Suggestions to API SuggestionModels."""
        return [
            ModelConverter.suggestion_to_model(suggestion)
            for suggestion in suggestions
        ]
    
    @staticmethod
    def vague_phrases_to_models(vague_phrases: List[VaguePhrase]) -> List[VaguePhraseModel]:
        """Convert a list of library VaguePhrases to API VaguePhraseModels."""
        return [
            ModelConverter.vague_phrase_to_model(vague_phrase)
            for vague_phrase in vague_phrases
        ]
    
    @staticmethod
    def vague_phrases_with_suggestions_to_models(
        vague_phrases: List[VaguePhrase],
        suggestions_dict: Optional[dict] = None
    ) -> List[VaguePhraseWithSuggestionsModel]:
        """
        Convert vague phrases with their associated suggestions to API models.
        
        Args:
            vague_phrases: List of VaguePhrase objects
            suggestions_dict: Dict mapping vague phrase IDs to their suggestions
        """
        result = []
        for vague_phrase in vague_phrases:
            # Get suggestions for this phrase if available
            phrase_suggestions = None
            if suggestions_dict and vague_phrase.id in suggestions_dict:
                phrase_suggestions = suggestions_dict[vague_phrase.id]
            
            model = ModelConverter.vague_phrase_with_suggestions_to_model(
                vague_phrase, phrase_suggestions
            )
            result.append(model)
        
        return result