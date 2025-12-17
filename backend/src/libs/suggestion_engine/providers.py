"""
AI provider implementations for suggestion generation.

This module contains concrete implementations of AIProvider for different
AI backends like Ollama, OpenAI, etc.
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional

from .engine import AIProvider, Suggestion, VaguePhrase, ImprovementType
try:
    from ..prompt_analyzer.analyzer import VagueType
except ImportError:
    from prompt_analyzer.analyzer import VagueType

# Configure logging
logger = logging.getLogger(__name__)


class OllamaProvider(AIProvider):
    """Ollama-based AI provider for local suggestion generation."""
    
    def __init__(self, model: str = "llama3:8b", host: str = "http://localhost:11434"):
        """
        Initialize Ollama provider.
        
        Args:
            model: Ollama model to use (default: llama3:8b)
            host: Ollama server host (default: http://localhost:11434)
        """
        self.model = model
        self.host = host
        self._client = None
    
    @property
    def name(self) -> str:
        return f"ollama-{self.model}"
    
    async def is_available(self) -> bool:
        """Check if Ollama is available."""
        try:
            # Try to import ollama client
            import ollama
            
            # Create client if not exists
            if self._client is None:
                self._client = ollama.AsyncClient(host=self.host)
            
            # Test connection with a simple request
            result = await self._client.list()
            
            # Check if our model is available (models is a list of Model objects)
            available_models = [m.model for m in result.models]
            return self.model in available_models
            
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")
            return False
    
    async def generate_suggestions(self, vague_phrase: VaguePhrase, context: str) -> List[Suggestion]:
        """Generate suggestions using Ollama."""
        if not await self.is_available():
            raise RuntimeError("Ollama not available")
        
        try:
            import ollama
            
            if self._client is None:
                self._client = ollama.AsyncClient(host=self.host)
            
            # Create prompt for the AI model
            prompt = self._create_prompt(vague_phrase, context)
            
            # Simple request without complex options for now
            response = await self._client.generate(
                model=self.model,
                prompt=prompt
            )
            
            # Parse response
            response_text = response.get('response', '') if isinstance(response, dict) else str(response)
            suggestions = self._parse_response(response_text, vague_phrase)
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating suggestions with Ollama: {e}")
            raise
    
    def _create_prompt(self, vague_phrase: VaguePhrase, context: str) -> str:
        """Create a prompt for the AI model."""
        prompt = f"""
I need help improving a vague phrase in an AI prompt to make it more specific and clear.

Original prompt: "{context}"
Vague phrase: "{vague_phrase.original_text}" (type: {vague_phrase.vague_type.value})
Position: characters {vague_phrase.start_position}-{vague_phrase.end_position}

Please suggest 3 specific improvements for the vague phrase "{vague_phrase.original_text}". 
For each suggestion, provide:
1. A specific replacement text
2. A brief rationale explaining why it's better
3. The type of improvement (specificity, clarity, context, precision, or strength)

Format your response as JSON:
{{
  "suggestions": [
    {{
      "replacement": "specific replacement text",
      "rationale": "why this is better",
      "improvement_type": "specificity|clarity|context|precision|strength"
    }}
  ]
}}

Focus on making the prompt more actionable and precise while maintaining the original intent.
"""
        return prompt.strip()
    
    def _parse_response(self, response_text: str, vague_phrase: VaguePhrase) -> List[Suggestion]:
        """Parse AI response into Suggestion objects."""
        try:
            # Log the raw response for debugging
            logger.debug(f"Raw Ollama response: {response_text[:200]}...")
            
            # Try to extract JSON from response
            response_text = response_text.strip()
            
            # Try to extract from markdown code block first
            if '```json' in response_text:
                start_marker = response_text.find('```json') + 7
                end_marker = response_text.find('```', start_marker)
                if end_marker > start_marker:
                    response_text = response_text[start_marker:end_marker].strip()
            elif '```' in response_text:
                start_marker = response_text.find('```') + 3
                end_marker = response_text.find('```', start_marker)
                if end_marker > start_marker:
                    response_text = response_text[start_marker:end_marker].strip()
            
            # Look for JSON content
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                logger.warning(f"No JSON found in response: {response_text[:100]}")
                raise ValueError("No JSON found in response")
            
            json_text = response_text[start_idx:end_idx]
            data = json.loads(json_text)
            
            suggestions = []
            for item in data.get('suggestions', []):
                improvement_type_str = item.get('improvement_type', 'specificity')
                
                # Map to enum
                try:
                    improvement_type = ImprovementType(improvement_type_str)
                except ValueError:
                    improvement_type = ImprovementType.SPECIFICITY
                
                suggestion = Suggestion.create(
                    improved_text=item.get('replacement', ''),
                    rationale=item.get('rationale', 'AI-generated improvement'),
                    improvement_type=improvement_type,
                    original_phrase=vague_phrase.original_text,
                    confidence=0.8  # AI suggestions get high confidence
                )
                suggestions.append(suggestion)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            # Return a fallback suggestion
            return [Suggestion.create(
                improved_text="[specific details]",
                rationale="AI response could not be parsed",
                improvement_type=ImprovementType.SPECIFICITY,
                original_phrase=vague_phrase.original_text,
                confidence=0.3
            )]

# Model Discovery and Recommendation System

class ModelInfo:
    """Information about an available Ollama model."""
    def __init__(self, name: str, size: str, modified: str):
        self.name = name
        self.size = size
        self.modified = modified
        self.size_gb = self._parse_size(size)
    
    def _parse_size(self, size_str: str) -> float:
        """Parse size string like '4.7 GB' into float."""
        try:
            parts = size_str.split()
            if len(parts) >= 2:
                num = float(parts[0])
                unit = parts[1].upper()
                if unit == 'GB':
                    return num
                elif unit == 'MB':
                    return num / 1024
            return 0.0
        except:
            return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'size': self.size,
            'size_gb': self.size_gb,
            'modified': self.modified
        }


class ModelRecommendation:
    """Recommendation for a model's suitability."""
    def __init__(self, model_name: str, suitable_for: List[str], warnings: List[str], score: float):
        self.model_name = model_name
        self.suitable_for = suitable_for  # ['analysis', 'rewriting', 'inline_checks']
        self.warnings = warnings
        self.score = score  # 0.0 to 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'model_name': self.model_name,
            'suitable_for': self.suitable_for,
            'warnings': self.warnings,
            'score': self.score
        }


class ModelDiscovery:
    """Discovers and recommends Ollama models."""
    
    def __init__(self, host: str = "http://localhost:11434"):
        self.host = host
        self._client = None
    
    async def discover_models(self) -> List[ModelInfo]:
        """Discover all locally available Ollama models."""
        try:
            import ollama
            if self._client is None:
                self._client = ollama.AsyncClient(host=self.host)
            
            response = await self._client.list()
            models = []
            
            # Handle both dict and object responses from Ollama
            models_list = response.get('models', []) if isinstance(response, dict) else getattr(response, 'models', [])
            
            for model_obj in models_list:
                # Handle both dict and object formats
                if isinstance(model_obj, dict):
                    model_name = model_obj.get('name', model_obj.get('model', ''))
                    size_bytes = model_obj.get('size', 0)
                    modified = model_obj.get('modified_at', '')
                else:
                    model_name = getattr(model_obj, 'model', getattr(model_obj, 'name', ''))
                    size_bytes = getattr(model_obj, 'size', 0)
                    modified = getattr(model_obj, 'modified_at', '')
                
                # Convert size from bytes to readable format
                size_gb = size_bytes / (1024 ** 3) if size_bytes > 0 else 0
                size_str = f"{size_gb:.1f} GB"
                
                model_info = ModelInfo(
                    name=model_name,
                    size=size_str,
                    modified=str(modified) if modified else ''
                )
                models.append(model_info)
            
            return models
        except Exception as e:
            logger.error(f"Error discovering models: {e}")
            return []
    
    def evaluate_model(self, model_info: ModelInfo) -> ModelRecommendation:
        """Evaluate a model's suitability for different tasks."""
        name_lower = model_info.name.lower()
        size_gb = model_info.size_gb
        
        suitable_for = []
        warnings = []
        score = 0.5  # Base score
        
        # Check model family
        if 'llama3' in name_lower or 'llama-3' in name_lower:
            suitable_for.extend(['analysis', 'rewriting'])
            score += 0.3
            if size_gb >= 7:
                suitable_for.append('inline_checks')
                score += 0.1
        elif 'qwen' in name_lower:
            suitable_for.extend(['analysis', 'rewriting'])
            score += 0.25
            warnings.append('Good at structured analysis')
        elif 'phi' in name_lower:
            suitable_for.append('inline_checks')
            score += 0.2
            warnings.append('Optimized for low-latency responses')
        elif 'mistral' in name_lower:
            suitable_for.extend(['analysis', 'rewriting'])
            score += 0.25
        elif 'gemma' in name_lower:
            suitable_for.append('analysis')
            score += 0.15
        
        # Size-based warnings
        if size_gb < 2:
            warnings.append('Very small model - may have weak reasoning')
            score -= 0.2
        elif size_gb < 4:
            warnings.append('Small model - adequate for basic analysis')
        elif size_gb > 15:
            warnings.append('Large model - may be slower for real-time use')
            score -= 0.1
        
        # If no specific strengths identified
        if not suitable_for:
            suitable_for.append('general')
            warnings.append('Unknown model - suitability uncertain')
        
        return ModelRecommendation(
            model_name=model_info.name,
            suitable_for=suitable_for,
            warnings=warnings,
            score=max(0.0, min(1.0, score))  # Clamp to 0-1
        )
    
    async def get_recommendations(self) -> Dict[str, Any]:
        """Get model discovery and recommendations."""
        models = await self.discover_models()
        
        if not models:
            return {
                'available_models': [],
                'recommendations': [],
                'status': 'no_models_found',
                'message': 'No Ollama models detected. Install models with: ollama pull llama3:8b'
            }
        
        recommendations = [self.evaluate_model(m) for m in models]
        recommendations.sort(key=lambda r: r.score, reverse=True)
        
        # Find best model for each task
        best_for_analysis = None
        best_for_rewriting = None
        best_for_inline = None
        
        for rec in recommendations:
            if not best_for_analysis and 'analysis' in rec.suitable_for:
                best_for_analysis = rec.model_name
            if not best_for_rewriting and 'rewriting' in rec.suitable_for:
                best_for_rewriting = rec.model_name
            if not best_for_inline and 'inline_checks' in rec.suitable_for:
                best_for_inline = rec.model_name
        
        return {
            'available_models': [m.to_dict() for m in models],
            'recommendations': [r.to_dict() for r in recommendations],
            'status': 'ok',
            'best_models': {
                'analysis': best_for_analysis,
                'rewriting': best_for_rewriting,
                'inline_checks': best_for_inline
            }
        }


class RuleBasedProvider(AIProvider):
    """Rule-based fallback provider that doesn't require external AI."""
    
    def __init__(self):
        """Initialize rule-based provider."""
        self._rules = self._load_rules()
    
    @property
    def name(self) -> str:
        return "rule-based"
    
    async def is_available(self) -> bool:
        """Rule-based provider is always available."""
        return True
    
    async def generate_suggestions(self, vague_phrase: VaguePhrase, context: str) -> List[Suggestion]:
        """Generate suggestions using predefined rules."""
        phrase_lower = vague_phrase.original_text.lower().strip()
        vague_type = vague_phrase.vague_type
        context_lower = context.lower()
        
        suggestions = []
        
        # Extract context around the phrase for smarter suggestions
        start = max(0, vague_phrase.start_position - 50)
        end = min(len(context), vague_phrase.end_position + 50)
        surrounding = context[start:end].lower()
        
        # Context-aware replacements based on surrounding words
        context_hints = {
            'make it': {
                'good': 'optimize it',
                'better': 'enhance it',
                'secure': 'secure it',
                'fast': 'optimize it',
                'automatic': 'automate it'
            },
            'it': {
                'feature': 'the feature',
                'bot': 'the bot',
                'function': 'the function',
                'component': 'the component',
                'code': 'the code'
            },
            'good': {
                'make': 'effective',
                'very': 'excellent',
                'bot': 'responsive',
                'feature': 'user-friendly'
            }
        }
        
        # Try to find context-aware suggestion
        if phrase_lower in context_hints:
            for keyword, replacement in context_hints[phrase_lower].items():
                if keyword in surrounding:
                    suggestions.append(Suggestion.create(
                        improved_text=replacement,
                        rationale=f"More specific based on context",
                        improvement_type=ImprovementType.SPECIFICITY,
                        original_phrase=vague_phrase.original_text,
                        confidence=0.85
                    ))
                    break
        
        # If no context match, use rule-based suggestions
        if not suggestions:
            type_rules = self._rules.get(vague_type, {})
            
            # Look for specific phrase rules first
            if phrase_lower in type_rules:
                rules = type_rules[phrase_lower]
            else:
                # Use general rules for this type
                rules = type_rules.get('general', [])
            
            # Generate suggestions from rules
            for rule in rules[:2]:  # Max 2 suggestions
                suggestion = Suggestion.create(
                    improved_text=rule['replacement'],
                    rationale=rule['rationale'],
                    improvement_type=ImprovementType(rule['type']),
                    original_phrase=vague_phrase.original_text,
                    confidence=rule.get('confidence', 0.6)
                )
                suggestions.append(suggestion)
        
        # If no suggestions generated, provide context-aware fallback
        if not suggestions:
            # Generate simple context-aware suggestion
            context_suggestions = {
                'it': ['the component', 'the function', 'the feature'],
                'this': ['this component', 'this feature', 'this module'],
                'that': ['that feature', 'that function', 'that module'],
                'the bot': ['the chatbot', 'the AI assistant', 'the automation script'],
                'the feature': ['the login feature', 'the search feature', 'the export feature'],
                'good': ['well-structured', 'effective', 'robust'],
                'better': ['more efficient', 'more reliable', 'more maintainable'],
                'make it': ['implement it', 'create it', 'develop it']
            }
            
            replacement = context_suggestions.get(phrase_lower, [f'specific {phrase_lower}'])[0]
            suggestions.append(Suggestion.create(
                improved_text=replacement,
                rationale=f"Use specific term instead of vague '{phrase_lower}'",
                improvement_type=ImprovementType.SPECIFICITY,
                original_phrase=vague_phrase.original_text,
                confidence=0.6
            ))
        
        return suggestions
    
    def _load_rules(self) -> Dict[Any, Dict[str, List[Dict[str, Any]]]]:
        """Load rule-based suggestions."""
        from .engine import VagueType
        
        return {
            VagueType.GENERIC_TERM: {
                'a new feature': [
                    {
                        'replacement': 'a user authentication system',
                        'rationale': 'Specify exactly what feature (e.g., authentication, search, export)',
                        'type': 'specificity',
                        'confidence': 0.9
                    },
                    {
                        'replacement': 'a data export function',
                        'rationale': 'Name the specific feature you want to add',
                        'type': 'specificity',
                        'confidence': 0.9
                    },
                    {
                        'replacement': 'a real-time notification system',
                        'rationale': 'Define the feature with concrete details',
                        'type': 'specificity',
                        'confidence': 0.9
                    }
                ],
                'my code': [
                    {
                        'replacement': 'the UserController.js file',
                        'rationale': 'Specify which file or module you\'re referring to',
                        'type': 'context',
                        'confidence': 0.9
                    },
                    {
                        'replacement': 'the authentication module',
                        'rationale': 'Name the specific component or module',
                        'type': 'context',
                        'confidence': 0.9
                    },
                    {
                        'replacement': 'the backend API endpoints',
                        'rationale': 'Identify the specific part of the codebase',
                        'type': 'context',
                        'confidence': 0.9
                    }
                ],
                'the code': [
                    {
                        'replacement': 'the React component',
                        'rationale': 'Specify which part of the code you mean',
                        'type': 'context',
                        'confidence': 0.9
                    },
                    {
                        'replacement': 'the API handler function',
                        'rationale': 'Identify the specific code section',
                        'type': 'context',
                        'confidence': 0.9
                    }
                ],
                'something': [
                    {
                        'replacement': 'a specific example',
                        'rationale': 'Replace vague "something" with concrete request',
                        'type': 'specificity',
                        'confidence': 0.8
                    },
                    {
                        'replacement': 'detailed information',
                        'rationale': 'Make the request more precise',
                        'type': 'clarity',
                        'confidence': 0.7
                    },
                    {
                        'replacement': 'a comprehensive analysis',
                        'rationale': 'Specify the type of content needed',
                        'type': 'specificity',
                        'confidence': 0.9
                    }
                ],
                'stuff': [
                    {
                        'replacement': 'specific items',
                        'rationale': 'Replace "stuff" with precise description',
                        'type': 'specificity',
                        'confidence': 0.8
                    },
                    {
                        'replacement': 'relevant details',
                        'rationale': 'Make the request more focused',
                        'type': 'clarity',
                        'confidence': 0.7
                    }
                ],
                'things': [
                    {
                        'replacement': 'specific elements',
                        'rationale': 'Replace "things" with concrete terms',
                        'type': 'specificity',
                        'confidence': 0.8
                    },
                    {
                        'replacement': 'key points',
                        'rationale': 'Focus on important aspects',
                        'type': 'clarity',
                        'confidence': 0.7
                    }
                ]
            },
            VagueType.SUBJECTIVE_QUALIFIER: {
                'good': [
                    {
                        'replacement': 'well-structured',
                        'rationale': 'Replace subjective "good" with specific quality',
                        'type': 'specificity',
                        'confidence': 0.8
                    },
                    {
                        'replacement': 'comprehensive',
                        'rationale': 'Define what makes it good',
                        'type': 'precision',
                        'confidence': 0.9
                    },
                    {
                        'replacement': 'professional',
                        'rationale': 'Specify the quality standard',
                        'type': 'clarity',
                        'confidence': 0.8
                    }
                ],
                'better': [
                    {
                        'replacement': 'more detailed',
                        'rationale': 'Specify how to improve',
                        'type': 'specificity',
                        'confidence': 0.8
                    },
                    {
                        'replacement': 'more efficient',
                        'rationale': 'Define improvement criteria',
                        'type': 'precision',
                        'confidence': 0.7
                    }
                ],
                'nice': [
                    {
                        'replacement': 'elegant',
                        'rationale': 'Replace vague "nice" with specific quality',
                        'type': 'specificity',
                        'confidence': 0.7
                    },
                    {
                        'replacement': 'user-friendly',
                        'rationale': 'Specify what makes it nice',
                        'type': 'clarity',
                        'confidence': 0.8
                    }
                ],
                'interesting': [
                    {
                        'replacement': 'comprehensive',
                        'rationale': 'Replace vague "interesting" with specific quality',
                        'type': 'specificity',
                        'confidence': 0.7
                    },
                    {
                        'replacement': 'detailed',
                        'rationale': 'Specify what makes it interesting',
                        'type': 'clarity',
                        'confidence': 0.8
                    },
                    {
                        'replacement': 'informative',
                        'rationale': 'Make the content more specific',
                        'type': 'specificity',
                        'confidence': 0.8
                    }
                ],
                'general': [
                    {
                        'replacement': 'specific',
                        'rationale': 'Replace vague qualifier with specific term',
                        'type': 'specificity',
                        'confidence': 0.6
                    },
                    {
                        'replacement': 'well-defined',
                        'rationale': 'Use more precise description',
                        'type': 'clarity',
                        'confidence': 0.6
                    }
                ]
            },
            VagueType.WEAK_INSTRUCTION: {
                'want to add': [
                    {
                        'replacement': 'Add',
                        'rationale': 'Replace weak "want to add" with direct imperative',
                        'type': 'strength',
                        'confidence': 0.9
                    },
                    {
                        'replacement': 'Implement',
                        'rationale': 'Use stronger action verb for clarity',
                        'type': 'strength',
                        'confidence': 0.9
                    },
                    {
                        'replacement': 'Create',
                        'rationale': 'Direct command is more effective than expressing desire',
                        'type': 'strength',
                        'confidence': 0.9
                    }
                ],
                'want to': [
                    {
                        'replacement': 'Create',
                        'rationale': 'Replace weak "want to" with direct action',
                        'type': 'strength',
                        'confidence': 0.9
                    },
                    {
                        'replacement': 'Build',
                        'rationale': 'Use imperative form for clearer instruction',
                        'type': 'strength',
                        'confidence': 0.9
                    }
                ],
                'need to': [
                    {
                        'replacement': 'Must',
                        'rationale': 'Replace "need to" with stronger requirement',
                        'type': 'strength',
                        'confidence': 0.8
                    },
                    {
                        'replacement': 'Should',
                        'rationale': 'Use direct modal verb',
                        'type': 'strength',
                        'confidence': 0.8
                    }
                ],
                'try to': [
                    {
                        'replacement': 'Create',
                        'rationale': 'Replace weak "try to" with direct command',
                        'type': 'strength',
                        'confidence': 0.9
                    },
                    {
                        'replacement': 'Generate',
                        'rationale': 'Use action verb instead of tentative language',
                        'type': 'strength',
                        'confidence': 0.9
                    }
                ],
                'maybe': [
                    {
                        'replacement': '',
                        'rationale': 'Remove uncertain "maybe" for clearer instruction',
                        'type': 'strength',
                        'confidence': 0.8
                    },
                    {
                        'replacement': 'Consider',
                        'rationale': 'Replace with more definitive instruction',
                        'type': 'strength',
                        'confidence': 0.7
                    }
                ]
            },
            VagueType.IMPRECISE_QUANTITY: {
                'some': [
                    {
                        'replacement': '3-5',
                        'rationale': 'Replace "some" with specific range',
                        'type': 'precision',
                        'confidence': 0.8
                    },
                    {
                        'replacement': 'several',
                        'rationale': 'Use more precise quantity indicator',
                        'type': 'precision',
                        'confidence': 0.6
                    }
                ],
                'many': [
                    {
                        'replacement': 'at least 10',
                        'rationale': 'Replace "many" with minimum threshold',
                        'type': 'precision',
                        'confidence': 0.8
                    },
                    {
                        'replacement': 'multiple',
                        'rationale': 'Use clearer quantity term',
                        'type': 'clarity',
                        'confidence': 0.6
                    }
                ],
                'few': [
                    {
                        'replacement': '2-3',
                        'rationale': 'Replace "few" with specific range',
                        'type': 'precision',
                        'confidence': 0.9
                    }
                ]
            },
            VagueType.MISSING_EXAMPLES: {
                'classify': [
                    {
                        'replacement': 'classify (example: "urgent" → Priority 1, "later" → Priority 3)',
                        'rationale': 'Add few-shot examples to clarify classification criteria',
                        'type': 'clarity',
                        'confidence': 0.9
                    },
                    {
                        'replacement': 'classify. Examples:\nInput: "urgent bug fix" → Output: "High Priority"\nInput: "minor typo" → Output: "Low Priority"',
                        'rationale': 'Use few-shot learning with input-output pairs',
                        'type': 'specificity',
                        'confidence': 0.95
                    }
                ],
                'extract': [
                    {
                        'replacement': 'extract. Example: From "Email: user@example.com, Phone: 555-1234" extract {"email": "user@example.com", "phone": "555-1234"}',
                        'rationale': 'Provide one-shot example showing desired format',
                        'type': 'clarity',
                        'confidence': 0.9
                    }
                ],
                'general': [
                    {
                        'replacement': '[task]. Example: [show expected input/output]',
                        'rationale': 'Add examples using few-shot prompting technique',
                        'type': 'clarity',
                        'confidence': 0.85
                    }
                ]
            },
            VagueType.MISSING_REASONING: {
                'explain': [
                    {
                        'replacement': 'explain step-by-step',
                        'rationale': 'Use Chain of Thought (CoT) prompting for better reasoning',
                        'type': 'strength',
                        'confidence': 0.9
                    },
                    {
                        'replacement': 'explain. Think through this step by step:\n1. First identify...\n2. Then analyze...\n3. Finally conclude...',
                        'rationale': 'Structure reasoning with explicit CoT steps',
                        'type': 'specificity',
                        'confidence': 0.95
                    }
                ],
                'analyze': [
                    {
                        'replacement': 'analyze. Break this down:\n1. Identify key components\n2. Examine relationships\n3. Draw conclusions',
                        'rationale': 'Apply Chain of Thought for complex analysis',
                        'type': 'specificity',
                        'confidence': 0.9
                    }
                ],
                'solve': [
                    {
                        'replacement': 'solve. Show your reasoning:\n1. Understand the problem\n2. List known information\n3. Work through solution step-by-step\n4. Verify answer',
                        'rationale': 'Use step-by-step CoT for problem solving',
                        'type': 'specificity',
                        'confidence': 0.95
                    }
                ],
                'general': [
                    {
                        'replacement': '[task]. Let\'s think through this step by step:',
                        'rationale': 'Trigger Chain of Thought reasoning',
                        'type': 'strength',
                        'confidence': 0.85
                    }
                ]
            },
            VagueType.MISSING_STRUCTURE: {
                'debug': [
                    {
                        'replacement': 'debug using this process:\n1. Observe: [describe symptoms]\n2. Thought: [analyze what could cause this]\n3. Action: [test hypothesis]\n4. Repeat until resolved',
                        'rationale': 'Apply ReAct pattern (Reasoning + Acting) for debugging',
                        'type': 'specificity',
                        'confidence': 0.95
                    }
                ],
                'plan': [
                    {
                        'replacement': 'create a plan. Consider multiple approaches:\nApproach A: [pros/cons]\nApproach B: [pros/cons]\nApproach C: [pros/cons]\nRecommended: [best option with reasoning]',
                        'rationale': 'Use Tree of Thoughts to explore multiple solutions',
                        'type': 'specificity',
                        'confidence': 0.9
                    }
                ],
                'multiple solutions': [
                    {
                        'replacement': 'generate 3 alternative solutions, evaluate each:\nSolution 1: [description] - Pros: [...] Cons: [...]\nSolution 2: [description] - Pros: [...] Cons: [...]\nSolution 3: [description] - Pros: [...] Cons: [...]',
                        'rationale': 'Use Tree of Thoughts (ToT) to explore solution space',
                        'type': 'specificity',
                        'confidence': 0.95
                    }
                ],
                'general': [
                    {
                        'replacement': '[task]. Use structured approach:\nThought: [reasoning]\nAction: [what to do]\nObservation: [result]',
                        'rationale': 'Apply ReAct framework for systematic problem solving',
                        'type': 'specificity',
                        'confidence': 0.85
                    }
                ]
            },
            VagueType.AMBIGUOUS_TASK: {
                'general': [
                    {
                        'replacement': 'create a user authentication feature',
                        'rationale': 'Specify the exact action and target clearly',
                        'type': 'clarity',
                        'confidence': 0.8
                    },
                    {
                        'replacement': 'analyze the login errors and fix them',
                        'rationale': 'State clear action verb with specific object',
                        'type': 'specificity',
                        'confidence': 0.8
                    },
                    {
                        'replacement': 'refactor the payment processing code',
                        'rationale': 'Use concrete action with specific target',
                        'type': 'clarity',
                        'confidence': 0.8
                    }
                ]
            }
        }