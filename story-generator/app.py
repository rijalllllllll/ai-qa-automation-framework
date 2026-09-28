"""AI Children's Story Generator — FastAPI application (System Under Test)."""
import time

from typing import Optional

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from story_engine import LENGTHS, MAX_AGE, MIN_AGE, MOODS, Story, build_provider

app = FastAPI(
    title="AI Children's Story Generator",
    version="1.0.0",
    description="SUT for the ai-qa-automation-framework. POST /api/generate-story returns a structured story.",
)
provider = build_provider()


class StoryRequest(BaseModel):
    child_name: str = Field(min_length=1, max_length=40, description="Child's name (1-40 chars)")
    age: int = Field(ge=MIN_AGE, le=MAX_AGE, description=f"Child's age ({MIN_AGE}-{MAX_AGE})")
    mood: str = Field(description=f"Story mood: {', '.join(MOODS)}")
    character: str = Field(default="", max_length=30, description="Optional companion character")
    moral: str = Field(default="", max_length=80, description="Optional lesson to include")
    length: str = Field(default="medium", description="short | medium | long")
    seed: Optional[int] = Field(default=None, description="Optional seed for reproducible output")

    @field_validator("mood")
    @classmethod
    def mood_valid(cls, v: str) -> str:
        if v not in MOODS:
            raise ValueError(f"mood must be one of: {', '.join(MOODS)}")
        return v

    @field_validator("length")
    @classmethod
    def length_valid(cls, v: str) -> str:
        if v not in LENGTHS:
            raise ValueError(f"length must be one of: {', '.join(LENGTHS)}")
        return v


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "app": app.title, "provider": type(provider).__name__}


@app.post("/api/generate-story")
def generate_story(payload: StoryRequest) -> dict:
    """Generate a children's story. Validation failures return FastAPI's 422."""
    started = time.monotonic()
    story: Story = provider.generate(payload.model_dump())
    latency_ms = round((time.monotonic() - started) * 1000, 1)
    return {
        "story_id": story.story_id,
        "title": story.title,
        "sections": story.sections,
        "moral": story.moral,
        "word_count": story.word_count,
        "request": payload.model_dump(exclude={"seed"}),
        "meta": {**story.meta, "latency_ms": latency_ms},
    }


app.mount("/", StaticFiles(directory="static", html=True), name="static")