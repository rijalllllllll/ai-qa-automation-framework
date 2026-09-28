"""AI Children's Story Generator — story engine (System Under Test).

The engine has two implementations behind one interface:
  - MockStoryProvider: deterministic template-based generator used in tests and
    local runs (fast, no API key, fully reproducible output shape).
  - LLMStoryProvider: pluggable real-LLM provider (interface documented; set
    STORY_PROVIDER=openai and OPENAI_API_KEY to wire an actual model).

This separation is intentional: it lets the QA framework test the product
contract (schema, validation, latency, UI flows) without depending on an
external AI service, exactly the pattern recommended for testing AI features.
"""
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

MOODS = ["happy", "brave", "curious", "sleepy", "silly", "calm"]
LENGTHS = ["short", "medium", "long"]
MIN_AGE, MAX_AGE = 2, 12

_OPENINGS = {
    "happy": "On a sunlit morning, tiny giggles floated through {place}.",
    "brave": "Far beyond the whispering woods, where shadows played tricks, {name} felt a brave spark.",
    "curious": "Under a blanket of stars, {name} found a question that simply had to be answered.",
    "sleepy": "When the moon tucked the world in, {place} grew soft and quiet.",
    "silly": "In {place}, the pudding was purple, the chickens wore hats, and {name} grinned.",
    "calm": "Beside a slow blue river, {name} sat and listened to the world breathe.",
}
_PLACES = ["the Rainbow Valley", "a kitchen that hums lullabies", "the Land of Soft Shapes",
           "a garden of talking flowers", "the attic of forgotten toys"]
_MIDDLES = [
    "A small problem appeared: {obstacle}. {name} thought, then tried something nobody else had tried.",
    "{obstacle} stood in the way, but {name} remembered what Grandma always said.",
    "Just then, a friendly helper arrived and whispered the secret of {skill}.",
]
_OBSTACLES = ["the grumpy cloud", "a maze of spilled blocks", "the Great Naptime Fog",
              "a riddle with no answer", "the sneaky shadow"]
_SKILLS = ["patience", "asking questions", "sharing", "taking a deep breath", "kindness"]
_ENDINGS = {
    "happy": "And so {place} sparkled a little brighter, because of {name}.",
    "brave": "The spark inside {name} never went out — it grew into a steady, quiet flame.",
    "curious": "Some questions lead to answers, and some lead to brand-new questions {name} loves.",
    "sleepy": "With a yawn as wide as a smile, {name} drifted into a dream of tomorrow.",
    "silly": "Everyone agreed: {place} was sillier and sweeter since {name} arrived.",
    "calm": "The river, the sky, and {name} all agreed: it had been a very good day.",
}
_MORALS = {
    "happy": "Happiness grows when it is shared.",
    "brave": "Bravery is trying even when you feel small.",
    "curious": "Curiosity is the start of every great discovery.",
    "sleepy": "Rest is part of every adventure.",
    "silly": "Laughter makes hard days softer.",
    "calm": "A calm heart sees clearly.",
}


@dataclass
class Story:
    story_id: str
    title: str
    sections: list  # [{heading, text}]
    moral: str
    word_count: int
    meta: dict = field(default_factory=dict)


class StoryProvider:
    """Interface: every provider must return a Story for valid StoryParams."""

    def generate(self, params: dict) -> Story:
        raise NotImplementedError


class MockStoryProvider(StoryProvider):
    """Deterministic template engine. Output shape mirrors a real LLM response."""

    def __init__(self, latency_ms: tuple = (200, 600)):
        self.latency_range = latency_ms

    def _one(self, seq):
        return seq[self._idx % len(seq)]

    def generate(self, params: dict, seed: Optional[int] = None) -> Story:
        # Simulated AI inference latency (configurable range) so loading-state
        # UI tests exercise a realistic delay.
        lo, hi = self.latency_range
        import random
        time.sleep(random.randint(lo, hi) / 1000.0)

        if seed is None:
            seed = int.from_bytes(uuid.uuid4().bytes[:4], "big")
        self._idx = seed
        name = params["child_name"]
        mood = params["mood"]
        length = params["length"]
        place = self._one(_PLACES)

        paragraphs = {
            "short": 1, "medium": 2, "long": 3,
        }[length]
        opening = _OPENINGS[mood].format(name=name, place=place)
        mids = []
        for i in range(paragraphs):
            self._idx += 1
            obstacle = self._one(_OBSTACLES)
            skill = self._one(_SKILLS)
            mids.append(_MIDDLES[i % len(_MIDDLES)].format(name=name, obstacle=obstacle, skill=skill))
        self._idx += 1
        ending = _ENDINGS[mood].format(name=name, place=place)

        title = f"{name}'s {mood.title()} Adventure"
        text = " ".join([opening, *mids, ending])
        story = Story(
            story_id=str(uuid.uuid4()),
            title=title,
            sections=[
                {"heading": "Once upon a time", "text": opening},
                *[{"heading": f"The {i + 1}. twist", "text": m} for i, m in enumerate(mids)],
                {"heading": "And then", "text": ending},
            ],
            moral=_MORALS[mood],
            word_count=len(text.split()),
            meta={
                "provider": "mock",
                "seed": seed,
                "generated_at": datetime.utcnow().isoformat() + "Z",
            },
        )
        return story


class LLMStoryProvider(StoryProvider):
    """Pluggable real-LLM provider.

    The wire contract (request/response schema) is identical to the mock so the
    QA suite never changes when the provider swaps. Real implementation would
    call the chosen LLM API here; the mock is used in CI to keep tests hermetic.
    """

    def generate(self, params: dict, seed: Optional[int] = None) -> Story:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise RuntimeError("LLMStoryProvider requires OPENAI_API_KEY (or use STORY_PROVIDER=mock)")
        # Real provider integration point — same Story contract as the mock.
        raise NotImplementedError("Wire your LLM call here; contract identical to MockStoryProvider.")


def build_provider() -> StoryProvider:
    provider = os.environ.get("STORY_PROVIDER", "mock").lower()
    if provider == "openai":
        return LLMStoryProvider()
    return MockStoryProvider()