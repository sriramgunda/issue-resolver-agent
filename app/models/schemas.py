from pydantic import BaseModel, Field
from typing import Optional, List, Any


# ── Shared request ─────────────────────────────────────────────────────────────
class UserQuery(BaseModel):
    user_id: str
    query: str


# ── Access Resolver Agent ──────────────────────────────────────────────────────
class AgentResponse(BaseModel):
    intent:     str             = Field(default="unknown")
    action:     str             = Field(default="none")
    result:     str             = Field(default="")
    ticket_id:  Optional[str]   = None
    user_id:    Optional[str]   = None
    query:      Optional[str]   = None
    decision:   Optional[str]   = None
    steps:      Optional[List[str]] = None
    confidence: Optional[float]     = None


# ── Investigation Agent ────────────────────────────────────────────────────────
class InvestigationQuery(BaseModel):
    user_id:     str
    query:       str
    server:      Optional[str] = None
    url:         Optional[str] = None
    db_instance: Optional[str] = None


class InvestigationResponse(BaseModel):
    issue_type:        str           = Field(default="unknown")
    severity:          str           = Field(default="medium")
    root_cause:        str           = Field(default="")
    affected_resource: Optional[str] = None
    resolution:        str           = Field(default="")
    ticket_raised:     bool          = False
    ticket_id:         Optional[str] = None
    confidence:        float         = 0.0
    steps:             Optional[List[str]] = None
    user_id:           Optional[str] = None
    query:             Optional[str] = None


# ── Router (unified) ───────────────────────────────────────────────────────────
class RouterQuery(BaseModel):
    """Single entry-point request — works for both agent types."""
    user_id:     str
    query:       str
    # Optional resource hints forwarded to investigation agent if needed
    server:      Optional[str] = None
    url:         Optional[str] = None
    db_instance: Optional[str] = None


class RouterResponse(BaseModel):
    """
    Unified response envelope returned by POST /query.
    Contains router metadata plus the fields from whichever agent handled it.
    Unknown extra fields from agents are captured in 'extra'.
    """
    # Router metadata
    agent_used:                str   = Field(default="unknown")
    category:                  str   = Field(default="unknown")
    classification_confidence: float = Field(default=0.0)
    classification_reason:     str   = Field(default="")

    # Common agent fields
    user_id:    Optional[str]       = None
    query:      Optional[str]       = None
    result:     Optional[str]       = None      # access agent
    resolution: Optional[str]       = None      # investigation agent
    ticket_id:  Optional[str]       = None
    steps:      Optional[List[str]] = None
    confidence: Optional[float]     = None

    # Ambiguous — supplementary result from the secondary agent
    supplementary: Optional[Any]    = None

    model_config = {"extra": "allow"}   # absorb any extra agent fields cleanly
