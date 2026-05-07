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


# Investigation Agent schemas
class InvestigationQuery(BaseModel):
    user_id:  str
    query:    str
    server:   Optional[str] = None   # optional hints the caller can provide
    url:      Optional[str] = None
    db_instance: Optional[str] = None
 
 
class InvestigationResponse(BaseModel):
    issue_type:        str            = Field(default="unknown")
    severity:          str            = Field(default="medium")
    root_cause:        str            = Field(default="")
    affected_resource: Optional[str]  = None
    resolution:        str            = Field(default="")
    ticket_raised:     bool           = False
    ticket_id:         Optional[str]  = None
    confidence:        float          = 0.0
    steps:             Optional[List[str]] = None
    user_id:           Optional[str]  = None
    query:             Optional[str]  = None