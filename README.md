# AI QA Automation Framework + Children's Story Generator

A QA automation framework built around a real product: an **AI Children's Story Generator** (FastAPI + vanilla JS, with a pluggable LLM provider interface). The framework covers **end-to-end UI automation (Playwright, TypeScript)** and **API contract testing (pytest)**, driven by a central **test-data strategy** (scenario fixtures) and wired into **GitHub Actions CI**.

This is a working demonstration of the whole QA discipline: product requirements → test plans → automated checks (including edge cases) → CI → failure triage → stable, maintainable suites.

## What's inside

```
ai-qa-automation-framework/
├── story-generator/            # System Under Test (SUT)
│   ├── app.py                  # FastAPI: POST /api/generate-story + validation (422s)
│   ├── story_engine.py         # Story engine: mock provider (tests) + pluggable LLM provider
│   ├── static/                 # Product UI (HTML/JS/CSS) — the E2E target
│   ├── qa-tests/               # API contract tests (pytest, scenario-driven)
│   └── requirements.txt
├── qa-framework/               # The QA automation framework
│   ├── tests/e2e/              # Playwright E2E specs (TypeScript)
│   ├── fixtures/scenarios.json # Central test-data strategy (valid + invalid cases)
│   ├── playwright.config.ts    # CI-aware config (retries, report artifact)
│   └── package.json
└── .github/workflows/ci.yml    # API tests + E2E tests in CI
```

## The product under test

The **AI Children's Story Generator** takes a child's name, age, mood, companion character, length, and lesson — and returns a structured bedtime story (title, sections, moral, word count) with simulated AI latency. Validation is strict: age 2–12, name 1–40 chars, mood/length enums, all enforced by the API (422s).

The story engine separates a **mock provider** (deterministic, hermetic — used in tests and CI) from a **pluggable LLM provider** (real model behind the same contract). This is the recommended pattern for testing AI features: the product contract is testable without an external model.

## Test coverage

### E2E (Playwright, TypeScript — 9 tests)
- Happy path: generate → story renders with title, sections, moral, word count
- Loading state visible during generation, hidden on completion
- Regenerate produces a new story
- Validation: empty name → inline error, no story view
- UI boundary: name input caps at 40 chars; API rejects 41+ (422)
- API-level checks from the UI context: age out of range → 422; unknown mood → clear message
- UI structure & accessibility: controls wrapped in labels, accessible heading
- Keyboard accessibility: Enter submits the form

### API contract (pytest — 13 tests)
- Scenario-driven from `fixtures/scenarios.json` (3 valid + 7 invalid cases)
- Response contract: `story_id`, `title`, `sections`, `moral`, `word_count`, `request`, `meta`
- Story IDs unique across calls; latency within budget

## Test-data strategy

All scenario data lives in **one place** — `qa-framework/fixtures/scenarios.json` — so test data is reviewable, reusable, and never scattered through test code. The API tests parametrize directly from it (`ids=` give readable test names).

## CI

`.github/workflows/ci.yml` runs two jobs on every push/PR:
1. **API tests** — pytest against the live SUT (readiness-waited)
2. **E2E tests** — Playwright on Chromium (with `--with-deps`), retries on flake in CI, HTML report uploaded as an artifact

## Running locally

```bash
# 1. SUT (terminal 1)
cd story-generator
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --port 8901            # → http://localhost:8901

# 2. API tests (terminal 2)
cd story-generator && pytest qa-tests -q

# 3. E2E tests (terminal 2)
cd qa-framework
npm install                            # @playwright/test
npx playwright install chromium        # one-time browser download
BASE_URL=http://localhost:8901 npx playwright test
```

## Proof it works

The E2E suite caught **two real product bugs** during development:
1. The loading spinner was **always visible** — CSS `display: flex` on `.loading` silently overrode the `hidden` attribute (author styles beat UA styles). Fixed with a global `[hidden] { display: none !important; }` guard.
2. The name input's `maxlength=40` masks API validation from the UI — clarified the contract: UI caps input, API enforces it (both now tested).

That is the point: the suite protects real behavior, not just happy paths.

## License

MIT — see [LICENSE](LICENSE). Built by [Rijalul Fahmi](https://github.com/rijalllllllll). Issues and PRs welcome.