"""
Suggestion Engine Library

Generates improvement suggestions for vague phrases using AI models.
This library is designed to be used standalone with CLI interface
or integrated into larger applications.

Features:
- Generate specific replacements for vague terms
- Provide rationale for improvements
- Support multiple AI backends (Ollama, OpenAI, etc.)
- Fallback to rule-based suggestions when AI unavailable
"""

from .engine import SuggestionEngine, AIProvider, Suggestion
from .providers import OllamaProvider, RuleBasedProvider
from .groq_provider import GroqProvider, GroqWithOllamaFallbackProvider
from .cli import main as cli_main

__version__ = "0.1.0"
__all__ = [
	"SuggestionEngine",
	"AIProvider",
	"Suggestion",
	"OllamaProvider",
	"GroqProvider",
	"GroqWithOllamaFallbackProvider",
	"RuleBasedProvider",
	"cli_main",
]