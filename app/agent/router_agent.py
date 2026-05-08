"""
Router Agent — LLM-based query classifier and dispatcher.

Flow:
  1. A lightweight LLM call classifies the query into:
       access_issue  → AccessResolverAgent
       investigation → InvestigationAgent
       ambiguous     → both agents run; higher-confidence result is primary

  2. The appropriate specialist agent is invoked (blocking or async streaming).

  3. A unified RouterResponse is returned so the caller always gets the
     same envelope regardless of which agent handled it.

Why LLM classification (not regex):
  - "I can't connect to the DB" is ambiguous: wrong password OR server down?
  - "App1 not working for me" could be access OR infra.
  - The LLM understands full sentence context; regex only pattern-matches keywords.
"""

import json
import logging
from typing import Any, AsyncIterator

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import MODEL_NAME, OLLAMA_BASE_URL, KEEP_ALIVE
from app.agent.agent import resolve_access, stream_resolve_access
from app.agent.investigation_agent import investigate, stream_investigate

logger = logging.getLogger(__name__)


# ── Classification prompt ─────────────────────────────────────────────────────
_CLASSIFY_SYSTEM = """\
You are a query classification engine for an IT support system.

Your ONLY job is to read a user's issue description and classify it into
exactly one category. Return JSON only — no explanation, no preamble.

## Categories

"access_issue"
  The root cause is about identity, credentials, or permissions:
  • Cannot log in / authentication failure / wrong password
  • Account locked, disabled, expired, or not found
  • Missing role or permission on an app or server (ACCESS_DENIED, 401, 403)
  • Password reset, MFA not working, SSO redirect loop
  • Access request ("I need access to X") or access revoked
  • VPN account expired

"investigation"
  The root cause is a technical or infrastructure failure:
  • RDP / Remote Desktop session failing, dropping, or not connecting
  • Server unreachable, not responding, crashed, or rebooting
  • Web URL returning errors (404, 502, 503, SSL error, timeout)
  • Database connection failing, pool exhausted, DB port unreachable
  • A specific service or process is down (nginx, tomcat, mssql, postgresql)
  • Network latency, packet loss, port closed, firewall blocking traffic
  • High CPU / memory / disk causing service degradation

"ambiguous"
  The query could plausibly be either category. Use sparingly:
  • "Can't connect to the database" (wrong credentials OR DB server down?)
  • "App is not working for me" (no permission OR server crashed?)

## Return ONLY this JSON object:
{
  "category":   "access_issue" | "investigation" | "ambiguous",
  "confidence": <float 0.00–1.00>,
  "reason":     "<one concise sentence explaining the classification>"
}
"""


# ── LLM — tiny context, deterministic ────────────────────────────────────────
def _build_classifier_llm() -> ChatOllama:
    kwargs: dict[str, Any] = {
        "model":       MODEL_NAME,
        "temperature": 0.0,      # must be deterministic
        "keep_alive":  KEEP_ALIVE,
        "num_ctx":     512,      # classification needs minimal context
    }
    if OLLAMA_BASE_URL:
        kwargs["base_url"] = OLLAMA_BASE_URL
    return ChatOllama(**kwargs)


# ── Classifier ────────────────────────────────────────────────────────────────
def classify_query(query: str) -> dict:
    """
    Use the LLM to classify a user query.

    Returns:
        {"category": str, "confidence": float, "reason": str}
    """
    llm = _build_classifier_llm()
    messages = [
        SystemMessage(content=_CLASSIFY_SYSTEM),
        HumanMessage(content=f"Classify this IT support query:\n\n{query}"),
    ]
    try:
        response = llm.invoke(messages)
        raw = response.content if hasattr(response, "content") else str(response)

        # Strip markdown fences if the model wraps output in ```json … ```
        clean = raw.strip()
        if "```" in clean:
            parts = clean.split("```")
            for part in parts:
                stripped = part.strip().lstrip("json").strip()
                if stripped.startswith("{"):
                    clean = stripped
                    break

        result = json.loads(clean)
        return {
            "category":   result.get("category", "ambiguous"),
            "confidence": float(result.get("confidence", 0.5)),
            "reason":     result.get("reason", ""),
        }

    except Exception as exc:
        logger.warning("LLM classification failed (%s) — defaulting to ambiguous", exc)
        return {
            "category":   "ambiguous",
            "confidence": 0.0,
            "reason":     f"classification error: {exc}",
        }


# ── Blocking router ───────────────────────────────────────────────────────────
def route_and_resolve(user_id: str, query: str) -> dict:
    """
    1. Classify the query with the LLM.
    2. Dispatch to access_resolver, investigation, or both agents.
    3. Return a unified response dict.
    """
    classification = classify_query(query)
    category       = classification["category"]

    logger.info(
        "Router | user=%s  category=%s  confidence=%.2f  reason=%s",
        user_id, category, classification["confidence"], classification["reason"],
    )

    if category == "access_issue":
        result = resolve_access(user_id, query)
        return _wrap(result, classification, agent_used="access_resolver")

    elif category == "investigation":
        result = investigate(user_id, query)
        return _wrap(result, classification, agent_used="investigation")

    else:   # ambiguous — run both, pick winner by confidence
        logger.info("Ambiguous — running both agents for user %s", user_id)
        access_result = resolve_access(user_id, query)
        invest_result = investigate(user_id, query)
        return _merge(access_result, invest_result, classification)


# ── Async streaming router ────────────────────────────────────────────────────
async def stream_route_and_resolve(user_id: str, query: str) -> AsyncIterator[str]:
    """
    1. Classify synchronously (fast, single LLM call, tiny context).
    2. Stream tokens from the chosen specialist agent.
    3. Yield a final SSE event with the classification metadata.
    """
    classification = classify_query(query)
    category       = classification["category"]

    logger.info(
        "Router (stream) | user=%s  category=%s  confidence=%.2f",
        user_id, category, classification["confidence"],
    )

    # Emit classification decision as first SSE event so the UI can show it
    yield json.dumps({
        "type":       "classification",
        "category":   category,
        "confidence": classification["confidence"],
        "reason":     classification["reason"],
        "agent_used": "access_resolver" if category == "access_issue"
                      else "investigation" if category == "investigation"
                      else "both",
    })

    if category == "access_issue":
        async for chunk in stream_resolve_access(user_id, query):
            yield chunk

    elif category == "investigation":
        async for chunk in stream_investigate(user_id, query):
            yield chunk

    else:
        # For ambiguous queries stream the investigation agent
        # (more verbose, better suited for streaming diagnostics)
        # and note that access resolution also ran (blocking, prepended as event)
        access_result = resolve_access(user_id, query)
        yield json.dumps({"type": "access_result", **access_result})
        async for chunk in stream_investigate(user_id, query):
            yield chunk


# ── Response helpers ──────────────────────────────────────────────────────────
def _wrap(agent_result: dict, classification: dict, agent_used: str) -> dict:
    """Attach router metadata to an agent result."""
    return {
        "agent_used":                agent_used,
        "category":                  classification["category"],
        "classification_confidence": classification["confidence"],
        "classification_reason":     classification["reason"],
        **agent_result,
    }


def _merge(access: dict, invest: dict, classification: dict) -> dict:
    """
    Merge results from both agents.
    The agent with the higher confidence score becomes the primary result.
    The other is attached under 'supplementary'.
    """
    access_conf = float(access.get("confidence") or 0.0)
    invest_conf = float(invest.get("confidence") or 0.0)

    if access_conf >= invest_conf:
        primary, secondary = access, invest
        primary_name, secondary_name = "access_resolver", "investigation"
    else:
        primary, secondary = invest, access
        primary_name, secondary_name = "investigation", "access_resolver"

    return {
        "agent_used":                "both",
        "category":                  "ambiguous",
        "classification_confidence": classification["confidence"],
        "classification_reason":     classification["reason"],
        **primary,
        "supplementary": {
            "agent":      secondary_name,
            "result":     secondary.get("result") or secondary.get("resolution"),
            "confidence": secondary.get("confidence"),
            "steps":      secondary.get("steps"),
        },
    }
