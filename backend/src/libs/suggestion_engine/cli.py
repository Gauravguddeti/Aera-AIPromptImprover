#!/usr/bin/env python3
"""
Command Line Interface for Suggestion Engine

Usage:
    suggestion-engine --help
    suggestion-engine --version
    suggestion-engine "vague phrase" "full context"
    suggestion-engine --file input.txt --format json
"""

import argparse
import json
import sys
import asyncio
from pathlib import Path
from typing import Dict, Any

from .engine import SuggestionEngine, SuggestionRequest, ImprovementType
from .providers import RuleBasedProvider
from ..prompt_analyzer.analyzer import VaguePhrase, VagueType


def create_parser() -> argparse.ArgumentParser:
    """Create command line parser."""
    parser = argparse.ArgumentParser(
        prog="suggestion-engine",
        description="Generate improvement suggestions for vague phrases in AI prompts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  suggestion-engine "something" "Write something good about AI"
  suggestion-engine --file prompt.txt --format json
        """
    )
    
    parser.add_argument(
        "phrase",
        nargs="?",
        help="Vague phrase to improve"
    )
    
    parser.add_argument(
        "context",
        nargs="?",
        help="Full context/prompt containing the phrase"
    )
    
    parser.add_argument(
        "--file", "-f",
        type=Path,
        help="Read prompt from file and analyze all vague phrases"
    )
    
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )
    
    parser.add_argument(
        "--max-suggestions",
        type=int,
        default=3,
        help="Maximum number of suggestions to generate (default: 3)"
    )
    
    parser.add_argument(
        "--version", "-v",
        action="version",
        version="%(prog)s 0.1.0"
    )
    
    return parser


def format_output(response: Dict[str, Any], format_type: str) -> str:
    """Format suggestion response for output."""
    if format_type == "json":
        return json.dumps(response, indent=2, default=str)
    else:  # text format
        lines = []
        lines.append("Suggestion Results")
        lines.append("=" * 18)
        lines.append(f"Original phrase: '{response.get('vague_phrase', {}).get('text', '')}'")
        lines.append(f"Context: \"{response.get('full_context', '')}\"")
        lines.append(f"Provider: {response.get('provider_used', 'unknown')}")
        lines.append(f"Generation time: {response.get('generation_time_ms', 0):.1f}ms")
        lines.append("")
        
        suggestions = response.get('suggestions', [])
        if suggestions:
            lines.append(f"Generated {len(suggestions)} suggestions:")
            lines.append("")
            
            for i, suggestion in enumerate(suggestions, 1):
                lines.append(f"Suggestion #{i}:")
                lines.append(f"  Replacement: '{suggestion.get('improved_text', '')}'")
                lines.append(f"  Rationale: {suggestion.get('rationale', '')}")
                lines.append(f"  Type: {suggestion.get('type', '')}")
                lines.append(f"  Confidence: {suggestion.get('confidence', 0):.2f}")
                lines.append("")
        else:
            lines.append("No suggestions generated.")
        
        if response.get('error'):
            lines.append(f"Error: {response['error']}")
        
        return "\n".join(lines)


def detect_vague_type(phrase: str) -> VagueType:
    """Simple heuristic to detect vague phrase type."""
    phrase_lower = phrase.lower()
    
    if phrase_lower in ['something', 'stuff', 'things', 'anything', 'everything']:
        return VagueType.GENERIC_TERM
    elif phrase_lower in ['good', 'better', 'bad', 'nice', 'great', 'awesome']:
        return VagueType.SUBJECTIVE_QUALIFIER
    elif phrase_lower in ['try to', 'maybe', 'perhaps', 'kind of', 'sort of']:
        return VagueType.WEAK_INSTRUCTION
    elif phrase_lower in ['some', 'many', 'few', 'several', 'lots']:
        return VagueType.IMPRECISE_QUANTITY
    elif phrase_lower in ['it', 'this', 'that', 'here', 'there']:
        return VagueType.MISSING_CONTEXT
    else:
        return VagueType.GENERIC_TERM  # Default


async def process_phrase(phrase: str, context: str, max_suggestions: int = 3) -> Dict[str, Any]:
    """Process a single vague phrase."""
    # Create a VaguePhrase object
    phrase_start = context.lower().find(phrase.lower())
    if phrase_start == -1:
        phrase_start = 0
    
    vague_phrase = VaguePhrase.create(
        start=phrase_start,
        end=phrase_start + len(phrase),
        text=phrase,
        vague_type=detect_vague_type(phrase),
        confidence=1.0
    )
    
    # Create suggestion engine with rule-based provider
    engine = SuggestionEngine([RuleBasedProvider()])
    
    # Create request
    request = SuggestionRequest(
        vague_phrase=vague_phrase,
        full_context=context,
        max_suggestions=max_suggestions
    )
    
    # Generate suggestions
    response = await engine.generate_suggestions(request)
    return response.to_dict()


async def process_file(file_path: Path, max_suggestions: int = 3) -> Dict[str, Any]:
    """Process a file and find all vague phrases."""
    try:
        content = file_path.read_text(encoding='utf-8')
        
        # Import prompt analyzer to find vague phrases
        from ..prompt_analyzer.analyzer import PromptAnalyzer
        
        analyzer = PromptAnalyzer()
        analysis = analyzer.analyze(content)
        
        if not analysis.vague_phrases:
            return {
                "context": content,
                "message": "No vague phrases detected in the file",
                "suggestions": []
            }
        
        # Generate suggestions for all vague phrases
        engine = SuggestionEngine([RuleBasedProvider()])
        
        all_suggestions = []
        for vague_phrase in analysis.vague_phrases:
            request = SuggestionRequest(
                vague_phrase=vague_phrase,
                full_context=content,
                max_suggestions=max_suggestions
            )
            
            response = await engine.generate_suggestions(request)
            all_suggestions.append(response.to_dict())
        
        return {
            "context": content,
            "vague_phrases_found": len(analysis.vague_phrases),
            "suggestions": all_suggestions
        }
        
    except Exception as e:
        return {
            "error": f"Error processing file: {e}",
            "suggestions": []
        }


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    try:
        if args.file:
            # Process file
            result = asyncio.run(process_file(args.file, args.max_suggestions))
            output = format_output(result, args.format)
            print(output)
            
        elif args.phrase and args.context:
            # Process single phrase
            result = asyncio.run(process_phrase(args.phrase, args.context, args.max_suggestions))
            output = format_output(result, args.format)
            print(output)
            
        else:
            # Show help
            parser.print_help()
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()