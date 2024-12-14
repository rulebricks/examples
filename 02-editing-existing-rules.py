from rulebricks.forge import Rule
from dotenv import load_dotenv

import rulebricks as rb
import os

# Ensure RULEBRICKS_API_KEY is set in a local .env file
load_dotenv()

def build_example_rule():
    # Initialize the rule
    rule = Rule()

    # Set basic metadata
    rule.set_name("Health Insurance Account Selector") \
        .set_description("Assists individuals in selecting the most suitable health insurance account option based on their healthcare needs, financial situation, and preferences.")

    # Define request fields with a more intuitive interface
    age = rule.add_number_field("age", "Age of the individual", 0)
    income = rule.add_number_field("income", "Annual income of the individual", 0)
    chronic = rule.add_boolean_field("chronic_conditions", "Whether the individual has chronic conditions", False)
    deductible = rule.add_number_field("deductible_preference", "Preferred deductible amount", 0)
    frequency = rule.add_string_field("medical_service_frequency", "Frequency of medical service needs", "")

    # Define response fields
    rule.add_string_response("recommended_plan", "Recommended health insurance plan", "")
    rule.add_number_response("estimated_premium", "Estimated monthly premium", 0)

    # Define conditions and outcomes
    # Note the named parameters need to match the *field* names defined above
    # (not the variable names)
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

    # The order in which conditions are defined matters significantly
    # The first one that matches will be executed
    # This is the second condition row in the table
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

    # Use .any() method to create an OR across conditions for a specific outcome
    rule.any(
        age=age.greater_than(60),
        income=income.greater_than(200000),
        chronic_conditions=chronic.equals(False),
    ).then(
        recommended_plan="PPO",
        estimated_premium=2500
    )

    # A fallback condition that will be executed if no other conditions match
    # Helps to ensure that the rule always produces a result
    # And prevents API errors when an outcome is not able to be determined
    rule.when(
        # Nothing here!
    ).then(
        recommended_plan="Unknown"
    )

    return rule

if __name__ == "__main__":
    # Create an example rule...
    rule = build_example_rule()

    # Initialize the Rulebricks SDK and import the rule into our workspace
    rb.configure(
        api_key=os.getenv("RULEBRICKS_API_KEY") or "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX" # Replace with your API key
    )
    created_rule = rb.assets.import_rule(rule=rule, publish=True)

    # Let's make some changes to conditions inside this rule
    # For example, let's look for the row in our decision table with the condition "age between 18 and 35"
    # and change it to be "age between 18 and 30"
    matched_conditions = created_rule.find_conditions(
        age=created_rule.get_number_field("age").between(18, 35)
    )
    print(matched_conditions)
    matched_conditions[0].when(
        age=created_rule.get_number_field("age").between(18, 30)
    )

    # Let's try one more change, this time to the outcome of the rule
    # Let's change the premium for when "age is greater than 60" to be $3000
    # instead of the current $2500
    matched_conditions = created_rule.find_conditions(
        age=created_rule.get_number_field("age").greater_than(60)
    )
    matched_conditions[0].then(
        estimated_premium=3000
    )

    # Let's preview our changes!
    print(created_rule.to_table())

    # We can also make changes to the rule's metadata and execution settings
    # For example, let's rename the rule
    created_rule.set_name("Health Insurance Plan Selector v2")

    # We can move the rule into a folder we create on the fly
    # But to do this particular action, we need to give the rule access
    # to the client for our Rulebricks workspace using the set_workspace method
    created_rule.set_workspace(rb)
    created_rule.set_folder("Health Insurance Rules")

    # We can turn on various data validation settings for this Rule
    # To ensure that the rule only runs when all required fields are present
    # and that the data types are correct before execution
    created_rule.enable_schema_validation()
    created_rule.require_all_properties()

    # We can also progammatically override the rule's API slug!
    # This is a powerful feature that allows you to create custom API endpoints
    # If we're using the public cloud instance, we can now access this rule at:
        # https://rulebricks.com/api/v1/solve/health-insurance-selector
    # The only requirement is that these slugs are unique across all rules in your workspace
    created_rule.set_alias("health-insurance-selector")

    # Alright, that's enough changes for now!
    # Let's import the updated rule back into our workspace
    updated_rule = rb.assets.import_rule(rule=created_rule, publish=True)

    # Check out the updated rule in your Rulebricks dashboard!
    # https://rulebricks.com/dashboard