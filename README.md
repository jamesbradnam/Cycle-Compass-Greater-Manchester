# Cycle Compass (Greater Manchester)

Proof-of-concept web app that personalises the TfGM Bee Network experience. Users complete a short questionnaire and receive two LLM-generated reports: an overview of relevant active travel options, then specific, actionable recommendations with links to official resources. Built with RAG. Not affiliated with TfGM.

## RAG pipeline (`src/`)

Sources are curated in [`manifest.csv`](manifest.csv). The pipeline scrapes each active
source, embeds it with OpenAI, and stores it in a local Chroma vector store, then answers
the questionnaire with two LangChain LCEL chains (overview + recommendations).

### Setup

```Shell
python -m venv venv
venv\Scripts\activate        # Windows (use `source venv/bin/activate` on macOS/Linux)
pip install -r requirements.txt
copy .env.example .env       # then add your OPENAI_API_KEY
```

### Usage

```Shell
python -m src.ingest   # scrape manifest.csv sources and build ./chroma_db (run once, or after editing manifest.csv)
python -m src.main     # CLI: answer the questionnaire and print both reports
```

The questionnaire has two stages: borough/persona/purpose/accessibility_relevant produce the
OVERVIEW report, then e_bike_focused/budget_band/employment_required produce the
RECOMMENDATIONS report (`src/questions.py` is the single source of truth for this order,
shared by both the CLI and the API).

### Testing

```Shell
pip install -r requirements-dev.txt
pytest              # free, local unit tests - no network/API calls, safe to run anytime
pytest -m live      # live tests against the real OpenAI API and an ingested ./chroma_db
```

The `live` suite runs a curated ~8-scenario profile matrix through `generate_overview`/
`generate_recommendations` (plus a couple of tests through the actual `/api/overview` and
`/api/recommendations` endpoints) and checks for real regressions (employment-mismatched
recommendations, hallucinated or duplicate URLs, missing disclaimer, raw links leaking into
the overview). It costs a small fraction of a cent per scenario with `gpt-4o-mini`, but isn't
run by default - only via the explicit `-m live` flag - so a plain `pytest` never spends money.

## Full-stack app (backend API + React frontend)

`src/api.py` is a FastAPI app exposing the same RAG pipeline over HTTP for the React frontend
in `frontend/`. It also records funnel analytics (question views/answers, the continue click,
recommendation link clicks) to a local SQLite file, `analytics.db` - profile answers and
generated report text are never stored, only the fact that these events happened.

### Run locally (two terminals)

```Shell
# Terminal 1 - backend API
venv\Scripts\activate
uvicorn src.api:app --reload --port 8000

# Terminal 2 - frontend
cd frontend
npm install     # first time only
npm run dev     # opens http://localhost:5173
```

The Vite dev server proxies `/api/*` requests to `http://localhost:8000` (see
`frontend/vite.config.js`), so no CORS setup is needed for local dev.

### Querying the analytics funnel

No dashboard yet - query `analytics.db` directly, e.g.:

```Shell
sqlite3 analytics.db "select event_type, count(*) from events group by event_type"
sqlite3 analytics.db "select payload, count(*) from events where event_type = 'recommendation_link_clicked' group by payload"
```
