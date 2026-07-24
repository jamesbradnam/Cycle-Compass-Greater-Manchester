import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault("USER_AGENT", "CycleCompassBot/0.1 (+https://github.com/jamesbradnam)")

ROOT_DIR = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT_DIR / "manifest.csv"
CHROMA_DIR = ROOT_DIR / "chroma_db"
ANALYTICS_DB_PATH = ROOT_DIR / "analytics.db"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
REQUEST_TIMEOUT = 15
RETRIEVER_K = 10

# Bound both how long we'll wait on a chat completion and how much it can
# generate, so a pathological or oversized prompt fails fast and visibly
# instead of hanging indefinitely (a real report generation should easily fit
# well within these).
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "45"))
OVERVIEW_MAX_TOKENS = int(os.getenv("OVERVIEW_MAX_TOKENS", "500"))
RECOMMENDATIONS_MAX_TOKENS = int(os.getenv("RECOMMENDATIONS_MAX_TOKENS", "700"))

# Keep each embeddings API call well under typical tokens-per-minute limits,
# and pace batches so consecutive calls don't stack up within the same
# rolling one-minute window. Override via env if your org's TPM tier differs.
EMBEDDING_BATCH_TOKEN_BUDGET = int(os.getenv("EMBEDDING_BATCH_TOKEN_BUDGET", "8000"))
EMBEDDING_BATCH_DELAY_SECONDS = float(os.getenv("EMBEDDING_BATCH_DELAY_SECONDS", "15"))
