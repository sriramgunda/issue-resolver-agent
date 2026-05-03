from langchain_core.tools import tool
import uuid


@tool
def create_ticket(user_id: str, issue: str) -> dict:
    """
    Create a support/incident ticket for a user's issue.

    Args:
        user_id: The ID of the user raising the ticket.
        issue: A short description of the problem or request.

    Returns:
        A dict with key 'ticket_id' containing the new ticket reference.
    """
    # Stubbed — replace with real ITSM / Jira / ServiceNow call
    ticket_id = f"INC{str(uuid.uuid4().int)[:5]}"
    return {"ticket_id": ticket_id}
