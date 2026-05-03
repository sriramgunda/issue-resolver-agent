from pydantic import BaseModel, Field
from typing import Optional, List

class UserQuery(BaseModel):
    user_id: str
    query: str

class AgentResponse_old(BaseModel):
    intent: str
    action: str
    result: str
    ticket_id: str | None = None

class AgentStep(BaseModel):
    step: str
    status: str
    details: Optional[str] = None


class AgentResponse(BaseModel):
    # Core fields returned by resolve_access()
    intent: str = Field(default="unknown", description="Classified intent of the issue")
    action: str = Field(default="none", description="Action taken by the agent")
    result: str = Field(default="", description="Human-readable outcome")
    ticket_id: Optional[str] = Field(default=None, description="Ticket ID if one was raised")
 
    # Extended fields — optional, populated when available
    user_id: Optional[str] = Field(default=None, description="User ID from the request")
    query: Optional[str] = Field(default=None, description="Original query from the request")
    decision: Optional[str] = Field(default=None, description="Agent's final decision")
    steps: Optional[List[str]] = Field(default=None, description="Tool call steps executed")
    confidence: Optional[float] = Field(default=None, description="Agent confidence score (0-1)")