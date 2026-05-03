from langchain_core.tools import tool

@tool
def create_ticket(user_id: str, issue: str) -> str:
    """Create access request ticket"""
    return "Ticket created: INC10001"