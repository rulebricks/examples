from random import choice, randint
from time import time
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

def generate_test_cases(num_test_cases):
    # Define the range of values for each field in the test cases
    # This will be used to generate random test data
    test_case_ranges = {
        "age": (18, 80),
        "income": (50000, 250000),
        "deductible_preference": (500, 5000),
        "medical_service_frequency": ["monthly", "quarterly", "annually"]
    }

    # Generate random test cases
    test_cases = []
    for _ in range(num_test_cases):
        test_case = {}
        for field, value_range in test_case_ranges.items():
            if isinstance(value_range, tuple):
                test_case[field] = randint(value_range[0], value_range[1])
            else:
                test_case[field] = choice(value_range)
        test_cases.append(test_case)

    return test_cases

if __name__ == "__main__":
    # Create and preview the rule's conditions...
    rule = build_example_rule()
    print(rule.to_table())

    # Export the rule to a .rbx file that can be imported into Rulebricks manually
    # rule.export()

    # Or, import the rule directly into your Rulebricks workspace
    rb.configure(
        api_key=os.getenv("RULEBRICKS_API_KEY") or "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX" # Replace with your API key
    )

    # Provide our configured workspace client to the Forge SDK
    rule.set_workspace(rb)

    # Publish the rule in our workspace
    rule.publish()

    # Perform a benchmark test to measure the rule's performance
    # This will execute the rule with a large number of randomly generated test cases
    # and measure the average time taken to solve each one

    # Define the number of test cases to generate
    # This will be the number of times the rule is solved
    num_test_cases_single = 50
    test_cases = generate_test_cases(num_test_cases_single)

    # Solve each test case and measure the time taken
    # This will give us an average time taken to solve each test case
    # NOTE: This is not the right way to solve multiple test cases in a single batch
    # And this will hit rate limits if the number of test cases is too high
    # Misrepresenting the performance of the rule engine
    single_start_time = time()
    for test_case in test_cases:
        try:
            outcome = rb.rules.solve(
                slug=rule.slug,
                request=test_case
            )
        except Exception as e:
            print(f"Failed to solve test case: {test_case}")
            print(e)
    single_end_time = time()
    print(f"Solved {num_test_cases_single} rules individually in {single_end_time - single_start_time:.2f} seconds")


    # Now let's solve much more test cases in a single batch
    # This will give us an average time taken to solve all test cases at once
    # This can be much more efficient than solving each test case individually
    num_test_cases_batch = 1000
    test_cases = generate_test_cases(num_test_cases_batch)
    batch_start_time = time()
    outcomes = rb.rules.bulk_solve(
        slug=rule.slug,
        request=test_cases
    )
    batch_end_time = time()
    print(f"Solved {num_test_cases_batch} rules in a single batch in {batch_end_time - batch_start_time:.2f} seconds")

    print("Avg time per rule (individual):", (single_end_time - single_start_time) / num_test_cases_single, "seconds")
    print("Avg time per rule (batch):", (batch_end_time - batch_start_time) / num_test_cases_batch, "seconds")

    # Delete the rule
    rb.assets.delete_rule(id=rule.id)
