# CLAUDE.md

Guidance for Claude Code working in this repo.

## Project

Multi-agent mortgage underwriting system. LangGraph orchestrates 6 agents (Credit, Income, Asset, Collateral, Critic, Decision) over a synthetic applicant profile, returns APPROVED / CONDITIONAL_APPROVAL / DENIED + risk score + memo. Live demo on Hugging Face Spaces.

Origin: Johns Hopkins / GreatLearning Agentic AI lab. Production-ized as portfolio piece.

## Architecture

- `app/` — FastAPI shell. Routes, SSE, Pydantic schemas. No business logic.
- `underwriter/` — pure domain. State, tools, agents, LangGraph workflow, RAG. Zero FastAPI imports.
- `frontend/` — static SPA (vanilla JS + Tailwind CDN + Mermaid). No build step.
- `data/` — PDF policies + JSON test cases + pre-built Chroma store.
- `tests/` — pyramid: unit (mocked LLM) → integration (TestClient + SSE parse) → e2e (real LLM, gated).

Full spec: `docs/superpowers/specs/2026-05-26-underwriter-mvp-design.md`.

## Workflow

1. Read latest spec + plan in `docs/superpowers/`. Update plan checkboxes as you work.
2. **TDD.** Write failing test → minimal implementation → green → commit. One concern per commit.
3. **Mock the LLM** in unit/integration tests via `FakeListLLM`. Real-LLM tests only in `test_e2e.py`, gated by `OPENAI_API_KEY`.
4. **Inject the LLM** into agent functions — never import a global `ChatOpenAI`. Per-request keys depend on this.
5. **Never log API keys.** Never echo them in error messages. `req.api_key` is `SecretStr`.
6. **Sanitize PII** before any LLM call. Agents read `state.sanitized_data`, tools read `state.applicant_data`.
7. **Pin deps** in requirements.txt. CI enforces lockstep with Python 3.11 + 3.12.

## Principles

- **Simplicity first** — touch only what the task needs.
- **No partial fixes** — root-cause bugs.
- **Boundary integrity** — `underwriter/` must remain framework-agnostic. If you need HTTP, the work belongs in `app/`.
- **One agent per file.** One responsibility per module.

## Quick Commands

```bash
# install
pip install -r requirements.txt -r requirements-dev.txt

# build vector store (one-time, needs OPENAI_API_KEY)
python scripts/build_chroma.py

# run dev server
uvicorn app.main:app --reload --port 7860

# lint + type-check + test
ruff check .
mypy app/ underwriter/
pytest --cov=underwriter --cov=app --cov-fail-under=85
```
