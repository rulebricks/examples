from rulebricks import Rulebricks
from rulebricks.forge import Rule, RuleTest
from dotenv import load_dotenv

import os

# Ensure RULEBRICKS_API_KEY is set in a local .env file
load_dotenv()


# See example 01 for more details on what we're doing here
def build_example_rule():
    rule = Rule()
    rule.set_name("Health Insurance Account Selector").set_description(
        "Assists individuals in selecting the most suitable health insurance account option based on their healthcare needs, financial situation, and preferences."
    )
    age = rule.add_number_field("age", "Age of the individual", 0)
    income = rule.add_number_field("income", "Annual income of the individual", 0)
    chronic = rule.add_boolean_field(
        "chronic_conditions", "Whether the individual has chronic conditions", False
    )
    deductible = rule.add_number_field(
        "deductible_preference", "Preferred deductible amount", 0
    )
    frequency = rule.add_string_field(
        "medical_service_frequency", "Frequency of medical service needs", ""
    )
    rule.add_string_response(
        "recommended_plan", "Recommended health insurance plan", ""
    )
    rule.add_number_response("estimated_premium", "Estimated monthly premium", 0)

    rule.when(
        age=age.between(18, 35),
        income=income.between(50000, 75000),
        chronic_conditions=chronic.equals(True),
        deductible_preference=deductible.between(500, 1000),
        medical_service_frequency=frequency.equals("monthly"),
    ).then(recommended_plan="HSA", estimated_premium=2000)

    rule.when(
        age=age.greater_than(35),
        income=income.greater_than(75000),
        chronic_conditions=chronic.equals(False),
        deductible_preference=deductible.greater_than(1000),
        medical_service_frequency=frequency.equals("quarterly"),
    ).then(recommended_plan="PPO", estimated_premium=3000)

    rule.any(
        age=age.greater_than(60),
        income=income.greater_than(200000),
        chronic_conditions=chronic.equals(False),
    ).then(recommended_plan="PPO", estimated_premium=2500)

    rule.when(
        # Nothing here!
    ).then(recommended_plan="Unknown")

    return rule


if __name__ == "__main__":
    # Create an example rule...
    rule = build_example_rule()

    # Initialize the Rulebricks SDK with the API key for our Rulebricks workspace
    rb = Rulebricks(
        base_url=os.getenv("RULEBRICKS_ENVIRONMENT") or "https://rulebricks.com/api/v1",
        api_key=os.getenv("RULEBRICKS_API_KEY")
        or "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",  # Replace with your API key
    )
    rule.set_workspace(rb)

    # This example, we're going to create some tests for our rule
    # Testing is a great way to ensure your rule behaves as expected
    # And to catch any issues before releasing new versions

    # Start by enabling continuous testing for the rule
    rule.enable_continous_testing()

    # Let's create a test for the first condition row in our decision table
    test_1 = RuleTest()
    test_1.set_name("First Example Test")
    test_1.expect(
        request={
            "age": 25,
            "income": 60000,
            "chronic_conditions": True,
            "deductible_preference": 750,
            "medical_service_frequency": "monthly",
        },
        response={"recommended_plan": "HSA", "estimated_premium": 2000},
    )
    # Criticality ensures that this test must pass for the rule to be published
    test_1.is_critical()

    # And let's add this test to our rule
    rule.add_test(test=test_1)

    # Let's publish the rule in our Rulebricks workspace
    # This will work because our critical test passes
    rule.publish()
    print("Rule published successfully!")

    # Uh oh! Someone's messing with our rule...
    # They're changing the age range in the first condition row
    matched_conditions = rule.find_conditions(
        age=rule.get_number_field("age").between(18, 35)
    )
    matched_conditions[0].when(age=rule.get_number_field("age").between(18, 24))

    # Let's see what happens when they try to publish this rule
    print("Example error scenario:")
    try:
        rule.publish()
    except Exception as e:
        # They're not allowed to!
        print(e)

    # Let's clean up our workspace
    print("Cleaning up workspace...")
    rb.assets.rules.delete(id=rule.id)
