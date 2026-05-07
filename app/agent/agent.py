"""
Access Resolver Agent — LangChain 1.0 + performance optimisations.

Speed improvements applied:
  1. Streaming  — agent.astream_events() fed to SSE endpoint (see main.py).
  2. Quantised model — qwen2.5:7b-instruct-q4_K_M (2-3× faster, same quality).
  3. RAG short-circuit — handled in main.py BEFORE agent is invoked.
  4. Async invocation — ainvoke() / astream_events() instead of blocking invoke().
  5. Ollama keep_alive=-1 — model stays loaded in VRAM between requests.
  6. Reduced context window (num_ctx=2048) — fewer KV-cache allocations.
"""

import logging
from typing import Any, AsyncIterator

from langchain_ollama import ChatOllama
from langchain.agents import create_agent

from app.config import MODEL_NAME, OLLAMA_BASE_URL, TEMPERATURE, KEEP_ALIVE, NUM_CTX
from app.agent.prompts import SYSTEM_PROMPT
from app.agent.utils import safe_parse

from app.tools.access_tools import (
    check_user_access, check_account_locked, check_account_exists, grant_access,
)
from app.tools.ticketing_tools import create_ticket
from app.tools.log_tools import query_logs
from app.rag.retriever import search_knowledge_base

logger = logging.getLogger(__name__)

TOOLS = [
    search_knowledge_base,
    check_account_exists,
    check_account_locked,
    check_user_access,
    query_logs,
    grant_access,
    create_ticket,
]


def _build_llm(model: str = MODEL_NAME) -> ChatOllama:
    kwargs: dict[str, Any] = {
        "model":       model,
        "temperature": TEMPERATURE,
        "keep_alive":  KEEP_ALIVE,   # ← keep model warm in VRAM
        "num_ctx":     NUM_CTX,      # ← smaller context = faster
    }
    if OLLAMA_BASE_URL:
        kwargs["base_url"] = OLLAMA_BASE_URL
    return ChatOllama(**kwargs)


def _build_agent(model: str = MODEL_NAME):
    return create_agent(
        model=_build_llm(model),
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
    )


# ── Blocking (used by tests / non-streaming callers) ──────────────────────────
def resolve_access(user_id: str, query: str) -> dict:
    agent = _build_agent()
    user_message = f"User ID: {user_id}\nIssue: {query}"
    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": user_message}]}
        )
        messages  = result.get("messages", [])
        raw_output = _extract_last_ai_text(messages)
        parsed    = safe_parse(raw_output)
    except Exception as exc:
        logger.exception("Agent execution failed: %s", exc)
        parsed = {}

    return _normalise(parsed, result.get("messages", []) if "result" in dir() else [])


# ── Async streaming (used by /stream SSE endpoint) ────────────────────────────
async def stream_resolve_access(user_id: str, query: str) -> AsyncIterator[str]:
    """
    Yield raw text tokens as they are produced by the model.
    Callers wrap this in a FastAPI StreamingResponse / EventSourceResponse.
    """
    agent = _build_agent()
    user_message = f"User ID: {user_id}\nIssue: {query}"

    async for event in agent.astream_events(
        {"messages": [{"role": "user", "content": user_message}]},
        version="v2",
    ):
        kind = event.get("event", "")
        # Yield text chunks as they arrive from the LLM
        if kind == "on_chat_model_stream":
            chunk = event.get("data", {}).get("chunk")
            if chunk and hasattr(chunk, "content") and isinstance(chunk.content, str):
                yield chunk.content
        # Yield tool-call notifications so the UI can show "checking access…"
        elif kind == "on_tool_start":
            tool_name = event.get("name", "tool")
            yield f"\n[tool:{tool_name}]\n"


# ── Helpers ───────────────────────────────────────────────────────────────────
def _extract_last_ai_text(messages: list) -> str:
    for msg in reversed(messages):
        if hasattr(msg, "content") and getattr(msg, "type", "") in ("ai", "assistant"):
            return msg.content if isinstance(msg.content, str) else ""
        if isinstance(msg, dict) and msg.get("role") == "assistant":
            return msg.get("content", "")
    return ""


def _extract_tool_steps(messages: list) -> list[str]:
    steps = []
    for msg in messages:
        for tc in getattr(msg, "tool_calls", None) or []:
            name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", None)
            if name:
                steps.append(name)
    return steps


def _normalise(parsed: dict, messages: list) -> dict:
    return {
        "intent":     parsed.get("intent", "unknown"),
        "action":     parsed.get("action", "error"),
        "result":     parsed.get("result", "Agent encountered an error — please retry."),
        "ticket_id":  parsed.get("ticket_id"),
        "decision":   parsed.get("decision"),
        "confidence": parsed.get("confidence"),
        "steps":      _extract_tool_steps(messages) or parsed.get("steps"),
    }