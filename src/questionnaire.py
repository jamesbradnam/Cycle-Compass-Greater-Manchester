"""Interactive CLI questionnaire that builds a user profile for the RAG reports."""

PERSONAS = ["non_cyclist", "fence_sitter", "occasional_cyclist", "regular_cyclist"]
PURPOSES = ["commuting", "leisure", "errands"]
BUDGETS = ["free", "low_cost", "mid_range", "high_investment"]
BOROUGHS = [
    "bolton",
    "bury",
    "manchester",
    "oldham",
    "rochdale",
    "salford",
    "stockport",
    "tameside",
    "trafford",
    "wigan",
]


def _ask_choice(prompt: str, options: list[str]) -> str:
    option_list = ", ".join(options)
    while True:
        answer = input(f"{prompt}\n[{option_list}]: ").strip().lower()
        if answer in options:
            return answer
        print(f"Please choose one of: {option_list}")


def _ask_multi(prompt: str, options: list[str]) -> list[str]:
    option_list = ", ".join(options)
    while True:
        raw = input(f"{prompt} (comma-separated)\n[{option_list}]: ").strip().lower()
        chosen = [item.strip() for item in raw.split(",") if item.strip()]
        if chosen and all(item in options for item in chosen):
            return chosen
        print(f"Please choose one or more of: {option_list}")


def _ask_yes_no(prompt: str) -> bool:
    while True:
        answer = input(f"{prompt} [y/n]: ").strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("Please answer y or n.")


def run() -> dict:
    print("Welcome to Cycle Compass! Answer a few questions to get your reports.\n")

    persona = _ask_choice("Which best describes you?", PERSONAS)
    purpose = _ask_multi("What would you use cycling for?", PURPOSES)
    borough = _ask_choice(
        "Which Greater Manchester borough are you in? (use 'greater_manchester' if unsure)",
        [*BOROUGHS, "greater_manchester"],
    )
    budget_band = _ask_choice("What's your budget?", BUDGETS)
    accessibility_relevant = _ask_yes_no("Do you have any accessibility needs we should factor in?")
    e_bike_focused = _ask_yes_no("Are you interested in e-bikes?")
    employment_required = _ask_yes_no("Are you employed? (relevant for workplace cycling schemes)")

    return {
        "persona": persona,
        "purpose": purpose,
        "borough": None if borough == "greater_manchester" else borough,
        "budget_band": budget_band,
        "accessibility_relevant": accessibility_relevant,
        "e_bike_focused": e_bike_focused,
        "employment_required": employment_required,
    }
