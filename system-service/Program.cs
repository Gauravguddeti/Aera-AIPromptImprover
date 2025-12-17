using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using System;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace AeraSystemService
{
    internal static class Program
    {
        /// <summary>
        /// The main entry point for the application.
        /// Can run as Windows Service or as tray application.
        /// </summary>
        [STAThread]
        static async Task Main(string[] args)
        {
            // Enable visual styles for Windows Forms
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);

            // Check if running as Windows Service
            bool isService = args.Length > 0 && args[0] == "--service";

            if (isService)
            {
                // Run as Windows Service
                await RunAsWindowsService();
            }
            else
            {
                // Run as tray application
                await RunAsTrayApplication();
            }
        }

        private static async Task RunAsWindowsService()
        {
            var builder = Host.CreateDefaultBuilder()
                .UseWindowsService(options =>
                {
                    options.ServiceName = "Aera AI Prompt Service";
                })
                .ConfigureServices(services =>
                {
                    services.AddSingleton<IAeraBackendClient, AeraBackendClient>();
                    services.AddSingleton<IGlobalTextCapture, GlobalTextCapture>();
                    services.AddSingleton<ITextAnalysisService, TextAnalysisService>();
                    services.AddHostedService<AeraBackgroundService>();
                })
                .ConfigureLogging(logging =>
                {
                    logging.AddEventLog();
                });

            var host = builder.Build();
            await host.RunAsync();
        }

        private static async Task RunAsTrayApplication()
        {
            // Create the services manually for tray app
            var serviceCollection = new ServiceCollection();
            serviceCollection.AddSingleton<IAeraBackendClient, AeraBackendClient>();
            serviceCollection.AddSingleton<IGlobalTextCapture, GlobalTextCapture>();
            serviceCollection.AddSingleton<ITextAnalysisService, TextAnalysisService>();
            serviceCollection.AddSingleton<ITextOverlayManager, TextOverlayManager>();
            serviceCollection.AddLogging(builder => builder.AddDebug());

            var serviceProvider = serviceCollection.BuildServiceProvider();

            // Create and run the tray application
            var trayApp = new AeraTrayApplication(serviceProvider);
            
            try
            {
                Application.Run(trayApp);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Aera System Service Error: {ex.Message}", 
                              "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }
    }
}