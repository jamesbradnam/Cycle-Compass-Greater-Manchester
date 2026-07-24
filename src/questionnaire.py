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
