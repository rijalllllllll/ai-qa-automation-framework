"""API contract tests for the AI Children's Story Generator.

Scenario-driven from qa-framework/fixtures/scenarios.json so the test data
strategy stays in one place. Run from story-generator/ against a live server:
    pytest qa-tests -q
"""
import json
import os
import time

import pytest
import requests

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8901")
_FIXTURES_ENV = os.environ.get("SCENARIOS_FIXTURE", "")
FIXTURES = _FIXTURES_ENV or os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),  # story-generator/
    "..", "qa-framework", "fixtures", "scenarios.json",
)


@pytest.fixture(scope="session")
def scenarios():
    with open(FIXTURES, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def story_api(scenarios):
    return BASE_URL.rstrip("/") + "/api/generate-story"


def test_healthz():
    r = requests.get(BASE_URL + "/healthz", timeout=5)
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.parametrize("scenario", json.load(open(FIXTURES, encoding="utf-8"))["valid_scenarios"],
                         ids=lambda s: s["child_name"])
def test_valid_scenario_returns_contract(scenario, story_api):
    r = requests.post(story_api, json=scenario, timeout=10)
    assert r.status_code == 200, r.text
    body = r.json()
    required = {"story_id", "title", "sections", "moral", "word_count", "request", "meta"}
    assert required <= set(body.keys())
    assert body["story_id"]
    assert len(body["sections"]) >= 3
    assert body["word_count"] > 0
    assert body["meta"]["provider"] == "mock"
    assert body["request"]["child_name"] == scenario["child_name"]


@pytest.mark.parametrize("case", json.load(open(FIXTURES, encoding="utf-8"))["invalid_cases"],
                         ids=lambda c: c["label"].replace(" ", "_"))
def test_invalid_cases_rejected(case, story_api):
    r = requests.post(story_api, json=case["payload"], timeout=10)
    assert r.status_code == case["expect"], r.text


def test_story_ids_are_unique(story_api):
    payload = {"child_name": "Rara", "age": 6, "mood": "curious", "length": "short"}
    ids = {requests.post(story_api, json=payload, timeout=10).json()["story_id"] for _ in range(3)}
    assert len(ids) == 3


def test_response_within_latency_budget(story_api):
    payload = {"child_name": "Zafa", "age": 7, "mood": "brave", "length": "medium"}
    start = time.monotonic()
    r = requests.post(story_api, json=payload, timeout=10)
    elapsed = time.monotonic() - start
    assert r.status_code == 200
    assert elapsed < 5.0, f"response took {elapsed:.2f}s"
    assert r.json()["meta"]["latency_ms"] < 5000