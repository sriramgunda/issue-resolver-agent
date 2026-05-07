import os
import dotenv
dotenv.load_dotenv()

MODEL_NAME: str      = os.getenv("MODEL_NAME", "qwen2.5:7b-instruct-q4_K_M")  # quantised by default
MODEL_FALLBACK: str  = os.getenv("MODEL_FALLBACK", "qwen2.5:3b")               # fast path for simple queries
TEMPERATURE: float   = float(os.getenv("TEMPERATURE", "0.0"))
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
KEEP_ALIVE: str      = os.getenv("KEEP_ALIVE", "-1m")   # -1 = keep model in VRAM forever
NUM_CTX: int         = int(os.getenv("NUM_CTX", "2048"))   # trim context window

VECTOR_DB_PATH: str  = os.getenv("VECTOR_DB_PATH", "vectorstore")
RAG_THRESHOLD: float = float(os.getenv("RAG_THRESHOLD", "0.80"))  # above this → skip LLM