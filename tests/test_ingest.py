import pandas as pd
from langchain_core.documents import Document

from src.ingest import _ENCODING, _batch_by_tokens, _clean_html, _to_bool, build_metadata
from src.validation import validate_manifest_df


def test_to_bool():
    assert _to_bool("true") is True
    assert _to_bool("True") is True
    assert _to_bool("  TRUE  ") is True
    assert _to_bool("false") is False
    assert _to_bool("") is False
    assert _to_bool("na") is False


def test_build_metadata_explodes_multi_value_columns(manifest_row):
    metadata = build_metadata(manifest_row)

    assert metadata["title"] == "Example scheme"
    assert metadata["url"] == "https://example.tfgm.com/scheme"
    assert metadata["accessibility_relevant"] is False
    assert metadata["e_bike_focused"] is True
    assert metadata["employment_required"] is False

    assert metadata["persona_occasional_cyclist"] is True
    assert metadata["persona_regular_cyclist"] is True
    assert metadata["purpose_commuting"] is True
    assert metadata["purpose_leisure"] is True
    assert metadata["region_manchester"] is True
    assert metadata["region_trafford"] is True


def test_build_metadata_handles_blank_and_na_values(manifest_row):
    manifest_row["region_scope"] = "na"
    metadata = build_metadata(manifest_row)
    # "na" is treated as a literal value, not a magic blank marker - it should
    # still produce exactly one region tag, not crash or produce empty keys.
    region_keys = [k for k in metadata if k.startswith("region_")]
    assert region_keys == ["region_na"]


def test_batch_by_tokens_never_exceeds_budget():
    docs = [Document(page_content=f"unique filler text number {i} " * 20) for i in range(20)]
    batches = _batch_by_tokens(docs, max_tokens=50)

    assert sum(len(b) for b in batches) == len(docs)
    for batch in batches:
        token_total = sum(len(_ENCODING.encode(d.page_content)) for d in batch)
        # A single oversized doc is still allowed alone in a batch; only
        # multi-doc batches must respect the budget.
        if len(batch) > 1:
            assert token_total <= 50


def test_clean_html_strips_nav_script_and_footer():
    html = """
    <html>
      <head><script>trackPageview();</script><style>.x{color:red}</style></head>
      <body>
        <nav>Home About Contact Close sub menu Close sub menu</nav>
        <header>Site header</header>
        <main><h1>Beat the weather</h1><p>Some real article content.</p></main>
        <footer>Copyright 2026</footer>
      </body>
    </html>
    """
    text = _clean_html(html)

    assert "Beat the weather" in text
    assert "Some real article content." in text
    assert "trackPageview" not in text
    assert "Close sub menu" not in text
    assert "Site header" not in text
    assert "Copyright 2026" not in text


def test_validate_manifest_df_accepts_well_formed_row(manifest_row):
    df = pd.DataFrame([manifest_row])
    assert validate_manifest_df(df) == []


def test_validate_manifest_df_flags_missing_column(manifest_row):
    df = pd.DataFrame([manifest_row]).drop(columns=["url"])
    problems = validate_manifest_df(df)
    assert any("missing required column" in p for p in problems)


def test_validate_manifest_df_flags_bad_url(manifest_row):
    manifest_row["url"] = "not-a-url"
    df = pd.DataFrame([manifest_row])
    problems = validate_manifest_df(df)
    assert any("does not start with http" in p for p in problems)


def test_validate_manifest_df_flags_unknown_persona(manifest_row):
    manifest_row["user_persona"] = "power_cyclist"
    df = pd.DataFrame([manifest_row])
    problems = validate_manifest_df(df)
    assert any("unknown user_persona" in p for p in problems)


def test_validate_manifest_df_flags_bad_boolean(manifest_row):
    manifest_row["employment_required"] = "yes"
    df = pd.DataFrame([manifest_row])
    problems = validate_manifest_df(df)
    assert any("employment_required is not true/false" in p for p in problems)
