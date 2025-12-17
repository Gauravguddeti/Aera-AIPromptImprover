using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using System;
using System.Drawing;
using System.Windows.Forms;
using System.Threading.Tasks;

namespace AeraSystemService
{
    public class AeraTrayApplication : ApplicationContext
    {
        private NotifyIcon? _trayIcon;
        private ContextMenuStrip? _contextMenu;
        private readonly IServiceProvider _serviceProvider;
        private readonly ILogger<AeraTrayApplication> _logger;
        private readonly IGlobalTextCapture _textCapture;
        private readonly ITextAnalysisService _analysisService;
        private readonly ITextOverlayManager _overlayManager;

        private AeraServiceMode _currentMode = AeraServiceMode.Active;
        private bool _isRunning = false;

        public AeraTrayApplication(IServiceProvider serviceProvider)
        {
            _serviceProvider = serviceProvider;
            _logger = serviceProvider.GetService<ILogger<AeraTrayApplication>>()!;
            _textCapture = serviceProvider.GetService<IGlobalTextCapture>()!;
            _analysisService = serviceProvider.GetService<ITextAnalysisService>()!;
            _overlayManager = serviceProvider.GetService<ITextOverlayManager>()!;

            InitializeTrayIcon();
            InitializeServices();
        }

        private void InitializeTrayIcon()
        {
            _contextMenu = new ContextMenuStrip();
            CreateContextMenu();

            _trayIcon = new NotifyIcon()
            {
                Icon = GetIconForMode(_currentMode),
                ContextMenuStrip = _contextMenu,
                Text = "Aera AI Assistant - Active",
                Visible = true
            };

            _trayIcon.MouseClick += OnTrayIconClick;
        }

        private void CreateContextMenu()
        {
            _contextMenu?.Items.Clear();

            // Header
            var headerItem = new ToolStripMenuItem("Aera AI Assistant")
            {
                Enabled = false,
                Font = new Font(_contextMenu.Font, FontStyle.Bold)
            };
            _contextMenu.Items.Add(headerItem);
            _contextMenu.Items.Add(new ToolStripSeparator());

            // Mode selection
            var activeItem = new ToolStripMenuItem("🟢 Enable Suggestions")
            {
                Checked = _currentMode == AeraServiceMode.Active
            };
            activeItem.Click += (s, e) => SetMode(AeraServiceMode.Active);
            _contextMenu.Items.Add(activeItem);

            var passiveItem = new ToolStripMenuItem("🟡 Passive Mode (underlines only)")
            {
                Checked = _currentMode == AeraServiceMode.Passive
            };
            passiveItem.Click += (s, e) => SetMode(AeraServiceMode.Passive);
            _contextMenu.Items.Add(passiveItem);

            var disabledItem = new ToolStripMenuItem("🔴 Disable for 1 hour")
            {
                Checked = _currentMode == AeraServiceMode.Disabled
            };
            disabledItem.Click += (s, e) => SetMode(AeraServiceMode.Disabled);
            _contextMenu.Items.Add(disabledItem);

            _contextMenu.Items.Add(new ToolStripSeparator());

            // Status and settings
            var statsItem = new ToolStripMenuItem("📊 Today's Stats (Loading...)")
            {
                Enabled = false
            };
            _contextMenu.Items.Add(statsItem);

            var currentAppItem = new ToolStripMenuItem("🎯 Current App: Detecting...")
            {
                Enabled = false
            };
            _contextMenu.Items.Add(currentAppItem);

            _contextMenu.Items.Add(new ToolStripSeparator());

            var settingsItem = new ToolStripMenuItem("⚙️ Settings...");
            settingsItem.Click += OnSettingsClick;
            _contextMenu.Items.Add(settingsItem);

            var exitItem = new ToolStripMenuItem("❌ Exit");
            exitItem.Click += OnExitClick;
            _contextMenu.Items.Add(exitItem);
        }

        private Icon GetIconForMode(AeraServiceMode mode)
        {
            // Create simple colored icons for different modes
            var bitmap = new Bitmap(16, 16);
            using (var g = Graphics.FromImage(bitmap))
            {
                var color = mode switch
                {
                    AeraServiceMode.Active => Color.Green,
                    AeraServiceMode.Passive => Color.Orange,
                    AeraServiceMode.Disabled => Color.Red,
                    AeraServiceMode.Silent => Color.Gray,
                    _ => Color.Blue
                };

                g.Clear(Color.Transparent);
                g.FillEllipse(new SolidBrush(color), 2, 2, 12, 12);
                g.DrawEllipse(Pens.Black, 2, 2, 12, 12);
                
                // Add "A" letter
                g.DrawString("A", new Font("Arial", 8, FontStyle.Bold), 
                           Brushes.White, new PointF(5, 3));
            }

            return Icon.FromHandle(bitmap.GetHicon());
        }

        private async void InitializeServices()
        {
            try
            {
                _logger.LogInformation("Initializing Aera services...");

                // Initialize text capture
                await _textCapture.InitializeAsync();
                _textCapture.TextChanged += OnTextChanged;

                // Start the analysis service
                await _analysisService.StartAsync();

                // Initialize overlay manager
                await _overlayManager.InitializeAsync();

                _isRunning = true;
                _logger.LogInformation("Aera services initialized successfully");

                UpdateTrayTooltip();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to initialize Aera services");
                MessageBox.Show($"Failed to initialize Aera services: {ex.Message}", 
                              "Aera Error", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            }
        }

        private async void OnTextChanged(object? sender, TextChangedEventArgs e)
        {
            if (!_isRunning || _currentMode == AeraServiceMode.Disabled)
                return;

            try
            {
                _logger.LogDebug($"Text changed in {e.ApplicationName}: {e.Text.Length} characters");

                // Analyze the text
                var analysis = await _analysisService.AnalyzeTextAsync(e.Text, e.Context);

                if (analysis?.VaguePhrases?.Count > 0)
                {
                    // Show underlines for vague phrases
                    await _overlayManager.ShowUnderlines(e.TextBounds, analysis.VaguePhrases, _currentMode);

                    _logger.LogDebug($"Found {analysis.VaguePhrases.Count} vague phrases");
                }
                else
                {
                    // Clear any existing underlines
                    await _overlayManager.ClearUnderlines(e.TextBounds);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error processing text change");
            }
        }

        private void SetMode(AeraServiceMode mode)
        {
            _currentMode = mode;
            _trayIcon.Icon = GetIconForMode(mode);
            
            var modeText = mode switch
            {
                AeraServiceMode.Active => "Active",
                AeraServiceMode.Passive => "Passive",
                AeraServiceMode.Disabled => "Disabled",
                AeraServiceMode.Silent => "Silent",
                _ => "Unknown"
            };

            _trayIcon.Text = $"Aera AI Assistant - {modeText}";
            CreateContextMenu(); // Refresh the menu to update checkmarks
            
            _logger.LogInformation($"Aera mode changed to: {mode}");
        }

        private void UpdateTrayTooltip()
        {
            var modeText = _currentMode switch
            {
                AeraServiceMode.Active => "Active - Full suggestions enabled",
                AeraServiceMode.Passive => "Passive - Underlines only",
                AeraServiceMode.Disabled => "Disabled - No suggestions",
                AeraServiceMode.Silent => "Silent - Background learning",
                _ => "Unknown mode"
            };

            _trayIcon.Text = $"Aera AI Assistant\n{modeText}\nClick for options";
        }

        private void OnTrayIconClick(object? sender, MouseEventArgs e)
        {
            if (e.Button == MouseButtons.Left)
            {
                // Left click - toggle between active and passive
                var newMode = _currentMode == AeraServiceMode.Active 
                    ? AeraServiceMode.Passive 
                    : AeraServiceMode.Active;
                SetMode(newMode);
            }
            // Right click automatically shows context menu
        }

        private void OnSettingsClick(object? sender, EventArgs e)
        {
            MessageBox.Show("Settings panel coming soon!", "Aera Settings", 
                          MessageBoxButtons.OK, MessageBoxIcon.Information);
        }

        private async void OnExitClick(object? sender, EventArgs e)
        {
            try
            {
                _logger.LogInformation("Shutting down Aera services...");

                if (_textCapture != null)
                {
                    _textCapture.TextChanged -= OnTextChanged;
                    await _textCapture.DisposeAsync();
                }

                if (_analysisService != null)
                    await _analysisService.StopAsync();

                if (_overlayManager != null)
                    await _overlayManager.DisposeAsync();

                _isRunning = false;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error during shutdown");
            }

            _trayIcon.Visible = false;
            Application.Exit();
        }

        protected override void Dispose(bool disposing)
        {
            if (disposing)
            {
                _trayIcon?.Dispose();
                _contextMenu?.Dispose();
            }
            base.Dispose(disposing);
        }
    }

    public enum AeraServiceMode
    {
        Active,     // Full suggestions with popups
        Passive,    // Underlines only
        Disabled,   // No visual feedback
        Silent      // Background learning only
    }
}