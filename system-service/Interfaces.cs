using System;
using System.Collections.Generic;
using System.Drawing;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

namespace AeraSystemService
{
    // Core service interfaces
    public interface IAeraBackendClient
    {
        Task<AnalysisResult?> AnalyzeTextAsync(string text);
        Task<bool> IsServiceHealthyAsync();
    }

    public interface IGlobalTextCapture : IAsyncDisposable
    {
        event EventHandler<TextChangedEventArgs>? TextChanged;
        Task InitializeAsync();
        Task<bool> IsInitializedAsync();
    }

    public interface ITextAnalysisService
    {
        Task StartAsync();
        Task StopAsync();
        Task<AnalysisResult?> AnalyzeTextAsync(string text, TextContext context);
    }

    public interface ITextOverlayManager : IAsyncDisposable
    {
        Task InitializeAsync();
        Task ShowUnderlines(Rectangle textBounds, List<VaguePhrase> phrases, AeraServiceMode mode);
        Task ClearUnderlines(Rectangle textBounds);
        Task ShowSuggestionPopup(Rectangle bounds, List<Suggestion> suggestions);
        Task HideSuggestionPopup();
    }

    // Data models
    public class TextChangedEventArgs : EventArgs
    {
        public string Text { get; set; } = string.Empty;
        public string ApplicationName { get; set; } = string.Empty;
        public string WindowTitle { get; set; } = string.Empty;
        public Rectangle TextBounds { get; set; }
        public TextContext Context { get; set; } = new();
    }

    public class TextContext
    {
        public string ApplicationPath { get; set; } = string.Empty;
        public string ProcessName { get; set; } = string.Empty;
        public string ControlType { get; set; } = string.Empty;
        public bool IsPasswordField { get; set; }
        public bool IsCodeEditor { get; set; }
        public string Language { get; set; } = "en";
    }

    public class AnalysisResult
    {
        public List<VaguePhrase> VaguePhrases { get; set; } = new();
        public List<Suggestion> Suggestions { get; set; } = new();
        public double AnalysisTimeMs { get; set; }
        public string Provider { get; set; } = string.Empty;
        public bool FallbackMode { get; set; }
    }

    public class VaguePhrase
    {
        public string Id { get; set; } = string.Empty;
        public int StartPosition { get; set; }
        public int EndPosition { get; set; }
        public string OriginalText { get; set; } = string.Empty;
        public string VagueType { get; set; } = string.Empty;
        public double ConfidenceScore { get; set; }
        public string Reason { get; set; } = string.Empty;
    }

    public class Suggestion
    {
        public string Id { get; set; } = string.Empty;
        public string ImprovedText { get; set; } = string.Empty;
        public string Rationale { get; set; } = string.Empty;
        public string ImprovementType { get; set; } = string.Empty;
        public double ConfidenceScore { get; set; }
    }

    // Background service for Windows Service mode
    public class AeraBackgroundService : Microsoft.Extensions.Hosting.BackgroundService
    {
        private readonly Microsoft.Extensions.Logging.ILogger<AeraBackgroundService> _logger;
        private readonly IGlobalTextCapture _textCapture;
        private readonly ITextAnalysisService _analysisService;

        public AeraBackgroundService(
            Microsoft.Extensions.Logging.ILogger<AeraBackgroundService> logger,
            IGlobalTextCapture textCapture,
            ITextAnalysisService analysisService)
        {
            _logger = logger;
            _textCapture = textCapture;
            _analysisService = analysisService;
        }

        protected override async Task ExecuteAsync(System.Threading.CancellationToken stoppingToken)
        {
            _logger.LogInformation("Aera Background Service starting...");

            try
            {
                await _textCapture.InitializeAsync();
                await _analysisService.StartAsync();

                _logger.LogInformation("Aera Background Service started successfully");

                // Keep the service running
                while (!stoppingToken.IsCancellationRequested)
                {
                    await Task.Delay(5000, stoppingToken);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error in Aera Background Service");
                throw;
            }
            finally
            {
                _logger.LogInformation("Aera Background Service stopping...");
                await _analysisService.StopAsync();
                await _textCapture.DisposeAsync();
            }
        }
    }
}