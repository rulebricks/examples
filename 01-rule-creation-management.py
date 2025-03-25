from rulebricks import Rulebricks
from rulebricks.forge import Rule
from dotenv import load_dotenv

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
    # Create and preview the rule's conditions...
    rule = build_example_rule()
    print(rule.to_table())

    # Export the rule to a .rbx file that can be imported into Rulebricks manually
    # rule.export()

    # Or, import the rule directly into your Rulebricks workspace
    rb = Rulebricks(
        base_url=os.getenv("RULEBRICKS_ENVIRONMENT") or "https://rulebricks.com/api/v1",
        api_key=os.getenv("RULEBRICKS_API_KEY") or "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX" # Replace with your API key
    )

    # Provide our configured workspace client to the Forge SDK
    rule.set_workspace(rb)

    # Push the rule to the workspace without publishing it...
    rule.update()

    # The new rule should appear in your Rulebricks workspace if we list all rules
    print(rb.assets.rules.list())

    # The URL to edit the rule in the Rulebricks web app should work!
    print(rule.get_editor_url())

    # Publish the rule to make it live
    rule.publish()

    # Let's try solving the rule with some test data!
    test_data = {
        "age": 25,
        "income": 60000,
        "chronic_conditions": True,
        "deductible_preference": 750,
        "medical_service_frequency": "monthly"
    }
    print(rule)
    test_data_solution = rb.rules.solve(
        slug=rule.slug,
        request=test_data
    )
    print(test_data_solution)

    # Delete the rule
    rb.assets.rules.delete(id=rule.id)
