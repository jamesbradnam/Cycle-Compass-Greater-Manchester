"""Canonical, ordered question list - the single source of truth for both the
CLI (questionnaire.py) and the API (api.py), so their order/text/options never
drift apart.

Stage 1 questions are asked first and feed the OVERVIEW report; stage 2
questions are asked after the user continues past the overview, and their
answers (combined with stage 1's) feed the RECOMMENDATIONS report.
"""

from .questionnaire import (
    BOROUGHS,
    BUDGETS,
    PERSONAS,
    PURPOSES,
    _ask_choice,
    _ask_multi,
    _ask_yes_no,
)

QUESTIONS = [
    {
        "id": "borough",
        "stage": 1,
        "type": "single",
        "prompt": "Which Greater Manchester borough are you in?",
        "options": [*BOROUGHS, "greater_manchester"],
    },
    {
        "id": "persona",
        "stage": 1,
        "type": "single",
        "prompt": "Which best describes you?",
        "options": PERSONAS,
    },
    {
        "id": "purpose",
        "stage": 1,
        "type": "multi",
        "prompt": "What would you use cycling for?",
        "options": PURPOSES,
    },
    {
        "id": "accessibility_relevant",
        "stage": 1,
        "type": "boolean",
        "prompt": "Do you have any accessibility needs we should factor in?",
    },
    {
        "id": "e_bike_focused",
        "stage": 2,
        "type": "boolean",
        "prompt": "Are you interested in e-bikes?",
    },
    {
        "id": "budget_band",
        "stage": 2,
        "type": "single",
        "prompt": "What's your budget?",
        "options": BUDGETS,
    },
    {
        "id": "employment_required",
        "stage": 2,
        "type": "boolean",
        "prompt": "Are you employed? (relevant for workplace cycling schemes)",
    },
]

STAGE_1_QUESTIONS = [q for q in QUESTIONS if q["stage"] == 1]
STAGE_2_QUESTIONS = [q for q in QUESTIONS if q["stage"] == 2]


def _ask_question(question: dict):
    if question["type"] == "single":
        return _ask_choice(question["prompt"], question["options"])
    if question["type"] == "multi":
        return _ask_multi(question["prompt"], question["options"])
    if question["type"] == "boolean":
        return _ask_yes_no(question["prompt"])
    raise ValueError(f"unknown question type: {question['type']!r}")


def run_stage(stage: int, profile: dict | None = None) -> dict:
    """CLI-prompt through one stage's questions, merging answers into profile."""
    profile = dict(profile or {})
    for question in QUESTIONS:
        if question["stage"] != stage:
            continue
        answer = _ask_question(question)
        if question["id"] == "borough" and answer == "greater_manchester":
            answer = None
        profile[question["id"]] = answer
    return profile
