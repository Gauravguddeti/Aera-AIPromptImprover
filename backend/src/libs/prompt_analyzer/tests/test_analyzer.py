"""
Tests for the PromptAnalyzer core functionality.

Following TDD principles with comprehensive test coverage.
"""

import pytest
from unittest.mock import patch, MagicMock

from ..analyzer import (
    PromptAnalyzer, 
    VaguePhrase, 
    AnalysisResult, 
    VagueType, 
    ImprovementType, 
    Suggestion
)


class TestVaguePhrase:
    """Test VaguePhrase data class functionality."""
    
    def test_create_vague_phrase(self):
        """Test creating a VaguePhrase with proper defaults."""
        phrase = VaguePhrase.create(
            start=0, 
            end=9, 
            text="something", 
            vague_type=VagueType.GENERIC_TERM
        )
        
        assert phrase.start_position == 0
        assert phrase.end_position == 9
        assert phrase.original_text == "something"
        assert phrase.vague_type == VagueType.GENERIC_TERM
        assert phrase.confidence_score == 1.0
        assert phrase.id is not None
    
    def test_vague_phrase_to_dict(self):
        """Test VaguePhrase serialization."""
        phrase = VaguePhrase.create(
            start=5, 
            end=12, 
            text="something", 
            vague_type=VagueType.GENERIC_TERM,
            confidence=0.9
        )
        
        result = phrase.to_dict()
        
        assert result["start"] == 5
        assert result["end"] == 12
        assert result["text"] == "something"
        assert result["type"] == "generic_term"
        assert result["confidence"] == 0.9
        assert "id" in result


class TestSuggestion:
    """Test Suggestion data class functionality."""
    
    def test_create_suggestion(self):
        """Test creating a Suggestion with proper defaults."""
        suggestion = Suggestion.create(
            improved_text="a specific task",
            rationale="More specific than 'something'",
            improvement_type=ImprovementType.SPECIFICITY
        )
        
        assert suggestion.improved_text == "a specific task"
        assert suggestion.rationale == "More specific than 'something'"
        assert suggestion.improvement_type == ImprovementType.SPECIFICITY
        assert suggestion.confidence_score == 1.0
        assert suggestion.id is not None
    
    def test_suggestion_to_dict(self):
        """Test Suggestion serialization."""
        suggestion = Suggestion.create(
            improved_text="clear instructions",
            rationale="Replace vague request",
            improvement_type=ImprovementType.CLARITY,
            confidence=0.8
        )
        
        result = suggestion.to_dict()
        
        assert result["improved_text"] == "clear instructions"
        assert result["rationale"] == "Replace vague request"
        assert result["type"] == "clarity"
        assert result["confidence"] == 0.8
        assert "id" in result


class TestAnalysisResult:
    """Test AnalysisResult data class functionality."""
    
    def test_analysis_result_to_dict(self):
        """Test AnalysisResult serialization."""
        phrase = VaguePhrase.create(0, 9, "something", VagueType.GENERIC_TERM)
        result = AnalysisResult(
            original_text="something good",
            vague_phrases=[phrase],
            analysis_time_ms=150.5
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["original_text"] == "something good"
        assert len(result_dict["vague_phrases"]) == 1
        assert result_dict["analysis_time_ms"] == 150.5
        assert result_dict["error"] is None
        assert result_dict["fallback_mode"] is False


class TestPromptAnalyzer:
    """Test PromptAnalyzer core functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = PromptAnalyzer()
    
    def test_analyzer_initialization(self):
        """Test that analyzer initializes properly."""
        assert self.analyzer is not None
        assert hasattr(self.analyzer, '_compiled_patterns')
        assert len(self.analyzer._compiled_patterns) > 0
    
    def test_detect_generic_terms(self):
        """Test detection of generic terms."""
        text = "Write something about stuff and things"
        result = self.analyzer.analyze(text)
        
        assert len(result.vague_phrases) >= 3
        
        # Check for "something"
        something_found = any(p.original_text == "something" for p in result.vague_phrases)
        assert something_found
        
        # Check for "stuff"
        stuff_found = any(p.original_text == "stuff" for p in result.vague_phrases)
        assert stuff_found
        
        # Check for "things"
        things_found = any(p.original_text == "things" for p in result.vague_phrases)
        assert things_found
    
    def test_detect_subjective_qualifiers(self):
        """Test detection of subjective qualifiers."""
        text = "Make it good and better than the bad version"
        result = self.analyzer.analyze(text)
        
        # Should detect "good", "better", "bad"
        assert len(result.vague_phrases) >= 3
        
        detected_words = [p.original_text for p in result.vague_phrases]
        assert "good" in detected_words
        assert "better" in detected_words
        assert "bad" in detected_words
    
    def test_detect_weak_instructions(self):
        """Test detection of weak instructions."""
        text = "Try to maybe write something kind of interesting"
        result = self.analyzer.analyze(text)
        
        # Should detect "try to", "maybe", "something", "kind of"
        assert len(result.vague_phrases) >= 4
        
        detected_phrases = [p.original_text.lower() for p in result.vague_phrases]
        assert "try to" in detected_phrases
        assert "maybe" in detected_phrases
        assert "something" in detected_phrases
        assert "kind of" in detected_phrases
    
    def test_detect_imprecise_quantities(self):
        """Test detection of imprecise quantities."""
        text = "Generate some examples with many details and few errors"
        result = self.analyzer.analyze(text)
        
        # Should detect "some", "many", "few"
        assert len(result.vague_phrases) >= 3
        
        detected_words = [p.original_text for p in result.vague_phrases]
        assert "some" in detected_words
        assert "many" in detected_words
        assert "few" in detected_words
    
    def test_confidence_scoring(self):
        """Test that confidence scores are assigned properly."""
        text = "Write something good"
        result = self.analyzer.analyze(text)
        
        assert len(result.vague_phrases) >= 2
        
        for phrase in result.vague_phrases:
            assert 0.0 <= phrase.confidence_score <= 1.0
    
    def test_position_tracking(self):
        """Test that phrase positions are tracked correctly."""
        text = "Write something good here"
        result = self.analyzer.analyze(text)
        
        # Find "something" phrase
        something_phrase = next(
            (p for p in result.vague_phrases if p.original_text == "something"), 
            None
        )
        assert something_phrase is not None
        assert text[something_phrase.start_position:something_phrase.end_position] == "something"
    
    def test_overlapping_phrase_removal(self):
        """Test that overlapping phrases are handled correctly."""
        # This is a edge case test - in practice overlaps should be rare
        text = "Write good stuff"
        result = self.analyzer.analyze(text)
        
        # Ensure no overlapping phrases
        phrases = sorted(result.vague_phrases, key=lambda p: p.start_position)
        for i in range(len(phrases) - 1):
            assert phrases[i].end_position <= phrases[i + 1].start_position
    
    def test_empty_text(self):
        """Test analysis of empty text."""
        result = self.analyzer.analyze("")
        
        assert result.original_text == ""
        assert len(result.vague_phrases) == 0
        assert result.error is None
        assert result.analysis_time_ms >= 0
    
    def test_clean_text_no_vague_phrases(self):
        """Test analysis of text with no vague phrases."""
        text = "Create a Python function that calculates the factorial of a number"
        result = self.analyzer.analyze(text)
        
        assert result.original_text == text
        assert len(result.vague_phrases) == 0
        assert result.error is None
        assert result.analysis_time_ms >= 0
    
    def test_case_insensitive_detection(self):
        """Test that detection works regardless of case."""
        text = "Write SOMETHING Good and Stuff"
        result = self.analyzer.analyze(text)
        
        detected_words = [p.original_text.lower() for p in result.vague_phrases]
        assert "something" in detected_words
        assert "good" in detected_words
        assert "stuff" in detected_words
    
    def test_analysis_timing(self):
        """Test that analysis timing is recorded."""
        text = "Write something good about AI"
        result = self.analyzer.analyze(text)
        
        assert result.analysis_time_ms > 0
        assert result.analysis_time_ms < 1000  # Should be very fast for simple text
    
    @patch('time.perf_counter', side_effect=Exception("Timer error"))
    def test_error_handling(self, mock_time):
        """Test error handling during analysis."""
        text = "Write something good"
        result = self.analyzer.analyze(text)
        
        assert result.error is not None
        assert result.fallback_mode is True
        assert len(result.vague_phrases) == 0

    def test_nlp_detection_for_missing_context_pronoun(self):
        """NLP detector should identify vague context pronouns in short prompts."""
        text = "Improve it"
        result = self.analyzer.analyze(text)

        assert any(
            p.original_text.lower() == "it" and p.vague_type == VagueType.MISSING_CONTEXT
            for p in result.vague_phrases
        )

    def test_nlp_fallback_without_model(self):
        """Analyzer should still work when NLP model is unavailable."""
        self.analyzer._nlp_available = False
        self.analyzer._nlp = None

        result = self.analyzer.analyze("Write something good")

        assert result.error is None
        assert any(p.original_text.lower() == "something" for p in result.vague_phrases)


class TestVagueTypeCoverage:
    """Test that all vague types are covered by patterns."""
    
    def test_all_vague_types_have_patterns(self):
        """Ensure all VagueType enum values have corresponding patterns."""
        analyzer = PromptAnalyzer()
        
        for vague_type in VagueType:
            assert vague_type in analyzer.VAGUE_PATTERNS
            assert len(analyzer.VAGUE_PATTERNS[vague_type]) > 0
    
    def test_pattern_compilation(self):
        """Test that all patterns compile successfully."""
        analyzer = PromptAnalyzer()
        
        # If initialization completes without error, patterns compiled successfully
        assert analyzer._compiled_patterns is not None
        
        for vague_type, patterns in analyzer._compiled_patterns.items():
            assert len(patterns) > 0
            for pattern in patterns:
                assert hasattr(pattern, 'search')  # Compiled regex object


class TestIntegrationScenarios:
    """Integration tests with realistic prompting scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = PromptAnalyzer()
    
    def test_typical_vague_prompt(self):
        """Test analysis of a typically vague prompt."""
        text = "Write something good about AI that is interesting and helpful"
        result = self.analyzer.analyze(text)
        
        # Should detect multiple vague phrases
        assert len(result.vague_phrases) >= 3
        
        detected_text = [p.original_text for p in result.vague_phrases]
        assert "something" in detected_text
        assert "good" in detected_text
        assert "interesting" in detected_text
    
    def test_improved_specific_prompt(self):
        """Test analysis of an improved, specific prompt."""
        text = "Create a Python function named 'calculate_fibonacci' that takes an integer n and returns the nth Fibonacci number using iterative approach"
        result = self.analyzer.analyze(text)
        
        # Should detect very few or no vague phrases
        assert len(result.vague_phrases) <= 1
    
    def test_mixed_quality_prompt(self):
        """Test analysis of a prompt with both specific and vague elements."""
        text = "Create a REST API endpoint for user authentication with good security practices and proper error handling"
        result = self.analyzer.analyze(text)
        
        # Should detect "good" but not much else
        vague_texts = [p.original_text for p in result.vague_phrases]
        assert "good" in vague_texts
        # Most other elements should be specific enough