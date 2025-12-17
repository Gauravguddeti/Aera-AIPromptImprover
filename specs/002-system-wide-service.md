# Aera System-Wide AI Prompt Enhancement Service

## Vision: Universal Prompt Intelligence
Transform Aera into a system-wide background service that provides AI-powered prompt suggestions across **all applications** on Windows - from WhatsApp and Discord to email clients, code editors, and browsers.

## Core Architecture

### Background Service Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    System Tray Application                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Tray Icon     │  │  Settings UI    │  │  Quick Stats │ │
│  │   (Toggle)      │  │  (Preferences)  │  │  (Overlay)   │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                  Global Input Hook Service                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  Text Capture   │  │  Context        │  │  UI Overlay  │ │
│  │  (Low-level     │  │  Detection      │  │  (Underlines │ │
│  │   keyboard)     │  │  (App aware)    │  │   & popups)  │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend Analysis Engine                  │
│         (Same FastAPI service we just built)               │
└─────────────────────────────────────────────────────────────┘
```

## Key Features

### 1. **Smart Context Awareness**
- **Application Detection**: Recognize current app (WhatsApp, email, code editor)
- **Content Type Recognition**: Distinguish between chat messages, emails, code comments, documents
- **User Intent Analysis**: Detect when user is writing vs reading
- **Trigger Conditions**: Only activate when typing in text fields

### 2. **Non-Intrusive UI Modes**

#### **Passive Mode (Default)**
- Show subtle underlines for vague phrases
- No popups unless user hovers/clicks
- Minimal visual interference

#### **Active Mode (On-Demand)**
- Keyboard shortcut (e.g., `Ctrl+Shift+A`) to trigger suggestions
- Right-click context menu integration
- Instant popup with improvements

#### **Silent Mode**
- Background analysis only
- No visual indicators
- Data collection for learning user patterns

### 3. **Universal Text Field Integration**

#### **Supported Input Methods**
- Standard Windows text boxes (Edit controls)
- Rich text editors (Word, Outlook, etc.)
- Web browser text areas (Gmail, WhatsApp Web, etc.)
- Chat applications (Discord, Slack, WhatsApp Desktop)
- Code editors (VS Code, Notepad++, etc.)

#### **Technical Implementation**
```
Windows API Hooks:
├── SetWindowsHookEx(WH_KEYBOARD_LL) - Global keyboard capture
├── GetForegroundWindow() - Active window detection  
├── GetWindowText() - Window title/app identification
├── AccessibleObjectFromWindow() - UI Automation for text access
└── SetWinEventHook() - Text change notifications
```

### 4. **Smart Filtering & Context Rules**

#### **Application Whitelist/Blacklist**
```json
{
  "enabled_apps": [
    "WhatsApp.exe",
    "OUTLOOK.EXE", 
    "notepad.exe",
    "Code.exe",
    "chrome.exe",
    "firefox.exe"
  ],
  "disabled_apps": [
    "PasswordSafe.exe",
    "KeePass.exe",
    "banking_app.exe"
  ],
  "context_rules": {
    "chat_apps": {
      "mode": "passive_underlines_only",
      "trigger_length": 10,
      "delay_ms": 1000
    },
    "email_apps": {
      "mode": "active_suggestions", 
      "trigger_length": 5,
      "delay_ms": 500
    },
    "code_editors": {
      "mode": "comment_detection_only",
      "file_types": [".md", ".txt", ".py", ".js"],
      "ignore_code_blocks": true
    }
  }
}
```

### 5. **System Tray Integration**

#### **Tray Icon States**
- 🟢 **Active**: Service running, suggestions enabled
- 🟡 **Passive**: Service running, underlines only
- 🔴 **Disabled**: Service paused
- ⚫ **Silent**: Background learning mode

#### **Right-Click Menu**
```
Aera AI Assistant
├── 🟢 Enable Suggestions
├── 🟡 Passive Mode (underlines only)  
├── 🔴 Disable for 1 hour
├── ⚙️  Settings...
├── 📊 Today's Stats (23 improvements suggested)
├── 🎯 Current App: WhatsApp (Enabled)
└── ❌ Exit
```

### 6. **Privacy-First Design**

#### **Local Processing Only**
- All AI analysis happens locally (existing Ollama backend)
- No text data sent to external servers
- Optional telemetry (anonymized usage stats only)

#### **Security Measures**
- Exclude password fields automatically
- Respect Windows credential UI patterns
- User-defined sensitive app exclusions
- Encrypted local storage for settings

## Technical Implementation Plan

### Phase 1: Core Service Foundation
1. **Windows Service Setup**
   - Create Windows Service wrapper around FastAPI backend
   - System tray application with basic controls
   - Low-level keyboard hook for text capture

2. **Text Extraction Engine** 
   - Windows UI Automation integration
   - Text field detection and content extraction
   - Real-time typing detection

3. **Basic Overlay System**
   - Transparent overlay windows
   - Underline rendering over detected text
   - Simple popup suggestions

### Phase 2: Smart Context Detection
1. **Application Awareness**
   - Process detection and identification
   - Window title and content analysis
   - Context-specific rule engine

2. **Content Type Recognition**
   - Email vs chat vs document detection
   - Code vs natural language identification
   - User intent pattern learning

### Phase 3: Advanced Features
1. **Multi-Application Testing**
   - WhatsApp Desktop integration
   - Browser extension companion
   - Office suite compatibility

2. **Performance Optimization**
   - Debounced analysis (avoid lag while typing)
   - Intelligent caching
   - Minimal resource usage

### Phase 4: Polish & Distribution
1. **User Experience**
   - Smooth animations
   - Customizable hotkeys
   - Theme integration (dark/light mode)

2. **Installation & Updates**
   - Silent installer
   - Auto-update mechanism
   - Uninstall cleanup

## Configuration Examples

### **WhatsApp Chat Mode**
```json
{
  "app": "WhatsApp.exe",
  "mode": "passive",
  "settings": {
    "show_underlines": true,
    "popup_on_hover": false,
    "popup_on_click": true,
    "min_text_length": 15,
    "analysis_delay_ms": 2000,
    "suggestions_on_shortcut": "Ctrl+Space"
  }
}
```

### **Email Composition Mode**
```json
{
  "app": "OUTLOOK.EXE", 
  "mode": "active",
  "settings": {
    "show_underlines": true,
    "popup_on_hover": true,
    "real_time_suggestions": true,
    "min_text_length": 5,
    "analysis_delay_ms": 500,
    "professional_tone_bias": true
  }
}
```

## Technical Challenges & Solutions

### Challenge 1: **Text Extraction Across Apps**
- **Problem**: Different apps use different text rendering methods
- **Solution**: Multi-layered approach with UI Automation, accessibility APIs, and OCR fallback

### Challenge 2: **Performance Impact**
- **Problem**: Real-time analysis could slow down typing
- **Solution**: Asynchronous processing, intelligent debouncing, and local caching

### Challenge 3: **Security & Privacy**
- **Problem**: Users typing sensitive information
- **Solution**: Smart exclusion patterns, user-controlled whitelist, and local-only processing

### Challenge 4: **Visual Integration**
- **Problem**: Overlays looking out of place in different apps
- **Solution**: Theme-aware rendering and minimal visual footprint

## Development Stack

### **System Integration Layer**
- **Language**: C# (.NET 6+) for Windows API integration
- **Frameworks**: Windows Forms/WPF for tray app, Win32 APIs for hooks
- **Libraries**: UIAutomation, Accessibility APIs

### **Backend Service** 
- **Language**: Python (existing FastAPI backend)
- **AI Processing**: Ollama (existing Mistral integration)
- **IPC**: Named pipes or HTTP for C# ↔ Python communication

### **Overlay & UI**
- **Rendering**: Direct2D or WPF for smooth overlays
- **Animations**: Hardware-accelerated transitions
- **Theming**: Windows 11 design system integration

## Success Metrics

### **User Experience**
- < 100ms response time for underline rendering
- < 500ms for suggestion popup display
- < 2% CPU usage during idle periods
- Zero text input lag or interference

### **Functionality**
- 95%+ text field detection accuracy across major apps
- Support for top 20 most-used Windows applications
- Privacy: 0% data transmission to external servers

This system-wide approach would make Aera incredibly powerful - imagine having AI-powered writing assistance available everywhere you type, from casual WhatsApp messages to important emails, all while maintaining complete privacy through local processing.

Would you like me to start implementing any specific part of this system-wide architecture?