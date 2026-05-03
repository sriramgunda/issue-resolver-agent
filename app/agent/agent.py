"""
Access Resolver Agent — LangChain 1.0 tool-calling edition with RAG.

Uses:
  • Ollama (qwen2.5:7b) as the local LLM via langchain-ollama
  • LangChain 1.0 create_agent (replaces deprecated AgentExecutor pattern)
  • @tool-decorated functions for every action including RAG retrieval
"""

import logging
from typing import Any

from langchain_ollama import ChatOllama
from langchain.agents import create_agent

from app.config import MODEL_NAME, OLLAMA_BASE_URL, TEMPERATURE
from app.agent.prompts import SYSTEM_PROMPT
from app.agent.utils import safe_parse

# ── Tool imports ─────────────────────────────────────────────────────────────
from app.tools.access_tools import (
    check_user_access,
    check_account_locked,
    check_account_exists,
    grant_access,
)
from app.tools.ticketing_tools import create_ticket
from app.tools.log_tools import query_logs
from app.rag.retriever import search_knowledge_base   # ← RAG tool

logger = logging.getLogger(__name__)

# ── Tool registry — RAG tool is listed FIRST so the agent tries it early ─────
TOOLS = [
    search_knowledge_base,      # RAG: check knowledge base before anything else
    check_account_exists,
    check_account_locked,
    check_user_access,
    query_logs,
    grant_access,
    create_ticket,
]


def _build_llm() -> ChatOllama:
    kwargs: dict[str, Any] = {
        "model": MODEL_NAME,
        "temperature": TEMPERATURE,
    }
    if OLLAMA_BASE_URL:
        kwargs["base_url"] = OLLAMA_BASE_URL
    return ChatOllama(**kwargs)


def _build_agent():
    """
    Build a LangChain 1.0 agent using create_agent.
    Backed by a LangGraph graph; handles tool-calling loop internally.
    """
    return create_agent(
        model=_build_llm(),
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
    )


def resolve_access(user_id: str, query: str) -> dict:
    """
    Entry point: resolve an access-related issue for *user_id*.

    Flow:
      1. Agent calls search_knowledge_base first.
         - If a relevant FAQ answer is found → agent returns it directly.
         - If NO_MATCH → agent proceeds to check account, access, logs, etc.
      2. Parses the structured JSON summary from the agent's final output.
      3. Returns a normalized dict for the FastAPI response model.
    """
    agent = _build_agent()

    user_message = f"User ID: {user_id}\nIssue: {query}"

    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": user_message}]}
        )

        messages = result.get("messages", [])
        raw_output = ""
        for msg in reversed(messages):
            if hasattr(msg, "content") and getattr(msg, "type", "") in ("ai", "assistant"):
                raw_output = msg.content if isinstance(msg.content, str) else ""
                break
            if isinstance(msg, dict) and msg.get("role") == "assistant":
                raw_output = msg.get("content", "")
                break

        parsed = safe_parse(raw_output)

    except Exception as exc:
        logger.exception("Agent execution failed: %s", exc)
        parsed = {}

    steps = _extract_tool_steps(result.get("messages", []) if "result" in dir() else [])

    return {
        "intent":     parsed.get("intent", "unknown"),
        "action":     parsed.get("action", "error"),
        "result":     parsed.get("result", "Agent encountered an error — please retry."),
        "ticket_id":  parsed.get("ticket_id"),
        "decision":   parsed.get("decision"),
        "confidence": parsed.get("confidence"),
        "steps":      steps or parsed.get("steps"),
    }


def _extract_tool_steps(messages: list) -> list[str]:
    """Collect tool call names in invocation order from the message trace."""
    steps = []
    for msg in messages:
        tool_calls = getattr(msg, "tool_calls", None)
        if tool_calls:
            for tc in tool_calls:
                name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", None)
                if name:
                    steps.append(name)
    return steps
