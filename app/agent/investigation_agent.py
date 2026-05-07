"""
Investigation Agent — diagnoses infrastructure issues.

Issue types handled:
  - RDP session failures
  - Server not responding / unreachable
  - Web URL / HTTP endpoint failures
  - Database session failures
  - General port / network / service issues

Separate from the Access Resolver Agent — each agent has its own
tool set, system prompt, and response schema.
"""

import logging
import re
from typing import Any, AsyncIterator

from langchain_ollama import ChatOllama
from langchain.agents import create_agent

from app.config import MODEL_NAME, OLLAMA_BASE_URL, TEMPERATURE, KEEP_ALIVE, NUM_CTX
from app.agent.investigation_prompts import INVESTIGATION_SYSTEM_PROMPT
from app.agent.utils import safe_parse
from app.tools.investigation_tools import (
    check_rdp_session,
    check_server_health,
    check_web_url,
    check_db_session,
    check_port_connectivity,
    check_service_status,
    check_network_latency,
)
from app.tools.ticketing_tools import create_ticket

logger = logging.getLogger(__name__)

INVESTIGATION_TOOLS = [
    check_server_health,
    check_rdp_session,
    check_web_url,
    check_db_session,
    check_port_connectivity,
    check_service_status,
    check_network_latency,
    create_ticket,
]

# ── Issue classifier (fast regex — avoids an extra LLM call) ─────────────────
_ISSUE_PATTERNS = {
    "rdp":        re.compile(r"\brdp\b|remote\s*desktop|mstsc", re.I),
    "server_down": re.compile(r"server.*(down|not.respond|unreachable|offline|crash)", re.I),
    "web_url":    re.compile(r"https?://|url|website|web\s*page|404|502|503|ssl|cert", re.I),
    "db_session": re.compile(r"\bdb\b|database|postgres|mysql|mssql|oracle|mongo|sql\s*server|connection\s*pool", re.I),
    "network":    re.compile(r"latency|packet.loss|ping|timeout|slow\s*connect|network", re.I),
    "service":    re.compile(r"service.*(stop|crash|restart|fail)|nginx|apache|tomcat|iis", re.I),
}

def _classify_issue(query: str) -> str:
    for issue_type, pattern in _ISSUE_PATTERNS.items():
        if pattern.search(query):
            return issue_type
    return "unknown"


# ── LLM / agent builder ───────────────────────────────────────────────────────
def _build_llm() -> ChatOllama:
    kwargs: dict[str, Any] = {
        "model":       MODEL_NAME,
        "temperature": TEMPERATURE,
        "keep_alive":  KEEP_ALIVE,
        "num_ctx":     NUM_CTX,
    }
    if OLLAMA_BASE_URL:
        kwargs["base_url"] = OLLAMA_BASE_URL
    return ChatOllama(**kwargs)


def _build_agent():
    return create_agent(
        model=_build_llm(),
        tools=INVESTIGATION_TOOLS,
        system_prompt=INVESTIGATION_SYSTEM_PROMPT,
    )


# ── Public API ────────────────────────────────────────────────────────────────
def investigate(user_id: str, query: str) -> dict:
    """
    Entry point — investigate a customer's infrastructure issue.

    1. Classifies the issue type (fast regex, no LLM call).
    2. Runs the investigation agent with tool-calling.
    3. Returns a structured diagnosis dict.
    """
    issue_type = _classify_issue(query)
    agent = _build_agent()
    message = f"User ID: {user_id}\nIssue: {query}\nDetected issue type: {issue_type}"

    result = {}
    try:
        result   = agent.invoke({"messages": [{"role": "user", "content": message}]})
        messages = result.get("messages", [])
        raw_text = _extract_last_ai_text(messages)
        parsed   = safe_parse(raw_text)
    except Exception as exc:
        logger.exception("Investigation agent failed: %s", exc)
        parsed = {}

    return _normalise(parsed, result.get("messages", []), issue_type)


async def stream_investigate(user_id: str, query: str) -> AsyncIterator[str]:
    """Streaming variant — yields tokens + tool-call notifications."""
    issue_type = _classify_issue(query)
    agent = _build_agent()
    message = f"User ID: {user_id}\nIssue: {query}\nDetected issue type: {issue_type}"

    async for event in agent.astream_events(
        {"messages": [{"role": "user", "content": message}]}, version="v2"
    ):
        kind = event.get("event", "")
        if kind == "on_chat_model_stream":
            chunk = event.get("data", {}).get("chunk")
            if chunk and hasattr(chunk, "content") and isinstance(chunk.content, str):
                yield chunk.content
        elif kind == "on_tool_start":
            yield f"\n[investigating:{event.get('name', 'tool')}]\n"


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


def _normalise(parsed: dict, messages: list, detected_type: str) -> dict:
    return {
        "issue_type":        parsed.get("issue_type", detected_type),
        "severity":          parsed.get("severity", "medium"),
        "root_cause":        parsed.get("root_cause", "Unknown — see steps for details"),
        "affected_resource": parsed.get("affected_resource"),
        "resolution":        parsed.get("resolution", "Investigation incomplete — please retry."),
        "ticket_raised":     parsed.get("ticket_raised", False),
        "ticket_id":         parsed.get("ticket_id"),
        "confidence":        float(parsed.get("confidence", 0.0)) if parsed.get("confidence") else 0.0,
        "steps":             _extract_tool_steps(messages) or parsed.get("steps_taken", []),
    }
