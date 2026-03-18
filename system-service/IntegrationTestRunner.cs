using System;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace AeraSystemService
{
    internal static class IntegrationTestRunner
    {
        public static async Task<int> RunAsync(ILogger logger)
        {
            int failures = 0;
            logger.LogInformation("Starting system-service integration tests...");

            if (!await TestBackendHealthAsync(logger)) failures++;
            if (!await TestBackendAnalyzeContractAsync(logger)) failures++;
            if (!await TestAnalysisFallbackAsync(logger)) failures++;
            if (!await TestSensitiveContextSkipAsync(logger)) failures++;

            if (failures == 0)
            {
                logger.LogInformation("All integration tests passed");
                return 0;
            }

            logger.LogError("Integration tests failed: {FailureCount} failing test(s)", failures);
            return 1;
        }

        private static async Task<bool> TestBackendHealthAsync(ILogger logger)
        {
            using var client = new AeraBackendClient();
            bool healthy = await client.IsServiceHealthyAsync();
            if (healthy)
            {
                logger.LogInformation("PASS TestBackendHealthAsync");
                return true;
            }

            logger.LogWarning("SKIP TestBackendHealthAsync: backend is not reachable at localhost:8000");
            return true;
        }

        private static async Task<bool> TestBackendAnalyzeContractAsync(ILogger logger)
        {
            using var client = new AeraBackendClient();
            bool healthy = await client.IsServiceHealthyAsync();
            if (!healthy)
            {
                logger.LogWarning("SKIP TestBackendAnalyzeContractAsync: backend unavailable");
                return true;
            }

            var result = await client.AnalyzeTextAsync("Write something good about AI");
            if (result == null)
            {
                logger.LogError("FAIL TestBackendAnalyzeContractAsync: analysis result was null");
                return false;
            }

            logger.LogInformation("PASS TestBackendAnalyzeContractAsync: {Count} phrase(s) detected", result.VaguePhrases.Count);
            return true;
        }

        private static async Task<bool> TestAnalysisFallbackAsync(ILogger logger)
        {
            var fakeBackend = new FakeBackendClient(isHealthy: false, analyzeResult: null);
            var service = new TextAnalysisService(fakeBackend);
            await service.StartAsync();

            var context = new TextContext
            {
                ProcessName = "notepad",
                IsPasswordField = false
            };

            var result = await service.AnalyzeTextAsync("This is something good", context);
            await service.StopAsync();

            if (result == null || !result.FallbackMode || result.VaguePhrases.Count == 0)
            {
                logger.LogError("FAIL TestAnalysisFallbackAsync: fallback result invalid");
                return false;
            }

            logger.LogInformation("PASS TestAnalysisFallbackAsync");
            return true;
        }

        private static async Task<bool> TestSensitiveContextSkipAsync(ILogger logger)
        {
            var fakeBackend = new FakeBackendClient(isHealthy: true, analyzeResult: new AnalysisResult());
            var service = new TextAnalysisService(fakeBackend);
            await service.StartAsync();

            var context = new TextContext
            {
                ProcessName = "banking-app",
                IsPasswordField = true
            };

            var result = await service.AnalyzeTextAsync("this is sensitive text", context);
            await service.StopAsync();

            if (result != null)
            {
                logger.LogError("FAIL TestSensitiveContextSkipAsync: expected null for sensitive context");
                return false;
            }

            logger.LogInformation("PASS TestSensitiveContextSkipAsync");
            return true;
        }

        private sealed class FakeBackendClient : IAeraBackendClient
        {
            private readonly bool _isHealthy;
            private readonly AnalysisResult? _analyzeResult;

            public FakeBackendClient(bool isHealthy, AnalysisResult? analyzeResult)
            {
                _isHealthy = isHealthy;
                _analyzeResult = analyzeResult;
            }

            public Task<AnalysisResult?> AnalyzeTextAsync(string text) => Task.FromResult(_analyzeResult);

            public Task<bool> IsServiceHealthyAsync() => Task.FromResult(_isHealthy);
        }
    }
}
