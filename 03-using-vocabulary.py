from rulebricks import BadRequestError, Rule, Rulebricks, Vocabulary
from rulebricks.forge import TypeMismatchError
from dotenv import load_dotenv
from time import sleep

import os

if __name__ == "__main__":
    # Ensure RULEBRICKS_API_KEY is set in a local .env file
    load_dotenv()

    # Initialize the Rulebricks SDK with the API key for our Rulebricks workspace
    rb = Rulebricks(
        base_url=os.getenv("RULEBRICKS_ENVIRONMENT") or "https://rulebricks.com/api/v1",
        api_key=os.getenv("RULEBRICKS_API_KEY")
        or "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",  # Replace with your API key
    )
    Vocabulary.configure(rb)

    # Scaffolding an example rule...
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

    # In the app, these values appear under "Vocabulary".
    # In this example, we're going to reference vocabulary values in our rule.
    # Read about vocabulary here: https://rulebricks.com/docs/advanced-features/values-and-functions
    # Let's say we have a vocabulary value that stores the maximum deductible amount for a health insurance plan
    # We can reference this vocabulary value in our rule to ensure our rule is always up-to-date

    # We might not have any vocabulary values created yet, so let's create them
    # If we wanted to, we could add a bunch of other vocabulary values here as well
    # The .set operation is an upsert operation, so it will create vocabulary values
    # if they don't exist, and update them if they do
    Vocabulary.set(
        {
            "max_deductible": 1000,
            "allowed_service_frequencies": ["monthly", "quarterly"],
        }
    )

    # Now we can reference the vocabulary value in our rule
    rule.when(
        age=age.between(18, 35),
        income=income.between(50000, 75000),
        chronic_conditions=chronic.equals(True),
        deductible_preference=deductible.between(
            500, Vocabulary.get("max_deductible")
        ),
        medical_service_frequency=frequency.is_included_in(
            Vocabulary.get("allowed_service_frequencies")
        ),
    ).then(recommended_plan="HSA", estimated_premium=2000)
    rule.when(
        deductible_preference=deductible.greater_than(
            Vocabulary.get("max_deductible")
        )
    ).then(recommended_plan="PPO", estimated_premium=300)
    rule.when().then(recommended_plan="Unknown")

    # Let's see what this looks like in a table
    print(rule.to_table())

    # Now let's create & publish the rule in our Rulebricks workspace
    rule.set_workspace(rb)
    rule.publish()

    # And let's solve the rule with some example data that matches the first condition
    request_under_1000_deductible = {
        "age": 25,
        "income": 60000,
        "chronic_conditions": True,
        "deductible_preference": 750,
        "medical_service_frequency": "monthly",
    }
    request_ppo = {
        "age": 25,
        "income": 60000,
        "chronic_conditions": True,
        "deductible_preference": 2000,
        "medical_service_frequency": "monthly",
    }
    outcome_under_1000_deductible = rb.rules.solve(
        slug=rule.slug, request=request_under_1000_deductible
    )
    outcome_ppo = rb.rules.solve(slug=rule.slug, request=request_ppo)

    # We can observe that our vocabulary value is being used
    # and respected by the rule
    print(request_under_1000_deductible, " => ", outcome_under_1000_deductible)
    print(request_ppo, " => ", outcome_ppo)

    # We can update the Vocabulary value programmatically at any time,
    # anywhere in your application, using our simple vocabulary API
    Vocabulary.set({"max_deductible": 2001})

    # Published rules, however, are pinned to the vocabulary they were
    # published with– every published version behaves exactly the same for
    # its entire lifetime, no matter how the vocabulary changes afterwards.
    # Our rule's published version still sees max_deductible = 1000,
    # so this request still recommends the PPO plan
    outcome_pinned_version = rb.rules.solve(
        slug=rule.slug, version="1", request=request_ppo
    )
    print(
        "\nEven though max_deductible is now 2001, the published version "
        "is pinned to the vocabulary it was published with, "
        "so it still recommends the PPO plan."
    )
    print(request_ppo, " => ", outcome_pinned_version)

    # To pick up the new vocabulary, publish a new version of the rule
    rule.publish()
    sleep(5)  # Give the newly published version a moment to propagate

    # The latest version sees max_deductible = 2001, so the same request's
    # deductible preference of 2000 now falls under the max– and the rule
    # recommends the HSA plan
    outcome_new_version = rb.rules.solve(
        slug=rule.slug, version="latest", request=request_ppo
    )
    print(
        "\nAfter publishing a new version, the request's deductible "
        f"preference of {request_ppo['deductible_preference']} is under "
        "the new max deductible of 2001, "
        "so the latest version recommends the HSA plan."
    )
    print(request_ppo, " => ", outcome_new_version)

    outcome_v1 = rb.rules.solve(slug=rule.slug, version="1", request=request_ppo)
    outcome_v2 = rb.rules.solve(slug=rule.slug, version="latest", request=request_ppo)

    print("\nSolving specific published versions:")
    print(f"{rule.slug}/1 (old vocabulary) => ", outcome_v1)
    print(f"{rule.slug}/latest (new vocabulary) => ", outcome_v2)

    print("\nExample error scenarios:")
    # Let's see what happens if we try to delete the Vocabulary value
    try:
        # This delete is expected to fail, so skip automatic retries
        rb.values.delete(
            id=Vocabulary.get("max_deductible").id,
            request_options={"max_retries": 0},
        )
    except BadRequestError as e:
        # We can't delete a Vocabulary value that is being used by a rule!
        # This makes sure your rules won't be broken by accidental deletions
        print(e.body.error)

    # Let's see what happens if we try to use the Vocabulary value
    # somewhere where its type doesn't match
    try:
        rule.when(
            age=age.greater_than(35),
            income=income.between(50000, 75000),
            chronic_conditions=chronic.equals(False),
            deductible_preference=deductible.between(500, 1000),
            # This will raise an error! Our Vocabulary value is a number and we're comparing it to a string
            medical_service_frequency=frequency.equals(
                Vocabulary.get("max_deductible")
            ),
        ).then(recommended_plan="HSA", estimated_premium=2000)
    except TypeMismatchError as e:
        # The SDK will catch this error for you
        # and let you know what went wrong
        print(e)

    # Let's clean up our workspace
    rb.assets.rules.delete(id=rule.id)

    # And let's clean up our Vocabulary
    for value_name in ["max_deductible", "allowed_service_frequencies"]:
        rb.values.delete(id=Vocabulary.get(value_name).id)
