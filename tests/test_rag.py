import pytest

from src.rag import (
    DISCLAIMER,
    Recommendation,
    RecommendationsReport,
    _format_docs,
    _profile_to_query,
    _region_filter,
    _region_tags,
    _retrieval_filter,
)
from src.validation import validate_profile


def test_region_filter_always_includes_universal_regions():
    result = _region_filter(None)
    assert result == {
        "$or": [{"region_greater_manchester": True}, {"region_national": True}]
    }


def test_region_filter_adds_borough_when_given():
    result = _region_filter("Trafford")
    clauses = result["$or"]
    assert {"region_trafford": True} in clauses
    assert {"region_greater_manchester": True} in clauses
    assert {"region_national": True} in clauses


def test_retrieval_filter_excludes_employment_required_when_not_employed(valid_profile):
    valid_profile["employment_required"] = False
    result = _retrieval_filter(valid_profile)
    assert {"employment_required": False} in result["$and"]


def test_retrieval_filter_does_not_exclude_when_employed(valid_profile):
    valid_profile["employment_required"] = True
    result = _retrieval_filter(valid_profile)
    # No $and wrapper needed - only the region clause applies.
    assert "$and" not in result
    assert "$or" in result


def test_retrieval_filter_does_not_exclude_when_employment_unknown():
    # Stage-1 (overview) profiles don't have employment_required yet - unknown
    # must not be treated the same as "known not employed".
    partial_profile = {
        "persona": "fence_sitter",
        "purpose": ["commuting"],
        "borough": "manchester",
        "accessibility_relevant": False,
    }
    result = _retrieval_filter(partial_profile)
    assert "$and" not in result
    assert "$or" in result


def test_profile_to_query_states_employment_explicitly_both_ways(valid_profile):
    valid_profile["employment_required"] = False
    query = _profile_to_query(valid_profile)
    assert "not employed" in query

    valid_profile["employment_required"] = True
    query = _profile_to_query(valid_profile)
    assert "employed - workplace cycling schemes are relevant" in query


def test_profile_to_query_states_accessibility_and_ebike_explicitly_both_ways(valid_profile):
    valid_profile["accessibility_relevant"] = False
    valid_profile["e_bike_focused"] = False
    query = _profile_to_query(valid_profile)
    assert "no accessibility needs stated" in query
    assert "not specifically interested in e-bikes" in query

    valid_profile["accessibility_relevant"] = True
    valid_profile["e_bike_focused"] = True
    query = _profile_to_query(valid_profile)
    assert "has accessibility needs" in query
    assert "interested in e-bikes" in query


def test_profile_to_query_omits_unknown_stage_2_facts():
    # Stage-1 profile: budget/e-bike/employment haven't been asked yet, so
    # they must be silent - not misrepresented as "false"/"not interested".
    partial_profile = {
        "persona": "fence_sitter",
        "purpose": ["commuting"],
        "borough": "manchester",
        "accessibility_relevant": True,
    }
    query = _profile_to_query(partial_profile)
    assert "has accessibility needs" in query
    assert "budget" not in query
    assert "e-bike" not in query
    assert "employed" not in query


def test_region_tags_extracts_true_region_keys_only():
    metadata = {
        "region_manchester": True,
        "region_national": True,
        "region_trafford": False,
        "unrelated": True,
    }
    assert _region_tags(metadata) == "manchester, national"


def test_region_tags_falls_back_when_no_region_keys():
    assert _region_tags({"title": "x"}) == "unspecified"


def test_format_docs_includes_title_url_and_region():
    from langchain_core.documents import Document

    doc = Document(
        page_content="Some content",
        metadata={"title": "Example", "url": "https://example.com", "region_national": True},
    )
    text = _format_docs([doc])
    assert "Source: Example (https://example.com)" in text
    assert "Region(s): national" in text
    assert "Some content" in text


def test_format_docs_exposes_full_structured_metadata():
    from langchain_core.documents import Document

    doc = Document(
        page_content="Some content",
        metadata={
            "title": "Example",
            "url": "https://example.com",
            "corpus_category": "schemes",
            "budget_band": "free;low_cost",
            "accessibility_relevant": True,
            "e_bike_focused": False,
            "employment_required": False,
            "region_greater_manchester": True,
        },
    )
    text = _format_docs([doc])
    assert "Category: schemes" in text
    assert "Budget: free;low_cost" in text
    assert "Accessibility-relevant: yes" in text
    assert "E-bike-focused: no" in text
    assert "Employment required: no" in text


def test_recommendations_report_dedupes_by_url_keeping_first_occurrence():
    report = RecommendationsReport(
        grouping_analysis="test",
        recommendations=[
            Recommendation(name="Get a bike", reason="first", url="https://x/get-a-bike"),
            Recommendation(name="Bike to Work", reason="second, duplicate url", url="https://x/get-a-bike"),
            Recommendation(name="Borrow an e-bike", reason="distinct", url="https://x/borrow-ebike"),
        ]
    )
    urls = [r.url for r in report.recommendations]
    assert urls == ["https://x/get-a-bike", "https://x/borrow-ebike"]
    assert report.recommendations[0].name == "Get a bike"  # first occurrence wins


def test_disclaimer_mentions_tfgm_affiliation_and_ai_generation():
    lowered = DISCLAIMER.lower()
    assert "not affiliated" in lowered
    assert "tfgm" in lowered
    assert "ai" in lowered or "artificial intelligence" in lowered


def test_validate_profile_accepts_well_formed_profile(valid_profile):
    validate_profile(valid_profile)  # should not raise


def test_validate_profile_rejects_unknown_persona(valid_profile):
    valid_profile["persona"] = "power_cyclist"
    with pytest.raises(ValueError, match="unknown persona"):
        validate_profile(valid_profile)


def test_validate_profile_rejects_empty_purpose(valid_profile):
    valid_profile["purpose"] = []
    with pytest.raises(ValueError, match="purpose must be non-empty"):
        validate_profile(valid_profile)


def test_validate_profile_rejects_unknown_borough(valid_profile):
    valid_profile["borough"] = "narnia"
    with pytest.raises(ValueError, match="unknown borough"):
        validate_profile(valid_profile)


def test_validate_profile_allows_none_borough(valid_profile):
    valid_profile["borough"] = None
    validate_profile(valid_profile)  # should not raise


def test_validate_profile_rejects_non_bool_flags(valid_profile):
    valid_profile["accessibility_relevant"] = "no"
    with pytest.raises(ValueError, match="accessibility_relevant must be a bool"):
        validate_profile(valid_profile)


def test_validate_profile_partial_accepts_stage_1_only_fields():
    partial_profile = {
        "persona": "fence_sitter",
        "purpose": ["commuting"],
        "borough": "manchester",
        "accessibility_relevant": True,
    }
    validate_profile(partial_profile, require_all=False)  # should not raise


def test_validate_profile_partial_still_requires_stage_1_fields():
    partial_profile = {
        "persona": "fence_sitter",
        "purpose": ["commuting"],
        "borough": "manchester",
        # accessibility_relevant missing
    }
    with pytest.raises(ValueError, match="accessibility_relevant must be a bool"):
        validate_profile(partial_profile, require_all=False)


def test_validate_profile_full_rejects_partial_profile():
    partial_profile = {
        "persona": "fence_sitter",
        "purpose": ["commuting"],
        "borough": "manchester",
        "accessibility_relevant": True,
    }
    with pytest.raises(ValueError, match="budget_band"):
        validate_profile(partial_profile)  # require_all defaults to True
