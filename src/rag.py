"""Retrieval-augmented generation over the Cycle Compass source corpus."""

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from . import config

REGION_NOTE = (
    "Each source in the context is tagged with the region(s) it applies to. "
    "Sources tagged 'greater_manchester' or 'national' apply to every user "
    "regardless of which borough they're in - never discount or downweight "
    "them just because they don't name the user's specific borough."
)

OVERVIEW_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are Cycle Compass, a friendly assistant that helps people in Greater "
            "Manchester get into cycling via the TfGM Bee Network. Using ONLY the "
            "provided context, write a plain-English OVERVIEW of the active travel "
            "options relevant to this person's profile. " + REGION_NOTE + " Do not "
            "invent facts, schemes, or links that aren't in the context. Keep it to "
            "3-5 short paragraphs and do not include links yet - those come in a "
            "separate report.",
        ),
        (
            "human",
            "User profile:\n{profile}\n\nContext:\n{context}\n\nWrite the overview report.",
        ),
    ]
)

RECOMMENDATIONS_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are Cycle Compass, a friendly assistant that helps people in Greater "
            "Manchester get into cycling via the TfGM Bee Network. Using ONLY the "
            "provided context, write a numbered list of SPECIFIC, ACTIONABLE "
            "recommendations for this person. " + REGION_NOTE + " For each item give: "
            "a short name, one sentence on why it fits their profile, and the "
            "official URL taken verbatim from the context. Only cite URLs that "
            "appear in the context. If nothing in the context fits well, say so "
            "honestly instead of guessing.",
        ),
        (
            "human",
            "User profile:\n{profile}\n\nContext:\n{context}\n\nWrite the recommendations report.",
        ),
    ]
)


def load_vectorstore() -> Chroma:
    embeddings = OpenAIEmbeddings(model=config.EMBEDDING_MODEL)
    return Chroma(persist_directory=str(config.CHROMA_DIR), embedding_function=embeddings)


# These region scopes apply to every user regardless of their borough, so
# they're always included in the retrieval filter alongside any borough match.
UNIVERSAL_REGIONS = ["region_greater_manchester", "region_national"]


def _region_filter(borough: str | None) -> dict:
    regions = list(UNIVERSAL_REGIONS)
    if borough:
        regions.append(f"region_{borough.strip().lower()}")
    return {"$or": [{region: True} for region in regions]}


def _region_tags(metadata: dict) -> str:
    tags = [
        key.removeprefix("region_")
        for key, value in metadata.items()
        if key.startswith("region_") and value
    ]
    return ", ".join(sorted(tags)) or "unspecified"


def _format_docs(docs: list[Document]) -> str:
    blocks = []
    for doc in docs:
        title = doc.metadata.get("title", "Untitled")
        url = doc.metadata.get("url", "")
        region = _region_tags(doc.metadata)
        blocks.append(f"Source: {title} ({url})\nRegion(s): {region}\n{doc.page_content}")
    return "\n\n---\n\n".join(blocks)


def _profile_to_query(profile: dict) -> str:
    borough = profile.get("borough")
    region_desc = (
        f"{borough} (Greater Manchester-wide and national resources also apply)"
        if borough
        else "greater_manchester (no specific borough given; Greater Manchester-wide and national resources apply)"
    )
    parts = [
        f"persona: {profile['persona']}",
        f"purpose: {', '.join(profile['purpose'])}",
        f"budget: {profile['budget_band']}",
        f"region: {region_desc}",
    ]
    if profile.get("accessibility_relevant"):
        parts.append("has accessibility needs")
    if profile.get("e_bike_focused"):
        parts.append("interested in e-bikes")
    if profile.get("employment_required"):
        parts.append("employed, interested in workplace cycling schemes")
    return "; ".join(parts)


def generate_reports(profile: dict, k: int = config.RETRIEVER_K) -> tuple[str, str]:
    vectorstore = load_vectorstore()
    retriever = vectorstore.as_retriever(
        search_kwargs={"k": k, "filter": _region_filter(profile.get("borough"))}
    )

    query = _profile_to_query(profile)
    docs = retriever.invoke(query)
    context = _format_docs(docs)

    llm = ChatOpenAI(model=config.CHAT_MODEL, temperature=0.3)
    parser = StrOutputParser()
    overview_chain = OVERVIEW_PROMPT | llm | parser
    recommendations_chain = RECOMMENDATIONS_PROMPT | llm | parser

    inputs = {"profile": query, "context": context}
    overview = overview_chain.invoke(inputs)
    recommendations = recommendations_chain.invoke(inputs)
    return overview, recommendations
