from pydantic import BaseModel

class UserQuery(BaseModel):
    user_id: str
    query: str

class AgentResponse(BaseModel):
    intent: str
    action: str
    result: str
    ticket_id: str | None = None