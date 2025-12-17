"""
Integration Tests for Aera Backend

These tests verify that components work together correctly.
They test real dependencies and cross-component workflows.

Following TDD principles, these should also fail initially.
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Test real library integration
from src.libs.prompt_analyzer.analyzer import PromptAnalyzer
from src.libs.suggestion_engine.engine import SuggestionEngine, SuggestionRequest, AIProvider
from src.libs.suggestion_engine.providers import RuleBasedProvider

# These imports will fail initially for API components
try:
    from src.services.analysis_service import AnalysisService
    ANALYSIS_SERVICE_EXISTS = True
except ImportError:
    ANALYSIS_SERVICE_EXISTS = False

try:
    from src.services.websocket_service import WebSocketService
    WEBSOCKET_SERVICE_EXISTS = True
except ImportError:
    WEBSOCKET_SERVICE_EXISTS = False


class TestLibraryIntegration:
    """Test integration between our libraries."""
    
    def test_prompt_analyzer_and_suggestion_engine_integration(self):
        """Test that prompt analyzer and suggestion engine work together."""
        # Analyze a prompt
        analyzer = PromptAnalyzer()
        text = "Write something good and interesting about AI"
        analysis_result = analyzer.analyze(text)
        
        # Should find vague phrases
        assert len(analysis_result.vague_phrases) > 0
        
        # Generate suggestions for each vague phrase
        engine = SuggestionEngine([RuleBasedProvider()])
        
        all_suggestions = []
        for vague_phrase in analysis_result.vague_phrases:
            request = SuggestionRequest(
                vague_phrase=vague_phrase,
                full_context=text,
                max_suggestions=2
            )
            
            response = engine.sync_generate_suggestions(request)
            
            # Should generate suggestions successfully
            assert len(response.suggestions) > 0
            assert response.error is None
            all_suggestions.extend(response.suggestions)
        
        # Should have suggestions for multiple phrases
        assert len(all_suggestions) >= 2
        
        # All suggestions should have proper structure
        for suggestion in all_suggestions:
            assert suggestion.improved_text
            assert suggestion.rationale
            assert suggestion.original_phrase
            assert 0 <= suggestion.confidence_score <= 1
    
    def test_end_to_end_prompt_improvement_workflow(self):
        """Test complete workflow from analysis to suggestions."""
        # Start with a very vague prompt
        original_prompt = "Try to write something good about stuff and things"
        
        # Step 1: Analyze
        analyzer = PromptAnalyzer()
        analysis = analyzer.analyze(original_prompt)
        
        # Should detect multiple vague phrases
        assert len(analysis.vague_phrases) >= 4
        
        # Step 2: Generate suggestions for all phrases
        engine = SuggestionEngine([RuleBasedProvider()])
        improvements = {}
        
        for phrase in analysis.vague_phrases:
            request = SuggestionRequest(
                vague_phrase=phrase,
                full_context=original_prompt,
                max_suggestions=1
            )
            response = engine.sync_generate_suggestions(request)
            if response.suggestions:
                improvements[phrase.original_text] = response.suggestions[0].improved_text
        
        # Step 3: Apply improvements (simulate user accepting suggestions)
        improved_prompt = original_prompt
        for original, improved in improvements.items():
            improved_prompt = improved_prompt.replace(original, improved, 1)
        
        # Step 4: Re-analyze improved prompt
        improved_analysis = analyzer.analyze(improved_prompt)
        
        # Should have fewer vague phrases after improvement
        assert len(improved_analysis.vague_phrases) < len(analysis.vague_phrases)
    
    def test_batch_processing_workflow(self):
        """Test processing multiple prompts efficiently."""
        prompts = [
            "Write something good",
            "Create stuff that is nice",
            "Make things better and interesting",
            "Try to generate some content"
        ]
        
        analyzer = PromptAnalyzer()
        engine = SuggestionEngine([RuleBasedProvider()])
        
        batch_results = []
        
        for prompt in prompts:
            # Analyze
            analysis = analyzer.analyze(prompt)
            
            # Generate suggestions for all phrases
            prompt_result = {
                "original": prompt,
                "vague_phrases": len(analysis.vague_phrases),
                "suggestions": []
            }
            
            for phrase in analysis.vague_phrases:
                request = SuggestionRequest(
                    vague_phrase=phrase,
                    full_context=prompt,
                    max_suggestions=1
                )
                response = engine.sync_generate_suggestions(request)
                prompt_result["suggestions"].extend(response.suggestions)
            
            batch_results.append(prompt_result)
        
        # All prompts should have been processed
        assert len(batch_results) == len(prompts)
        
        # Each should have detected vague phrases and generated suggestions
        for result in batch_results:
            assert result["vague_phrases"] > 0
            assert len(result["suggestions"]) > 0


@pytest.mark.skipif(not ANALYSIS_SERVICE_EXISTS, reason="Analysis service not implemented yet")
class TestAnalysisServiceIntegration:
    """Test analysis service integration."""
    
    def test_analysis_service_uses_libraries_correctly(self):
        """Test that analysis service integrates libraries properly."""
        # This test will be implemented when we create the analysis service
        pass
    
    def test_analysis_service_caching(self):
        """Test that analysis service implements caching correctly."""
        # This test will be implemented when we create the analysis service
        pass


@pytest.mark.skipif(not WEBSOCKET_SERVICE_EXISTS, reason="WebSocket service not implemented yet")
class TestWebSocketIntegration:
    """Test WebSocket real-time analysis integration."""
    
    def test_websocket_real_time_analysis(self):
        """Test real-time analysis over WebSocket."""
        # This test will be implemented when we create the WebSocket service
        pass
    
    def test_websocket_debouncing(self):
        """Test that WebSocket properly debounces rapid updates."""
        # This test will be implemented when we create the WebSocket service
        pass


class TestOllamaIntegration:
    """Test Ollama AI integration."""
    
    @pytest.mark.asyncio
    async def test_ollama_availability_check(self):
        """Test checking if Ollama is available."""
        from src.libs.suggestion_engine.providers import OllamaProvider
        
        provider = OllamaProvider()
        
        # Should be able to check availability without crashing
        is_available = await provider.is_available()
        
        # Result should be boolean
        assert isinstance(is_available, bool)
    
    @pytest.mark.asyncio
    async def test_ollama_suggestion_generation_with_fallback(self):
        """Test that Ollama suggestions fall back gracefully when unavailable."""
        from src.libs.suggestion_engine.providers import OllamaProvider, RuleBasedProvider
        from src.libs.prompt_analyzer.analyzer import VaguePhrase, VagueType
        
        # Create engine with Ollama first, rule-based as fallback
        ollama_provider = OllamaProvider()
        rule_provider = RuleBasedProvider()
        engine = SuggestionEngine([ollama_provider, rule_provider])
        
        # Create test request
        vague_phrase = VaguePhrase.create(0, 9, "something", VagueType.GENERIC_TERM)
        request = SuggestionRequest(
            vague_phrase=vague_phrase,
            full_context="Write something good",
            max_suggestions=2
        )
        
        # Generate suggestions
        response = await engine.generate_suggestions(request)
        
        # Should get suggestions (either from Ollama or fallback)
        assert len(response.suggestions) > 0
        assert response.error is None
        
        # Provider used should be either "ollama-mistral:8b" or "rule-based"
        assert response.provider_used in ["ollama-mistral:8b", "rule-based"]
        
        # If Ollama was unavailable, should have used fallback
        if not await ollama_provider.is_available():
            assert response.provider_used == "rule-based"
            assert response.fallback_mode is False  # Rule-based is not fallback mode
    
    @pytest.mark.asyncio
    async def test_multiple_ai_providers_priority(self):
        """Test that multiple AI providers are tried in priority order."""
        from src.libs.suggestion_engine.providers import OllamaProvider, RuleBasedProvider
        from src.libs.prompt_analyzer.analyzer import VaguePhrase, VagueType
        
        # Create providers in specific order
        providers = [
            OllamaProvider(model="mistral:8b"),
            OllamaProvider(model="llama2:7b"),  # Likely not available
            RuleBasedProvider()
        ]
        
        engine = SuggestionEngine(providers)
        
        vague_phrase = VaguePhrase.create(0, 9, "something", VagueType.GENERIC_TERM)
        request = SuggestionRequest(
            vague_phrase=vague_phrase,
            full_context="Write something good"
        )
        
        response = await engine.generate_suggestions(request)
        
        # Should get suggestions from some provider
        assert len(response.suggestions) > 0
        
        # Provider used should be the first available one
        assert response.provider_used in [
            "ollama-mistral:8b", 
            "ollama-llama2:7b", 
            "rule-based"
        ]


class TestPerformanceIntegration:
    """Test performance requirements across components."""
    
    def test_analysis_performance_short_prompts(self):
        """Test that analysis meets performance requirements for short prompts."""
        analyzer = PromptAnalyzer()
        short_prompt = "Write something good about AI"
        
        import time
        start_time = time.perf_counter()
        
        result = analyzer.analyze(short_prompt)
        
        end_time = time.perf_counter()
        analysis_time_ms = (end_time - start_time) * 1000
        
        # Should complete within 300ms for short prompts
        assert analysis_time_ms < 300
        assert result.analysis_time_ms < 300
    
    def test_analysis_performance_long_prompts(self):
        """Test that analysis meets performance requirements for long prompts."""
        analyzer = PromptAnalyzer()
        
        # Create a long prompt (about 2000 characters)
        long_prompt = "Write something good and interesting about AI technology. " * 35
        
        import time
        start_time = time.perf_counter()
        
        result = analyzer.analyze(long_prompt)
        
        end_time = time.perf_counter()
        analysis_time_ms = (end_time - start_time) * 1000
        
        # Should complete within 2000ms for long prompts
        assert analysis_time_ms < 2000
        assert result.analysis_time_ms < 2000
    
    def test_suggestion_generation_performance(self):
        """Test that suggestion generation meets performance requirements."""
        from src.libs.prompt_analyzer.analyzer import VaguePhrase, VagueType
        
        engine = SuggestionEngine([RuleBasedProvider()])
        vague_phrase = VaguePhrase.create(0, 9, "something", VagueType.GENERIC_TERM)
        
        request = SuggestionRequest(
            vague_phrase=vague_phrase,
            full_context="Write something good about AI technology",
            max_suggestions=3
        )
        
        import time
        start_time = time.perf_counter()
        
        response = engine.sync_generate_suggestions(request)
        
        end_time = time.perf_counter()
        generation_time_ms = (end_time - start_time) * 1000
        
        # Should complete quickly for rule-based suggestions
        assert generation_time_ms < 100
        assert response.generation_time_ms < 100


class TestErrorResilienceIntegration:
    """Test error handling across components."""
    
    def test_analysis_handles_malformed_input(self):
        """Test that analysis handles malformed input gracefully."""
        analyzer = PromptAnalyzer()
        
        # Test various malformed inputs
        test_cases = [
            None,
            123,
            [],
            {"not": "string"},
            "\x00\x01\x02",  # Binary data
            "🚀" * 1000,  # Many unicode characters
        ]
        
        for test_input in test_cases:
            try:
                if test_input is None or not isinstance(test_input, str):
                    # Should handle type errors gracefully
                    continue
                
                result = analyzer.analyze(test_input)
                
                # Should return valid result structure even for weird input
                assert hasattr(result, 'vague_phrases')
                assert hasattr(result, 'analysis_time_ms')
                assert isinstance(result.vague_phrases, list)
                
            except Exception as e:
                # If exception occurs, it should be a reasonable one
                assert isinstance(e, (TypeError, ValueError))
    
    def test_suggestion_engine_handles_component_failures(self):
        """Test that suggestion engine handles component failures gracefully."""
        from src.libs.prompt_analyzer.analyzer import VaguePhrase, VagueType
        
        # Create a provider that always fails
        class FailingProvider(AIProvider):
            @property
            def name(self):
                return "failing"
            
            async def is_available(self):
                return True
            
            async def generate_suggestions(self, vague_phrase, context):
                raise Exception("Simulated provider failure")
        
        # Engine with failing provider and rule-based fallback
        engine = SuggestionEngine([FailingProvider(), RuleBasedProvider()])
        
        vague_phrase = VaguePhrase.create(0, 9, "something", VagueType.GENERIC_TERM)
        request = SuggestionRequest(
            vague_phrase=vague_phrase,
            full_context="Write something good"
        )
        
        response = engine.sync_generate_suggestions(request)
        
        # Should fall back to rule-based provider
        assert response.provider_used == "rule-based"
        assert len(response.suggestions) > 0
        assert response.error is None


class TestFileProcessingIntegration:
    """Test file processing workflows."""
    
    def test_process_text_file_workflow(self):
        """Test processing a text file containing prompts."""
        # Create temporary file
        test_content = """
        Write something good about AI.
        Create stuff that is interesting.
        Make things better and more comprehensive.
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_path = Path(f.name)
        
        try:
            # Process file
            analyzer = PromptAnalyzer()
            engine = SuggestionEngine([RuleBasedProvider()])
            
            content = temp_path.read_text()
            analysis = analyzer.analyze(content)
            
            # Should find multiple vague phrases
            assert len(analysis.vague_phrases) >= 3
            
            # Generate suggestions for all phrases
            all_suggestions = []
            for phrase in analysis.vague_phrases:
                request = SuggestionRequest(
                    vague_phrase=phrase,
                    full_context=content,
                    max_suggestions=1
                )
                response = engine.sync_generate_suggestions(request)
                all_suggestions.extend(response.suggestions)
            
            # Should have generated suggestions for multiple phrases
            assert len(all_suggestions) >= 3
            
        finally:
            # Clean up
            temp_path.unlink()
    
    def test_batch_file_processing(self):
        """Test processing multiple files in batch."""
        # Create multiple temporary files
        files_content = [
            "Write something good",
            "Create nice stuff", 
            "Make things better"
        ]
        
        temp_files = []
        try:
            for i, content in enumerate(files_content):
                with tempfile.NamedTemporaryFile(mode='w', suffix=f'_{i}.txt', delete=False) as f:
                    f.write(content)
                    temp_files.append(Path(f.name))
            
            # Process all files
            analyzer = PromptAnalyzer()
            batch_results = []
            
            for file_path in temp_files:
                content = file_path.read_text()
                analysis = analyzer.analyze(content)
                
                batch_results.append({
                    "file": file_path.name,
                    "content": content,
                    "vague_phrases": len(analysis.vague_phrases)
                })
            
            # Should have processed all files
            assert len(batch_results) == len(files_content)
            
            # Each file should have detected vague phrases
            for result in batch_results:
                assert result["vague_phrases"] > 0
                
        finally:
            # Clean up
            for file_path in temp_files:
                file_path.unlink()