"""
FastAPI entrypoint for the Access Resolver Agent.
"""

from fastapi import FastAPI, HTTPException
from app.models.schemas import UserQuery, AgentResponse
from app.agent.agent import resolve_access

app = FastAPI(
    title="Access Resolver Agent",
    description="Agentic AI service that resolves access issues using Ollama + LangChain tool-calling.",
    version="2.0.0",
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/resolve", response_model=AgentResponse)
def resolve(query: UserQuery) -> AgentResponse:
    """
    Resolve an access-related issue for the given user.

    The agent will automatically call the appropriate tools
    (check_account_locked, check_user_access, grant_access, create_ticket, …)
    and return a structured response.
    """
    try:
        agent_result = resolve_access(query.user_id, query.query)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    # Merge request context into the response so all fields are populated
    return AgentResponse(
        intent=agent_result.get("intent", "unknown"),
        action=agent_result.get("action", "none"),
        result=agent_result.get("result", ""),
        ticket_id=agent_result.get("ticket_id"),
        user_id=query.user_id,
        query=query.query,
        decision=agent_result.get("decision"),
        steps=agent_result.get("steps"),
        confidence=agent_result.get("confidence"),
    )