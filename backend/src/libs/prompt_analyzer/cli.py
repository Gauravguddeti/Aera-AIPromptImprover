#!/usr/bin/env python3
"""
Command Line Interface for Prompt Analyzer

Usage:
    prompt-analyzer --help
    prompt-analyzer --version
    prompt-analyzer "Your prompt text here"
    prompt-analyzer --file input.txt --format json
    prompt-analyzer --interactive
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

from .analyzer import PromptAnalyzer


def create_parser() -> argparse.ArgumentParser:
    """Create command line parser."""
    parser = argparse.ArgumentParser(
        prog="prompt-analyzer",
        description="Analyze AI prompts for vague phrases and improvement opportunities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  prompt-analyzer "Write something good about AI"
  prompt-analyzer --file my_prompt.txt --format json
  prompt-analyzer --interactive
        """
    )
    
    parser.add_argument(
        "prompt",
        nargs="?",
        help="Prompt text to analyze (if not using --file or --interactive)"
    )
    
    parser.add_argument(
        "--file", "-f",
        type=Path,
        help="Read prompt from file"
    )
    
    parser.add_argument(
        "--format",
        choices=["text", "json", "yaml"],
        default="text",
        help="Output format (default: text)"
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Interactive mode"
    )
    
    parser.add_argument(
        "--version", "-v",
        action="version",
        version="%(prog)s 0.1.0"
    )
    
    return parser


def format_output(result: Dict[str, Any], format_type: str) -> str:
    """Format analysis result for output."""
    if format_type == "json":
        return json.dumps(result, indent=2, default=str)
    elif format_type == "yaml":
        try:
            import yaml
            return yaml.dump(result, default_flow_style=False)
        except ImportError:
            print("Warning: PyYAML not installed, falling back to JSON", file=sys.stderr)
            return json.dumps(result, indent=2, default=str)
    else:  # text format
        lines = []
        lines.append(f"Prompt Analysis Results")
        lines.append("=" * 25)
        lines.append(f"Original length: {len(result.get('original_text', ''))}")
        lines.append(f"Vague phrases found: {len(result.get('vague_phrases', []))}")
        lines.append("")
        
        for i, phrase in enumerate(result.get('vague_phrases', []), 1):
            lines.append(f"Vague Phrase #{i}:")
            lines.append(f"  Text: '{phrase.get('text', '')}'")
            lines.append(f"  Type: {phrase.get('type', 'unknown')}")
            lines.append(f"  Position: {phrase.get('start')}-{phrase.get('end')}")
            lines.append(f"  Confidence: {phrase.get('confidence', 0):.2f}")
            lines.append("")
        
        return "\n".join(lines)


def interactive_mode():
    """Run in interactive mode."""
    print("Prompt Analyzer - Interactive Mode")
    print("Type 'quit' or 'exit' to leave")
    print("-" * 40)
    
    analyzer = PromptAnalyzer()
    
    while True:
        try:
            prompt = input("\nEnter prompt to analyze: ").strip()
            if prompt.lower() in ["quit", "exit", ""]:
                break
                
            result = analyzer.analyze(prompt)
            output = format_output(result.to_dict(), "text")
            print(output)
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Determine input source
    prompt_text = None
    if args.file:
        try:
            prompt_text = args.file.read_text(encoding='utf-8')
        except Exception as e:
            print(f"Error reading file {args.file}: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.prompt:
        prompt_text = args.prompt
    elif args.interactive:
        interactive_mode()
        return
    else:
        parser.print_help()
        sys.exit(1)
    
    # Analyze prompt
    try:
        analyzer = PromptAnalyzer()
        result = analyzer.analyze(prompt_text)
        output = format_output(result.to_dict(), args.format)
        print(output)
    except Exception as e:
        print(f"Analysis error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()