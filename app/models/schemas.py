from pydantic import BaseModel
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
    user_id: str
    query: str

    decision: str
    result: str

    ticket_id: Optional[str] = None

    steps: List[AgentStep]
    confidence: float