"""Shared validation for manifest.csv rows and user profile dicts.

Both this module's manifest checks and rag.py's profile checks validate
against the same vocab defined in questionnaire.py, so a manifest value the
questionnaire can never produce (or vice versa) is caught early instead of
silently going unmatched at query time.
"""

import pandas as pd

from .questionnaire import BOROUGHS, BUDGETS, PERSONAS, PURPOSES

REQUIRED_MANIFEST_COLUMNS = [
    "title",
    "source_org",
    "url",
    "corpus_category",
    "region_scope",
    "user_persona",
    "purpose",
    "accessibility_relevant",
    "e-bike_focused",
    "employment_required",
    "budget_band",
    "source_type",
    "status",
]

# region_scope also allows "national" - a valid scope with no questionnaire
# equivalent, since it's never a value the user selects directly.
VALID_REGIONS = set(BOROUGHS) | {"greater_manchester", "national"}
VALID_PERSONAS = set(PERSONAS)
VALID_PURPOSES = set(PURPOSES)
VALID_BUDGETS = set(BUDGETS)
VALID_BOOLEAN_STRINGS = {"true", "false"}


def _split(value: object) -> list[str]:
    return [v.strip().lower() for v in str(value).split(";") if v.strip()]


def validate_manifest_df(df: pd.DataFrame) -> list[str]:
    """Return a list of human-readable problems; empty means the manifest is valid."""
    problems: list[str] = []

    missing_columns = [c for c in REQUIRED_MANIFEST_COLUMNS if c not in df.columns]
    if missing_columns:
        problems.append(f"missing required column(s): {', '.join(missing_columns)}")
        return problems  # can't safely check rows without the columns present

    for idx, row in df.iterrows():
        label = f"row {idx} ({row.get('title', '<untitled>')!r})"

        if not str(row["title"]).strip():
            problems.append(f"{label}: empty title")

        url = str(row["url"]).strip()
        if not url.startswith("http"):
            problems.append(f"{label}: url does not start with http(s): {url!r}")

        for persona in _split(row["user_persona"]):
            if persona not in VALID_PERSONAS:
                problems.append(f"{label}: unknown user_persona {persona!r}")

        for purpose in _split(row["purpose"]):
            if purpose not in VALID_PURPOSES:
                problems.append(f"{label}: unknown purpose {purpose!r}")

        for region in _split(row["region_scope"]):
            if region not in VALID_REGIONS:
                problems.append(f"{label}: unknown region_scope {region!r}")

        for budget in _split(row["budget_band"]):
            if budget not in VALID_BUDGETS:
                problems.append(f"{label}: unknown budget_band {budget!r}")

        for column in ("accessibility_relevant", "e-bike_focused", "employment_required"):
            value = str(row[column]).strip().lower()
            if value not in VALID_BOOLEAN_STRINGS:
                problems.append(f"{label}: {column} is not true/false: {value!r}")

    return problems


def validate_profile(profile: dict) -> None:
    """Raise ValueError with a clear message if a profile dict is malformed."""
    errors: list[str] = []

    if profile.get("persona") not in VALID_PERSONAS:
        errors.append(f"unknown persona: {profile.get('persona')!r}")

    purposes = profile.get("purpose") or []
    if not purposes:
        errors.append("purpose must be non-empty")
    unknown_purposes = [p for p in purposes if p not in VALID_PURPOSES]
    if unknown_purposes:
        errors.append(f"unknown purpose(s): {unknown_purposes}")

    if profile.get("budget_band") not in VALID_BUDGETS:
        errors.append(f"unknown budget_band: {profile.get('budget_band')!r}")

    borough = profile.get("borough")
    if borough is not None and borough not in BOROUGHS:
        errors.append(f"unknown borough: {borough!r}")

    for key in ("accessibility_relevant", "e_bike_focused", "employment_required"):
        if not isinstance(profile.get(key), bool):
            errors.append(f"{key} must be a bool")

    if errors:
        raise ValueError("Invalid profile: " + "; ".join(errors))
