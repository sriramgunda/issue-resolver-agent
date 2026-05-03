from langchain_core.tools import tool

@tool
def check_account_locked(user_id: str) -> str:
    """Check if user account is locked"""
    return "false"

@tool
def check_user_access(user_id: str, app: str) -> str:
    """Check if user has access to application"""
    return "false"

@tool
def grant_access(user_id: str, app: str) -> str:
    """Grant access to user"""
    return "Access granted successfully"