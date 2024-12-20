from rulebricks.forge import Rule
from dotenv import load_dotenv

import rulebricks as rb
import os

# Ensure RULEBRICKS_API_KEY is set in a local .env file
load_dotenv()

# See example 01 for more details on what we're doing here
def build_example_rule():
    rule = Rule()
    rule.set_name("Health Insurance Account Selector") \
        .set_description("Assists individuals in selecting the most suitable health insurance account option based on their healthcare needs, financial situation, and preferences.")
    age = rule.add_number_field("age", "Age of the individual", 0)
    income = rule.add_number_field("income", "Annual income of the individual", 0)
    chronic = rule.add_boolean_field("chronic_conditions", "Whether the individual has chronic conditions", False)
    deductible = rule.add_number_field("deductible_preference", "Preferred deductible amount", 0)
    frequency = rule.add_string_field("medical_service_frequency", "Frequency of medical service needs", "")
    rule.add_string_response("recommended_plan", "Recommended health insurance plan", "")
    rule.add_number_response("estimated_premium", "Estimated monthly premium", 0)

    rule.when(
        age=age.between(18,35),
        income=income.between(50000, 75000),
        chronic_conditions=chronic.equals(True),
        deductible_preference=deductible.between(500, 1000),
        medical_service_frequency=frequency.equals("monthly")
    ).then(
        recommended_plan="HSA",
        estimated_premium=2000
    )

    rule.when(
        age=age.greater_than(35),
        income=income.greater_than(75000),
        chronic_conditions=chronic.equals(False),
        deductible_preference=deductible.greater_than(1000),
        medical_service_frequency=frequency.equals("quarterly")
    ).then(
        recommended_plan="PPO",
        estimated_premium=3000
    )

    rule.any(
        age=age.greater_than(60),
        income=income.greater_than(200000),
        chronic_conditions=chronic.equals(False),
    ).then(
        recommended_plan="PPO",
        estimated_premium=2500
    )

    rule.when(
        # Nothing here!
    ).then(
        recommended_plan="Unknown"
    )

    return rule

if __name__ == "__main__":
    # Create an example rule...
    rule = build_example_rule()

    # Initialize the Rulebricks SDK and publish the rule in our workspace
    rb.configure(
        api_key=os.getenv("RULEBRICKS_API_KEY") or "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX" # Replace with your API key
    )

    # To push updates to our workspace using the Forge SDK, we need to use set_workspace
    rule.set_workspace(rb)

    # Import the rule into our cloud workspace and publish it
    rule.publish()

    # Let's make some changes to conditions inside this rule
    # For example, let's look for the row in our decision table with the condition "age between 18 and 35"
    # and change it to be "age between 18 and 30"
    matched_conditions = rule.find_conditions(
        age=rule.get_number_field("age").between(18, 35)
    )
    print(matched_conditions)
    matched_conditions[0].when(
        age=rule.get_number_field("age").between(18, 30)
    )

    # Let's try one more change, this time to the outcome of the rule
    # Let's change the premium for when "age is greater than 60" to be $3000
    # instead of the current $2500
    matched_conditions = rule.find_conditions(
        age=rule.get_number_field("age").greater_than(60)
    )
    matched_conditions[0].then(
        estimated_premium=3000
    )

    # Let's preview our changes!
    print(rule.to_table())

    # We can also make changes to the rule's metadata and execution settings
    # For example, let's rename the rule
    rule.set_name("Health Insurance Plan Selector v2")

    # We can move the rule into a folder we create on the fly
    rule.set_folder("Health Insurance Rules", create_if_missing=True)

    # We can turn on various data validation settings for this Rule
    # To ensure that the rule only runs when all required fields are present
    # and that the data types are correct before execution
    rule.enable_schema_validation()
    rule.require_all_properties()

    # We can also progammatically override the rule's API slug!
    # This is a powerful feature that allows you to create custom API endpoints
    # If we're using the public cloud instance, we can now access this rule at:
        # https://rulebricks.com/api/v1/solve/health-insurance-selector
    # The only requirement is that these slugs are unique across all rules in your workspace
    rule.set_alias("health-insurance-selector")

    # Alright, that's enough changes for now!
    # Let's publish a new version of the updated rule
    # But note that publish() is only required because we changed the rule's conditions and outcomes
    # Otherwise, you can just use update() to update the rule's metadata
    rule.publish()

    # Check out the updated rule in your Rulebricks dashboard!
    # https://rulebricks.com/dashboard
