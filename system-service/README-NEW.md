# Aera System Service

System-wide Windows service that provides AI-powered prompt suggestions across all applications with real-time visual underlines and non-intrusive feedback.

## 🚀 Quick Start

### Prerequisites
- Windows 10/11
- .NET 6.0 Runtime
- Aera FastAPI Backend running (see `../backend/README.md`)

### Build and Install

1. **Build the service:**
   ```bash
   dotnet build --configuration Release
   ```

2. **Install as Windows Service (Administrator required):**
   ```bash
   # Replace [PATH] with actual path to your executable
   sc create "AeraSystemService" binPath="D:\projects\aiprompter\aera\system-service\bin\Release\net6.0-windows\AeraSystemService.exe"
   sc start AeraSystemService
   ```

3. **Quick Test (Tray Mode):**
   ```bash
   # Run directly in tray mode for testing
   .\bin\Release\net6.0-windows\AeraSystemService.exe
   ```

## ✨ Features

### 🎯 System-Wide Text Analysis
- **Global text capture** across all Windows applications
- **WhatsApp, email, and any text field** - works everywhere
- **Privacy-first**: All processing happens locally via Ollama

### 🎨 Visual Feedback
- **Real-time underlines** for vague phrases (red wavy lines)
- **Non-intrusive tooltips** with AI suggestions
- **Transparent overlays** that don't interfere with your workflow

### 🎛️ Smart Control
- **System tray icon** with context menu
- **Multiple modes**:
  - 🟢 **Active**: Full analysis + suggestions
  - 🟡 **Passive**: Underlines only (no interruptions)
  - 🔴 **Disabled**: Temporarily off for 1 hour
  - 🔘 **Silent**: Background analysis only
- **Sensitive app detection**: Automatically pauses for password fields

### 🔒 Privacy & Security
- **Password field exclusion** - never captures sensitive input
- **Sensitive app detection** - banking/security apps automatically excluded
- **Local processing only** - no data leaves your device
- **Configurable sensitivity** for different application types

## 🎛️ Service Modes

| Mode | Visual Underlines | AI Suggestions | Tooltips | Use Case |
|------|------------------|----------------|----------|----------|
| 🟢 Active | ✅ | ✅ | ✅ | Full assistance while writing |
| 🟡 Passive | ✅ | ❌ | ❌ | Quiet awareness of vague text |
| 🔴 Disabled | ❌ | ❌ | ❌ | Temporary break |
| 🔘 Silent | ❌ | ✅ | ❌ | Background learning only |

## 🏗️ Architecture

### Core Components

1. **AeraTrayApplication** - System tray interface and mode control
2. **GlobalTextCapture** - Windows API hooks for text detection
3. **TextOverlayManager** - Transparent underline rendering
4. **AeraBackendClient** - Communication with FastAPI analysis service
5. **TextAnalysisService** - Orchestrates analysis workflow

### System Integration

```
Windows Applications (WhatsApp, Email, etc.)
           ↓ (Global Hooks)
    GlobalTextCapture
           ↓ (Text Events)
    TextAnalysisService
           ↓ (HTTP)
    FastAPI Backend (localhost:8000)
           ↓ (AI Analysis)
    Ollama + Mistral 8B
           ↓ (Suggestions)
    TextOverlayManager
           ↓ (Visual Feedback)
    Transparent Overlays
```

## 🔧 Configuration

### Service Management
```bash
# Check service status
sc query AeraSystemService

# Stop service
sc stop AeraSystemService

# Remove service
sc delete AeraSystemService

# View service logs
Get-EventLog -LogName Application -Source "AeraSystemService" -Newest 10
```

### Backend Connection
- Service connects to FastAPI backend at `http://localhost:8000`
- Health check endpoint: `/health`
- Analysis endpoint: `/api/prompts/analyze`

### Sensitive Applications (Auto-excluded)
- Banking applications (keywords: "bank", "finance", "payment")
- Password managers
- Security applications
- Any field marked as password type

## 🛠️ Development

### Building from Source
```bash
git clone <repo>
cd aera/system-service
dotnet restore
dotnet build
```

### Testing
```bash
# Build and test
.\test-build.bat

# Run in console mode for debugging
dotnet run
```

### Debugging Tips

1. **Check backend connection:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **View real-time logs:**
   ```bash
   # Run in console mode to see logs
   .\bin\Release\net6.0-windows\AeraSystemService.exe --console
   ```

3. **Test global hooks:**
   - Service should detect typing in any application
   - Check Event Viewer for hook installation messages

## 🚨 Troubleshooting

### Service Won't Start
- **Check .NET 6.0 Runtime**: `dotnet --version`
- **Verify backend**: FastAPI must be running on port 8000
- **Administrator rights**: Service installation requires admin privileges

### No Text Detection
- **Windows Security**: Some antivirus may block global hooks
- **Hook installation**: Check Event Viewer for error messages
- **Permissions**: Service needs access to input monitoring

### Missing Underlines
- **Display scaling**: High DPI may affect overlay positioning
- **Graphics drivers**: Update to latest version
- **Transparency support**: Verify Windows composition is enabled

## 📝 Known Limitations

1. **Text Layout Detection**: Simplified character-based positioning (font metrics not yet implemented)
2. **Application Compatibility**: Some applications may not support text extraction
3. **High DPI Scaling**: Overlay positioning may need adjustment on high DPI displays
4. **Performance**: Real-time analysis may impact performance on slower systems

## 🔄 Integration with Backend

This service requires the Aera FastAPI backend to be running. See `../backend/README.md` for setup instructions.

Key endpoints used:
- `GET /health` - Service health check
- `POST /api/prompts/analyze` - Text analysis for vague phrases
- `GET /api/suggestions/{id}` - Retrieve suggestion details

## 📊 Performance Notes

- **Memory usage**: ~50-100MB (excluding AI model)
- **CPU impact**: Minimal when idle, ~5-10% during active analysis
- **Network**: Local HTTP only (no external connections)
- **Startup time**: ~2-3 seconds for hook installation

---

**Next Steps:**
1. Install and test the service with your existing backend
2. Try different modes in the system tray
3. Test across various applications (WhatsApp, email, etc.)
4. Report any issues or feedback!

For backend setup, see: `../backend/README.md`