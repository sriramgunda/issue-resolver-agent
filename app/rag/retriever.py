"""
RAG retriever — exposed as a LangChain @tool AND as a direct fast-path function.

Two usage modes:
  1. search_knowledge_base(@tool) — called by the agent inside the tool-calling loop.
  2. rag_fast_path() — called BEFORE the agent in main.py.
     If confidence >= RAG_THRESHOLD, we return immediately without touching the LLM.
     Typical latency: < 50 ms (pure vector similarity, no tokens generated).
"""

from langchain_core.tools import tool
from app.rag.vector_store import get_vector_store
from app.config import RAG_THRESHOLD

TOP_K = 3


def _search(query: str, k: int = TOP_K) -> list[tuple[float, object]]:
    """Run similarity search; return (similarity, doc) pairs sorted best-first."""
    store = get_vector_store()
    raw = store.similarity_search_with_score(query, k=k)
    hits = []
    for doc, score in raw:
        similarity = float(1.0 / (1.0 + score))   # cast numpy.float32 → Python float
        hits.append((similarity, doc))
    hits.sort(key=lambda x: x[0], reverse=True)
    return hits


def rag_fast_path(query: str) -> dict | None:
    """
    Attempt to answer the query purely from the knowledge base.

    Returns a response dict (same shape as resolve_access()) if a high-confidence
    match is found, or None if the agent should handle it instead.

    Threshold is set via RAG_THRESHOLD env var (default 0.80).
    """
    hits = _search(query, k=1)
    if not hits:
        return None
    similarity, doc = hits[0]
    if similarity < RAG_THRESHOLD:
        return None
    return {
        "intent":     "faq_match",
        "action":     "knowledge_base_answer",
        "result":     doc.metadata["answer"],
        "ticket_id":  None,
        "decision":   f"High-confidence FAQ match (relevance {similarity:.0%}): {doc.metadata['question']}",
        "confidence": round(similarity, 3),
        "steps":      ["search_knowledge_base"],
    }


@tool
def search_knowledge_base(query: str) -> str:
    """
    Search the internal FAQ / knowledge base for answers related to the user query.

    Use this tool FIRST whenever the user describes a problem that might already
    have a documented solution (login issues, MFA, VPN, access requests, etc.).

    Args:
        query: The user's issue or question in natural language.

    Returns:
        Formatted string with top matching FAQ answers, or 'NO_MATCH'.
    """
    hits = _search(query)
    if not hits:
        return "NO_MATCH"

    threshold = 0.65
    filtered = [(s, d) for s, d in hits if s >= threshold]
    if not filtered:
        return "NO_MATCH"

    lines = ["Relevant solutions from the knowledge base:\n"]
    for i, (sim, doc) in enumerate(filtered, 1):
        lines.append(
            f"{i}. Q: {doc.metadata['question']}\n"
            f"   A: {doc.metadata['answer']}\n"
            f"   (relevance: {sim:.0%}, category: {doc.metadata['category']})\n"
        )
    return "\n".join(lines)