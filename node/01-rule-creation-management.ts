import { Rule, type Rulebricks, RulebricksClient } from "@rulebricks/sdk";
import "dotenv/config";

// Initialize the Rulebricks client
const rb = new RulebricksClient({
  environment:
    process.env.RULEBRICKS_ENVIRONMENT || "https://rulebricks.com/api/v1",
  apiKey:
    process.env.RULEBRICKS_API_KEY || "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
});

function buildExampleRule() {
  // Initialize the rule
  const rule = new Rule();

  // Set basic metadata
  rule
    .setName("Health Insurance Account Selector")
    .setDescription(
      "Assists individuals in selecting the most suitable health insurance account option based on their healthcare needs, financial situation, and preferences.",
    );

  // Define request fields with a more intuitive interface
  const age = rule.addNumberField("age", "Age of the individual", 0);
  const income = rule.addNumberField(
    "income",
    "Annual income of the individual",
    0,
  );
  const chronic = rule.addBooleanField(
    "chronic_conditions",
    "Whether the individual has chronic conditions",
    false,
  );
  const deductible = rule.addNumberField(
    "deductible_preference",
    "Preferred deductible amount",
    0,
  );
  const frequency = rule.addStringField(
    "medical_service_frequency",
    "Frequency of medical service needs",
    "",
  );

  // Define response fields
  rule.addStringResponse(
    "recommended_plan",
    "Recommended health insurance plan",
    "",
  );
  rule.addNumberResponse("estimated_premium", "Estimated monthly premium", 0);

  // Define conditions and outcomes
  // Note the named parameters need to match the *field* names defined above
  // (not the variable names)
  rule
    .when({
      age: age.between(18, 35),
      income: income.between(50000, 75000),
      chronic_conditions: chronic.equals(true),
      deductible_preference: deductible.between(500, 1000),
      medical_service_frequency: frequency.equals("monthly"),
    })
    .then({
      recommended_plan: "HSA",
      estimated_premium: 2000,
    });

  // The order in which conditions are defined matters significantly
  // The first one that matches will be executed
  // This is the second condition row in the table
  rule
    .when({
      age: age.greater_than(35),
      income: income.greater_than(75000),
      chronic_conditions: chronic.equals(false),
      deductible_preference: deductible.greater_than(1000),
      medical_service_frequency: frequency.equals("quarterly"),
    })
    .then({
      recommended_plan: "PPO",
      estimated_premium: 3000,
    });

  // Use .any() method to create an OR across conditions for a specific outcome
  rule
    .any({
      age: age.greater_than(60),
      income: income.greater_than(200000),
      chronic_conditions: chronic.equals(false),
    })
    .then({
      recommended_plan: "PPO",
      estimated_premium: 2500,
    });

  // A fallback condition that will be executed if no other conditions match
  // Helps to ensure that the rule always produces a result
  // And prevents API errors when an outcome is not able to be determined
  rule.when({}).then({
    recommended_plan: "Unknown",
  });

  return rule;
}

async function main() {
  try {
    // Create and preview the rule's conditions...
    const rule = buildExampleRule();
    console.log(rule.toTable());

    // Provide our configured workspace client to the Forge SDK
    rule.setWorkspace(rb);

    // Push the rule to the workspace without publishing it...
    await rule.update();

    // The new rule should appear in your Rulebricks workspace if we list all rules
    // console.log(await rb.assets.listRules({}, {}));

    // The URL to edit the rule in the Rulebricks web app should work!
    console.log(rule.getEditorUrl());

    // Publish the rule to make it live
    await rule.publish();

    // Let's try solving the rule with some test data!
    const testData = {
      age: 25,
      income: 60000,
      chronic_conditions: true,
      deductible_preference: 750,
      medical_service_frequency: "monthly",
    };
    const testDataSolution = await rb.rules.solve(rule.slug, testData);
    console.log(testDataSolution);

    // Delete the rule
    await rb.assets.rules.delete({
      id: rule.id,
    } satisfies Rulebricks.assets.DeleteRuleRequest);
  } catch (error) {
    console.error("Error:", error);
    process.exit(1);
  }
}

main();
