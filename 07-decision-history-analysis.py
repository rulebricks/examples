from rulebricks import Rulebricks
from rulebricks.forge import Rule
from dotenv import load_dotenv

import pprint
import time
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
    rule = build_example_rule()

    # Initialize the Rulebricks SDK with the API key for our Rulebricks workspace
    rb = Rulebricks(
        base_url=os.getenv("RULEBRICKS_ENVIRONMENT") or "https://rulebricks.com/api/v1",
        api_key=os.getenv("RULEBRICKS_API_KEY") or "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX" # Replace with your API key
    )
    rule.set_workspace(rb)

    # Let's toss this rule into our workspace
    rule.publish()

    # Now let's solve the rule with varying example data
    request_1 = {
        "age": 25,
        "income": 60000,
        "chronic_conditions": True,
        "deductible_preference": 750,
        "medical_service_frequency": "monthly"
    }
    request_2 = {
        "age": 25,
        "income": 60000,
        "chronic_conditions": True,
        "deductible_preference": 2000,
        "medical_service_frequency": "monthly"
    }
    request_3 = {
        "age": 25,
        "income": 60000,
        "chronic_conditions": True,
        "deductible_preference": 750,
        "medical_service_frequency": "quarterly"
    }
    payloads = [request_1, request_2, request_3]
    start_time = time.time()
    for payload in payloads:
        outcome = rb.rules.solve(
            slug=rule.slug,
            request=payload
        )
    end_time = time.time()
    print(f"Solved {len(payloads)} rules in {end_time - start_time:.2f} seconds")

    # Solving rules in Rulebricks results in log entries– "decisions"
    # We provide a simple way to query past decisions for log export and analysis
    # This can be useful for auditing, debugging, and performance monitoring purposes

    # Logs usually take a few seconds to be indexed and available for querying
    # So we'll wait a bit before querying
    print("Waiting for logs to be indexed... (15s)")
    time.sleep(15)

    # Let's query the decisions for the rule we just solved
    decisions = rb.decisions.query(
        slug=rule.slug,
        limit=50 # Limit has to be between 50 and 1000 results
        # There are some other optional parameters you can use to filter the results
        # See https://rulebricks.com/docs/api-reference#tag/decisions/get/api/v1/decisions/query
    )

    # You're free to do whatever you want with the decisions data
    # Here, we'll just print it out, so you can see what it looks like
    # If you're not seeing any decisions, try increasing the sleep time above
    print(str(len(decisions.data or [])) + " decision logs found")
    pp = pprint.PrettyPrinter(depth=4)
    pp.pprint(decisions.data)

    # Clean up by deleting the rule
    rb.assets.rules.delete(id=rule.id)
