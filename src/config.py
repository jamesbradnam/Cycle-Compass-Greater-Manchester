import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault("USER_AGENT", "CycleCompassBot/0.1 (+https://github.com/jamesbradnam)")

ROOT_DIR = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT_DIR / "manifest.csv"
CHROMA_DIR = ROOT_DIR / "chroma_db"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
REQUEST_TIMEOUT = 15
RETRIEVER_K = 8

# Keep each embeddings API call well under typical tokens-per-minute limits,
# and pace batches so consecutive calls don't stack up within the same
# rolling one-minute window. Override via env if your org's TPM tier differs.
EMBEDDING_BATCH_TOKEN_BUDGET = int(os.getenv("EMBEDDING_BATCH_TOKEN_BUDGET", "8000"))
EMBEDDING_BATCH_DELAY_SECONDS = float(os.getenv("EMBEDDING_BATCH_DELAY_SECONDS", "15"))
