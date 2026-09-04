import { Rule, RulebricksClient } from "@rulebricks/sdk";
import "dotenv/config";

const rb = new RulebricksClient({
  environment:
    process.env.RULEBRICKS_ENVIRONMENT || "https://rulebricks.com/api/v1",
  apiKey:
    process.env.RULEBRICKS_API_KEY || "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
});

function buildEligibilityRule() {
  const rule = new Rule();
  rule.setName("Membership Eligibility");

  const age = rule.addNumberField("age", "Applicant age", 0);
  const activeMember = rule.addBooleanField(
    "active_member",
    "Whether the applicant has an active membership",
    false,
  );
  rule.addBooleanResponse(
    "eligible",
    "Whether the applicant is eligible",
    false,
  );
  rule.addStringResponse("reason", "Eligibility explanation", "");

  rule
    .when({
      age: age.between(18, 64),
      active_member: activeMember.equals(true),
    })
    .then({ eligible: true, reason: "Eligible active member" });
  rule.when({}).then({ eligible: false, reason: "Not eligible" });

  return rule;
}

async function main() {
  const rule = buildEligibilityRule();
  rule.setWorkspace(rb);
  await rule.publish();

  const outcomes = await rb.rules.bulkSolve({
    slug: rule.slug,
    version: "latest",
    body: [
      { age: 32, active_member: true },
      { age: 17, active_member: true },
      { age: 45, active_member: false },
    ],
  });
  console.log("Bulk outcomes:", outcomes);

  const rules = await rb.assets.rules.list();
  console.log(
    "Created rule:",
    rules.find((candidate) => candidate.id === rule.id),
  );

  await rb.assets.rules.delete({ id: rule.id });
}

main();
