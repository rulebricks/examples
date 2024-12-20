using System;
using System.Threading.Tasks;
using System.Collections.Generic;
using RulebricksApi;
using RulebricksApi.Forge;

class Program
{
    static async Task Main()
    {
        try
        {
            // Configure the Rulebricks client with your API key
            var rb = new RulebricksApiClient(
                Environment.GetEnvironmentVariable("RULEBRICKS_API_KEY") ?? "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
            );

            // Get an existing rule from the workspace
            var rule = await rb.Assets.GetRule("health-insurance-selector");

            // Update the rule's metadata
            rule.SetName("Updated Health Insurance Selector")
                .SetDescription("An updated version of the health insurance selector with refined logic.")
                .SetFolder("insurance/health");

            // Enable data validation
            rule.EnableDataValidation();

            // Update the rule's conditions
            rule.When(new Dictionary<string, object[]>
            {
                { "age", new object[] { "between", 25, 45 } },
                { "income", new object[] { "between", 75000, 100000 } },
                { "chronicConditions", new object[] { "equals", true } },
                { "deductiblePreference", new object[] { "between", 1000, 2000 } },
                { "medicalServiceFrequency", new object[] { "equals", "monthly" } }
            })
            .Then(new Dictionary<string, object>
            {
                { "recommendedPlan", "PPO" },
                { "estimatedPremium", 2500 }
            });

            // Add a new condition for high-income individuals
            rule.When(new Dictionary<string, object[]>
            {
                { "income", new object[] { "greater_than", 150000 } },
                { "deductiblePreference", new object[] { "greater_than", 5000 } }
            })
            .Then(new Dictionary<string, object>
            {
                { "recommendedPlan", "HDHP" },
                { "estimatedPremium", 1500 }
            });

            // Update the rule in the workspace
            await rule.Update();

            // Publish the updated rule
            await rule.Publish();

            // Test the updated rule
            var testData = new Dictionary<string, object>
            {
                { "age", 30 },
                { "income", 85000 },
                { "chronicConditions", true },
                { "deductiblePreference", 1500 },
                { "medicalServiceFrequency", "monthly" }
            };

            var solution = await rb.Rules.Solve(rule.Id, testData);
            Console.WriteLine($"Test solution for updated rule: {solution}");

            // Clean up
            await rb.Assets.DeleteRule(rule.Id);
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error: {ex.Message}");
            Environment.Exit(1);
        }
    }
}
