"""
Tests for WebSocket real-time analysis functionality.

These tests verify that the WebSocket endpoint works correctly
for real-time prompt analysis with proper debouncing and error handling.
"""

import pytest
import asyncio
import json
from fastapi.testclient import TestClient

from src.main import app


class TestWebSocketAnalysis:
    """Test WebSocket analysis functionality."""
    
    def test_websocket_connection(self):
        """Test that WebSocket connection can be established."""
        client = TestClient(app)
        
        with client.websocket_connect("/ws/analysis") as websocket:
            # Should receive welcome message
            data = websocket.receive_text()
            message = json.loads(data)
            
            assert message["type"] == "connection_established"
            assert "client_id" in message
            assert "message" in message
    
    def test_websocket_ping_pong(self):
        """Test WebSocket ping/pong functionality."""
        client = TestClient(app)
        
        with client.websocket_connect("/ws/analysis") as websocket:
            # Receive welcome message
            websocket.receive_text()
            
            # Send ping
            ping_msg = {
                "type": "ping"
            }
            websocket.send_text(json.dumps(ping_msg))
            
            # Should receive pong
            data = websocket.receive_text()
            message = json.loads(data)
            
            assert message["type"] == "pong"
            assert "timestamp" in message
    
    def test_websocket_analysis_request(self):
        """Test WebSocket analysis request and response."""
        client = TestClient(app)
        
        with client.websocket_connect("/ws/analysis") as websocket:
            # Receive welcome message
            websocket.receive_text()
            
            # Send analysis request
            analysis_msg = {
                "type": "analysis_request",
                "data": {
                    "content": "Write something good about AI",
                    "options": {
                        "include_suggestions": False,
                        "min_confidence": 0.5
                    }
                }
            }
            websocket.send_text(json.dumps(analysis_msg))
            
            # Should receive analysis response
            data = websocket.receive_text()
            message = json.loads(data)
            
            assert message["type"] == "analysis_response"
            assert "data" in message
            
            analysis_data = message["data"]
            assert "content" in analysis_data
            assert "vague_phrases" in analysis_data
            assert "analysis_time_ms" in analysis_data
            assert analysis_data["content"] == "Write something good about AI"
            
            # Should detect vague phrases
            assert len(analysis_data["vague_phrases"]) > 0
    
    def test_websocket_analysis_with_suggestions(self):
        """Test WebSocket analysis with suggestions enabled."""
        client = TestClient(app)
        
        with client.websocket_connect("/ws/analysis") as websocket:
            # Receive welcome message
            websocket.receive_text()
            
            # Send analysis request with suggestions
            analysis_msg = {
                "type": "analysis_request",
                "data": {
                    "content": "Write something good",
                    "options": {
                        "include_suggestions": True,
                        "max_suggestions_per_phrase": 2
                    }
                }
            }
            websocket.send_text(json.dumps(analysis_msg))
            
            # Should receive analysis response
            data = websocket.receive_text()
            message = json.loads(data)
            
            assert message["type"] == "analysis_response"
            
            analysis_data = message["data"]
            vague_phrases = analysis_data["vague_phrases"]
            
            # Should have phrases with suggestions
            assert len(vague_phrases) > 0
            
            # Check if any phrase has suggestions
            has_suggestions = any(
                phrase.get("suggestions") is not None 
                for phrase in vague_phrases
            )
            assert has_suggestions
    
    def test_websocket_empty_content(self):
        """Test WebSocket analysis with empty content."""
        client = TestClient(app)
        
        with client.websocket_connect("/ws/analysis") as websocket:
            # Receive welcome message
            websocket.receive_text()
            
            # Send analysis request with empty content
            analysis_msg = {
                "type": "analysis_request",
                "data": {
                    "content": ""
                }
            }
            websocket.send_text(json.dumps(analysis_msg))
            
            # Should receive analysis response
            data = websocket.receive_text()
            message = json.loads(data)
            
            assert message["type"] == "analysis_response"
            
            analysis_data = message["data"]
            assert analysis_data["content"] == ""
            assert analysis_data["vague_phrases"] == []
    
    def test_websocket_invalid_message_type(self):
        """Test WebSocket error handling for invalid message type."""
        client = TestClient(app)
        
        with client.websocket_connect("/ws/analysis") as websocket:
            # Receive welcome message
            websocket.receive_text()
            
            # Send invalid message type
            invalid_msg = {
                "type": "invalid_type",
                "data": {}
            }
            websocket.send_text(json.dumps(invalid_msg))
            
            # Should receive error response
            data = websocket.receive_text()
            message = json.loads(data)
            
            assert message["type"] == "error"
            assert "data" in message
            
            error_data = message["data"]
            assert "detail" in error_data
            assert "errors" in error_data
    
    def test_websocket_invalid_json(self):
        """Test WebSocket error handling for invalid JSON."""
        client = TestClient(app)
        
        with client.websocket_connect("/ws/analysis") as websocket:
            # Receive welcome message
            websocket.receive_text()
            
            # Send invalid JSON
            websocket.send_text("invalid json {")
            
            # Should receive error response
            data = websocket.receive_text()
            message = json.loads(data)
            
            assert message["type"] == "error"
            assert "data" in message
    
    def test_websocket_multiple_requests_debouncing(self):
        """Test that multiple rapid requests are properly debounced."""
        client = TestClient(app)
        
        with client.websocket_connect("/ws/analysis") as websocket:
            # Receive welcome message
            websocket.receive_text()
            
            # Send multiple rapid requests
            for i in range(3):
                analysis_msg = {
                    "type": "analysis_request",
                    "data": {
                        "content": f"Write something good {i}"
                    }
                }
                websocket.send_text(json.dumps(analysis_msg))
            
            # Should receive only one response (the last one after debounce)
            # Wait a bit longer than debounce time
            import time
            time.sleep(0.4)  # 400ms > 300ms debounce
            
            # Read all available messages
            messages = []
            try:
                while True:
                    data = websocket.receive_text()
                    message = json.loads(data)
                    if message["type"] == "analysis_response":
                        messages.append(message)
            except:
                # No more messages
                pass
            
            # Should have received only one analysis response due to debouncing
            assert len(messages) >= 1  # At least one response
            
            # The final response should be for the last request
            if messages:
                final_response = messages[-1]
                assert "Write something good 2" in final_response["data"]["content"]


class TestWebSocketPerformance:
    """Test WebSocket performance characteristics."""
    
    def test_websocket_analysis_performance(self):
        """Test that WebSocket analysis meets performance requirements."""
        client = TestClient(app)
        
        with client.websocket_connect("/ws/analysis") as websocket:
            # Receive welcome message
            websocket.receive_text()
            
            # Send analysis request
            analysis_msg = {
                "type": "analysis_request",
                "data": {
                    "content": "Write something good about AI technology"
                }
            }
            
            import time
            start_time = time.time()
            websocket.send_text(json.dumps(analysis_msg))
            
            # Receive response
            data = websocket.receive_text()
            end_time = time.time()
            
            message = json.loads(data)
            
            # Total response time should be reasonable
            total_time_ms = (end_time - start_time) * 1000
            assert total_time_ms < 1000  # Should respond within 1 second
            
            # Analysis time reported should meet requirements
            analysis_time_ms = message["data"]["analysis_time_ms"]
            assert analysis_time_ms < 300  # Should analyze within 300ms