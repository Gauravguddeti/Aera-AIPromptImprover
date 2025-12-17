using System;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace AeraSystemService.Test
{
    class TestProgram
    {
        [STAThread]
        static async Task Main(string[] args)
        {
            Console.WriteLine("Aera System Service Test");
            Console.WriteLine("========================");

            try
            {
                // Test backend client
                Console.WriteLine("Testing backend client...");
                using var backendClient = new AeraBackendClient();
                var isHealthy = await backendClient.IsServiceHealthyAsync();
                Console.WriteLine($"Backend healthy: {isHealthy}");

                if (isHealthy)
                {
                    var result = await backendClient.AnalyzeTextAsync("This is something good to test");
                    Console.WriteLine($"Analysis result: {result?.VaguePhrases?.Count ?? 0} vague phrases found");
                }

                Console.WriteLine("\nPress any key to exit...");
                Console.ReadKey();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error: {ex.Message}");
                Console.WriteLine("\nPress any key to exit...");
                Console.ReadKey();
            }
        }
    }
}