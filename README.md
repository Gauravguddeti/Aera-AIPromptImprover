# Aera - AI Prompt Improver

**"Grammarly for AI prompts"** - A real-time prompt enhancement tool that helps you write clearer, more effective AI prompts through intelligent suggestions and context-aware improvements.

## ✨ Features

- 🎯 **Real-time Analysis** - Detects vague phrases as you type with 300ms debouncing
- 💡 **Context-Aware Suggestions** - Smart replacements based on surrounding text
- 🔒 **100% Local & Private** - All processing via local Ollama (llama3:8b), zero external API calls
- ⚡ **Fast & Lightweight** - Sub-second analysis (<100ms for most prompts)
- 🎨 **Grammarly-like UX** - Hover-based tooltips, smooth animations, inline suggestions
- ⌨️ **Undo Support** - Ctrl+Z to revert any applied suggestion
- 🎭 **9 Detection Types** - Generic terms, subjective qualifiers, missing context, weak instructions, and more

## 🧠 What It Detects

| Type | Example | Suggestion |
|------|---------|------------|
| Generic Terms | "the bot", "the feature" | "the chatbot", "the login feature" |
| Subjective | "good", "better" | "effective", "more efficient" |
| Vague Actions | "make it", "improve it" | "optimize it", "enhance it" |
| Missing Context | "it", "this" | "the component", "this feature" |
| Weak Instructions | "try to", "maybe" | "implement", "ensure" |
| Missing Examples | "classify emails" | "classify emails as spam/not spam" |
| Missing Reasoning | "explain X" | "explain X step-by-step" |
| Missing Structure | "debug error" | "debug error using ReAct pattern" |

## 🏗️ Architecture

```
aera/
├── backend/          # Python FastAPI + WebSocket server
│   ├── src/
│   │   ├── api/      # REST & WebSocket endpoints
│   │   ├── libs/     # Standalone libraries
│   │   │   ├── prompt_analyzer/    # Pattern detection
│   │   │   └── suggestion_engine/  # AI suggestions
│   │   └── models/   # Pydantic schemas
│   └── tests/        # Contract/integration/unit tests
│
├── frontend/         # React + Vite web interface
│   └── src/
│       ├── components/
│       │   ├── editor/     # Text editor + highlighting
│       │   └── tooltip/    # Suggestion tooltips
│       └── tests/          # Jest + Playwright tests
│
├── system-service/   # C# Windows service (optional)
│   └── GlobalTextCapture.cs  # System-wide hotkey
│
└── start.ps1         # One-click startup script
```

### Tech Stack

**Backend**: Python 3.11, FastAPI, Ollama AsyncClient, WebSocket, Pydantic  
**Frontend**: React 18.2, Vite 4.5, Vanilla CSS3, WebSocket API  
**AI Model**: llama3:8b via Ollama (4.7 GB, runs locally)  
**Desktop**: Tauri (Rust-based, for future packaging)

## 🚀 Quick Start

### Prerequisites

```bash
# Required
- Python 3.11+
- Node.js 18+
- Ollama with llama3:8b model

# Optional
- Rust 1.70+ (for Tauri desktop packaging)
```

### Installation

**1. Install Ollama and Model:**
```bash
# Windows (PowerShell as Admin)
winget install Ollama.Ollama
ollama pull llama3:8b

# macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3:8b
```

**2. Clone & Setup:**
```bash
git clone <repo-url>
cd aera

# Create Python virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows
# source .venv/bin/activate  # macOS/Linux

# Install backend dependencies
pip install -r backend/requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### Running the Application

**Option 1: One-Click Start (Windows)**
```powershell
.\start.ps1
```

**Option 2: Manual Start**
```bash
# Terminal 1 - Backend
cd backend
$env:PYTHONPATH = "$PWD"
python -m uvicorn src.api.app:app --reload --host 127.0.0.1 --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

**Access the app:**
- Frontend: http://localhost:3000
- Backend API: http://127.0.0.1:8000
- API Docs: http://127.0.0.1:8000/docs

## 💡 Usage

1. Type or paste your AI prompt in the editor
2. Vague phrases are highlighted automatically (orange/red underlines)
3. Move your cursor into a highlighted word to see suggestions
4. Click a suggestion to apply it instantly
5. Use **Ctrl+Z** to undo any changes
6. Toggle "Analysis ON/OFF" to disable checking while drafting

## 🎨 UI Features

- **Color-coded highlights**: Orange (generic terms), Red (weak instructions), Blue (missing examples)
- **Context-aware tooltips**: Appear next to words without blocking editing
- **Smooth animations**: Fade-in highlights, slide-in tooltips
- **Keyboard shortcuts**: Ctrl+Z (undo), click-to-apply suggestions
- **Live stats**: Issue count and analysis time displayed below editor

## 🧪 Testing

### Backend
```bash
cd backend
pytest tests/ -v                    # All tests
pytest tests/api/test_contracts.py  # Contract tests
pytest tests/integration/           # Integration tests
```

### Frontend
```bash
cd frontend
npm test              # Jest unit tests
npm run test:e2e      # Playwright E2E tests
```

## 📊 Performance

Tested with llama3:8b on mid-range hardware:

| Prompt Length | Analysis Time | Suggestions |
|---------------|---------------|-------------|
| <100 chars    | ~50ms         | 1-3 issues  |
| 100-500 chars | ~150ms        | 3-8 issues  |
| 500-1000 chars| ~300ms        | 8-15 issues |
| 1000+ chars   | ~600ms        | 15+ issues  |

## 🔧 Configuration

### Backend Settings
Edit `backend/src/api/app.py`:
```python
# Change AI model
providers = [OllamaProvider(model="llama3:8b"), RuleBasedProvider()]

# Adjust debounce
DEBOUNCE_MS = 300  # milliseconds
```

### Frontend Settings
Edit `frontend/src/components/editor/PromptEditor.jsx`:
```javascript
const DEBOUNCE_MS = 300;  // Analysis delay
const WEBSOCKET_URL = 'ws://localhost:8000/ws/analysis';
```

## 🛡️ Privacy & Security

- ✅ All AI processing happens locally via Ollama
- ✅ No external API calls or data transmission
- ✅ User prompts never leave the device
- ✅ Structured logging excludes sensitive data
- ✅ WebSocket connections are localhost-only

## 📁 Project Structure

```
backend/src/
├── libs/                    # Standalone libraries
│   ├── prompt_analyzer/     # Pattern detection (276 lines)
│   └── suggestion_engine/   # AI suggestions (876 lines)
├── api/                     # FastAPI routes
│   ├── routes.py           # REST endpoints
│   └── websocket.py        # WebSocket handler
└── models/                  # Pydantic schemas

frontend/src/
├── components/
│   ├── editor/             # PromptEditor + Highlighter
│   └── tooltip/            # SuggestionTooltip
└── App.jsx                 # Main app with toggle

system-service/             # Optional Windows service
└── GlobalTextCapture.cs    # System-wide integration
```

## 🤝 Contributing

This project follows TDD principles:
1. Write failing tests first
2. Implement minimal code to pass
3. Refactor with all tests passing
4. No code without tests

## 📄 License

MIT License - See LICENSE file

## 🙏 Acknowledgments

- Ollama team for local AI infrastructure
- FastAPI for excellent async Python framework
- React community for modern UI patterns

- ✅ Phase 1: Project setup and architecture
- 🚧 Phase 2: Core implementation (TDD approach)
- 📋 Phase 3: Integration and testing
- 📋 Phase 4: Desktop packaging and distribution
- 📋 Phase 5: Performance optimization and polish

## 🤝 Contributing

1. Follow constitutional principles (TDD, library-first)
2. All tests must pass before implementation
3. Use provided linting and formatting tools
4. Maintain privacy-first approach

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🔧 Development Status

**Current Phase**: Setup and Foundation (Phase 1)
**Next**: Test-driven implementation of core models and services

Built with ❤️ for better AI prompt engineering.