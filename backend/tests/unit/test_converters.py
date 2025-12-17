"""
Tests for model converters.

These tests ensure that the ModelConverter correctly bridges between
library models and API models without data loss or corruption.
"""

import pytest
from uuid import uuid4

from src.libs.prompt_analyzer.analyzer import VaguePhrase, VagueType
from src.libs.suggestion_engine.engine import Suggestion, ImprovementType
from src.models.schemas import VagueTypeModel, ImprovementTypeModel
from src.models.converters import ModelConverter


class TestModelConverter:
    """Test ModelConverter methods."""
    
    def test_vague_type_conversion(self):
        """Test conversion between VagueType and VagueTypeModel."""
        # Test all enum values are mapped correctly
        mappings = [
            (VagueType.GENERIC_TERM, VagueTypeModel.GENERIC_TERM),
            (VagueType.SUBJECTIVE_QUALIFIER, VagueTypeModel.SUBJECTIVE_QUALIFIER),
            (VagueType.MISSING_CONTEXT, VagueTypeModel.MISSING_CONTEXT),
            (VagueType.IMPRECISE_QUANTITY, VagueTypeModel.IMPRECISE_QUANTITY),
            (VagueType.WEAK_INSTRUCTION, VagueTypeModel.WEAK_INSTRUCTION)
        ]
        
        for lib_type, api_type in mappings:
            converted = ModelConverter.vague_type_to_model(lib_type)
            assert converted == api_type
    
    def test_improvement_type_conversion(self):
        """Test conversion between ImprovementType and ImprovementTypeModel."""
        mappings = [
            (ImprovementType.SPECIFICITY, ImprovementTypeModel.SPECIFICITY),
            (ImprovementType.CLARITY, ImprovementTypeModel.CLARITY),
            (ImprovementType.CONTEXT, ImprovementTypeModel.CONTEXT),
            (ImprovementType.PRECISION, ImprovementTypeModel.PRECISION),
            (ImprovementType.STRENGTH, ImprovementTypeModel.STRENGTH)
        ]
        
        for lib_type, api_type in mappings:
            converted = ModelConverter.improvement_type_to_model(lib_type)
            assert converted == api_type
    
    def test_vague_phrase_conversion(self):
        """Test conversion from VaguePhrase to VaguePhraseModel."""
        phrase_id = uuid4()
        lib_phrase = VaguePhrase(
            id=phrase_id,
            start_position=5,
            end_position=14,
            original_text="something",
            vague_type=VagueType.GENERIC_TERM,
            confidence_score=0.9
        )
        
        api_phrase = ModelConverter.vague_phrase_to_model(lib_phrase)
        
        assert api_phrase.id == phrase_id
        assert api_phrase.start_position == 5
        assert api_phrase.end_position == 14
        assert api_phrase.text == "something"
        assert api_phrase.type == VagueTypeModel.GENERIC_TERM
        assert api_phrase.confidence == 0.9
    
    def test_suggestion_conversion(self):
        """Test conversion from Suggestion to SuggestionModel."""
        suggestion_id = uuid4()
        lib_suggestion = Suggestion(
            id=suggestion_id,
            improved_text="a specific example",
            rationale="Replace vague 'something' with concrete request",
            improvement_type=ImprovementType.SPECIFICITY,
            confidence_score=0.8,
            original_phrase="something"
        )
        
        api_suggestion = ModelConverter.suggestion_to_model(lib_suggestion)
        
        assert api_suggestion.id == suggestion_id
        assert api_suggestion.improved_text == "a specific example"
        assert api_suggestion.rationale == "Replace vague 'something' with concrete request"
        assert api_suggestion.type == ImprovementTypeModel.SPECIFICITY
        assert api_suggestion.confidence == 0.8
        assert api_suggestion.original_phrase == "something"
    
    def test_vague_phrase_with_suggestions_conversion(self):
        """Test conversion of vague phrase with associated suggestions."""
        phrase_id = uuid4()
        suggestion_id = uuid4()
        
        lib_phrase = VaguePhrase(
            id=phrase_id,
            start_position=5,
            end_position=14,
            original_text="something",
            vague_type=VagueType.GENERIC_TERM,
            confidence_score=0.9
        )
        
        lib_suggestion = Suggestion(
            id=suggestion_id,
            improved_text="a specific example",
            rationale="Replace vague 'something' with concrete request",
            improvement_type=ImprovementType.SPECIFICITY,
            confidence_score=0.8,
            original_phrase="something"
        )
        
        api_phrase = ModelConverter.vague_phrase_with_suggestions_to_model(
            lib_phrase, [lib_suggestion]
        )
        
        assert api_phrase.id == phrase_id
        assert api_phrase.text == "something"
        assert api_phrase.suggestions is not None
        assert len(api_phrase.suggestions) == 1
        assert api_phrase.suggestions[0].id == suggestion_id
        assert api_phrase.suggestions[0].improved_text == "a specific example"
    
    def test_vague_phrase_without_suggestions(self):
        """Test conversion of vague phrase without suggestions."""
        phrase_id = uuid4()
        
        lib_phrase = VaguePhrase(
            id=phrase_id,
            start_position=5,
            end_position=14,
            original_text="something",
            vague_type=VagueType.GENERIC_TERM,
            confidence_score=0.9
        )
        
        api_phrase = ModelConverter.vague_phrase_with_suggestions_to_model(lib_phrase)
        
        assert api_phrase.id == phrase_id
        assert api_phrase.suggestions is None
    
    def test_bulk_suggestions_conversion(self):
        """Test converting a list of suggestions."""
        suggestions = [
            Suggestion(
                id=uuid4(),
                improved_text="option 1",
                rationale="First option",
                improvement_type=ImprovementType.SPECIFICITY,
                confidence_score=0.8,
                original_phrase="something"
            ),
            Suggestion(
                id=uuid4(),
                improved_text="option 2",
                rationale="Second option",
                improvement_type=ImprovementType.CLARITY,
                confidence_score=0.7,
                original_phrase="something"
            )
        ]
        
        api_suggestions = ModelConverter.suggestions_to_models(suggestions)
        
        assert len(api_suggestions) == 2
        assert api_suggestions[0].improved_text == "option 1"
        assert api_suggestions[1].improved_text == "option 2"
        assert api_suggestions[0].type == ImprovementTypeModel.SPECIFICITY
        assert api_suggestions[1].type == ImprovementTypeModel.CLARITY
    
    def test_bulk_vague_phrases_conversion(self):
        """Test converting a list of vague phrases."""
        phrases = [
            VaguePhrase(
                id=uuid4(),
                start_position=5,
                end_position=14,
                original_text="something",
                vague_type=VagueType.GENERIC_TERM,
                confidence_score=0.9
            ),
            VaguePhrase(
                id=uuid4(),
                start_position=15,
                end_position=19,
                original_text="good",
                vague_type=VagueType.SUBJECTIVE_QUALIFIER,
                confidence_score=0.8
            )
        ]
        
        api_phrases = ModelConverter.vague_phrases_to_models(phrases)
        
        assert len(api_phrases) == 2
        assert api_phrases[0].text == "something"
        assert api_phrases[1].text == "good"
        assert api_phrases[0].type == VagueTypeModel.GENERIC_TERM
        assert api_phrases[1].type == VagueTypeModel.SUBJECTIVE_QUALIFIER
    
    def test_vague_phrases_with_suggestions_dict(self):
        """Test converting vague phrases with suggestions dictionary."""
        phrase1_id = uuid4()
        phrase2_id = uuid4()
        
        phrases = [
            VaguePhrase(
                id=phrase1_id,
                start_position=5,
                end_position=14,
                original_text="something",
                vague_type=VagueType.GENERIC_TERM,
                confidence_score=0.9
            ),
            VaguePhrase(
                id=phrase2_id,
                start_position=15,
                end_position=19,
                original_text="good",
                vague_type=VagueType.SUBJECTIVE_QUALIFIER,
                confidence_score=0.8
            )
        ]
        
        suggestions_dict = {
            phrase1_id: [
                Suggestion(
                    id=uuid4(),
                    improved_text="a specific example",
                    rationale="Be more specific",
                    improvement_type=ImprovementType.SPECIFICITY,
                    confidence_score=0.8,
                    original_phrase="something"
                )
            ]
            # phrase2_id has no suggestions
        }
        
        api_phrases = ModelConverter.vague_phrases_with_suggestions_to_models(
            phrases, suggestions_dict
        )
        
        assert len(api_phrases) == 2
        
        # First phrase should have suggestions
        assert api_phrases[0].suggestions is not None
        assert len(api_phrases[0].suggestions) == 1
        assert api_phrases[0].suggestions[0].improved_text == "a specific example"
        
        # Second phrase should have no suggestions
        assert api_phrases[1].suggestions is None