using Microsoft.Extensions.Logging;
using System;
using System.Diagnostics;
using System.Drawing;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace AeraSystemService
{
    public class GlobalTextCapture : IGlobalTextCapture
    {
        private readonly ILogger<GlobalTextCapture> _logger;
        private bool _isInitialized = false;
        private bool _disposed = false;

        // Windows API constants
        private const int WH_KEYBOARD_LL = 13;
        private const int WH_MOUSE_LL = 14;
        private const int WM_KEYDOWN = 0x0100;
        private const int WM_CHAR = 0x0102;
        private const int WM_LBUTTONDOWN = 0x0201;

        // Hook handles
        private IntPtr _keyboardHook = IntPtr.Zero;
        private IntPtr _mouseHook = IntPtr.Zero;
        private LowLevelKeyboardProc _keyboardProc;
        private LowLevelMouseProc _mouseProc;

        // Text tracking
        private string _currentText = string.Empty;
        private IntPtr _currentWindow = IntPtr.Zero;
        private string _currentAppName = string.Empty;
        private DateTime _lastTextChange = DateTime.MinValue;
        private readonly System.Timers.Timer _analysisTimer;

        public event EventHandler<TextChangedEventArgs>? TextChanged;

        public GlobalTextCapture(ILogger<GlobalTextCapture>? logger = null)
        {
            _logger = logger ?? Microsoft.Extensions.Logging.Abstractions.NullLogger<GlobalTextCapture>.Instance;
            
            _keyboardProc = KeyboardHookCallback;
            _mouseProc = MouseHookCallback;
            
            // Timer to debounce text analysis (avoid analyzing on every keystroke)
            _analysisTimer = new System.Timers.Timer(1000); // 1 second delay
            _analysisTimer.Elapsed += OnAnalysisTimerElapsed;
            _analysisTimer.AutoReset = false;
        }

        public async Task InitializeAsync()
        {
            if (_isInitialized) return;

            try
            {
                _logger.LogInformation("Initializing global text capture...");

                // Install keyboard hook
                _keyboardHook = SetWindowsHookEx(
                    WH_KEYBOARD_LL,
                    _keyboardProc,
                    GetModuleHandle(Process.GetCurrentProcess().MainModule?.ModuleName),
                    0);

                if (_keyboardHook == IntPtr.Zero)
                {
                    throw new InvalidOperationException("Failed to install keyboard hook");
                }

                // Install mouse hook for click detection
                _mouseHook = SetWindowsHookEx(
                    WH_MOUSE_LL,
                    _mouseProc,
                    GetModuleHandle(Process.GetCurrentProcess().MainModule?.ModuleName),
                    0);

                if (_mouseHook == IntPtr.Zero)
                {
                    UnhookWindowsHookEx(_keyboardHook);
                    throw new InvalidOperationException("Failed to install mouse hook");
                }

                _isInitialized = true;
                _logger.LogInformation("Global text capture initialized successfully");

                await Task.CompletedTask;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to initialize global text capture");
                throw;
            }
        }

        public async Task<bool> IsInitializedAsync()
        {
            await Task.CompletedTask;
            return _isInitialized;
        }

        private IntPtr KeyboardHookCallback(int nCode, IntPtr wParam, IntPtr lParam)
        {
            try
            {
                if (nCode >= 0 && (wParam == (IntPtr)WM_KEYDOWN || wParam == (IntPtr)WM_CHAR))
                {
                    // Check if the current window has changed
                    var foregroundWindow = GetForegroundWindow();
                    if (foregroundWindow != _currentWindow)
                    {
                        _currentWindow = foregroundWindow;
                        _currentAppName = GetWindowProcessName(foregroundWindow);
                        _currentText = string.Empty; // Reset text for new window
                        
                        _logger.LogDebug($"Switched to application: {_currentAppName}");
                    }

                    // Get the current text from the focused control
                    var newText = GetCurrentText();
                    if (!string.IsNullOrEmpty(newText) && newText != _currentText)
                    {
                        _currentText = newText;
                        _lastTextChange = DateTime.Now;
                        
                        // Restart the analysis timer
                        _analysisTimer.Stop();
                        _analysisTimer.Start();
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error in keyboard hook callback");
            }

            return CallNextHookEx(_keyboardHook, nCode, wParam, lParam);
        }

        private IntPtr MouseHookCallback(int nCode, IntPtr wParam, IntPtr lParam)
        {
            try
            {
                if (nCode >= 0 && wParam == (IntPtr)WM_LBUTTONDOWN)
                {
                    // Mouse click might change text focus - check for text changes
                    var foregroundWindow = GetForegroundWindow();
                    if (foregroundWindow != _currentWindow)
                    {
                        _currentWindow = foregroundWindow;
                        _currentAppName = GetWindowProcessName(foregroundWindow);
                        _currentText = string.Empty;
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error in mouse hook callback");
            }

            return CallNextHookEx(_mouseHook, nCode, wParam, lParam);
        }

        private void OnAnalysisTimerElapsed(object? sender, System.Timers.ElapsedEventArgs e)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(_currentText) || _currentText.Length < 5)
                    return;

                // Skip if it's likely a password field or sensitive data
                if (IsPasswordField(_currentWindow) || IsSensitiveApplication(_currentAppName))
                    return;

                var textBounds = GetCurrentTextBounds();
                var context = CreateTextContext();

                var eventArgs = new TextChangedEventArgs
                {
                    Text = _currentText,
                    ApplicationName = _currentAppName,
                    WindowTitle = GetWindowTitle(_currentWindow),
                    TextBounds = textBounds,
                    Context = context
                };

                _logger.LogDebug($"Triggering text analysis for {_currentAppName}: {_currentText.Length} chars");
                TextChanged?.Invoke(this, eventArgs);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error during text analysis trigger");
            }
        }

        private string GetCurrentText()
        {
            try
            {
                // Try to get text from the currently focused control
                var focusedControl = GetFocus();
                if (focusedControl != IntPtr.Zero)
                {
                    var length = SendMessage(focusedControl, WM_GETTEXTLENGTH, IntPtr.Zero, IntPtr.Zero).ToInt32();
                    if (length > 0 && length < 10000) // Reasonable text length limit
                    {
                        var buffer = new StringBuilder(length + 1);
                        SendMessage(focusedControl, WM_GETTEXT, new IntPtr(buffer.Capacity), buffer);
                        return buffer.ToString();
                    }
                }

                // Fallback: try to get selected text via clipboard (more intrusive)
                return GetSelectedTextViaClipboard();
            }
            catch (Exception ex)
            {
                _logger.LogDebug(ex, "Failed to get current text");
                return string.Empty;
            }
        }

        private string GetSelectedTextViaClipboard()
        {
            // This is a more intrusive method - temporarily store clipboard, send Ctrl+C, get text, restore clipboard
            // For now, return empty to avoid interfering with user's clipboard
            return string.Empty;
        }

        private string GetWindowProcessName(IntPtr window)
        {
            try
            {
                GetWindowThreadProcessId(window, out uint processId);
                var process = Process.GetProcessById((int)processId);
                return process.ProcessName;
            }
            catch
            {
                return "Unknown";
            }
        }

        private string GetWindowTitle(IntPtr window)
        {
            try
            {
                var length = GetWindowTextLength(window);
                if (length == 0) return string.Empty;

                var buffer = new StringBuilder(length + 1);
                GetWindowText(window, buffer, buffer.Capacity);
                return buffer.ToString();
            }
            catch
            {
                return string.Empty;
            }
        }

        private Rectangle GetCurrentTextBounds()
        {
            // For now, return the window bounds - in a full implementation,
            // we'd get the exact text control bounds
            try
            {
                var rect = new RECT();
                GetWindowRect(_currentWindow, out rect);
                return new Rectangle(rect.Left, rect.Top, rect.Right - rect.Left, rect.Bottom - rect.Top);
            }
            catch
            {
                return Rectangle.Empty;
            }
        }

        private TextContext CreateTextContext()
        {
            return new TextContext
            {
                ApplicationPath = GetApplicationPath(_currentWindow),
                ProcessName = _currentAppName,
                ControlType = "textbox", // TODO: Detect actual control type
                IsPasswordField = IsPasswordField(_currentWindow),
                IsCodeEditor = IsCodeEditor(_currentAppName),
                Language = "en"
            };
        }

        private string GetApplicationPath(IntPtr window)
        {
            try
            {
                GetWindowThreadProcessId(window, out uint processId);
                var process = Process.GetProcessById((int)processId);
                return process.MainModule?.FileName ?? string.Empty;
            }
            catch
            {
                return string.Empty;
            }
        }

        private bool IsPasswordField(IntPtr window)
        {
            // TODO: Implement password field detection using UI Automation
            return false;
        }

        private bool IsSensitiveApplication(string appName)
        {
            var sensitiveApps = new[] { "keepass", "passwordsafe", "banking", "wallet", "vault" };
            var lowerAppName = appName.ToLowerInvariant();
            
            foreach (var sensitive in sensitiveApps)
            {
                if (lowerAppName.Contains(sensitive))
                    return true;
            }
            
            return false;
        }

        private bool IsCodeEditor(string appName)
        {
            var codeEditors = new[] { "code", "notepad++", "sublime", "atom", "vim", "emacs", "devenv" };
            var lowerAppName = appName.ToLowerInvariant();
            
            foreach (var editor in codeEditors)
            {
                if (lowerAppName.Contains(editor))
                    return true;
            }
            
            return false;
        }

        public async ValueTask DisposeAsync()
        {
            if (_disposed) return;

            try
            {
                _analysisTimer?.Stop();
                _analysisTimer?.Dispose();

                if (_keyboardHook != IntPtr.Zero)
                {
                    UnhookWindowsHookEx(_keyboardHook);
                    _keyboardHook = IntPtr.Zero;
                }

                if (_mouseHook != IntPtr.Zero)
                {
                    UnhookWindowsHookEx(_mouseHook);
                    _mouseHook = IntPtr.Zero;
                }

                _isInitialized = false;
                _disposed = true;

                _logger.LogInformation("Global text capture disposed");
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error disposing global text capture");
            }

            await Task.CompletedTask;
        }

        // Windows API declarations
        private delegate IntPtr LowLevelKeyboardProc(int nCode, IntPtr wParam, IntPtr lParam);
        private delegate IntPtr LowLevelMouseProc(int nCode, IntPtr wParam, IntPtr lParam);

        [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
        private static extern IntPtr SetWindowsHookEx(int idHook, LowLevelKeyboardProc lpfn, IntPtr hMod, uint dwThreadId);

        [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
        private static extern IntPtr SetWindowsHookEx(int idHook, LowLevelMouseProc lpfn, IntPtr hMod, uint dwThreadId);

        [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool UnhookWindowsHookEx(IntPtr hhk);

        [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
        private static extern IntPtr CallNextHookEx(IntPtr hhk, int nCode, IntPtr wParam, IntPtr lParam);

        [DllImport("kernel32.dll", CharSet = CharSet.Auto, SetLastError = true)]
        private static extern IntPtr GetModuleHandle(string lpModuleName);

        [DllImport("user32.dll")]
        private static extern IntPtr GetForegroundWindow();

        [DllImport("user32.dll")]
        private static extern IntPtr GetFocus();

        [DllImport("user32.dll", SetLastError = true)]
        private static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);

        [DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Auto)]
        private static extern int GetWindowTextLength(IntPtr hWnd);

        [DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Auto)]
        private static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

        [DllImport("user32.dll")]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);

        private const int WM_GETTEXT = 0x000D;
        private const int WM_GETTEXTLENGTH = 0x000E;

        [DllImport("user32.dll", CharSet = CharSet.Auto)]
        private static extern IntPtr SendMessage(IntPtr hWnd, int Msg, IntPtr wParam, StringBuilder lParam);

        [DllImport("user32.dll", CharSet = CharSet.Auto)]
        private static extern IntPtr SendMessage(IntPtr hWnd, int Msg, IntPtr wParam, IntPtr lParam);

        [StructLayout(LayoutKind.Sequential)]
        private struct RECT
        {
            public int Left;
            public int Top;
            public int Right;
            public int Bottom;
        }
    }
}