from dotenv import load_dotenv

import rulebricks as rb
import os

from rulebricks.resources.users.types import InviteRequestRole

# Ensure RULEBRICKS_API_KEY is set in a local .env file
load_dotenv()

if __name__ == "__main__":
    # Initialize the Rulebricks SDK with the API key for our Rulebricks workspace
    rb.configure(
        api_key=os.getenv("RULEBRICKS_API_KEY") or "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX" # Replace with your API key
    )

    # This example isn't going to be runnable
    # unless you really want a user named John who works at Acme Co to join your workspace
    # Hope our invites find him well
    # It's just a demonstration of how you can programmatically manage teams in Rulebricks

    # Invite a new team member to your workspace
    # Developer roles give full access to assets in the workspace
    rb.users.invite(
        email="john@acme.co",
        role=InviteRequestRole.DEVELOPER
    )

    # But let's say we want to give John a "fresh" Rulebricks workspace
    # We can do this by creating a new access group for John and his team
    rb.users.create_group(
        name="John's Team",
        description="A new team for John and his colleagues"
    )

    # Now we can add John to the new group
    # Simply use the invite method again
    rb.users.invite(
        email="john@acme.co",
        role=InviteRequestRole.DEVELOPER,
        access_groups=["John's Team"] # Name should match the name of the group
    )

    # Now when John logs onto Rulebricks, even though he's technically
    # in the same workspace, he'll only see the assets that are shared
    # with him. This is a powerful way to manage access control in Rulebricks.
