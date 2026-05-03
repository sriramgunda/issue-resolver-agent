"""
RAG retriever exposed as a LangChain @tool so the agent can call it
whenever it decides the user query might be answerable from the knowledge base.

Search strategy:
  1. Cosine-similarity search against the FAISS FAQ index.
  2. Only return results whose similarity score is above SIMILARITY_THRESHOLD.
  3. Return the top-k answers formatted as a numbered list.
  4. If nothing relevant is found, return a clear "no match" string so the
     agent knows to fall back to the tool-calling resolution flow.
"""

from langchain_core.tools import tool
from app.rag.vector_store import get_vector_store

# Tune these via env vars if needed
TOP_K = 3
SIMILARITY_THRESHOLD = 0.65   # cosine distance; lower = more similar in FAISS


@tool
def search_knowledge_base(query: str) -> str:
    """
    Search the internal FAQ / knowledge base for answers related to the user query.

    Use this tool FIRST whenever the user describes a problem or asks a question
    that might already have a documented solution (e.g. login issues, MFA problems,
    VPN troubleshooting, access request procedures, password reset steps).

    Args:
        query: The user's issue or question in natural language.

    Returns:
        A formatted string with the top matching FAQ answers,
        or "NO_MATCH" if no relevant entries were found.
    """
    store = get_vector_store()

    # similarity_search_with_score returns (Document, score) pairs
    # FAISS returns L2 distances — lower is better; convert to similarity
    results = store.similarity_search_with_score(query, k=TOP_K)

    hits = []
    for doc, score in results:
        # FAISS L2 distance → approximate cosine similarity (for normalised vectors)
        similarity = 1.0 / (1.0 + score)
        if similarity >= SIMILARITY_THRESHOLD:
            hits.append((similarity, doc))

    if not hits:
        return "NO_MATCH"

    # Sort best-first
    hits.sort(key=lambda x: x[0], reverse=True)

    lines = ["Here are the relevant solutions from the knowledge base:\n"]
    for i, (sim, doc) in enumerate(hits, 1):
        lines.append(
            f"{i}. Q: {doc.metadata['question']}\n"
            f"   A: {doc.metadata['answer']}\n"
            f"   (relevance: {sim:.0%}, category: {doc.metadata['category']})\n"
        )

    return "\n".join(lines)
