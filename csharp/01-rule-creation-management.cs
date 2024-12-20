using System;
using System.Threading.Tasks;
using System.Collections.Generic;
using RulebricksApi;
using RulebricksApi.Forge;

class Program
{
    static Rule BuildExampleRule()
    {
        // Initialize the rule
        var rule = new Rule();

        // Set basic metadata
        rule.SetName("Health Insurance Account Selector")
            .SetDescription("Assists individuals in selecting the most suitable health insurance account option based on their healthcare needs, financial situation, and preferences.");

        // Define request fields with a more intuitive interface
        var age = rule.AddNumberField("age", "Age of the individual", 0);
        var income = rule.AddNumberField("income", "Annual income of the individual", 0);
        var chronic = rule.AddBooleanField("chronicConditions", "Whether the individual has chronic conditions", false);
        var deductible = rule.AddNumberField("deductiblePreference", "Preferred deductible amount", 0);
        var frequency = rule.AddStringField("medicalServiceFrequency", "Frequency of medical service needs");

        // Define response fields
        rule.AddStringResponse("recommendedPlan", "Recommended health insurance plan")
            .AddNumberResponse("estimatedPremium", "Estimated monthly premium", 0);

        // Define conditions and outcomes
        // Note the named parameters need to match the *field* names defined above
        rule.When(new Dictionary<string, object[]>
        {
            { "age", new object[] { "between", 18, 35 } },
            { "income", new object[] { "between", 50000, 75000 } },
            { "chronicConditions", new object[] { "equals", true } },
            { "deductiblePreference", new object[] { "between", 500, 1000 } },
            { "medicalServiceFrequency", new object[] { "equals", "monthly" } }
        })
        .Then(new Dictionary<string, object>
        {
            { "recommendedPlan", "HSA" },
            { "estimatedPremium", 2000 }
        });

        // The order in which conditions are defined matters significantly
        // The first one that matches will be executed
        rule.When(new Dictionary<string, object[]>
        {
            { "age", new object[] { "greater_than", 35 } },
            { "income", new object[] { "greater_than", 75000 } },
            { "chronicConditions", new object[] { "equals", false } },
            { "deductiblePreference", new object[] { "greater_than", 1000 } },
            { "medicalServiceFrequency", new object[] { "equals", "quarterly" } }
        })
        .Then(new Dictionary<string, object>
        {
            { "recommendedPlan", "PPO" },
            { "estimatedPremium", 3000 }
        });

        // Use .Any() method to create an OR across conditions for a specific outcome
        rule.Any(new Dictionary<string, object[]>
        {
            { "age", new object[] { "greater_than", 60 } },
            { "income", new object[] { "greater_than", 200000 } },
            { "chronicConditions", new object[] { "equals", false } }
        })
        .Then(new Dictionary<string, object>
        {
            { "recommendedPlan", "PPO" },
            { "estimatedPremium", 2500 }
        });

        // A fallback condition that will be executed if no other conditions match
        rule.When(new Dictionary<string, object[]>())
            .Then(new Dictionary<string, object>
            {
                { "recommendedPlan", "Unknown" }
            });

        return rule;
    }

    static async Task Main()
    {
        try
        {
            // Create and preview the rule's conditions...
            var rule = BuildExampleRule();
            Console.WriteLine(rule.ToTable());

            // Configure the Rulebricks client with your API key
            var rb = new RulebricksApiClient(
                Environment.GetEnvironmentVariable("RULEBRICKS_API_KEY") ?? "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
            );

            // Provide our configured workspace client to the Forge SDK
            rule.SetWorkspace(rb);

            // Push the rule to the workspace without publishing it...
            await rule.Update();

            // The new rule should appear in your Rulebricks workspace if we list all rules
            var rules = await rb.Assets.ListRules();
            Console.WriteLine("Available rules: {0}", string.Join(", ", rules));

            // The URL to edit the rule in the Rulebricks web app should work!
            Console.WriteLine("Editor URL: {0}", rule.GetEditorUrl());

            // Publish the rule to make it live
            await rule.Publish();

            // Let's try solving the rule with some test data!
            var testData = new Dictionary<string, object>
            {
                { "age", 25 },
                { "income", 60000 },
                { "chronicConditions", true },
                { "deductiblePreference", 750 },
                { "medicalServiceFrequency", "monthly" }
            };

            Console.WriteLine("Testing rule with data: {0}", testData);
            var testDataSolution = await rb.Rules.Solve(rule.Id, testData);
            Console.WriteLine("Solution: {0}", testDataSolution);

            // Delete the rule
            await rb.Assets.DeleteRule(rule.Id);
            Console.WriteLine("Rule deleted successfully");
        }
        catch (Exception ex)
        {
            Console.WriteLine("Error: {0}", ex.Message);
            Environment.Exit(1);
        }
    }
}
