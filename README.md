# Cycle Compass (Greater Manchester)
Proof-of-concept web app that personalises the TfGM Bee Network experience. Users complete a short questionnaire and receive two LLM-generated reports: an overview of relevant active travel options, then specific, actionable recommendations with links to official resources. Built with RAG. Not affiliated with TfGM.

## RAG pipeline (`src/`)

Sources are curated in [`manifest.csv`](manifest.csv). The pipeline scrapes each active
source, embeds it with OpenAI, and stores it in a local Chroma vector store, then answers
the questionnaire with two LangChain LCEL chains (overview + recommendations).

### Setup

```bash
python -m venv venv
venv\Scripts\activate        # Windows (use `source venv/bin/activate` on macOS/Linux)
pip install -r requirements.txt
copy .env.example .env       # then add your OPENAI_API_KEY
```

### Usage

```bash
python -m src.ingest   # scrape manifest.csv sources and build ./chroma_db (run once, or after editing manifest.csv)
python -m src.main     # answer the questionnaire and print the two reports
```
