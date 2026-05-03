from langchain_core.tools import tool
import random

@tool
def check_user_access(user_id: str, app: str) -> dict:
    """
    Check whether a user has access to a given application.

    Args:
        user_id: The ID of the user to check.
        app: The application name to check access for.

    Returns:
        A dict with key 'has_access' (bool).
    """
    # Stubbed — replace with real DB / IAM call
    sample_access = [True, False]
    return {"has_access": random.choice(sample_access)}


@tool
def check_account_locked(user_id: str) -> dict:
    """
    Check whether a user's account is locked.

    Args:
        user_id: The ID of the user to check.

    Returns:
        A dict with key 'locked' (bool).
    """
    # Stubbed — replace with real identity-provider call
    sample_locked = [True, False]
    return {"locked": random.choice(sample_locked)}


@tool
def check_account_exists(user_id: str) -> dict:
    """
    Verify whether a user account exists in the system.

    Args:
        user_id: The ID of the user to look up.

    Returns:
        A dict with key 'exists' (bool).
    """
    return {"exists": random.choice([True, False])}


@tool
def grant_access(user_id: str, app: str) -> dict:
    """
    Grant a user access to a given application.

    Args:
        user_id: The ID of the user to grant access to.
        app: The application to grant access to.

    Returns:
        A dict with key 'status' set to 'granted'.
    """
    # Stubbed — replace with real IAM provisioning call
    sample_granted = ["granted", "denied"]
    return {"status": random.choice(sample_granted)}
