# GitHub Copilot Instructions: Aera AI Prompt Enhancement Tool

## Project Overview
Aera is a desktop application that provides real-time AI-powered suggestions to improve prompt clarity and effectiveness. Think "Grammarly for AI prompts" - it detects vague phrases and offers specific improvements while maintaining complete privacy through local processing.

## Architecture & Technology Stack

### Backend (Python)
- **Framework**: FastAPI with async/await for real-time processing
- **AI Integration**: Ollama client for local Mistral 8B model
- **Communication**: REST APIs + WebSocket for real-time analysis
- **Testing**: pytest with TDD approach (tests before implementation)

### Frontend (JavaScript)
- **UI**: Vanilla JavaScript/TypeScript with modern CSS3
- **Communication**: WebSocket for real-time + fetch for REST calls
- **Editor**: Custom text editor with overlay system for underlines/tooltips
- **Testing**: Jest for unit tests, Playwright for E2E

### Desktop Packaging
- **Framework**: Tauri (Rust-based, lightweight alternative to Electron)
- **Distribution**: Cross-platform (Windows/macOS/Linux)
- **Security**: Local-only processing, no external API calls

## Constitutional Principles (CRITICAL)

### 1. Test-Driven Development (NON-NEGOTIABLE)
- **RED-GREEN-Refactor cycle strictly enforced**
- Write failing tests FIRST, then implement to make them pass
- Order: Contract tests → Integration tests → E2E tests → Unit tests
- Never implement without failing tests first

### 2. Library-First Architecture
- Every feature starts as a standalone library
- Libraries must be self-contained and independently testable
- Clear CLI interface for each library (--help, --version, --format)
- Example libraries:
  - `prompt-analyzer`: Detects vague phrases
  - `suggestion-engine`: Generates improvements via Mistral
  - `ui-components`: Editor, tooltip, toggle components

### 3. Simplicity & Direct Patterns
- Use frameworks directly (FastAPI, no wrapper classes)
- Single data model (no DTOs unless serialization differs)
- Avoid patterns like Repository/UoW without proven need
- Maximum 3 projects: backend, frontend, desktop wrapper

### 4. Privacy & Local Processing
- ALL AI processing happens locally via Ollama
- NO external API calls or data transmission
- User prompts never leave the device
- Structured logging for debugging but no sensitive data

## Key Implementation Patterns

### Real-time Analysis Flow
```python
# Backend: WebSocket handler
@app.websocket("/ws/analysis")
async def analysis_websocket(websocket: WebSocket):
    await websocket.accept()
    while True:
        text = await websocket.receive_text()
        suggestions = await analyze_prompt_with_ollama(text)
        await websocket.send_json(suggestions)

# Debounced analysis to avoid excessive processing
async def analyze_prompt_with_ollama(text: str) -> List[Suggestion]:
    response = await ollama.AsyncClient().chat(
        model='mistral:8b',
        messages=[{'role': 'user', 'content': f"Analyze: {text}"}]
    )
    return parse_vague_phrases(response['message']['content'])
```

### Frontend Text Analysis
```javascript
// Debounced analysis with caching
class TextAnalyzer {
    constructor() {
        this.debounceMs = 300;
        this.cache = new Map();
        this.ws = new WebSocket('ws://localhost:8000/ws/analysis');
    }
    
    analyzeText = debounce(async (text) => {
        if (this.cache.has(text)) return this.cache.get(text);
        
        this.ws.send(JSON.stringify({
            type: 'analyze',
            data: { content: text }
        }));
    }, this.debounceMs);
}
```

### Error Handling Pattern
```python
# Graceful degradation when Ollama unavailable
async def safe_analyze_prompt(text: str) -> AnalysisResult:
    try:
        return await analyze_with_ollama(text)
    except OllamaConnectionError:
        return AnalysisResult(
            error="AI model temporarily unavailable",
            suggestions=[],
            fallback_mode=True
        )
```

## Data Models & Entities

### Core Entities
```python
@dataclass
class VaguePhrase:
    id: UUID
    start_position: int
    end_position: int
    original_text: str
    vague_type: VagueType  # GENERIC_TERM, MISSING_CONTEXT, etc.
    confidence_score: float

@dataclass
class Suggestion:
    id: UUID
    improved_text: str
    rationale: str
    improvement_type: ImprovementType  # SPECIFICITY, CLARITY, etc.
    confidence_score: float
```

### API Contracts
- REST endpoints: `/api/prompts/analyze`, `/api/suggestions/{id}`, `/api/preferences`
- WebSocket: `/ws/analysis` for real-time communication
- All schemas defined in OpenAPI spec at `/contracts/api-spec.yaml`

## Performance Requirements
- **Short prompts** (<500 chars): <300ms analysis time
- **Long prompts** (up to 4000 chars): <2s analysis time
- **UI responsiveness**: No blocking during analysis
- **Memory usage**: <100MB for application, 4-6GB for AI model

## Testing Strategy

### Contract Tests (Write FIRST)
```python
def test_analyze_prompt_endpoint_contract():
    """MUST FAIL until endpoint implemented"""
    response = client.post("/api/prompts/analyze", json={
        "content": "Write something good"
    })
    assert response.status_code == 200
    assert "vague_phrases" in response.json()
    assert len(response.json()["vague_phrases"]) > 0
```

### Integration Tests
```python
def test_real_ollama_integration():
    """Test with actual Ollama instance"""
    analyzer = PromptAnalyzer()
    result = analyzer.analyze("Write something good about AI")
    assert len(result.vague_phrases) >= 2  # "something" and "good"
    assert result.analysis_time_ms < 2000
```

### E2E Tests (Playwright)
```javascript
test('user can improve vague prompt with suggestions', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.fill('#prompt-editor', 'Write something good');
    await expect(page.locator('.vague-underline')).toHaveCount(2);
    await page.hover('.vague-underline:first-child');
    await expect(page.locator('.suggestion-tooltip')).toBeVisible();
    await page.click('.suggestion-tooltip .suggestion:first-child');
    await expect(page.locator('#prompt-editor')).not.toContainText('something');
});
```

## Code Style & Conventions

### Python (Backend)
- Use `async/await` for all I/O operations
- Type hints required for all function signatures
- Pydantic models for API validation
- Structured logging with JSON format

### JavaScript (Frontend)
- Modern ES2022+ features
- Async/await over Promises.then()
- CSS custom properties for theming
- No framework dependencies unless justified

### File Organization
```
backend/src/
├── models/          # Data classes and validation
├── services/        # Business logic libraries
├── api/            # FastAPI routes and WebSocket handlers
└── tests/          # All test categories

frontend/src/
├── components/     # Reusable UI components
├── services/       # API clients and utilities
└── tests/         # Jest + Playwright tests
```

## Recent Changes & Context
- Project initialized with TDD constitutional principles
- OpenAPI contracts defined for all endpoints
- WebSocket protocol designed for real-time analysis
- Ollama integration pattern researched and documented
- Performance targets established based on user requirements

## Common Tasks & Helpers

When implementing new features:
1. **Start with failing contract test** that defines the expected API
2. **Write integration test** that uses real dependencies (Ollama, WebSocket)
3. **Implement minimal code** to make tests pass
4. **Add unit tests** for edge cases and error conditions
5. **Update OpenAPI spec** if API changes

For debugging:
- Check Ollama status: `ollama list` and `ollama show mistral:8b`
- WebSocket messages visible in browser dev tools
- Structured logs in JSON format for easy parsing
- Health check endpoint at `/health` shows AI model status

Remember: Every piece of code should have a clear purpose, be independently testable, and follow the constitutional principles. Privacy and local processing are non-negotiable requirements.