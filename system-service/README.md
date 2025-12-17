# Aera System Service

A Windows system service that provides AI-powered prompt improvement suggestions across all applications.

## Features

- **System-wide text analysis**: Works with any Windows application (WhatsApp, Outlook, browsers, etc.)
- **Real-time underlines**: Visual indicators for vague phrases
- **Multiple modes**: Active (suggestions), Passive (underlines only), Disabled, Silent
- **System tray integration**: Easy control and status monitoring
- **Privacy-first**: All processing happens locally via the Aera backend service

## Architecture

```
System Tray App (AeraTrayApplication)
    ↓
Global Text Capture (Windows API Hooks)
    ↓
Text Analysis Service (Backend Client)
    ↓
Text Overlay Manager (Visual Feedback)
```

## Components

### Core Services
- **AeraTrayApplication**: System tray interface with mode controls
- **GlobalTextCapture**: Low-level Windows hooks for text detection
- **TextAnalysisService**: Coordinates text analysis with backend
- **TextOverlayManager**: Renders underlines and popups
- **AeraBackendClient**: HTTP client for FastAPI backend

### Service Modes
- 🟢 **Active**: Full suggestions with popups and underlines
- 🟡 **Passive**: Underlines only, click for suggestions
- 🔴 **Disabled**: No visual feedback for 1 hour
- ⚫ **Silent**: Background learning mode only

## Building

```bash
# Build the project
dotnet build AeraSystemService.csproj

# Run as tray application (development)
dotnet run

# Run as Windows Service
dotnet run -- --service
```

## Installation

1. **Prerequisites**: 
   - Windows 10/11
   - .NET 6.0 Runtime
   - Aera backend service running on localhost:8000

2. **Install as Windows Service**:
   ```cmd
   sc create "Aera AI Service" binPath="C:\path\to\AeraSystemService.exe --service"
   sc start "Aera AI Service"
   ```

3. **Run as tray application**:
   ```cmd
   AeraSystemService.exe
   ```

## Configuration

The service automatically detects:
- **Password fields**: Excluded from analysis
- **Sensitive applications**: Banking, password managers (excluded)
- **Code editors**: Different analysis rules
- **Chat vs email contexts**: Mode adjustments

## Privacy & Security

- **No external connections**: All data stays on your device
- **Sensitive app detection**: Automatic exclusion of password managers, banking apps
- **Password field filtering**: Never analyzes password inputs
- **Local processing only**: Uses local Ollama backend

## Supported Applications

- **Chat**: WhatsApp Desktop, Discord, Slack, Teams
- **Email**: Outlook, Thunderbird, web clients
- **Browsers**: Chrome, Firefox, Edge (text areas)
- **Editors**: Notepad++, VS Code, Sublime Text
- **Office**: Word, Excel, PowerPoint
- **Any Windows text control**

## Troubleshooting

### Service won't start
- Check if running as Administrator (required for global hooks)
- Verify backend service is running on localhost:8000
- Check Windows Event Log for errors

### No underlines showing
- Verify current mode (should be Active or Passive)
- Check if current app is in excluded list
- Try switching to different text field

### High CPU usage
- Check analysis delay settings
- Verify debouncing is working (1-second delay)
- Consider switching to Passive mode

## Development

### Testing with specific apps
```csharp
// Test with WhatsApp
var context = new TextContext
{
    ProcessName = "WhatsApp",
    ControlType = "textbox"
};

var result = await analysisService.AnalyzeTextAsync("something good", context);
```

### Adding new application support
1. Update `IsSensitiveApplication()` in GlobalTextCapture
2. Add context rules in `CreateTextContext()`
3. Test with the target application

## API Integration

The service communicates with the Aera FastAPI backend:

```http
POST /api/prompts/analyze
{
  "content": "User typed text",
  "settings": {
    "min_confidence": 0.5,
    "max_suggestions": 5
  }
}
```

Response includes vague phrases with positions for accurate underline placement.

## Future Enhancements

- **Hot keys**: Global shortcuts for manual analysis
- **Custom rules**: User-defined application behaviors
- **Statistics dashboard**: Usage analytics and improvements
- **Voice feedback**: Audio cues for accessibility
- **Theme integration**: Windows 11 design system
- **Multi-language support**: Analysis in different languages