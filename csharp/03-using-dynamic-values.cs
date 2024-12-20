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

        rule.SetName("Dynamic Health Insurance Selector")
            .SetDescription("Health insurance selector with dynamic maximum deductible.");

        var age = rule.AddNumberField("age", "Age of the individual", 0);
        var income = rule.AddNumberField("income", "Annual income", 0);
        var chronic = rule.AddBooleanField("chronicConditions", "Has chronic conditions", false);
        var deductible = rule.AddNumberField("deductiblePreference", "Preferred deductible", 0);
        var frequency = rule.AddStringField("medicalServiceFrequency", "Medical service frequency");

        rule.AddStringResponse("recommendedPlan", "Recommended health insurance plan")
            .AddNumberResponse("estimatedPremium", "Estimated monthly premium", 0);

        return rule;
    }

    static async Task Main()
    {
        try
        {
            var rb = new RulebricksApiClient(
                Environment.GetEnvironmentVariable("RULEBRICKS_API_KEY") ?? "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
            );

            // Create a new rule
            var rule = BuildExampleRule();
            rule.SetWorkspace(rb);

            // Set up a dynamic value for maximum deductible
            await rb.Values.Update(new Dictionary<string, object>
            {
                { "max_deductible", 2000 }
            });

            // Get the current dynamic values
            var values = await rb.Values.ListDynamicValues();
            var maxDeductible = values.Find(v => v.Name == "max_deductible");

            if (maxDeductible != null)
            {
                // Add conditions using the dynamic value
                rule.When(new Dictionary<string, object[]>
                {
                    { "deductiblePreference", new object[] { "less_than", maxDeductible.Value } }
                })
                .Then(new Dictionary<string, object>
                {
                    { "recommendedPlan", "Standard" },
                    { "estimatedPremium", 1500 }
                });

                // Update and publish the rule
                await rule.Update();
                await rule.Publish();

                // Test the rule
                var testData = new Dictionary<string, object>
                {
                    { "age", 30 },
                    { "income", 75000 },
                    { "chronicConditions", false },
                    { "deductiblePreference", 1500 },
                    { "medicalServiceFrequency", "quarterly" }
                };

                var solution = await rb.Rules.Solve(rule.Id, testData);
                Console.WriteLine($"Solution with dynamic value: {solution}");

                // Update the dynamic value
                await rb.Values.Update(new Dictionary<string, object>
                {
                    { "max_deductible", 3000 }
                });

                // Test again with updated dynamic value
                solution = await rb.Rules.Solve(rule.Id, testData);
                Console.WriteLine($"Solution with updated dynamic value: {solution}");
            }

            // Clean up
            await rb.Assets.DeleteRule(rule.Id);
            Console.WriteLine("Dynamic values are managed through workspace settings");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error: {ex.Message}");
            Environment.Exit(1);
        }
    }
}
