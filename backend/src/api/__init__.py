"""
API package for Aera backend.

This package contains the FastAPI application and route definitions
for the AI prompt enhancement service.
"""

from .app import app
from .routes import router

__all__ = ["app", "router"]