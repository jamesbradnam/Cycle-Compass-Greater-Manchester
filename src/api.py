"""FastAPI backend for the Cycle Compass React frontend.

Run with:  uvicorn src.api:app --reload --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import analytics
from .questions import QUESTIONS
from .rag import DISCLAIMER, generate_overview, generate_recommendations


@asynccontextmanager
async def lifespan(app: FastAPI):
    analytics.init_db()
    yield


app = FastAPI(title="Cycle Compass API", lifespan=lifespan)

# The Vite dev server proxies /api to this app (see frontend/vite.config.js),
# so CORS isn't needed for local dev - this is just a fallback for anyone
# hitting the API directly from a browser at a different origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/questions")
def get_questions() -> dict:
    return {"questions": QUESTIONS, "disclaimer": DISCLAIMER}


class EventIn(BaseModel):
    session_id: str
    event_type: str
    payload: dict | None = None


@app.post("/api/events", status_code=204)
def post_event(event: EventIn) -> None:
    analytics.record_event(event.session_id, event.event_type, event.payload)


class OverviewProfileIn(BaseModel):
    persona: str
    purpose: list[str]
    borough: str | None = None
    accessibility_relevant: bool


class RecommendationsProfileIn(OverviewProfileIn):
    e_bike_focused: bool
    budget_band: str
    employment_required: bool


@app.post("/api/overview")
def post_overview(profile: OverviewProfileIn) -> dict:
    try:
        return generate_overview(profile.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/recommendations")
def post_recommendations(profile: RecommendationsProfileIn) -> dict:
    try:
        return generate_recommendations(profile.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
