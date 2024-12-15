from rulebricks.errors.bad_request_error import BadRequestError
from rulebricks.forge.types.values import TypeMismatchError
from rulebricks.forge import Rule, DynamicValues
from dotenv import load_dotenv
from time import sleep

import rulebricks as rb
import os

# Ensure RULEBRICKS_API_KEY is set in a local .env file
load_dotenv()

if __name__ == "__main__":
    # Initialize the Rulebricks SDK with the API key for our Rulebricks workspace
    rb.configure(
        api_key=os.getenv("RULEBRICKS_API_KEY") or "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
    )

    # Scaffolding an example rule...
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

    # In this example, we're going to reference a Dynamic Value in our rule
    # Read about Dynamic Values here: https://rulebricks.com/docs/advanced-features/values-and-functions
    # Let's say we have a Dynamic Value that stores the maximum deductible amount for a health insurance plan
    # We can reference this Dynamic Value in our rule to ensure our rule is always up-to-date

    # First, let's configure our Dynamic Values client with our Rulebricks workspace
    DynamicValues.configure(rb)

    # We might not have any Dynamic Values created yet, so let's create it
    # If we wanted to, we could add a bunch of other values here as well
    # The .set operation is an upsert operation, so it will create the
    # Dynamic Value if it doesn't exist, and update it if it does
    DynamicValues.set({
        "max_deductible": 1000
    })
    sleep(5)

    # Now we can reference the Dynamic Value in our rule
    rule.when(
        age=age.between(18, 35),
        income=income.between(50000, 75000),
        chronic_conditions=chronic.equals(True),
        deductible_preference=deductible.between(500, DynamicValues.get("max_deductible")),
        medical_service_frequency=frequency.equals("monthly")
    ).then(
        recommended_plan="HSA",
        estimated_premium=2000
    )
    rule.when(
        deductible_preference=deductible.greater_than(DynamicValues.get("max_deductible"))
    ).then(
        recommended_plan="PPO",
        estimated_premium=300
    )
    rule.when().then(
        recommended_plan="Unknown"
    )

    # Let's see what this looks like in a table
    print(rule.to_table())

    # Now let's create & publish the rule in our Rulebricks workspace
    created_rule = rb.assets.import_rule(rule=rule, publish=True)

    # And let's solve the rule with some example data that matches the first condition
    request_under_1000_deductible = {
        "age": 25,
        "income": 60000,
        "chronic_conditions": True,
        "deductible_preference": 750,
        "medical_service_frequency": "monthly"
    }
    request_ppo = {
        "age": 25,
        "income": 60000,
        "chronic_conditions": True,
        "deductible_preference": 2000,
        "medical_service_frequency": "monthly"
    }
    outcome_under_1000_deductible = rb.rules.solve(
        slug=created_rule.slug,
        request=request_under_1000_deductible
    )
    outcome_ppo = rb.rules.solve(
        slug=created_rule.slug,
        request=request_ppo
    )

    # We can observe that our dynamic value is being used
    # and respected by the rule
    print(request_under_1000_deductible, " => ", outcome_under_1000_deductible)
    print(request_ppo, " => ", outcome_ppo)

    # The particularly powerful part is that we can update the Dynamic Value
    # progammatically and see the rule's behavior change in real-time
    # You can call this dynamically anywhere in your application
    # using our simple Dynamic Values API
    #
    # Our SDK just makes it easy to do it here
    DynamicValues.set({
        "max_deductible": 2001
    })

    # Now the rule should recommend the first plan, even though we're passing in
    # the data that just a moment ago would have recommended the PPO plan–
    # because the max deductible dynamic value has been increased
    outcome_equal_2000_deductible = rb.rules.solve(
        slug=created_rule.slug,
        request=request_ppo
    )
    print("\nThe request's deductible preference of "
          f"{request_ppo['deductible_preference']} is now "
          "less than the new max deductible of 2001, "
          "so the rule should now recommend the HSA plan.")
    print(request_ppo, " => ", outcome_equal_2000_deductible)

    print("\nExample error scenarios:")
    # Let's see what happens if we try to delete the Dynamic Value
    try:
        rb.values.delete_dynamic_value(id=DynamicValues.get("max_deductible").id)
    except BadRequestError as e:
        # We can't delete a Dynamic Value that is being used by a rule!
        # This makes sure your rules won't be broken by accidental deletions
        print(e)

    # Let's see what happens if we try to use the Dynamic Value
    # somewhere where its type doesn't match
    try:
        rule.when(
            age=age.greater_than(35),
            income=income.between(50000, 75000),
            chronic_conditions=chronic.equals(False),
            deductible_preference=deductible.between(500, 1000),
            # This will raise an error! Our Dynamic Value is a number and we're comparing it to a string
            medical_service_frequency=frequency.equals(DynamicValues.get("max_deductible"))
        ).then(
            recommended_plan="HSA",
            estimated_premium=2000
        )
    except TypeMismatchError as e:
        # The SDK will catch this error for you
        # and let you know what went wrong
        print(e)

    # Let's clean up our workspace
    rb.assets.delete_rule(id=created_rule.id)

    # And let's clean up our Dynamic Values
    rb.values.delete_dynamic_value(id=DynamicValues.get("max_deductible").id)
