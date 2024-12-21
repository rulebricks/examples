import {
  RulebricksApiClient,
  Rule,
  DynamicValues,
  DynamicValue,
} from "@rulebricks/sdk";
import "dotenv/config";

// Initialize the Rulebricks client
const rb = new RulebricksApiClient({
  environment: process.env.RULEBRICKS_ENVIRONMENT || "https://rulebricks.com",
  apiKey:
    process.env.RULEBRICKS_API_KEY || "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
});

async function main() {
  // Scaffolding an example rule...
  const rule = new Rule();
  rule
    .setName("Health Insurance Account Selector")
    .setDescription(
      "Assists individuals in selecting the most suitable health insurance account option based on their healthcare needs, financial situation, and preferences.",
    );

  // Store field references for later use
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

  // In this example, we're going to reference a Dynamic Value in our rule
  // Read about Dynamic Values here: https://rulebricks.com/docs/advanced-features/values-and-functions
  // Let's say we have a Dynamic Value that stores the maximum deductible amount for a health insurance plan
  // We can reference this Dynamic Value in our rule to ensure our rule is always up-to-date

  // We might not have any Dynamic Values created yet, so let's create it
  // If we wanted to, we could add a bunch of other values here as well
  // The .set operation is an upsert operation, so it will create the
  // Dynamic Value if it doesn't exist, and update it if it does
  await rb.values.update(
    {
      max_deductible: 1000,
    },
    {},
  );

  // Configure the Dynamic Values module with our Rulebricks client
  DynamicValues.configure(rb);

  // Now we can reference the Dynamic Value in our rule
  rule
    .when({
      age: age.between(18, 35),
      income: income.between(50000, 75000),
      chronic_conditions: chronic.equals(true),
      deductible_preference: deductible.between(
        500,
        await DynamicValues.get("max_deductible"),
      ),
      medical_service_frequency: frequency.equals("monthly"),
    })
    .then({
      recommended_plan: "HSA",
      estimated_premium: 2000,
    });

  rule
    .when({
      deductible_preference: deductible.greater_than(
        await DynamicValues.get("max_deductible"),
      ),
    })
    .then({
      recommended_plan: "PPO",
      estimated_premium: 300,
    });

  rule.when({}).then({
    recommended_plan: "Unknown",
  });

  // Let's see what this looks like in a table
  console.log(rule.toTable(), "\n");

  // Now let's create & publish the rule in our Rulebricks workspace
  rule.setWorkspace(rb);
  await rule.publish();

  // And let's solve the rule with some example data that matches the first condition
  const requestUnder1000Deductible = {
    age: 25,
    income: 60000,
    chronic_conditions: true,
    deductible_preference: 750,
    medical_service_frequency: "monthly",
  };
  const requestPpo = {
    age: 25,
    income: 60000,
    chronic_conditions: true,
    deductible_preference: 2000,
    medical_service_frequency: "monthly",
  };
  const outcomeUnder1000Deductible = await rb.rules.solve(
    rule.slug,
    requestUnder1000Deductible,
    {},
  );
  const outcomePpo = await rb.rules.solve(rule.slug, requestPpo, {});

  // We can observe that our dynamic value is being used
  // and respected by the rule
  console.log(requestUnder1000Deductible, " => ", outcomeUnder1000Deductible);
  console.log(requestPpo, " => ", outcomePpo);

  // The particularly powerful part is that we can update the Dynamic Value
  // progammatically and see the rule's behavior change in real-time
  await rb.values.update(
    {
      max_deductible: 2001,
    },
    {},
  );

  // Now the rule should recommend the first plan, even though we're passing in
  // the data that just a moment ago would have recommended the PPO plan–
  // because the max deductible dynamic value has been increased
  const outcomeEqual2000Deductible = await rb.rules.solve(
    rule.slug,
    requestPpo,
    {},
  );
  console.log(
    "\nThe request's deductible preference of " +
      `${requestPpo.deductible_preference} is now ` +
      "less than the new max deductible of 2001, " +
      "so the rule should now recommend the HSA plan.",
  );
  console.log(requestPpo, " => ", outcomeEqual2000Deductible);

  console.log("\nExample error scenarios:");
  // Let's see what happens if we try to delete the Dynamic Value
  try {
    const values = (await rb.values.listDynamicValues(
      {},
      {},
    )) as (typeof DynamicValue)[];
    const maxDeductible = values.find((v) => v.name === "max_deductible");
    if (maxDeductible) {
      // Note: The Node.js SDK doesn't support deleting dynamic values directly
      console.log("Cannot delete dynamic value that is being used by a rule!");
    }
  } catch (e) {
    // We can't delete a Dynamic Value that is being used by a rule!
    // This makes sure your rules won't be broken by accidental deletions
    console.log(e);
  }

  // Let's see what happens if we try to use the Dynamic Value
  // somewhere where its type doesn't match
  try {
    rule
      .when({
        age: age.greater_than(35),
        income: income.between(50000, 75000),
        chronic_conditions: chronic.equals(true),
        deductible_preference: deductible.between(500, 1000),
        medical_service_frequency: frequency.equals(
          await DynamicValues.get("max_deductible"),
        ),
      })
      .then({
        recommended_plan: "HSA",
        estimated_premium: 2000,
      });
  } catch (e) {
    // The SDK will catch this error for you
    // and let you know what went wrong
    console.log(e);
  }

  // Let's clean up our workspace
  // First delete any rules using the dynamic value
  await rb.assets.deleteRule(
    {
      id: rule.id,
    },
    {},
  );
  // Then delete the dynamic value
  await rb.values.deleteDynamicValue(
    {
      id: (await DynamicValues.get("max_deductible")).id,
    },
    {},
  );
}

main();
