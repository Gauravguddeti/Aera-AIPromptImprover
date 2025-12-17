using Microsoft.Extensions.Logging;
using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;

namespace AeraSystemService
{
    public class AeraBackendClient : IAeraBackendClient, IDisposable
    {
        private readonly HttpClient _httpClient;
        private readonly ILogger<AeraBackendClient> _logger;
        private readonly string _baseUrl;

        public AeraBackendClient(ILogger<AeraBackendClient>? logger = null)
        {
            _logger = logger ?? Microsoft.Extensions.Logging.Abstractions.NullLogger<AeraBackendClient>.Instance;
            _baseUrl = "http://localhost:8000"; // Our FastAPI backend
            
            _httpClient = new HttpClient()
            {
                BaseAddress = new Uri(_baseUrl),
                Timeout = TimeSpan.FromSeconds(10)
            };

            _httpClient.DefaultRequestHeaders.Add("User-Agent", "Aera-SystemService/1.0");
        }

        public async Task<AnalysisResult?> AnalyzeTextAsync(string text)
        {
            try
            {
                var request = new
                {
                    content = text,
                    settings = new
                    {
                        min_confidence = 0.5,
                        max_suggestions = 5,
                        analysis_type = "comprehensive"
                    }
                };

                var json = JsonConvert.SerializeObject(request);
                var content = new StringContent(json, Encoding.UTF8, "application/json");

                _logger.LogDebug($"Sending analysis request for {text.Length} characters");

                var response = await _httpClient.PostAsync("/api/prompts/analyze", content);

                if (response.IsSuccessStatusCode)
                {
                    var responseJson = await response.Content.ReadAsStringAsync();
                    var backendResult = JsonConvert.DeserializeObject<BackendAnalysisResponse>(responseJson);

                    if (backendResult != null)
                    {
                        return ConvertBackendResponse(backendResult);
                    }
                }
                else
                {
                    _logger.LogWarning($"Backend analysis failed: {response.StatusCode}");
                }
            }
            catch (HttpRequestException ex)
            {
                _logger.LogWarning(ex, "Failed to connect to Aera backend service");
            }
            catch (TaskCanceledException ex)
            {
                _logger.LogWarning(ex, "Backend analysis request timed out");
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Unexpected error during text analysis");
            }

            return null;
        }

        public async Task<bool> IsServiceHealthyAsync()
        {
            try
            {
                var response = await _httpClient.GetAsync("/health");
                return response.IsSuccessStatusCode;
            }
            catch
            {
                return false;
            }
        }

        private AnalysisResult ConvertBackendResponse(BackendAnalysisResponse backendResult)
        {
            var result = new AnalysisResult
            {
                AnalysisTimeMs = backendResult.AnalysisTimeMs,
                Provider = backendResult.ProviderUsed ?? "unknown",
                FallbackMode = backendResult.FallbackMode
            };

            // Convert vague phrases
            if (backendResult.VaguePhrases != null)
            {
                foreach (var phrase in backendResult.VaguePhrases)
                {
                    result.VaguePhrases.Add(new VaguePhrase
                    {
                        Id = phrase.Id ?? Guid.NewGuid().ToString(),
                        StartPosition = phrase.StartPosition,
                        EndPosition = phrase.EndPosition,
                        OriginalText = phrase.OriginalText ?? string.Empty,
                        VagueType = phrase.VagueType ?? "unknown",
                        ConfidenceScore = phrase.ConfidenceScore,
                        Reason = phrase.Reason ?? string.Empty
                    });
                }
            }

            // Convert suggestions
            if (backendResult.Suggestions != null)
            {
                foreach (var suggestion in backendResult.Suggestions)
                {
                    result.Suggestions.Add(new Suggestion
                    {
                        Id = suggestion.Id ?? Guid.NewGuid().ToString(),
                        ImprovedText = suggestion.ImprovedText ?? string.Empty,
                        Rationale = suggestion.Rationale ?? string.Empty,
                        ImprovementType = suggestion.ImprovementType ?? "unknown",
                        ConfidenceScore = suggestion.ConfidenceScore
                    });
                }
            }

            return result;
        }

        public void Dispose()
        {
            _httpClient?.Dispose();
        }

        // Backend response models (matching our FastAPI schema)
        private class BackendAnalysisResponse
        {
            [JsonProperty("vague_phrases")]
            public List<BackendVaguePhrase>? VaguePhrases { get; set; }

            [JsonProperty("suggestions")]
            public List<BackendSuggestion>? Suggestions { get; set; }

            [JsonProperty("analysis_time_ms")]
            public double AnalysisTimeMs { get; set; }

            [JsonProperty("provider_used")]
            public string? ProviderUsed { get; set; }

            [JsonProperty("fallback_mode")]
            public bool FallbackMode { get; set; }
        }

        private class BackendVaguePhrase
        {
            [JsonProperty("id")]
            public string? Id { get; set; }

            [JsonProperty("start_position")]
            public int StartPosition { get; set; }

            [JsonProperty("end_position")]
            public int EndPosition { get; set; }

            [JsonProperty("original_text")]
            public string? OriginalText { get; set; }

            [JsonProperty("vague_type")]
            public string? VagueType { get; set; }

            [JsonProperty("confidence_score")]
            public double ConfidenceScore { get; set; }

            [JsonProperty("reason")]
            public string? Reason { get; set; }
        }

        private class BackendSuggestion
        {
            [JsonProperty("id")]
            public string? Id { get; set; }

            [JsonProperty("improved_text")]
            public string? ImprovedText { get; set; }

            [JsonProperty("rationale")]
            public string? Rationale { get; set; }

            [JsonProperty("improvement_type")]
            public string? ImprovementType { get; set; }

            [JsonProperty("confidence_score")]
            public double ConfidenceScore { get; set; }
        }
    }
}