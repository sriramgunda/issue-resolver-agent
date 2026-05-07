"""
FastAPI entrypoint — Access Resolver Agent + Investigation Agent.
"""

import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from app.models.schemas import (
    UserQuery, AgentResponse,
    InvestigationQuery, InvestigationResponse,
)
from app.agent.agent import resolve_access, stream_resolve_access
from app.agent.investigation_agent import investigate, stream_investigate
from app.rag.retriever import rag_fast_path

app = FastAPI(
    title="Agentic Issue Resolver",
    description="Access Resolver + Infrastructure Investigation — Ollama + LangChain tool-calling.",
    version="4.0.0",
)


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok"}


# ── Access Resolver Agent ─────────────────────────────────────────────────────
@app.post("/resolve", response_model=AgentResponse)
def resolve(query: UserQuery) -> AgentResponse:
    """Resolve an access-related issue. Uses RAG short-circuit for known FAQs."""
    fast = rag_fast_path(query.query)
    if fast:
        return AgentResponse(user_id=query.user_id, query=query.query, **fast)
    try:
        result = resolve_access(query.user_id, query.query)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return AgentResponse(user_id=query.user_id, query=query.query, **result)


@app.post("/resolve/stream")
async def resolve_stream(query: UserQuery):
    """Streaming SSE variant of /resolve."""
    fast = rag_fast_path(query.query)
    if fast:
        async def _fast():
            yield f"data: {json.dumps(fast)}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(_fast(), media_type="text/event-stream")

    async def _stream():
        async for chunk in stream_resolve_access(query.user_id, query.query):
            yield f"data: {chunk.replace(chr(10), '\\n')}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(_stream(), media_type="text/event-stream")


# ── Investigation Agent ───────────────────────────────────────────────────────
@app.post("/investigate", response_model=InvestigationResponse)
def investigate_issue(query: InvestigationQuery) -> InvestigationResponse:
    """
    Investigate an infrastructure issue: RDP failures, server down,
    web URL errors, DB session failures, network/service issues.

    Optional fields (server, url, db_instance) are appended to the query
    so the agent has precise targets to check.
    """
    # Build an enriched query string from the optional hints
    enriched = query.query
    if query.server:      enriched += f" | server: {query.server}"
    if query.url:         enriched += f" | url: {query.url}"
    if query.db_instance: enriched += f" | db_instance: {query.db_instance}"

    try:
        result = investigate(query.user_id, enriched)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return InvestigationResponse(
        user_id=query.user_id,
        query=query.query,
        **result,
    )


@app.post("/investigate/stream")
async def investigate_stream(query: InvestigationQuery):
    """Streaming SSE variant of /investigate."""
    enriched = query.query
    if query.server:      enriched += f" | server: {query.server}"
    if query.url:         enriched += f" | url: {query.url}"
    if query.db_instance: enriched += f" | db_instance: {query.db_instance}"

    async def _stream():
        async for chunk in stream_investigate(query.user_id, enriched):
            yield f"data: {chunk.replace(chr(10), '\\n')}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(_stream(), media_type="text/event-stream")
