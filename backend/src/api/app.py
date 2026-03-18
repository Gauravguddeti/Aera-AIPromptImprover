"""
Main FastAPI application for Aera backend.

This module sets up the FastAPI app with all routes, middleware,
and configuration for the AI prompt enhancement service.
"""

from contextlib import asynccontextmanager
from typing import Dict, Any
import time
import json
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError

from .routes import router as api_router
from .websocket import ws_router
from ..models import ErrorResponse, ErrorDetail, HealthResponse, HealthStatus, DependencyHealth


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events for the FastAPI app."""
    # Startup
    print("🚀 Aera backend starting up...")
    
    # TODO: Initialize database connections, AI models, etc.
    
    yield
    
    # Shutdown
    print("👋 Aera backend shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Aera AI Prompt Enhancement API",
    description="Backend API for the Aera desktop application that provides real-time AI-powered suggestions to improve prompt clarity and effectiveness.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicitly include OPTIONS
    allow_headers=["*"],
)


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors."""
    errors = []
    for error in exc.errors():
        error_detail = ErrorDetail(
            type="validation_error",
            message=error["msg"],
            field=".".join(str(loc) for loc in error["loc"]) if error["loc"] else None,
            code="VALIDATION_FAILED"
        )
        errors.append(error_detail)
    
    error_response = ErrorResponse(
        detail="Request validation failed",
        errors=errors
    )
    
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder(error_response.model_dump())
    )


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle FastAPI request validation errors."""
    errors = []
    for error in exc.errors():
        error_detail = ErrorDetail(
            type="validation_error",
            message=error["msg"],
            field=".".join(str(loc) for loc in error["loc"]) if error["loc"] else None,
            code="REQUEST_VALIDATION_FAILED"
        )
        errors.append(error_detail)
    
    error_response = ErrorResponse(
        detail="Request validation failed",
        errors=errors
    )
    
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder(error_response.model_dump())
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with proper error format."""
    if isinstance(exc.detail, dict):
        # Already properly formatted
        return JSONResponse(
            status_code=exc.status_code,
            content=jsonable_encoder(exc.detail)
        )
    
    # Convert simple string detail to proper error response
    error_response = ErrorResponse(
        detail=str(exc.detail),
        errors=[
            ErrorDetail(
                type="http_error",
                message=str(exc.detail),
                code=f"HTTP_{exc.status_code}"
            )
        ]
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(error_response.model_dump())
    )


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns the health status of the service and its dependencies.
    """
    try:
        dependencies = {}
        overall_status = HealthStatus.HEALTHY
        
        # Check Groq availability
        try:
            from ..libs.suggestion_engine import GroqProvider, OllamaProvider
            from ..config import settings
            groq_provider = GroqProvider(api_key=settings.GROQ_API_KEY, model=settings.GROQ_MODEL)
            
            start_time = time.time()
            is_available = await groq_provider.is_available()
            response_time = (time.time() - start_time) * 1000
            
            if is_available:
                dependencies["groq"] = DependencyHealth(
                    available=True,
                    response_time_ms=response_time,
                    version=settings.GROQ_MODEL,
                    model=settings.GROQ_MODEL
                )
            else:
                dependencies["groq"] = DependencyHealth(
                    available=False,
                    error="Groq API key missing"
                )
                overall_status = HealthStatus.DEGRADED
                
        except Exception as e:
            dependencies["groq"] = DependencyHealth(
                available=False,
                error=f"Groq check failed: {str(e)}"
            )
            # Don't mark as unhealthy since we have rule-based fallback
            overall_status = HealthStatus.DEGRADED

        # Check local Ollama availability (optional fallback)
        try:
            from ..config import settings
            ollama_provider = OllamaProvider(model=settings.OLLAMA_MODEL, host=settings.OLLAMA_HOST)
            start_time = time.time()
            ollama_available = await ollama_provider.is_available()
            response_time = (time.time() - start_time) * 1000

            if ollama_available:
                dependencies["ollama"] = DependencyHealth(
                    available=True,
                    response_time_ms=response_time,
                    version=settings.OLLAMA_MODEL,
                    model=settings.OLLAMA_MODEL
                )
            else:
                dependencies["ollama"] = DependencyHealth(
                    available=False,
                    error="Ollama not running or model unavailable"
                )
        except Exception as e:
            dependencies["ollama"] = DependencyHealth(
                available=False,
                error=f"Ollama check failed: {str(e)}"
            )
        
        # Check database health (placeholder for future implementation)
        # For now, mark as healthy since we're using in-memory storage
        dependencies["database"] = DependencyHealth(
            available=True,
            response_time_ms=1.0,  # Very fast since it's in-memory
            version="in-memory"
        )
        
        return HealthResponse(
            status=overall_status,
            version="0.1.0",
            dependencies=dependencies
        )
        
    except Exception as e:
        return HealthResponse(
            status=HealthStatus.UNHEALTHY,
            version="0.1.0",
            dependencies={
                "error": DependencyHealth(
                    available=False,
                    error=f"Health check failed: {str(e)}"
                )
            }
        )


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Aera AI Prompt Enhancement API",
        "version": "0.1.0",
        "description": "Backend API for real-time AI-powered prompt improvement suggestions",
        "docs": "/docs",
        "health": "/health",
        "privacy": "All processing happens locally - no data leaves your device"
    }


# Include API routes
app.include_router(api_router)
app.include_router(ws_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)