"""
Main module for Aera backend.

This module provides the FastAPI application instance that can be
imported by tests, deployment scripts, and development servers.
"""

from src.api.app import app

__all__ = ["app"]