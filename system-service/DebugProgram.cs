using System;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

namespace AeraSystemService
{
    class DebugProgram
    {
        static async Task Main(string[] args)
        {
            if (args.Length > 0 && args[0] == "--integration-test")
            {
                using var loggerFactory = LoggerFactory.Create(builder =>
                {
                    builder.AddConsole();
                    builder.SetMinimumLevel(LogLevel.Information);
                });
                var integrationLogger = loggerFactory.CreateLogger("IntegrationTestRunner");
                int exitCode = await IntegrationTestRunner.RunAsync(integrationLogger);
                Environment.Exit(exitCode);
                return;
            }

            Console.WriteLine("🚀 Aera Debug Mode - Testing Text Capture");
            Console.WriteLine("Backend should be running at: http://localhost:8000");
            Console.WriteLine("Press Ctrl+C to exit\n");

            // Create service collection
            var services = new ServiceCollection();
            
            // Add logging
            services.AddLogging(builder =>
            {
                builder.AddConsole();
                builder.SetMinimumLevel(LogLevel.Debug);
            });
            
            // Add our services
            services.AddSingleton<IGlobalTextCapture, GlobalTextCapture>();
            services.AddSingleton<IAeraBackendClient, AeraBackendClient>();
            services.AddSingleton<ITextAnalysisService, TextAnalysisService>();
            services.AddSingleton<ITextOverlayManager, TextOverlayManager>();
            
            var serviceProvider = services.BuildServiceProvider();
            var logger = serviceProvider.GetRequiredService<ILogger<DebugProgram>>();
            
            try
            {
                // Test backend connection first
                logger.LogInformation("Testing backend connection...");
                var backendClient = serviceProvider.GetRequiredService<IAeraBackendClient>();
                
                var healthCheck = await backendClient.IsServiceHealthyAsync();
                if (healthCheck)
                {
                    logger.LogInformation("✅ Backend connection successful!");
                }
                else
                {
                    logger.LogWarning("⚠️ Backend connection failed - but continuing anyway");
                }
                
                // Test text analysis
                logger.LogInformation("Testing text analysis...");
                var analysisService = serviceProvider.GetRequiredService<ITextAnalysisService>();
                await analysisService.StartAsync();
                
                var testContext = new TextContext 
                { 
                    ApplicationPath = "test", 
                    ProcessName = "debug" 
                };
                var testResult = await analysisService.AnalyzeTextAsync("Write something good about this", testContext);
                if (testResult != null && testResult.VaguePhrases.Count > 0)
                {
                    logger.LogInformation($"✅ Text analysis working! Found {testResult.VaguePhrases.Count} vague phrases:");
                    foreach (var phrase in testResult.VaguePhrases)
                    {
                        logger.LogInformation($"  - '{phrase.OriginalText}' ({phrase.VagueType})");
                    }
                }
                else
                {
                    logger.LogWarning("⚠️ Text analysis returned no results");
                }
                
                // Initialize text capture
                logger.LogInformation("Initializing global text capture...");
                var textCapture = serviceProvider.GetRequiredService<IGlobalTextCapture>();
                
                // Set up event handler
                textCapture.TextChanged += async (sender, e) =>
                {
                    logger.LogInformation($"📝 Text detected: '{e.Text}' in app: {e.ApplicationName}");
                    
                    if (!string.IsNullOrWhiteSpace(e.Text) && e.Text.Length > 5)
                    {
                        logger.LogInformation("🔍 Analyzing text...");
                        var result = await analysisService.AnalyzeTextAsync(e.Text, e.Context);
                        if (result != null && result.VaguePhrases.Count > 0)
                        {
                            logger.LogInformation($"🎯 Found {result.VaguePhrases.Count} vague phrases - should show underlines!");
                            
                            // Try to show overlays
                            var overlayManager = serviceProvider.GetRequiredService<ITextOverlayManager>();
                            await overlayManager.ShowUnderlines(e.TextBounds, result.VaguePhrases, AeraServiceMode.Active);
                        }
                    }
                };
                
                await textCapture.InitializeAsync();
                
                if (await textCapture.IsInitializedAsync())
                {
                    logger.LogInformation("✅ Global text capture initialized successfully!");
                    logger.LogInformation("🎯 Now type in any application to test...");
                    logger.LogInformation("👀 Watch console for text detection events");
                }
                else
                {
                    logger.LogError("❌ Failed to initialize text capture");
                    return;
                }
                
                // Keep running until Ctrl+C
                var tcs = new TaskCompletionSource<bool>();
                Console.CancelKeyPress += (sender, e) =>
                {
                    e.Cancel = true;
                    tcs.SetResult(true);
                };
                
                logger.LogInformation("\n🔥 Debug mode active! Type anywhere and watch console...");
                await tcs.Task;
                
                logger.LogInformation("Shutting down...");
                await textCapture.DisposeAsync();
            }
            catch (Exception ex)
            {
                logger.LogError(ex, "❌ Error in debug mode");
            }
            
            Console.WriteLine("👋 Debug session ended");
        }
    }
}