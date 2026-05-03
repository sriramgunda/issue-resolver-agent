from langchain_core.tools import tool
import random

@tool
def query_logs(user_id: str) -> dict:
    """
    Retrieve the most recent access or error logs for a user.

    Args:
        user_id: The ID of the user whose logs to fetch.

    Returns:
        A dict containing 'error' (error code string) and
        'reason' (machine-readable reason code, e.g. ROLE_MISSING).
    """
    # Stubbed — replace with real log aggregation (ELK, CloudWatch, etc.)
    sample_errors = [
        {"error": "ACCESS_DENIED", "reason": "ROLE_MISSING"},
        {"error": "ACCESS_DENIED", "reason": "ACCOUNT_LOCKED"},
        {"error": "ACCESS_DENIED", "reason": "EXPIRED_CREDENTIALS"},
        {"error": "ACCESS_DENIED", "reason": "NOT_PERMITTED"},
    ]
    return random.choice(sample_errors)
