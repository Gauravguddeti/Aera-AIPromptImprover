import logging
import json
from typing import List
from .engine import AIProvider, Suggestion, ImprovementType, VaguePhrase

logger = logging.getLogger(__name__)


NETWORK_ERROR_MARKERS = (
    "timeout",
    "timed out",
    "connection",
    "connect",
    "dns",
    "network",
    "unreachable",
    "name resolution",
    "temporary failure",
    "ssl",
)


def _is_network_error(exc: Exception) -> bool:
    """Return True when an exception likely indicates a network/connectivity failure."""
    message = str(exc).lower()
    return any(marker in message for marker in NETWORK_ERROR_MARKERS)

class GroqProvider(AIProvider):
    """Groq-based AI provider for suggestion generation."""
    
    def __init__(self, api_key: str, model: str = "llama3-8b-8192"):
        """
        Initialize Groq provider.
        
        Args:
            api_key: Groq API Key
            model: Groq model to use (default: llama3-8b-8192)
        """
        self.api_key = api_key
        self.model = model
        self._client = None
    
    @property
    def name(self) -> str:
        return f"groq-{self.model}"
    
    async def is_available(self) -> bool:
        """Check if Groq is available (has API key)."""
        return bool(self.api_key)
    
    async def generate_suggestions(self, vague_phrase: VaguePhrase, context: str) -> List[Suggestion]:
        """Generate suggestions using Groq."""
        if not await self.is_available():
            raise RuntimeError("Groq API key not configured")
        
        try:
            import groq
            
            if self._client is None:
                self._client = groq.AsyncGroq(api_key=self.api_key)
            
            # Create prompt for the AI model
            prompt = self._create_prompt(vague_phrase, context)
            
            # Call Groq API
            chat_completion = await self._client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=self.model,
                temperature=0.7,
            )
            
            response_text = chat_completion.choices[0].message.content
            
            # Parse response
            suggestions = self._parse_response(response_text, vague_phrase)
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating suggestions with Groq: {e}")
            raise
    
    def _create_prompt(self, vague_phrase: VaguePhrase, context: str) -> str:
        """Create a prompt for the AI model (Same as Ollama for consistency)."""
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
        """Parse AI response into Suggestion objects (Reused logic)."""
        try:
            # Log the raw response for debugging
            logger.debug(f"Raw Groq response: {response_text[:200]}...")
            
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
                    confidence=0.9  # Groq suggestions get high confidence
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


class GroqWithOllamaFallbackProvider(AIProvider):
    """Use Groq by default and fallback to Ollama only on network failure."""

    def __init__(
        self,
        api_key: str,
        groq_model: str = "llama3-8b-8192",
        ollama_model: str = "llama3:8b",
        ollama_host: str = "http://localhost:11434",
    ):
        self._groq = GroqProvider(api_key=api_key, model=groq_model)
        # Lazy import avoids circular import since providers.py imports this module.
        from .providers import OllamaProvider
        self._ollama = OllamaProvider(model=ollama_model, host=ollama_host)

    @property
    def name(self) -> str:
        return f"{self._groq.name}-with-ollama-fallback"

    async def is_available(self) -> bool:
        """This provider is available when Groq is configured."""
        return await self._groq.is_available()

    async def generate_suggestions(self, vague_phrase: VaguePhrase, context: str) -> List[Suggestion]:
        """Generate suggestions with Groq first, fallback to Ollama only on network issues."""
        if not await self._groq.is_available():
            raise RuntimeError("Groq provider is not configured")

        try:
            return await self._groq.generate_suggestions(vague_phrase, context)
        except Exception as exc:
            if not _is_network_error(exc):
                raise

            if not await self._ollama.is_available():
                logger.warning(
                    "Groq network failure detected and local Ollama is unavailable; "
                    "falling through to next provider"
                )
                raise

            logger.warning(
                "Groq network failure detected; using local Ollama fallback",
                extra={"error": str(exc), "ollama_model": self._ollama.model},
            )
            return await self._ollama.generate_suggestions(vague_phrase, context)
