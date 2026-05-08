"""
FastAPI entrypoint.

Endpoints
---------
POST /query          — Smart router: LLM classifies then delegates to the right agent
POST /query/stream   — Streaming SSE variant of /query

POST /resolve        — Access Resolver Agent (direct, bypasses router)
POST /resolve/stream — Streaming variant

POST /investigate        — Investigation Agent (direct, bypasses router)
POST /investigate/stream — Streaming variant

GET  /health
"""

import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from app.models.schemas import (
    UserQuery, AgentResponse,
    InvestigationQuery, InvestigationResponse,
    RouterQuery, RouterResponse,
)
from app.agent.agent import resolve_access, stream_resolve_access
from app.agent.investigation_agent import investigate, stream_investigate
from app.agent.router_agent import route_and_resolve, stream_route_and_resolve
from app.rag.retriever import rag_fast_path

app = FastAPI(
    title="Agentic Issue Resolver",
    description=(
        "LLM-routed IT support: one endpoint classifies the query and dispatches "
        "to the Access Resolver or Investigation Agent automatically."
    ),
    version="5.0.0",
)


# ── Health ─────────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok"}


# ══════════════════════════════════════════════════════════════════════════════
#  SMART ROUTER  —  single entry point for all queries
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/query", response_model=RouterResponse,
          summary="Smart router — LLM classifies query and delegates to the right agent")
def query(req: RouterQuery) -> RouterResponse:
    """
    **Recommended endpoint.**

    The LLM first classifies the query:
    - `access_issue`  → Access Resolver Agent (login, permissions, roles)
    - `investigation` → Investigation Agent   (RDP, server, URL, DB, network)
    - `ambiguous`     → both agents run; higher-confidence result is primary

    Optional `server`, `url`, `db_instance` hints are forwarded to the
    Investigation Agent if it is selected.
    """
    # RAG short-circuit for well-known FAQ queries (no LLM needed)
    fast = rag_fast_path(req.query)
    if fast:
        return RouterResponse(
            agent_used="rag",
            category="access_issue",
            classification_confidence=fast.get("confidence", 1.0),
            classification_reason="High-confidence FAQ match — no LLM call required.",
            user_id=req.user_id,
            query=req.query,
            result=fast.get("result"),
            confidence=fast.get("confidence"),
            steps=fast.get("steps"),
        )

    # Enrich query with optional resource hints for investigation
    enriched = req.query
    if req.server:      enriched += f" | server: {req.server}"
    if req.url:         enriched += f" | url: {req.url}"
    if req.db_instance: enriched += f" | db_instance: {req.db_instance}"

    try:
        result = route_and_resolve(req.user_id, enriched)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return RouterResponse(user_id=req.user_id, query=req.query, **result)


@app.post("/query/stream",
          summary="Streaming SSE variant of /query")
async def query_stream(req: RouterQuery):
    """
    SSE stream. Events:
    - First event: `{"type":"classification", "category":..., "confidence":..., ...}`
    - Subsequent events: raw token chunks from the selected agent
    - Final event: `data: [DONE]`
    """
    fast = rag_fast_path(req.query)
    if fast:
        async def _fast():
            yield f"data: {json.dumps({'type':'classification','category':'access_issue','agent_used':'rag','confidence':fast.get('confidence')})}\n\n"
            yield f"data: {json.dumps(fast)}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(_fast(), media_type="text/event-stream")

    enriched = req.query
    if req.server:      enriched += f" | server: {req.server}"
    if req.url:         enriched += f" | url: {req.url}"
    if req.db_instance: enriched += f" | db_instance: {req.db_instance}"

    async def _stream():
        async for chunk in stream_route_and_resolve(req.user_id, enriched):
            safe = chunk.replace("\n", "\\n") if not chunk.startswith("{") else chunk
            yield f"data: {safe}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(_stream(), media_type="text/event-stream")


# ══════════════════════════════════════════════════════════════════════════════
#  DIRECT AGENT ENDPOINTS  (bypass the router)
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/resolve", response_model=AgentResponse,
          summary="Access Resolver Agent — direct (no router)")
def resolve(query: UserQuery) -> AgentResponse:
    fast = rag_fast_path(query.query)
    if fast:
        return AgentResponse(user_id=query.user_id, query=query.query, **fast)
    try:
        result = resolve_access(query.user_id, query.query)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return AgentResponse(user_id=query.user_id, query=query.query, **result)


@app.post("/resolve/stream",
          summary="Streaming variant of /resolve")
async def resolve_stream(query: UserQuery):
    fast = rag_fast_path(query.query)
    if fast:
        async def _fast():
            yield f"data: {json.dumps(fast)}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(_fast(), media_type="text/event-stream")

    async def _stream():
        async for chunk in stream_resolve_access(query.user_id, query.query):
            yield f"data: {chunk.replace(chr(10), chr(92)+'n')}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(_stream(), media_type="text/event-stream")


@app.post("/investigate", response_model=InvestigationResponse,
          summary="Investigation Agent — direct (no router)")
def investigate_issue(query: InvestigationQuery) -> InvestigationResponse:
    enriched = query.query
    if query.server:      enriched += f" | server: {query.server}"
    if query.url:         enriched += f" | url: {query.url}"
    if query.db_instance: enriched += f" | db_instance: {query.db_instance}"
    try:
        result = investigate(query.user_id, enriched)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return InvestigationResponse(user_id=query.user_id, query=query.query, **result)


@app.post("/investigate/stream",
          summary="Streaming variant of /investigate")
async def investigate_stream(query: InvestigationQuery):
    enriched = query.query
    if query.server:      enriched += f" | server: {query.server}"
    if query.url:         enriched += f" | url: {query.url}"
    if query.db_instance: enriched += f" | db_instance: {query.db_instance}"

    async def _stream():
        async for chunk in stream_investigate(query.user_id, enriched):
            yield f"data: {chunk.replace(chr(10), chr(92)+'n')}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(_stream(), media_type="text/event-stream")
