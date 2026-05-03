"""
Access Resolver Agent — LangChain 1.0 tool-calling edition.

Uses:
  • Ollama  (qwen2.5:7b) as the local LLM via langchain-ollama
  • LangChain 1.0  create_agent  (replaces the deprecated
    create_tool_calling_agent + AgentExecutor pattern)
  • @tool-decorated functions for every side-effectful action
"""

import logging
from typing import Any

from langchain_ollama import ChatOllama
from langchain.agents import create_agent          # LangChain 1.0 API

from app.config import MODEL_NAME, OLLAMA_BASE_URL, TEMPERATURE
from app.agent.prompts import SYSTEM_PROMPT
from app.agent.utils import safe_parse

# ── Tool imports (all decorated with @tool) ──────────────────────────────────
from app.tools.access_tools import (
    check_user_access,
    check_account_locked,
    check_account_exists,
    grant_access,
)
from app.tools.ticketing_tools import create_ticket
from app.tools.log_tools import query_logs

logger = logging.getLogger(__name__)

# ── Tool registry ─────────────────────────────────────────────────────────────
TOOLS = [
    check_account_exists,
    check_account_locked,
    check_user_access,
    query_logs,
    grant_access,
    create_ticket,
]


# ── LLM factory ───────────────────────────────────────────────────────────────
def _build_llm() -> ChatOllama:
    kwargs: dict[str, Any] = {
        "model": MODEL_NAME,
        "temperature": TEMPERATURE,
    }
    if OLLAMA_BASE_URL:
        kwargs["base_url"] = OLLAMA_BASE_URL
    return ChatOllama(**kwargs)


# ── Agent factory ─────────────────────────────────────────────────────────────
def _build_agent():
    """
    Build a LangChain 1.0 agent using create_agent.

    create_agent:
      - Replaces the deprecated create_tool_calling_agent + AgentExecutor.
      - Backed by a LangGraph graph for durability and streaming support.
      - Accepts tools as plain @tool-decorated functions.
      - system_prompt sets the agent's persona and resolution rules.
    """
    llm = _build_llm()

    return create_agent(
        model=llm,
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
    )


# ── Public API ────────────────────────────────────────────────────────────────
def resolve_access(user_id: str, query: str) -> dict:
    """
    Entry point: resolve an access-related issue for *user_id*.

    1. Builds a fresh create_agent instance.
    2. Invokes it with the user query — the agent autonomously calls tools.
    3. Parses the structured JSON summary from the agent's final output.
    4. Returns a normalized dict for the FastAPI response model.
    """
    agent = _build_agent()

    user_message = (
        f"User ID: {user_id}\n"
        f"Issue: {query}"
    )

    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": user_message}]}
        )

        # Extract final assistant message from the messages list
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

    # Collect tool call names as the "steps" trace
    steps = _extract_tool_steps(result.get("messages", []))

    return {
        "intent":    parsed.get("intent", "unknown"),
        "action":    parsed.get("action", "error"),
        "result":    parsed.get("result", "Agent encountered an error — please retry."),
        "ticket_id": parsed.get("ticket_id"),
        "decision":  parsed.get("decision"),
        "confidence": parsed.get("confidence"),
        "steps":     steps or parsed.get("steps"),
    }


def _extract_tool_steps(messages: list) -> list[str]:
    """
    Walk the message trace and collect each tool call name in order.
    Gives the caller visibility into which tools the agent invoked.
    """
    steps = []
    for msg in messages:
        # LangChain AIMessage with tool_calls attribute
        tool_calls = getattr(msg, "tool_calls", None)
        if tool_calls:
            for tc in tool_calls:
                name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", None)
                if name:
                    steps.append(name)
    return steps