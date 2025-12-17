"""
Tests for the CLI interface of prompt analyzer.

Testing command line argument parsing, output formatting, and integration.
"""

import pytest
import json
from unittest.mock import patch, MagicMock, mock_open
from io import StringIO
import sys
import tempfile
from pathlib import Path

from ..cli import (
    create_parser, 
    format_output, 
    main,
    interactive_mode
)
from ..analyzer import AnalysisResult, VaguePhrase, VagueType


class TestArgumentParsing:
    """Test command line argument parsing."""
    
    def test_create_parser(self):
        """Test parser creation."""
        parser = create_parser()
        assert parser.prog == "prompt-analyzer"
    
    def test_parse_prompt_argument(self):
        """Test parsing prompt as positional argument."""
        parser = create_parser()
        args = parser.parse_args(["Write something good"])
        
        assert args.prompt == "Write something good"
        assert args.file is None
        assert args.format == "text"
        assert args.interactive is False
    
    def test_parse_file_argument(self):
        """Test parsing file input argument."""
        parser = create_parser()
        args = parser.parse_args(["--file", "test.txt"])
        
        assert args.file == Path("test.txt")
        assert args.prompt is None
        assert args.format == "text"
    
    def test_parse_format_argument(self):
        """Test parsing output format argument."""
        parser = create_parser()
        args = parser.parse_args(["--format", "json", "test prompt"])
        
        assert args.format == "json"
        assert args.prompt == "test prompt"
    
    def test_parse_interactive_flag(self):
        """Test parsing interactive mode flag."""
        parser = create_parser()
        args = parser.parse_args(["--interactive"])
        
        assert args.interactive is True
        assert args.prompt is None
    
    def test_version_argument(self):
        """Test version argument."""
        parser = create_parser()
        
        with pytest.raises(SystemExit):
            parser.parse_args(["--version"])


class TestOutputFormatting:
    """Test output formatting functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.sample_result = {
            "original_text": "Write something good",
            "vague_phrases": [
                {
                    "id": "test-id-1",
                    "start": 6,
                    "end": 15,
                    "text": "something",
                    "type": "generic_term",
                    "confidence": 0.9
                },
                {
                    "id": "test-id-2", 
                    "start": 16,
                    "end": 20,
                    "text": "good",
                    "type": "subjective_qualifier",
                    "confidence": 0.8
                }
            ],
            "analysis_time_ms": 125.5,
            "error": None,
            "fallback_mode": False
        }
    
    def test_format_output_text(self):
        """Test text format output."""
        output = format_output(self.sample_result, "text")
        
        assert "Prompt Analysis Results" in output
        assert "Vague phrases found: 2" in output
        assert "Original length: 20" in output
        assert "Vague Phrase #1:" in output
        assert "Text: 'something'" in output
        assert "Type: generic_term" in output
        assert "Position: 6-15" in output
        assert "Confidence: 0.90" in output
    
    def test_format_output_json(self):
        """Test JSON format output."""
        output = format_output(self.sample_result, "json")
        
        # Should be valid JSON
        parsed = json.loads(output)
        assert parsed["original_text"] == "Write something good"
        assert len(parsed["vague_phrases"]) == 2
        assert parsed["analysis_time_ms"] == 125.5
    
    @patch('yaml.dump')
    def test_format_output_yaml(self, mock_yaml_dump):
        """Test YAML format output."""
        mock_yaml_dump.return_value = "yaml output"
        
        output = format_output(self.sample_result, "yaml")
        
        mock_yaml_dump.assert_called_once()
        assert output == "yaml output"
    
    @patch('yaml.dump', side_effect=ImportError)
    def test_format_output_yaml_fallback(self, mock_yaml_dump):
        """Test YAML format fallback to JSON when PyYAML not available."""
        with patch('sys.stderr', new=StringIO()) as mock_stderr:
            output = format_output(self.sample_result, "yaml")
        
        # Should fallback to JSON
        parsed = json.loads(output)
        assert parsed["original_text"] == "Write something good"
        
        # Should print warning
        assert "PyYAML not installed" in mock_stderr.getvalue()
    
    def test_format_output_empty_result(self):
        """Test formatting output with no vague phrases."""
        empty_result = {
            "original_text": "Create a Python function",
            "vague_phrases": [],
            "analysis_time_ms": 50.0,
            "error": None,
            "fallback_mode": False
        }
        
        output = format_output(empty_result, "text")
        
        assert "Vague phrases found: 0" in output
        assert "Original length: 24" in output


class TestMainFunction:
    """Test main CLI function."""
    
    @patch('sys.argv', ['prompt-analyzer', 'Write something good'])
    @patch('builtins.print')
    def test_main_with_prompt_argument(self, mock_print):
        """Test main function with prompt argument."""
        with patch('sys.exit') as mock_exit:
            main()
        
        # Should not exit with error
        mock_exit.assert_not_called()
        
        # Should print analysis results
        mock_print.assert_called()
        output = str(mock_print.call_args[0][0])
        assert "Prompt Analysis Results" in output
    
    @patch('sys.argv', ['prompt-analyzer', '--file', 'nonexistent.txt'])
    @patch('sys.exit')
    def test_main_with_nonexistent_file(self, mock_exit):
        """Test main function with nonexistent file."""
        with patch('sys.stderr', new=StringIO()):
            main()
        
        # Should exit with error code 1
        mock_exit.assert_called_with(1)
    
    @patch('sys.argv', ['prompt-analyzer', '--file', 'test.txt'])
    @patch('builtins.print')
    def test_main_with_file_input(self, mock_print):
        """Test main function with file input."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Write something good about AI")
            temp_path = f.name
        
        try:
            with patch('sys.argv', ['prompt-analyzer', '--file', temp_path]):
                with patch('sys.exit') as mock_exit:
                    main()
            
            # Should not exit with error
            mock_exit.assert_not_called()
            
            # Should print analysis results
            mock_print.assert_called()
            output = str(mock_print.call_args[0][0])
            assert "Prompt Analysis Results" in output
        finally:
            Path(temp_path).unlink()
    
    @patch('sys.argv', ['prompt-analyzer', '--format', 'json', 'Write something'])
    @patch('builtins.print')
    def test_main_with_json_format(self, mock_print):
        """Test main function with JSON output format."""
        with patch('sys.exit') as mock_exit:
            main()
        
        # Should not exit with error
        mock_exit.assert_not_called()
        
        # Should print JSON output
        mock_print.assert_called()
        output = str(mock_print.call_args[0][0])
        
        # Should be valid JSON
        parsed = json.loads(output)
        assert "original_text" in parsed
        assert "vague_phrases" in parsed
    
    @patch('sys.argv', ['prompt-analyzer', '--interactive'])
    @patch('builtins.input', side_effect=['Write something good', 'quit'])
    @patch('builtins.print')
    def test_main_interactive_mode(self, mock_print, mock_input):
        """Test main function in interactive mode."""
        with patch('sys.exit') as mock_exit:
            main()
        
        # Should not exit with error
        mock_exit.assert_not_called()
        
        # Should have prompted for input and displayed results
        mock_input.assert_called()
        mock_print.assert_called()
    
    @patch('sys.argv', ['prompt-analyzer'])
    @patch('sys.exit')
    def test_main_no_arguments(self, mock_exit):
        """Test main function with no arguments shows help."""
        with patch('sys.stdout', new=StringIO()):
            main()
        
        # Should exit with error code 1
        mock_exit.assert_called_with(1)


class TestInteractiveMode:
    """Test interactive mode functionality."""
    
    @patch('builtins.input', side_effect=['Write something good', 'quit'])
    @patch('builtins.print')
    def test_interactive_mode_normal_flow(self, mock_print, mock_input):
        """Test normal interactive mode flow."""
        interactive_mode()
        
        # Should prompt for input
        mock_input.assert_called()
        
        # Should print results and prompts
        mock_print.assert_called()
        
        # Check that analysis results were printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        results_printed = any("Prompt Analysis Results" in call for call in print_calls)
        assert results_printed
    
    @patch('builtins.input', side_effect=['', 'exit'])
    @patch('builtins.print')
    def test_interactive_mode_empty_input(self, mock_print, mock_input):
        """Test interactive mode with empty input."""
        interactive_mode()
        
        # Should handle empty input gracefully
        mock_input.assert_called()
        mock_print.assert_called()
    
    @patch('builtins.input', side_effect=KeyboardInterrupt)
    @patch('builtins.print')
    def test_interactive_mode_keyboard_interrupt(self, mock_print, mock_input):
        """Test interactive mode handles Ctrl+C gracefully."""
        interactive_mode()
        
        # Should print goodbye message
        goodbye_printed = any("Goodbye!" in str(call) for call in mock_print.call_args_list)
        assert goodbye_printed
    
    @patch('builtins.input', side_effect=['invalid input that causes error'])
    @patch('builtins.print')
    def test_interactive_mode_error_handling(self, mock_print, mock_input):
        """Test interactive mode handles analysis errors."""
        # Mock analyzer to raise exception
        with patch('src.libs.prompt_analyzer.cli.PromptAnalyzer') as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer.analyze.side_effect = Exception("Test error")
            mock_analyzer_class.return_value = mock_analyzer
            
            # Add second input to exit
            mock_input.side_effect = ['problematic input', 'quit']
            
            interactive_mode()
        
        # Should handle error and continue
        mock_print.assert_called()


class TestCLIIntegration:
    """Integration tests for CLI functionality."""
    
    def test_cli_help_message(self):
        """Test that help message is informative."""
        parser = create_parser()
        help_text = parser.format_help()
        
        assert "prompt-analyzer" in help_text
        # The help text should contain something about analyzing prompts
        assert ("analyze" in help_text.lower() and "prompt" in help_text.lower()) or "vague phrase" in help_text.lower()
        assert "--file" in help_text
        assert "--format" in help_text
        assert "--interactive" in help_text
        assert "examples:" in help_text.lower()
    
    def test_format_choices_validation(self):
        """Test that format argument validates choices."""
        parser = create_parser()
        
        # Valid format should work
        args = parser.parse_args(["--format", "json", "test"])
        assert args.format == "json"
        
        # Invalid format should raise error
        with pytest.raises(SystemExit):
            parser.parse_args(["--format", "invalid", "test"])
    
    @patch('sys.argv', ['prompt-analyzer', 'Test prompt'])
    def test_end_to_end_text_analysis(self):
        """Test end-to-end analysis with text output."""
        with patch('builtins.print') as mock_print:
            with patch('sys.exit') as mock_exit:
                main()
        
        # Should complete successfully
        mock_exit.assert_not_called()
        
        # Should produce expected output format
        mock_print.assert_called()
        output = str(mock_print.call_args[0][0])
        assert "Prompt Analysis Results" in output
        assert "=" in output  # Header underline
    
    def test_real_file_processing(self):
        """Test processing a real temporary file."""
        test_content = "Write something good and interesting about AI"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_path = f.name
        
        try:
            with patch('sys.argv', ['prompt-analyzer', '--file', temp_path, '--format', 'json']):
                with patch('builtins.print') as mock_print:
                    with patch('sys.exit') as mock_exit:
                        main()
            
            # Should complete successfully
            mock_exit.assert_not_called()
            
            # Should produce valid JSON
            output = str(mock_print.call_args[0][0])
            parsed = json.loads(output)
            assert parsed["original_text"] == test_content
            assert len(parsed["vague_phrases"]) > 0
        finally:
            Path(temp_path).unlink()