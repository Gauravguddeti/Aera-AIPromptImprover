"""
Prompt Analyzer Library

Detects vague phrases and provides analysis of AI prompts.
This library is designed to be used standalone with CLI interface
or integrated into larger applications.

Features:
- Detect vague terms (something, good, better, etc.)
- Identify missing context
- Analyze prompt structure
- Provide improvement suggestions
"""

from .analyzer import PromptAnalyzer, VaguePhrase, AnalysisResult
from .cli import main as cli_main

__version__ = "0.1.0"
__all__ = ["PromptAnalyzer", "VaguePhrase", "AnalysisResult", "cli_main"]