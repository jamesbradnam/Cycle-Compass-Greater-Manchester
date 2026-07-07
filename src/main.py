"""Entry point: run the questionnaire, then print the two RAG-generated reports.

Run with:  python -m src.main
"""

from . import config
from .questionnaire import run as run_questionnaire
from .rag import generate_reports


def main() -> None:
    if not config.CHROMA_DIR.exists():
        print("No vector store found. Run `python -m src.ingest` first.")
        return

    profile = run_questionnaire()
    print("\nGenerating your reports...\n")
    overview, recommendations = generate_reports(profile)

    print("=" * 60)
    print("OVERVIEW")
    print("=" * 60)
    print(overview)
    print()
    print("=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    print(recommendations)


if __name__ == "__main__":
    main()
