"""Scrape the sources listed in manifest.csv and build a persisted Chroma vector store.

Run with:  python -m src.ingest
"""

import os
import shutil
import time

import pandas as pd
import requests
import tiktoken
from bs4 import BeautifulSoup
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import APIConnectionError, RateLimitError

from . import config
from .validation import validate_manifest_df

_ENCODING = tiktoken.get_encoding("cl100k_base")

# APIConnectionError also covers APITimeoutError (a subclass) - transient network
# blips (DNS hiccups, dropped connections) as well as rate limits are worth retrying.
RETRYABLE_ERRORS = (RateLimitError, APIConnectionError)

# Structural/non-content tags to drop before extracting text, so nav menus,
# footers, and scripts don't pollute the scraped page content.
STRIP_TAGS = [
    "script",
    "style",
    "noscript",
    "nav",
    "header",
    "footer",
    "iframe",
    "svg",
    "form",
    "button",
    "aside",
]

MULTI_VALUE_COLUMNS = {
    "user_persona": "persona",
    "purpose": "purpose",
    "region_scope": "region",
}
BOOLEAN_COLUMNS = ["accessibility_relevant", "e-bike_focused", "employment_required"]


def _to_bool(value: str) -> bool:
    return str(value).strip().lower() == "true"


def build_metadata(row: pd.Series) -> dict:
    metadata = {
        "title": row["title"],
        "source_org": row["source_org"],
        "url": row["url"],
        "corpus_category": row["corpus_category"],
        "source_type": row["source_type"],
        "budget_band": row["budget_band"],
        "status": row["status"],
        "accessibility_relevant": _to_bool(row["accessibility_relevant"]),
        "e_bike_focused": _to_bool(row["e-bike_focused"]),
        "employment_required": _to_bool(row["employment_required"]),
    }
    for column, prefix in MULTI_VALUE_COLUMNS.items():
        for value in str(row[column]).split(";"):
            value = value.strip().lower()
            if value:
                metadata[f"{prefix}_{value}"] = True
    return metadata


def _clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup.find_all(STRIP_TAGS):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def _fetch_clean_text(url: str) -> str:
    response = requests.get(
        url,
        timeout=config.REQUEST_TIMEOUT,
        headers={"User-Agent": os.environ["USER_AGENT"]},
    )
    response.raise_for_status()
    return _clean_html(response.text)


def load_documents() -> list[Document]:
    df = pd.read_csv(config.MANIFEST_PATH)

    problems = validate_manifest_df(df)
    if problems:
        formatted = "\n".join(f"  - {p}" for p in problems)
        raise ValueError(f"manifest.csv failed validation:\n{formatted}")

    df = df[df["status"] == "active"]

    documents: list[Document] = []
    for _, row in df.iterrows():
        url = row["url"]
        try:
            text = _fetch_clean_text(url)
        except Exception as exc:  # noqa: BLE001 - keep ingesting the rest of the manifest
            print(f"  skip ({exc.__class__.__name__}): {url}")
            continue

        metadata = build_metadata(row)
        metadata["source"] = url
        documents.append(Document(page_content=text, metadata=metadata))
        print(f"  loaded: {url}")

    return documents


def _batch_by_tokens(chunks: list[Document], max_tokens: int) -> list[list[Document]]:
    batches: list[list[Document]] = []
    current_batch: list[Document] = []
    current_tokens = 0

    for chunk in chunks:
        token_count = len(_ENCODING.encode(chunk.page_content))
        if current_batch and current_tokens + token_count > max_tokens:
            batches.append(current_batch)
            current_batch = []
            current_tokens = 0
        current_batch.append(chunk)
        current_tokens += token_count

    if current_batch:
        batches.append(current_batch)
    return batches


def _add_batch_with_retry(
    vectorstore: Chroma, batch: list[Document], max_attempts: int = 5
) -> None:
    delay = config.EMBEDDING_BATCH_DELAY_SECONDS
    for attempt in range(1, max_attempts + 1):
        try:
            vectorstore.add_documents(batch)
            return
        except RETRYABLE_ERRORS as exc:
            if attempt == max_attempts:
                raise
            print(f"    {exc.__class__.__name__}, retrying in {delay:.0f}s... ({exc})")
            time.sleep(delay)
            delay *= 2


def build_vectorstore(documents: list[Document]) -> Chroma:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE, chunk_overlap=config.CHUNK_OVERLAP
    )
    chunks = splitter.split_documents(documents)

    if config.CHROMA_DIR.exists():
        shutil.rmtree(config.CHROMA_DIR)

    embeddings = OpenAIEmbeddings(model=config.EMBEDDING_MODEL)
    vectorstore = Chroma(
        persist_directory=str(config.CHROMA_DIR), embedding_function=embeddings
    )

    batches = _batch_by_tokens(chunks, config.EMBEDDING_BATCH_TOKEN_BUDGET)
    print(f"Embedding {len(chunks)} chunk(s) in {len(batches)} batch(es)...")
    for i, batch in enumerate(batches, start=1):
        _add_batch_with_retry(vectorstore, batch)
        print(f"  batch {i}/{len(batches)} embedded ({len(batch)} chunks)")
        if i < len(batches):
            time.sleep(config.EMBEDDING_BATCH_DELAY_SECONDS)

    return vectorstore


def main() -> None:
    print(f"Reading manifest: {config.MANIFEST_PATH}")
    documents = load_documents()
    print(f"Loaded {len(documents)} page(s). Splitting and embedding...")

    vectorstore = build_vectorstore(documents)
    count = vectorstore._collection.count()
    print(f"Persisted {count} chunk(s) to {config.CHROMA_DIR}")


if __name__ == "__main__":
    main()
