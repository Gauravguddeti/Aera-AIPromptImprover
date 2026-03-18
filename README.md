# Aera - AI Prompt Improver

**"Grammarly for AI prompts"** - A real-time prompt enhancement tool that helps you write clearer, more effective AI prompts through intelligent suggestions and context-aware improvements.

## ✨ Features

- 🎯 **Real-time Analysis** - Detects vague phrases as you type with 300ms debouncing
- 💡 **AI-Powered Suggestions** - Powered by **Groq (Llama-3-70b)** for high-quality, instant replacements
- 🔒 **Private & Secure** - Flexible architecture supports both local (Ollama) and secure cloud (Groq) providers
- ⚡ **Lightning Fast** - Sub-second analysis powered by Groq's LPU
- 🎨 **Grammarly-like UX** - Hover-based tooltips, smooth animations, inline suggestions
- ⌨️ **Undo Support** - Ctrl+Z to revert any applied suggestion

## 🧠 What It Detects

| Type | Example | Suggestion |
|------|---------|------------|
| Generic Terms | "the bot", "the feature" | "the chatbot", "the login feature" |
| Subjective | "good", "better" | "effective", "more efficient" |
| Vague Actions | "make it", "improve it" | "optimize it", "enhance it" |
| Missing Context | "it", "this" | "the component", "this feature" |
| Weak Instructions | "try to", "maybe" | "implement", "ensure" |
| Missing Examples | "classify emails" | "classify emails as spam/not spam" |

## 🏗️ Architecture

```
aera/
├── backend/          # Python FastAPI (Groq Integrated)
│   ├── src/
│   │   ├── api/      # REST & WebSocket endpoints
│   │   ├── libs/     # Standalone libraries
│   │   │   └── suggestion_engine/  # AI suggestions (Groq/Ollama)
│   │   └── config.py # Environment configuration
│   └── tests/        # Contract/integration/unit tests
│
├── frontend/         # React + Vite web interface
│   └── src/
│       ├── components/  # Editor & Tooltips
│       └── App.jsx      # Main Application
│
└── start.ps1         # One-click startup script
```

### Tech Stack

**Backend**: Python 3.11, FastAPI, Groq Client, Pydantic  
**Frontend**: React 18.2, Vite, Vanilla CSS3  
**AI Model**: Llama-3-70b (via Groq API)

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Groq API Key

### Installation

**1. Clone & Setup:**
```bash
git clone https://github.com/Gauravguddeti/Aera-AIPromptImprover
cd aera

# Create Python virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows

# Install backend dependencies
pip install -r backend/requirements.txt
```

**2. Configure Environment:**
Create `backend/.env` file:
```env
GROQ_API_KEY=your_api_key_here
GROQ_MODEL=llama3-70b-8192
```

**3. Install Frontend:**
```bash
cd frontend
npm install
cd ..
```

### Running the Application

```bash
# Terminal 1 - Backend
cd backend
python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2 - Frontend
cd frontend
npm run dev -- --host 0.0.0.0 --port 3000
```

**Access the app:**
- Frontend: http://localhost:3000

## 🔮 Future Roadmap & Improvements

### Advanced AI Integrations
- **NLP-Based Detection**: Using a small local NLP model (like spaCy or gliner) instead of simple regex to detect vague phrases, reducing false positives and saving LLM calls.
- **Few-Shot Learning**: Dynamically construct prompts with examples from the user's past improvements to tailor suggestions.
- **RLHF (User Feedback Loop)**: Add "Thumbs Up/Down" on suggestions to fine-tune the ranking algorithm based on user preference.

### UX Improvements
- **Prompt Templates**: Library of best-practice prompts for Coding, Writing, and Data Analysis.
- **Diff View**: Show "Before vs After" comparison of the entire prompt.
- **Tone Adjustment**: Toggle between "Professional", "Creative", or "Concise" suggestion modes.

### Technical Enhancements
- **Hybrid Mode**: Fallback to local Ollama if internet connection is lost.
- **Plugin System**: Export as VS Code extension or Browser Extension.