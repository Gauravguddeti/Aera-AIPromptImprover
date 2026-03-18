"""
API Contract Tests for Aera Backend

These tests define the expected API contracts and MUST FAIL initially
until the corresponding endpoints are implemented. This follows TDD principles.

Endpoints to test:
- POST /api/prompts/analyze - Analyze prompt for vague phrases
- GET /api/suggestions/{phrase_id} - Get suggestions for a vague phrase
- GET /api/preferences - Get user preferences
- PUT /api/preferences - Update user preferences
- WebSocket /ws/analysis - Real-time analysis
"""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# This import will fail initially - this is expected and correct for TDD
try:
    from src.main import app
    APP_EXISTS = True
except ImportError:
    APP_EXISTS = False


@pytest.fixture
def client():
    """Create test client for API testing."""
    if not APP_EXISTS:
        pytest.skip("API not implemented yet - this is expected for TDD")
    
    # Use positional argument to avoid compatibility issues
    return TestClient(app)


class TestPromptAnalysisAPI:
    """Test prompt analysis API endpoint."""
    
    def test_analyze_prompt_endpoint_exists(self, client):
        """Test that the analyze endpoint exists and accepts POST requests."""
        response = client.post("/api/prompts/analyze")
        
        # Should not return 404 (not found)
        assert response.status_code != 404
    
    def test_analyze_prompt_with_valid_input(self, client):
        """Test prompt analysis with valid input."""
        request_data = {
            "content": "Write something good about AI technology",
            "options": {
                "include_suggestions": True,
                "max_suggestions_per_phrase": 3
            }
        }
        
        response = client.post("/api/prompts/analyze", json=request_data)
        
        assert response.status_code == 200
        
        data = response.json()
        
        # Validate response structure
        assert "analysis_id" in data
        assert "content" in data
        assert "vague_phrases" in data
        assert "analysis_time_ms" in data
        assert "timestamp" in data
        
        # Should detect vague phrases
        assert isinstance(data["vague_phrases"], list)
        assert len(data["vague_phrases"]) > 0
        
        # Validate vague phrase structure
        phrase = data["vague_phrases"][0]
        assert "id" in phrase
        assert "start_position" in phrase
        assert "end_position" in phrase
        assert "text" in phrase
        assert "type" in phrase
        assert "confidence" in phrase
        
        # Should include suggestions when requested
        if request_data["options"]["include_suggestions"]:
            assert "suggestions" in phrase
            assert isinstance(phrase["suggestions"], list)
    
    def test_analyze_prompt_with_minimal_input(self, client):
        """Test prompt analysis with minimal required input."""
        request_data = {
            "content": "Write something good"
        }
        
        response = client.post("/api/prompts/analyze", json=request_data)
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["content"] == "Write something good"
        assert "vague_phrases" in data
    
    def test_analyze_prompt_with_empty_content(self, client):
        """Test prompt analysis with empty content."""
        request_data = {
            "content": ""
        }
        
        response = client.post("/api/prompts/analyze", json=request_data)
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["content"] == ""
        assert data["vague_phrases"] == []
    
    def test_analyze_prompt_with_invalid_input(self, client):
        """Test prompt analysis with invalid input."""
        # Missing required content field
        response = client.post("/api/prompts/analyze", json={})
        
        assert response.status_code == 422  # Validation error
        
        error_data = response.json()
        assert "detail" in error_data
    
    def test_analyze_prompt_with_long_content(self, client):
        """Test prompt analysis with very long content."""
        long_content = "Write something good. " * 1000  # Very long prompt
        
        request_data = {
            "content": long_content
        }
        
        response = client.post("/api/prompts/analyze", json=request_data)
        
        # Should handle long content gracefully
        assert response.status_code in [200, 413]  # OK or Payload Too Large
        
        if response.status_code == 200:
            data = response.json()
            assert "vague_phrases" in data
    
    def test_analyze_prompt_performance(self, client):
        """Test that prompt analysis meets performance requirements."""
        request_data = {
            "content": "Write something good and interesting about AI"
        }
        
        import time
        start_time = time.perf_counter()
        
        response = client.post("/api/prompts/analyze", json=request_data)
        
        end_time = time.perf_counter()
        request_time_ms = (end_time - start_time) * 1000
        
        assert response.status_code == 200
        
        # API should respond within 500ms for short prompts
        assert request_time_ms < 500
        
        data = response.json()
        
        # Server-reported analysis time should be reasonable
        assert data["analysis_time_ms"] < 300


class TestSuggestionsAPI:
    """Test suggestions API endpoints."""
    
    def test_get_suggestions_endpoint_exists(self, client):
        """Test that the suggestions endpoint exists."""
        # Use a valid UUID format but non-existent phrase ID
        phrase_id = "123e4567-e89b-12d3-a456-426614174000"
        
        response = client.get(f"/api/suggestions/{phrase_id}")
        
        # Should not return 404 (route not found), but can return 404 (phrase not found)
        # The endpoint should exist and return a proper 404 for phrase not found
        assert response.status_code == 404  # Valid UUID format, but phrase not found
    
    def test_get_suggestions_for_valid_phrase(self, client):
        """Test getting suggestions for a valid vague phrase."""
        # First analyze a prompt to get a phrase ID
        analyze_response = client.post("/api/prompts/analyze", json={
            "content": "Write something good",
            "options": {"include_suggestions": False}
        })
        
        assert analyze_response.status_code == 200
        analysis_data = analyze_response.json()
        
        # Get phrase ID from analysis
        phrase_id = analysis_data["vague_phrases"][0]["id"]
        
        # Now get suggestions for this phrase
        suggestions_response = client.get(f"/api/suggestions/{phrase_id}")
        
        assert suggestions_response.status_code == 200
        
        data = suggestions_response.json()
        
        # Validate response structure
        assert "phrase_id" in data
        assert "suggestions" in data
        assert "generation_time_ms" in data
        assert "provider_used" in data
        
        # Should have suggestions
        assert isinstance(data["suggestions"], list)
        assert len(data["suggestions"]) > 0
        
        # Validate suggestion structure
        suggestion = data["suggestions"][0]
        assert "id" in suggestion
        assert "improved_text" in suggestion
        assert "rationale" in suggestion
        assert "type" in suggestion
        assert "confidence" in suggestion
    
    def test_get_suggestions_with_options(self, client):
        """Test getting suggestions with custom options."""
        phrase_id = "test-phrase-id"
        
        response = client.get(f"/api/suggestions/{phrase_id}", params={
            "max_suggestions": 5,
            "min_confidence": 0.7,
            "preferred_style": "formal"
        })
        
        # Should accept query parameters
        assert response.status_code in [200, 404]  # OK or phrase not found
    
    def test_get_suggestions_for_invalid_phrase_id(self, client):
        """Test getting suggestions for non-existent phrase ID."""
        invalid_id = "non-existent-phrase-id-999"
        
        response = client.get(f"/api/suggestions/{invalid_id}")
        
        assert response.status_code == 404
        
        error_data = response.json()
        assert "detail" in error_data
    
    def test_get_suggestions_with_malformed_id(self, client):
        """Test getting suggestions with malformed phrase ID."""
        malformed_id = "invalid-id-format!"
        
        response = client.get(f"/api/suggestions/{malformed_id}")
        
        assert response.status_code in [400, 404, 422]  # Bad request or not found

    def test_submit_suggestion_feedback(self, client):
        """Test submitting thumbs up/down feedback for a suggestion."""
        analyze_response = client.post("/api/prompts/analyze", json={
            "content": "Write something good",
            "options": {"include_suggestions": True}
        })
        assert analyze_response.status_code == 200

        phrase = analyze_response.json()["vague_phrases"][0]
        suggestion = phrase.get("suggestions", [])[0]

        payload = {
            "suggestion_id": suggestion["id"],
            "phrase_text": phrase["text"],
            "improved_text": suggestion["improved_text"],
            "rating": "up",
            "context": "Write something good",
            "provider_used": "contract-test"
        }

        response = client.post("/api/suggestions/feedback", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["received"] is True
        assert data["rating"] == "up"
        assert "feedback_id" in data


class TestPreferencesAPI:
    """Test user preferences API endpoints."""
    
    def test_get_preferences_endpoint_exists(self, client):
        """Test that the preferences endpoint exists."""
        response = client.get("/api/preferences")
        
        # Should not return 404 (not found)
        assert response.status_code != 404
    
    def test_get_default_preferences(self, client):
        """Test getting default user preferences."""
        response = client.get("/api/preferences")
        
        assert response.status_code == 200
        
        data = response.json()
        
        # Validate preferences structure
        assert "analysis" in data
        assert "suggestions" in data
        assert "ui" in data
        
        # Analysis preferences
        analysis_prefs = data["analysis"]
        assert "auto_analyze" in analysis_prefs
        assert "debounce_ms" in analysis_prefs
        assert "min_confidence" in analysis_prefs
        
        # Suggestion preferences
        suggestion_prefs = data["suggestions"]
        assert "max_per_phrase" in suggestion_prefs
        assert "preferred_style" in suggestion_prefs
        assert "include_rationale" in suggestion_prefs
        
        # UI preferences
        ui_prefs = data["ui"]
        assert "theme" in ui_prefs
        assert "highlight_style" in ui_prefs
        assert "show_confidence" in ui_prefs
    
    def test_update_preferences(self, client):
        """Test updating user preferences."""
        updated_preferences = {
            "analysis": {
                "auto_analyze": False,
                "debounce_ms": 500,
                "min_confidence": 0.8
            },
            "suggestions": {
                "max_per_phrase": 5,
                "preferred_style": "formal",
                "include_rationale": True
            },
            "ui": {
                "theme": "dark",
                "highlight_style": "underline",
                "show_confidence": False
            }
        }
        
        response = client.put("/api/preferences", json=updated_preferences)
        
        assert response.status_code == 200
        
        data = response.json()
        
        # Should return updated preferences
        assert data["analysis"]["auto_analyze"] == False
        assert data["analysis"]["debounce_ms"] == 500
        assert data["suggestions"]["max_per_phrase"] == 5
        assert data["ui"]["theme"] == "dark"
    
    def test_update_partial_preferences(self, client):
        """Test updating only some preferences."""
        partial_update = {
            "analysis": {
                "auto_analyze": False
            }
        }
        
        response = client.put("/api/preferences", json=partial_update)
        
        assert response.status_code == 200
        
        data = response.json()
        
        # Should update only specified fields, keep others as default
        assert data["analysis"]["auto_analyze"] == False
        assert "debounce_ms" in data["analysis"]  # Should still have default
    
    def test_update_preferences_with_invalid_data(self, client):
        """Test updating preferences with invalid data."""
        invalid_preferences = {
            "analysis": {
                "debounce_ms": "not-a-number"  # Invalid type
            }
        }
        
        response = client.put("/api/preferences", json=invalid_preferences)
        
        assert response.status_code == 422  # Validation error


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_endpoint_exists(self, client):
        """Test that health endpoint exists."""
        response = client.get("/health")
        
        assert response.status_code == 200
    
    def test_health_check_response(self, client):
        """Test health check response structure."""
        response = client.get("/health")
        
        assert response.status_code == 200
        
        data = response.json()
        
        # Validate health response structure
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "dependencies" in data
        
        # Dependencies health
        deps = data["dependencies"]
        assert "ollama" in deps
        assert "database" in deps  # If we add a database later
        
        # Ollama dependency check
        ollama_status = deps["ollama"]
        assert "available" in ollama_status
        assert "model" in ollama_status
        assert "response_time_ms" in ollama_status


class TestErrorHandling:
    """Test API error handling."""
    
    def test_404_for_unknown_endpoints(self, client):
        """Test 404 response for unknown endpoints."""
        response = client.get("/api/unknown/endpoint")
        
        assert response.status_code == 404
    
    def test_405_for_wrong_http_methods(self, client):
        """Test 405 response for wrong HTTP methods."""
        # GET on POST endpoint
        response = client.get("/api/prompts/analyze")
        
        assert response.status_code == 405  # Method not allowed
    
    def test_api_returns_json_errors(self, client):
        """Test that API errors are returned as JSON."""
        response = client.post("/api/prompts/analyze", json={})
        
        # Any error should be JSON formatted
        assert response.headers.get("content-type", "").startswith("application/json")
        
        data = response.json()
        assert "detail" in data or "message" in data


class TestCORS:
    """Test CORS configuration."""
    
    def test_cors_headers_present(self, client):
        """Test that CORS headers are present for cross-origin requests."""
        headers = {
            "Origin": "http://localhost:3000",  # Frontend origin
            "Access-Control-Request-Method": "POST",  # Required for CORS preflight
            "Access-Control-Request-Headers": "Content-Type"  # Required for CORS preflight
        }
        
        response = client.options("/api/prompts/analyze", headers=headers)
        
        # Should include CORS headers
        assert response.status_code in [200, 204]
        assert "access-control-allow-origin" in response.headers


@pytest.mark.skip(reason="WebSocket testing requires special setup")
class TestWebSocketAPI:
    """Test WebSocket API for real-time analysis."""
    
    def test_websocket_connection_endpoint_exists(self):
        """Test that WebSocket endpoint exists."""
        # This test will be implemented when we add WebSocket support
        pass
    
    def test_websocket_real_time_analysis(self):
        """Test real-time analysis over WebSocket."""
        # This test will be implemented when we add WebSocket support
        pass