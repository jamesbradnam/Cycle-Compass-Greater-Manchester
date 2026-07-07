import pandas as pd
import pytest


@pytest.fixture
def manifest_row() -> pd.Series:
    return pd.Series(
        {
            "title": "Example scheme",
            "source_org": "TfGM",
            "url": "https://example.tfgm.com/scheme",
            "corpus_category": "schemes",
            "region_scope": "manchester;trafford",
            "user_persona": "occasional_cyclist;regular_cyclist",
            "purpose": "commuting;leisure",
            "accessibility_relevant": "false",
            "e-bike_focused": "true",
            "employment_required": "false",
            "budget_band": "low_cost;mid_range",
            "source_type": "official",
            "date_added": "2026/06/29",
            "last_checked": "2026/06/29",
            "status": "active",
            "rationale": "",
            "external_links": "na",
        }
    )


@pytest.fixture
def valid_profile() -> dict:
    return {
        "persona": "fence_sitter",
        "purpose": ["commuting", "leisure"],
        "borough": "manchester",
        "budget_band": "low_cost",
        "accessibility_relevant": False,
        "e_bike_focused": True,
        "employment_required": False,
    }
