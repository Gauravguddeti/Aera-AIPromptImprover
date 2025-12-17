"""
WebSocket handler for real-time prompt analysis.

This module implements the WebSocket endpoint for real-time analysis
that provides instant feedback as users type their prompts.
"""

import asyncio
import json
import logging
import time
from typing import Dict, Set, Optional

from fastapi import WebSocket, WebSocketDisconnect, status
from fastapi.routing import APIRouter

from ..libs.prompt_analyzer.analyzer import PromptAnalyzer
from ..libs.suggestion_engine.engine import SuggestionEngine, SuggestionRequest as LibSuggestionRequest
from ..libs.suggestion_engine.providers import OllamaProvider, RuleBasedProvider
from ..models import (
    WebSocketAnalysisRequest,
    WebSocketAnalysisResponse,
    WebSocketError,
    WebSocketMessageType,
    AnalysisRequest,
    AnalysisResponse,
    AnalysisOptionsModel,
    ModelConverter,
    ErrorResponse,
    ErrorDetail
)

# Configure logging
logger = logging.getLogger(__name__)

# WebSocket router
ws_router = APIRouter()

# Initialize libraries for WebSocket use
ws_prompt_analyzer = PromptAnalyzer()
ws_suggestion_engine = SuggestionEngine([
    OllamaProvider(),       # AI-powered suggestions
    RuleBasedProvider()     # Fallback
])


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_tasks: Dict[str, asyncio.Task] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket connection established for client {client_id}")
    
    def disconnect(self, client_id: str):
        """Remove a WebSocket connection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        
        # Cancel any running tasks for this client
        if client_id in self.connection_tasks:
            task = self.connection_tasks[client_id]
            if not task.done():
                task.cancel()
            del self.connection_tasks[client_id]
        
        logger.info(f"WebSocket connection closed for client {client_id}")
    
    def cancel_task(self, client_id: str):
        """Cancel any running analysis task for a client."""
        if client_id in self.connection_tasks:
            task = self.connection_tasks[client_id]
            if not task.done():
                task.cancel()
                logger.debug(f"Cancelled stale analysis task for client {client_id}")
    
    async def send_message(self, client_id: str, message: dict):
        """Send a message to a specific client."""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_text(json.dumps(message, default=str))
            except Exception as e:
                logger.error(f"Error sending message to client {client_id}: {e}")
                self.disconnect(client_id)
    
    async def send_error(self, client_id: str, error_message: str, error_type: str = "websocket_error"):
        """Send an error message to a client."""
        error_response = ErrorResponse(
            detail=error_message,
            errors=[
                ErrorDetail(
                    type=error_type,
                    message=error_message,
                    code="WEBSOCKET_ERROR"
                )
            ]
        )
        
        error_msg = WebSocketError(data=error_response)
        await self.send_message(client_id, error_msg.model_dump())


# Global connection manager
manager = ConnectionManager()


class AnalysisDebouncer:
    """Debounces analysis requests to avoid excessive processing."""
    
    def __init__(self, delay_ms: int = 300):
        self.delay_ms = delay_ms
        self.pending_tasks: Dict[str, asyncio.Task] = {}
    
    async def debounced_analysis(self, client_id: str, content: str, options: Optional[dict] = None):
        """Perform debounced analysis for a client."""
        # Cancel any pending analysis for this client
        if client_id in self.pending_tasks:
            self.pending_tasks[client_id].cancel()
        
        # Create new debounced task
        async def delayed_analysis():
            await asyncio.sleep(self.delay_ms / 1000.0)
            await self._perform_analysis(client_id, content, options)
        
        task = asyncio.create_task(delayed_analysis())
        self.pending_tasks[client_id] = task
        
        try:
            await task
        except asyncio.CancelledError:
            # Task was cancelled by newer request
            pass
        finally:
            # Clean up completed task
            if client_id in self.pending_tasks and self.pending_tasks[client_id] == task:
                del self.pending_tasks[client_id]
    
    async def _perform_analysis(self, client_id: str, content: str, options: Optional[dict] = None):
        """Perform the actual analysis and send results."""
        try:
            start_time = time.perf_counter()
            
            # Create analysis request
            analysis_request = AnalysisRequest(content=content)
            if options:
                # Apply options if provided - convert dict to AnalysisOptionsModel
                try:
                    analysis_request.options = AnalysisOptionsModel(**options)
                except Exception as e:
                    logger.warning(f"Invalid options provided: {e}. Using defaults.")
                    analysis_request.options = None
            
            # Analyze the prompt
            analysis_result = ws_prompt_analyzer.analyze(content)
            
            # Get default options
            include_suggestions = False
            max_suggestions = 3
            min_confidence = 0.5
            
            if analysis_request.options:
                include_suggestions = analysis_request.options.include_suggestions
                max_suggestions = analysis_request.options.max_suggestions_per_phrase
                min_confidence = analysis_request.options.min_confidence
            
            # Filter by confidence threshold
            filtered_phrases = [
                phrase for phrase in analysis_result.vague_phrases 
                if phrase.confidence_score >= min_confidence
            ]
            
            # Generate suggestions if requested
            suggestions_dict = {}
            if include_suggestions and filtered_phrases:
                for phrase in filtered_phrases:
                    try:
                        # Create suggestion request for this phrase
                        lib_request = LibSuggestionRequest(
                            vague_phrase=phrase,
                            full_context=content,
                            max_suggestions=max_suggestions
                        )
                        
                        # Get suggestions for this phrase
                        suggestion_response = await ws_suggestion_engine.generate_suggestions(lib_request)
                        
                        if suggestion_response.suggestions:
                            suggestions_dict[phrase.id] = suggestion_response.suggestions
                    
                    except Exception as e:
                        logger.error(f"Error generating suggestions for phrase '{phrase.original_text}': {e}")
                        continue
            
            # Convert to API models
            api_phrases = ModelConverter.vague_phrases_with_suggestions_to_models(
                filtered_phrases, suggestions_dict if include_suggestions else None
            )
            
            end_time = time.perf_counter()
            analysis_time_ms = (end_time - start_time) * 1000
            
            # Create response
            analysis_response = AnalysisResponse(
                content=content,
                vague_phrases=api_phrases,
                analysis_time_ms=analysis_time_ms
            )
            
            # Send WebSocket response
            ws_response = WebSocketAnalysisResponse(data=analysis_response)
            await manager.send_message(client_id, ws_response.model_dump())
            
            logger.debug(f"Analysis completed for client {client_id} in {analysis_time_ms:.2f}ms")
            
        except Exception as e:
            error_msg = str(e)
            # Handle enum representation in error messages
            if '<VagueType.' in error_msg:
                error_msg = error_msg.split(':')[0].replace('<VagueType.', '').replace('>', '')
            logger.error(f"Error during analysis for client {client_id}: {error_msg}")
            await manager.send_error(client_id, f"Analysis failed: {error_msg}", "analysis_error")


# Global debouncer
debouncer = AnalysisDebouncer()


@ws_router.websocket("/ws/analysis")
async def websocket_analysis_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time prompt analysis.
    
    Accepts WebSocket connections and provides real-time analysis
    of prompts as users type, with debouncing to prevent excessive processing.
    """
    # Generate unique client ID
    client_id = f"client_{id(websocket)}_{int(time.time())}"
    
    try:
        # Accept connection
        await manager.connect(websocket, client_id)
        
        # Send welcome message
        welcome_msg = {
            "type": "connection_established",
            "client_id": client_id,
            "message": "WebSocket connection established for real-time analysis"
        }
        await manager.send_message(client_id, welcome_msg)
        
        # Listen for messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                message_type = message.get("type")
                
                if message_type == "ping":
                    # Respond to ping with pong
                    pong_msg = {
                        "type": "pong",
                        "timestamp": time.time()
                    }
                    await manager.send_message(client_id, pong_msg)
                
                elif message_type == "analysis_request":
                    # Handle analysis request
                    request_data = message.get("data", {})
                    content = request_data.get("content", "")
                    options = request_data.get("options")
                    
                    # Perform debounced analysis
                    await debouncer.debounced_analysis(client_id, content, options)
                
                else:
                    # Unknown message type
                    await manager.send_error(
                        client_id, 
                        f"Unknown message type: {message_type}",
                        "invalid_message_type"
                    )
            
            except json.JSONDecodeError:
                try:
                    await manager.send_error(
                        client_id,
                        "Invalid JSON message format",
                        "json_decode_error"
                    )
                except:
                    break  # Connection closed, exit loop
            
            except WebSocketDisconnect:
                # Client disconnected
                break
            
            except Exception as e:
                logger.error(f"Error processing message from client {client_id}: {e}")
                try:
                    await manager.send_error(
                        client_id,
                        f"Error processing message: {str(e)}",
                        "message_processing_error"
                    )
                except:
                    break  # Connection closed, exit loop
    
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
    
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
    
    finally:
        # Clean up connection
        manager.disconnect(client_id)