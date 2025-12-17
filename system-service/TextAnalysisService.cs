using Microsoft.Extensions.Logging;
using System;
using System.Threading.Tasks;

namespace AeraSystemService
{
    public class TextAnalysisService : ITextAnalysisService
    {
        private readonly IAeraBackendClient _backendClient;
        private readonly ILogger<TextAnalysisService> _logger;
        private bool _isRunning = false;

        public TextAnalysisService(
            IAeraBackendClient backendClient,
            ILogger<TextAnalysisService>? logger = null)
        {
            _backendClient = backendClient;
            _logger = logger ?? Microsoft.Extensions.Logging.Abstractions.NullLogger<TextAnalysisService>.Instance;
        }

        public async Task StartAsync()
        {
            if (_isRunning) return;

            _logger.LogInformation("Starting text analysis service...");

            // Check if backend is healthy
            var isHealthy = await _backendClient.IsServiceHealthyAsync();
            if (!isHealthy)
            {
                _logger.LogWarning("Backend service is not healthy, but continuing anyway (fallback mode)");
            }

            _isRunning = true;
            _logger.LogInformation("Text analysis service started");
        }

        public async Task StopAsync()
        {
            if (!_isRunning) return;

            _logger.LogInformation("Stopping text analysis service...");
            _isRunning = false;
            _logger.LogInformation("Text analysis service stopped");

            await Task.CompletedTask;
        }

        public async Task<AnalysisResult?> AnalyzeTextAsync(string text, TextContext context)
        {
            if (!_isRunning)
            {
                _logger.LogWarning("Analysis requested but service is not running");
                return null;
            }

            if (string.IsNullOrWhiteSpace(text) || text.Length < 5)
            {
                return null;
            }

            // Skip analysis for sensitive contexts
            if (context.IsPasswordField || IsSensitiveContext(context))
            {
                _logger.LogDebug("Skipping analysis for sensitive context");
                return null;
            }

            try
            {
                _logger.LogDebug($"Analyzing text from {context.ProcessName}: {text.Length} characters");

                var result = await _backendClient.AnalyzeTextAsync(text);
                
                if (result != null)
                {
                    _logger.LogDebug($"Analysis completed: {result.VaguePhrases.Count} vague phrases found");
                    return result;
                }
                else
                {
                    _logger.LogDebug("Backend analysis returned no results");
                    return CreateFallbackAnalysis(text, context);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error during text analysis");
                return CreateFallbackAnalysis(text, context);
            }
        }

        private bool IsSensitiveContext(TextContext context)
        {
            if (context.IsPasswordField) return true;

            var sensitiveProcesses = new[] { "keepass", "passwordsafe", "banking", "wallet", "vault" };
            var processName = context.ProcessName.ToLowerInvariant();

            foreach (var sensitive in sensitiveProcesses)
            {
                if (processName.Contains(sensitive))
                    return true;
            }

            return false;
        }

        private AnalysisResult CreateFallbackAnalysis(string text, TextContext context)
        {
            // Simple rule-based fallback when backend is unavailable
            var result = new AnalysisResult
            {
                FallbackMode = true,
                Provider = "rule-based-fallback",
                AnalysisTimeMs = 1.0
            };

            // Simple rules for common vague words
            var vagueWords = new[] { "thing", "stuff", "something", "anything", "good", "bad", "nice", "great", "awesome" };
            
            foreach (var vagueWord in vagueWords)
            {
                int index = text.ToLowerInvariant().IndexOf(vagueWord);
                if (index >= 0)
                {
                    result.VaguePhrases.Add(new VaguePhrase
                    {
                        Id = Guid.NewGuid().ToString(),
                        StartPosition = index,
                        EndPosition = index + vagueWord.Length,
                        OriginalText = text.Substring(index, vagueWord.Length),
                        VagueType = "generic_term",
                        ConfidenceScore = 0.7,
                        Reason = $"'{vagueWord}' is a vague term that could be more specific"
                    });
                }
            }

            return result;
        }
    }
}