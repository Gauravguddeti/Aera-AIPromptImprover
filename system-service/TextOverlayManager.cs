using Microsoft.Extensions.Logging;
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Runtime.InteropServices;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace AeraSystemService
{
    public class TextOverlayManager : ITextOverlayManager
    {
        private readonly ILogger<TextOverlayManager> _logger;
        private readonly List<OverlayWindow> _activeOverlays = new();
        private bool _isInitialized = false;
        private bool _disposed = false;

        public TextOverlayManager(ILogger<TextOverlayManager>? logger = null)
        {
            _logger = logger ?? Microsoft.Extensions.Logging.Abstractions.NullLogger<TextOverlayManager>.Instance;
        }

        public async Task InitializeAsync()
        {
            if (_isInitialized) return;

            _logger.LogInformation("Initializing text overlay manager...");
            _isInitialized = true;
            _logger.LogInformation("Text overlay manager initialized");

            await Task.CompletedTask;
        }

        public async Task ShowUnderlines(Rectangle textBounds, List<VaguePhrase> phrases, AeraServiceMode mode)
        {
            if (!_isInitialized || phrases.Count == 0) return;

            try
            {
                // Clear existing overlays for this area
                await ClearUnderlines(textBounds);

                // Only show underlines in Active or Passive mode
                if (mode == AeraServiceMode.Disabled || mode == AeraServiceMode.Silent)
                    return;

                _logger.LogDebug($"Showing underlines for {phrases.Count} vague phrases");

                foreach (var phrase in phrases)
                {
                    // Calculate approximate position of the phrase within the text bounds
                    var underlineBounds = CalculateUnderlineBounds(textBounds, phrase);
                    
                    var overlay = new OverlayWindow(phrase, underlineBounds, mode, _logger);
                    overlay.Show();
                    
                    _activeOverlays.Add(overlay);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error showing underlines");
            }

            await Task.CompletedTask;
        }

        public async Task ClearUnderlines(Rectangle textBounds)
        {
            try
            {
                // Close overlays that intersect with the given bounds
                for (int i = _activeOverlays.Count - 1; i >= 0; i--)
                {
                    var overlay = _activeOverlays[i];
                    if (overlay.Bounds.IntersectsWith(textBounds))
                    {
                        overlay.Close();
                        overlay.Dispose();
                        _activeOverlays.RemoveAt(i);
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error clearing underlines");
            }

            await Task.CompletedTask;
        }

        public async Task ShowSuggestionPopup(Rectangle bounds, List<Suggestion> suggestions)
        {
            // TODO: Implement suggestion popup
            _logger.LogDebug($"Would show suggestion popup with {suggestions.Count} suggestions");
            await Task.CompletedTask;
        }

        public async Task HideSuggestionPopup()
        {
            // TODO: Implement popup hiding
            await Task.CompletedTask;
        }

        private Rectangle CalculateUnderlineBounds(Rectangle textBounds, VaguePhrase phrase)
        {
            // This is a simplified calculation - in a real implementation,
            // we'd need to know the exact text layout and font metrics
            
            var charWidth = 8; // Approximate character width
            
            var x = textBounds.X + (phrase.StartPosition * charWidth);
            var y = textBounds.Y + textBounds.Height - 4; // Position underline at bottom
            var width = (phrase.EndPosition - phrase.StartPosition) * charWidth;
            var height = 3; // Underline thickness

            return new Rectangle(x, y, width, height);
        }

        public async ValueTask DisposeAsync()
        {
            if (_disposed) return;

            try
            {
                // Close all active overlays
                foreach (var overlay in _activeOverlays)
                {
                    overlay.Close();
                    overlay.Dispose();
                }
                _activeOverlays.Clear();

                _isInitialized = false;
                _disposed = true;

                _logger.LogInformation("Text overlay manager disposed");
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error disposing overlay manager");
            }

            await Task.CompletedTask;
        }
    }

    internal class OverlayWindow : Form
    {
        private readonly VaguePhrase _phrase;
        private readonly AeraServiceMode _mode;
        private readonly ILogger _logger;

        public OverlayWindow(VaguePhrase phrase, Rectangle bounds, AeraServiceMode mode, ILogger logger)
        {
            _phrase = phrase;
            _mode = mode;
            _logger = logger;

            InitializeOverlay(bounds);
        }

        private void InitializeOverlay(Rectangle bounds)
        {
            // Configure the overlay window
            SetStyle(ControlStyles.SupportsTransparentBackColor, true);
            
            BackColor = Color.Lime; // Use lime as transparent color
            TransparencyKey = Color.Lime;
            
            FormBorderStyle = FormBorderStyle.None;
            WindowState = FormWindowState.Normal;
            ShowInTaskbar = false;
            TopMost = true;
            
            Bounds = bounds;

            // Make the window click-through
            MakeClickThrough();

            Paint += OnPaint;
            MouseEnter += OnMouseEnter;
            MouseLeave += OnMouseLeave;
        }

        private void MakeClickThrough()
        {
            // Make the window transparent to mouse clicks
            var initialStyle = GetWindowLong(Handle, GWL_EXSTYLE);
            SetWindowLong(Handle, GWL_EXSTYLE, initialStyle | WS_EX_LAYERED | WS_EX_TRANSPARENT);
        }

        private void OnPaint(object? sender, PaintEventArgs e)
        {
            // Draw the underline
            var color = _mode switch
            {
                AeraServiceMode.Active => Color.Red,
                AeraServiceMode.Passive => Color.Orange,
                _ => Color.Gray
            };

            using var pen = new Pen(color, 2);
            
            // Draw a wavy underline
            var points = new PointF[Width / 4];
            for (int i = 0; i < points.Length; i++)
            {
                var x = i * 4;
                var y = Height / 2 + (float)(Math.Sin(x * 0.2) * 2);
                points[i] = new PointF(x, y);
            }

            if (points.Length > 1)
            {
                e.Graphics.DrawCurve(pen, points);
            }
        }

        private void OnMouseEnter(object? sender, EventArgs e)
        {
            if (_mode == AeraServiceMode.Active)
            {
                // Show tooltip with suggestion
                var tooltip = new ToolTip();
                tooltip.SetToolTip(this, $"Vague phrase: '{_phrase.OriginalText}'\n{_phrase.Reason}");
                _logger.LogDebug($"Showing tooltip for phrase: {_phrase.OriginalText}");
            }
        }

        private void OnMouseLeave(object? sender, EventArgs e)
        {
            // Hide tooltip if any
        }

        // Windows API for click-through functionality
        private const int GWL_EXSTYLE = -20;
        private const int WS_EX_LAYERED = 0x80000;
        private const int WS_EX_TRANSPARENT = 0x20;

        [DllImport("user32.dll")]
        private static extern int GetWindowLong(IntPtr hwnd, int index);

        [DllImport("user32.dll")]
        private static extern int SetWindowLong(IntPtr hwnd, int index, int newStyle);

        protected override CreateParams CreateParams
        {
            get
            {
                var createParams = base.CreateParams;
                createParams.ExStyle |= WS_EX_LAYERED | WS_EX_TRANSPARENT;
                return createParams;
            }
        }
    }
}