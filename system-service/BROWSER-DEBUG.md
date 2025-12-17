# Browser Text Detection Debug Guide

## Testing Text Capture in Browsers

The system service might not be capturing browser text properly. Here's how to debug:

### 1. Run Debug Mode (Administrator Required)
```bash
# Should be running now as Admin - check the console window
```

### 2. Test Different Text Fields

**Easy Test (Notepad)**:
1. Open Notepad
2. Type: "Write something good about this"
3. Watch debug console for detection

**Browser Test (More Complex)**:
1. Open Chrome/Edge
2. Go to: https://www.google.com
3. Click search box
4. Type: "help me fix something important"
5. Watch console

### 3. Common Issues & Solutions

**Issue**: No text detected at all
- **Cause**: Windows hooks not installed (need Admin rights)
- **Solution**: Run as Administrator

**Issue**: Notepad works, browser doesn't
- **Cause**: Browsers use complex text rendering (DOM vs native controls)
- **Solution**: Need different capture method for browsers

**Issue**: Service crashes
- **Cause**: Backend not running or Ollama issues
- **Solution**: Ensure backend is running at localhost:8000

### 4. Browser-Specific Solutions

For browser text capture, we need:
1. **Browser extension** (most reliable)
2. **DOM injection** (complex)
3. **Accessibility API** (what we're trying)

### 5. Quick Test Script

Run this in browser console to test if our backend works:
```javascript
// Test if backend is reachable
fetch('http://localhost:8000/api/prompts/analyze', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ content: 'write something good about this' })
})
.then(r => r.json())
.then(d => console.log('Backend working:', d))
.catch(e => console.log('Backend error:', e));
```

### 6. Expected Debug Output

If working correctly, you should see:
```
🚀 Aera Debug Mode - Testing Text Capture
✅ Backend connection successful!
✅ Text analysis working! Found 3 vague phrases:
  - 'something' (generic_term)
  - 'good' (subjective_qualifier)  
  - 'this' (missing_context)
✅ Global text capture initialized successfully!
🎯 Now type in any application to test...
📝 Text detected: 'your text here' in app: notepad.exe
🔍 Analyzing text...
🎯 Found 2 vague phrases - should show underlines!
```

### Next Steps

If text detection works in Notepad but not browsers:
1. **Browser Extension**: Create Chrome/Edge extension for reliable text capture
2. **JavaScript Injection**: Inject scripts into web pages
3. **Alternative Approach**: Use browser automation tools

The current Windows API approach works best with native Windows controls (Notepad, Word, etc.) but has limitations with modern web browsers.