import {
  RbmManifest,
  Rule,
  Rulebricks,
  RulebricksClient,
  TypeMismatchError,
  Vocabulary,
} from "@rulebricks/sdk";

import "dotenv/config";

// Initialize the Rulebricks client
const rb = new RulebricksClient({
  environment:
    process.env.RULEBRICKS_ENVIRONMENT || "https://rulebricks.com/api/v1",
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

  // In the app, these values appear under "Vocabulary". The generated API still
  // exposes them through rb.values.*, and rule JSON stores them as globalValue refs.
  // In this example, we're going to reference vocabulary values in our rule.
  // Read about vocabulary here: https://rulebricks.com/docs/advanced-features/values-and-functions
  // Let's say we have a vocabulary value that stores the maximum deductible amount for a health insurance plan
  // We can reference this vocabulary value in our rule to ensure our rule is always up-to-date

  // We might not have any vocabulary values created yet, so let's create them
  // If we wanted to, we could add a bunch of other vocabulary values here as well
  // The set operation is an upsert, so it will create vocabulary values
  // if they don't exist, and update them if they do
  Vocabulary.configure(rb);
  await Vocabulary.set({
    max_deductible: 1000,
    allowed_service_frequencies: ["monthly", "quarterly"],
  });

  // Now we can reference the vocabulary value in our rule
  rule
    .when({
      age: age.between(18, 35),
      income: income.between(50000, 75000),
      chronic_conditions: chronic.equals(true),
      deductible_preference: deductible.between(
        500,
        await Vocabulary.get("max_deductible"),
      ),
      medical_service_frequency: frequency.is_included_in(
        await Vocabulary.get("allowed_service_frequencies"),
      ),
    })
    .then({
      recommended_plan: "HSA",
      estimated_premium: 2000,
    });

  rule
    .when({
      deductible_preference: deductible.greater_than(
        await Vocabulary.get("max_deductible"),
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

  // Server-backed export resolves and includes the referenced Vocabulary values
  const manifest = await RbmManifest.exportRule(rb, rule);
  await manifest.save("health-insurance-with-vocabulary.rbm");

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
  const outcomeUnder1000Deductible = await rb.rules.solve({
    slug: rule.slug,
    body: requestUnder1000Deductible,
  });
  const outcomePpo = await rb.rules.solve({
    slug: rule.slug,
    body: requestPpo,
  });

  // We can observe that our vocabulary value is being used
  // and respected by the rule
  console.log(requestUnder1000Deductible, " => ", outcomeUnder1000Deductible);
  console.log(requestPpo, " => ", outcomePpo);

  // We can update the vocabulary value programmatically at any time,
  // anywhere in your application, using our simple vocabulary API
  await Vocabulary.set({ max_deductible: 2001 });

  // Published rules, however, are pinned to the vocabulary they were
  // published with– every published version behaves exactly the same for
  // its entire lifetime, no matter how the vocabulary changes afterwards.
  // Our rule's published version still sees max_deductible = 1000,
  // so this request still recommends the PPO plan
  const outcomePinnedVersion = await rb.rules.solve({
    slug: rule.slug,
    version: "1",
    body: requestPpo,
  });
  console.log(
    "\nEven though max_deductible is now 2001, the published version is pinned to the vocabulary it was published with, so it still recommends the PPO plan.",
  );
  console.log(requestPpo, " => ", outcomePinnedVersion);

  // To pick up the new vocabulary, publish a new version of the rule
  await rule.publish();
  // Give the newly published version a moment to propagate
  await new Promise((resolve) => setTimeout(resolve, 5000));

  // The latest version sees max_deductible = 2001, so the same request's
  // deductible preference of 2000 now falls under the max– and the rule
  // recommends the HSA plan
  const outcomeNewVersion = await rb.rules.solve({
    slug: rule.slug,
    version: "latest",
    body: requestPpo,
  });
  console.log(
    `\nAfter publishing a new version, the request's deductible preference of ${requestPpo.deductible_preference} is under the new max deductible of 2001, so the latest version recommends the HSA plan.`,
  );
  console.log(requestPpo, " => ", outcomeNewVersion);

  // Every published version stays addressable, and "latest" explicitly
  // targets the newest published version.
  const outcomeV1 = await rb.rules.solve({
    slug: rule.slug,
    version: "1",
    body: requestPpo,
  });
  const outcomeV2 = await rb.rules.solve({
    slug: rule.slug,
    version: "latest",
    body: requestPpo,
  });
  console.log("\nSolving specific published versions:");
  console.log(`${rule.slug}/1 (old vocabulary) => `, outcomeV1);
  console.log(`${rule.slug}/latest (new vocabulary) => `, outcomeV2);

  console.log("\nExample error scenarios:");
  // Let's see what happens if we try to delete the vocabulary value
  try {
    // This delete is expected to fail, so skip automatic retries
    await rb.values.delete(
      { id: (await Vocabulary.get("max_deductible")).id },
      { maxRetries: 0 },
    );
  } catch (error) {
    if (error instanceof Rulebricks.BadRequestError) {
      // Values referenced by a rule cannot be deleted accidentally.
      console.log(error instanceof Error ? error.message : String(error));
    } else {
      throw error;
    }
  }

  // Let's see what happens if we try to use the vocabulary value
  // somewhere where its type doesn't match
  try {
    rule
      .when({
        age: age.greater_than(35),
        income: income.between(50000, 75000),
        chronic_conditions: chronic.equals(true),
        deductible_preference: deductible.between(500, 1000),
        medical_service_frequency: frequency.equals(
          await Vocabulary.get("max_deductible"),
        ),
      })
      .then({
        recommended_plan: "HSA",
        estimated_premium: 2000,
      });
  } catch (error) {
    if (error instanceof TypeMismatchError) {
      console.log(error instanceof Error ? error.message : String(error));
    } else {
      throw error;
    }
  }

  // Let's clean up our workspace
  // First delete any rules using the vocabulary value
  await rb.assets.rules.delete({
    id: rule.id,
  });

  // Then delete the vocabulary values
  for (const valueName of ["max_deductible", "allowed_service_frequencies"]) {
    await rb.values.delete({
      id: (await Vocabulary.get(valueName)).id,
    });
  }
}

main();
