import { RulebricksClient, Rule } from "@rulebricks/sdk";
import "dotenv/config";

// Initialize the Rulebricks client
const rb = new RulebricksClient({
  environment:
    process.env.RULEBRICKS_ENVIRONMENT || "https://rulebricks.com/api/v1",
  apiKey:
    process.env.RULEBRICKS_API_KEY || "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
});

// See example 01 for more details on what we're doing here
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
  // Create an example rule...
  const rule = buildExampleRule();

  // To push updates to our workspace using the Forge SDK, we need to use setWorkspace
  rule.setWorkspace(rb);

  // Publish the rule to the cloud workspace
  await rule.publish();

  // Let's make some changes to conditions inside this rule
  // For example, let's look for the row in our decision table with the condition "age between 18 and 35"
  // and change it to be "age between 18 and 30"
  const age = rule.getNumberField("age");
  let matchedConditions = rule.findConditions({
    age: age.between(18, 35),
  });
  console.log(matchedConditions[0]);
  matchedConditions[0].when({
    age: age.between(18, 30),
  });

  // Let's try one more change, this time to the outcome of the rule
  // Let's change the premium for when "age is greater than 60" to be $3000
  // instead of the current $2500
  matchedConditions = rule.findConditions({
    age: age.greater_than(60),
  });
  matchedConditions[0].then({
    estimated_premium: 3000,
  });

  // Let's preview our changes!
  console.log(rule.toTable());

  // We can also make changes to the rule's metadata and execution settings
  // For example, let's rename the rule
  rule.setName("Health Insurance Plan Selector v2");

  // We can move the rule into a folder
  await rule.setFolder("Health Insurance Rules", true);

  // We can turn on various data validation settings for this Rule
  // To ensure that the rule only runs when all required fields are present
  // and that the data types are correct before execution
  rule.enableSchemaValidation();
  rule.requireAllProperties();

  // We can also progammatically override the rule's API slug!
  // This is a powerful feature that allows you to create custom API endpoints
  // If we're using the public cloud instance, we can now access this rule at:
  // https://rulebricks.com/api/v1/solve/health-insurance-selector
  // The only requirement is that these slugs are unique across all rules in your workspace
  await rule.setAlias("health-insurance-selector");

  // Alright, that's enough changes for now!
  // Let's publish a new version of the updated rule
  // But note that publish() is only required because we changed the rule's conditions and outcomes
  // Otherwise, you can just use update() to update the rule's metadata
  await rule.publish();

  // Check out the updated rule in your Rulebricks dashboard!
  // https://rulebricks.com/dashboard
}

main();
