"""Live scenario tests against the real OpenAI API and the ingested Chroma store.

Run explicitly with:  pytest -m live
Requires OPENAI_API_KEY to be set and `python -m src.ingest` to have already
been run. Each scenario costs two small gpt-4o-mini calls (overview +
structured recommendations); the full ~8-scenario matrix is well under $1.
"""

import re

import pandas as pd
import pytest

from src import config
from src.rag import DISCLAIMER, generate_overview, generate_recommendations

pytestmark = pytest.mark.live

if not config.CHROMA_DIR.exists():
    pytest.skip(
        "no vector store found - run `python -m src.ingest` before running live tests",
        allow_module_level=True,
    )

_manifest_df = pd.read_csv(config.MANIFEST_PATH)
MANIFEST_URLS = set(_manifest_df["url"])
EMPLOYMENT_REQUIRED_URLS = set(
    _manifest_df[_manifest_df["employment_required"].astype(str).str.lower() == "true"]["url"]
)

# Curated to cover: every persona at least once; accessibility, e-bike, and
# employment each True and False at least once; a handful of real boroughs
# plus the greater_manchester (None) fallback.
SCENARIOS = [
    {
        "persona": "non_cyclist", "purpose": ["leisure"], "borough": None,
        "budget_band": "free", "accessibility_relevant": True,
        "e_bike_focused": False, "employment_required": False,
    },
    {
        "persona": "fence_sitter", "purpose": ["commuting", "leisure", "errands"], "borough": "manchester",
        "budget_band": "low_cost", "accessibility_relevant": False,
        "e_bike_focused": True, "employment_required": False,
    },
    {
        "persona": "occasional_cyclist", "purpose": ["commuting"], "borough": "trafford",
        "budget_band": "mid_range", "accessibility_relevant": False,
        "e_bike_focused": False, "employment_required": True,
    },
    {
        "persona": "regular_cyclist", "purpose": ["commuting", "errands"], "borough": "salford",
        "budget_band": "high_investment", "accessibility_relevant": False,
        "e_bike_focused": False, "employment_required": True,
    },
    {
        "persona": "non_cyclist", "purpose": ["errands"], "borough": "wigan",
        "budget_band": "low_cost", "accessibility_relevant": True,
        "e_bike_focused": True, "employment_required": False,
    },
    {
        "persona": "fence_sitter", "purpose": ["leisure"], "borough": None,
        "budget_band": "free", "accessibility_relevant": False,
        "e_bike_focused": False, "employment_required": True,
    },
    {
        "persona": "occasional_cyclist", "purpose": ["commuting", "leisure"], "borough": "stockport",
        "budget_band": "mid_range", "accessibility_relevant": True,
        "e_bike_focused": True, "employment_required": False,
    },
    {
        "persona": "regular_cyclist", "purpose": ["leisure", "errands"], "borough": "bolton",
        "budget_band": "free", "accessibility_relevant": False,
        "e_bike_focused": True, "employment_required": False,
    },
]


@pytest.mark.parametrize(
    "profile",
    SCENARIOS,
    ids=[f"{p['persona']}-{p['borough'] or 'gm'}-employed={p['employment_required']}" for p in SCENARIOS],
)
def test_scenario_report_is_well_formed(profile):
    # Stage 1: only what's known after the first 4 questions.
    overview_profile = {
        "persona": profile["persona"],
        "purpose": profile["purpose"],
        "borough": profile["borough"],
        "accessibility_relevant": profile["accessibility_relevant"],
    }
    overview = generate_overview(overview_profile)

    # Guaranteed by code (see rag.py), asserted here as a regression guard.
    assert overview["disclaimer"] == DISCLAIMER
    assert not re.search(r"https?://", overview["overview"]), (
        "overview should not include raw links - those belong in the recommendations report"
    )

    # Stage 2: all 7 answers known.
    recommendations = generate_recommendations(profile)
    assert recommendations["disclaimer"] == DISCLAIMER

    recs = recommendations["recommendations"]
    assert recs or recommendations["note"], "no recommendations and no honest note"

    urls = [r.url for r in recs]
    assert len(urls) == len(set(urls)), f"duplicate URLs cited: {urls}"

    for url in urls:
        assert url in MANIFEST_URLS, f"hallucinated url not in manifest.csv: {url}"
        if not profile["employment_required"]:
            assert url not in EMPLOYMENT_REQUIRED_URLS, (
                f"recommended an employment-required source for a non-employed profile: {url}"
            )
