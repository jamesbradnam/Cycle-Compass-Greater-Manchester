"""Entry point: run the two-stage questionnaire, printing each report as it's ready.

Run with:  python -m src.main
"""

from . import config
from .questions import run_stage
from .rag import generate_overview, generate_recommendations


def main() -> None:
    if not config.CHROMA_DIR.exists():
        print("No vector store found. Run `python -m src.ingest` first.")
        return

    print("Welcome to Cycle Compass! Answer a few questions to get your reports.\n")

    profile = run_stage(1)
    print("\nGenerating your overview...\n")
    overview = generate_overview(profile)

    print("=" * 60)
    print(overview["disclaimer"])
    print("=" * 60)
    print()
    print("=" * 60)
    print("OVERVIEW")
    print("=" * 60)
    print(overview["overview"])
    print()

    input("Press enter to continue to the rest of the questionnaire...")
    print()

    profile = run_stage(2, profile)
    print("\nGenerating your recommendations...\n")
    recommendations = generate_recommendations(profile)

    print("=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    for i, item in enumerate(recommendations["recommendations"], start=1):
        print(f"{i}. {item.name}")
        print(f"   {item.reason}")
        print(f"   {item.url}")
        print()
    if recommendations["note"]:
        print(recommendations["note"])
    print()
    print("=" * 60)
    print(recommendations["disclaimer"])
    print("=" * 60)


if __name__ == "__main__":
    main()
