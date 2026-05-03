import os
import dotenv

dotenv.load_dotenv()

# ── LLM ─────────────────────────────────────────────────────────────────────
# Default to qwen2.5:7b as requested; override via MODEL_NAME env var
MODEL_NAME: str = os.getenv("MODEL_NAME", "qwen2.5:7b")
TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.0"))

# Ollama endpoint — defaults to localhost; override for Docker / k8s
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# ── Vector store ─────────────────────────────────────────────────────────────
VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", "vectorstore")
