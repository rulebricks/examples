import { RulebricksApiClient, Rule, RuleTest } from "@rulebricks/sdk";
import "dotenv/config";

// Initialize the Rulebricks client
const rb = new RulebricksApiClient({
  environment: process.env.RULEBRICKS_ENVIRONMENT || "https://rulebricks.com",
  apiKey:
    process.env.RULEBRICKS_API_KEY || "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
});

// See example 01 for more details on what we're doing here
function buildExampleRule() {
  const rule = new Rule();
  rule
    .setName("Health Insurance Account Selector")
    .setDescription(
      "Assists individuals in selecting the most suitable health insurance account option based on their healthcare needs, financial situation, and preferences.",
    );

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
  rule.addStringResponse(
    "recommended_plan",
    "Recommended health insurance plan",
    "",
  );
  rule.addNumberResponse("estimated_premium", "Estimated monthly premium", 0);

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

  // PLACEHOLDER: Add remaining conditions similar to example 01

  return rule;
}

async function main() {
  // Create an example rule...
  const rule = buildExampleRule();

  // Set our Rulebricks workspace
  rule.setWorkspace(rb);

  // This example, we're going to create some tests for our rule
  // Testing is a great way to ensure your rule behaves as expected
  // And to catch any issues before releasing new versions

  // Start by enabling continuous testing for the rule
  rule.enableContinuousTesting();

  // Let's create a test for the first condition row in our decision table
  const test1 = new RuleTest();
  test1.setName("First Example Test");
  test1.expect(
    // Simulate this request
    {
      age: 25,
      income: 60000,
      chronic_conditions: true,
      deductible_preference: 750,
      medical_service_frequency: "monthly",
    },
    // And expect this response
    {
      recommended_plan: "HSA",
      estimated_premium: 2000,
    },
  );
  // Criticality ensures that this test must pass for the rule to be published
  test1.isCritical();

  // And let's add this test to our rule
  rule.addTest(test1);

  // Let's publish the rule in our Rulebricks workspace
  // This will work because our critical test passes
  await rule.publish();
  console.log("Rule published successfully!");

  // Uh oh! Someone's messing with our rule...
  // They're changing the age range in the first condition row
  const matchedConditions = rule.findConditions({
    age: rule.getNumberField("age").between(18, 35),
  });
  matchedConditions[0].when({
    age: rule.getNumberField("age").between(18, 24),
  });

  // Let's see what happens when they try to publish this rule
  console.log("Example error scenario:");
  try {
    await rule.publish();
  } catch (e) {
    // They're not allowed to!
    console.log(e);
  }

  // Let's clean up our workspace
  console.log("Cleaning up workspace...");
  await rb.assets.deleteRule({ id: rule.id }, {});
}

main();
