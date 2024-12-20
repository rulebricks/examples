using System;
using System.Threading.Tasks;
using System.Collections.Generic;
using RulebricksApi;
using RulebricksApi.Forge;

class Program
{
    static Rule BuildExampleRule()
    {
        var rule = new Rule();

        rule.SetName("Tested Health Insurance Selector")
            .SetDescription("Health insurance selector with comprehensive test cases");

        var age = rule.AddNumberField("age", "Age of the individual", 0);
        var income = rule.AddNumberField("income", "Annual income", 0);
        var chronic = rule.AddBooleanField("chronicConditions", "Has chronic conditions", false);
        var deductible = rule.AddNumberField("deductiblePreference", "Preferred deductible", 0);
        var frequency = rule.AddStringField("medicalServiceFrequency", "Medical service frequency");

        rule.AddStringResponse("recommendedPlan", "Recommended health insurance plan")
            .AddNumberResponse("estimatedPremium", "Estimated monthly premium", 0);

        // Add rule conditions
        rule.When(new Dictionary<string, object[]>
        {
            { "age", new object[] { "between", 25, 35 } },
            { "income", new object[] { "between", 50000, 75000 } },
            { "chronicConditions", new object[] { "equals", true } }
        })
        .Then(new Dictionary<string, object>
        {
            { "recommendedPlan", "HSA" },
            { "estimatedPremium", 2000 }
        });

        return rule;
    }

    static async Task Main()
    {
        try
        {
            var rb = new RulebricksApiClient(
                Environment.GetEnvironmentVariable("RULEBRICKS_API_KEY") ?? "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
            );

            var rule = BuildExampleRule();
            rule.SetWorkspace(rb);

            // Add test cases
            var test1 = new RuleTest
            {
                Name = "Young adult with chronic conditions",
                Description = "Tests recommendation for a young adult with chronic conditions",
                IsCritical = true,
                Inputs = new Dictionary<string, object>
                {
                    { "age", 30 },
                    { "income", 60000 },
                    { "chronicConditions", true },
                    { "deductiblePreference", 1000 },
                    { "medicalServiceFrequency", "monthly" }
                },
                Expected = new Dictionary<string, object>
                {
                    { "recommendedPlan", "HSA" },
                    { "estimatedPremium", 2000 }
                }
            };
            rule.AddTest(test1);

            // Add a test for edge case
            var test2 = new RuleTest
            {
                Name = "Edge case - Minimum age",
                Description = "Tests behavior at minimum age boundary",
                IsCritical = false,
                Inputs = new Dictionary<string, object>
                {
                    { "age", 25 },
                    { "income", 50000 },
                    { "chronicConditions", true },
                    { "deductiblePreference", 1000 },
                    { "medicalServiceFrequency", "monthly" }
                },
                Expected = new Dictionary<string, object>
                {
                    { "recommendedPlan", "HSA" },
                    { "estimatedPremium", 2000 }
                }
            };
            rule.AddTest(test2);

            // Enable continuous testing
            rule.EnableContinuousTesting();

            // Update and publish the rule
            await rule.Update();
            await rule.Publish();

            // Run the tests
            var testResults = await rb.Rules.RunTests(rule.Id);
            Console.WriteLine($"Test results: {testResults}");

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
