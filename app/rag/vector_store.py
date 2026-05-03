"""
FAISS vector store — built from FAQ_DATA at startup and cached in memory.

Uses OllamaEmbeddings (nomic-embed-text) as the embedding model so we
stay fully local with no external API keys.
Falls back to a lightweight sentence-transformers model if Ollama is
unavailable (useful for CI / unit tests).
"""

import logging
from functools import lru_cache
from typing import Optional

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from app.rag.faq_data import FAQ_DATA

logger = logging.getLogger(__name__)

# ── Embedding model ───────────────────────────────────────────────────────────

def _build_embeddings():
    """
    Try OllamaEmbeddings first; fall back to HuggingFaceEmbeddings.
    """
    try:
        from langchain_ollama import OllamaEmbeddings
        from app.config import OLLAMA_BASE_URL
        logger.info("Using OllamaEmbeddings (nomic-embed-text)")
        return OllamaEmbeddings(
            model="nomic-embed-text",
            base_url=OLLAMA_BASE_URL,
        )
    except Exception as exc:
        logger.warning("OllamaEmbeddings unavailable (%s); falling back to HuggingFace.", exc)
        from langchain_community.embeddings import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


# ── Document preparation ──────────────────────────────────────────────────────

def _build_documents() -> list[Document]:
    """
    Convert FAQ_DATA entries into LangChain Documents.
    The page_content is the canonical question so similarity search
    finds the best question match; the answer is stored in metadata.
    """
    docs = []
    for entry in FAQ_DATA:
        docs.append(
            Document(
                page_content=entry["question"],
                metadata={
                    "answer": entry["answer"],
                    "category": entry["category"],
                    "question": entry["question"],
                },
            )
        )
    return docs


# ── Singleton vector store ────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_vector_store() -> FAISS:
    """
    Build (once) and cache the FAISS index from FAQ documents.
    Thread-safe via Python's GIL + lru_cache.
    """
    logger.info("Building FAISS vector store from %d FAQ entries …", len(FAQ_DATA))
    embeddings = _build_embeddings()
    docs = _build_documents()
    store = FAISS.from_documents(docs, embeddings)
    logger.info("FAISS vector store ready.")
    return store
