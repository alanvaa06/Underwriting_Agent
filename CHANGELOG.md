# Changelog

All notable changes to this project are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Mock-data button: loads a random bundled applicant (`feat(frontend): mock data button`)
- In-memory per-IP rate limit on `/api/run` — 5 runs/min (`feat(api): in-memory per-IP rate limit`)
- README architecture diagram (Mermaid) above the fold
- OG / Twitter card meta tags
- `CHANGELOG.md`
- `.pre-commit-config.yaml` (ruff + mypy)
- `.github/dependabot.yml` (pip + github-actions weekly)

### Fixed
- Mermaid graph wiped by i18n `data-i18n` attribute on container (`fix(frontend): remove data-i18n from graph container`)
- Mermaid graph not rendered at page load + dark-theme mismatch on first paint (`fix(frontend): render mermaid graph at page load`)
- Dark-mode contrast on form inputs / textareas / select (`fix(frontend): dark mode variants on form inputs`)

## [0.3.0] — 2026-05-27

Polish bundle: cost meter, PDF export, dark mode, live token streaming, Spanish i18n.

### Added
- GPT-4o pricing constants + `compute_cost(usage)` (`underwriter/pricing.py`)
- `usage` state field with `_merge_usage` reducer
- Async `invoke_agent` returning `(parsed, usage)`; streaming `ChatOpenAI`
- All 6 agent nodes converted to async + emit per-agent usage
- `build_workflow(..., callback_factory=...)` for per-agent LangChain async callbacks
- `token` and `cost` SSE event types; `asyncio.Queue` token bridge
- Dark mode toggle (Tailwind class strategy + Mermaid theme swap, persisted)
- Decision-memo PDF export via jsPDF
- Cost breakdown table + live per-agent token stream in agent tabs
- Spanish i18n with EN/ES toggle (~80 string keys)

### Fixed
- mypy + ruff cleanup (Callable import, type-ignore placement, RUF012 noqa)
- Duplicate `<strong>` in banner.demo i18n span

## [0.2.0] — 2026-05-27

Form polish + section notes.

### Added
- Optional `notes` field (max 2000 chars) on 5 applicant sub-models
- Specialist agent prompts include section notes
- 5 section-notes textareas with character counter
- Money input formatter (`format.js`) + `$n()` strips commas before parse
- Tooltip popover CSS + tooltips on every form field
- 3 manual-test checks for tooltips and section notes

### Fixed
- `sanitize_pii` deep-scrubs SSN + email in nested strings
- Ruff I001 import order in `test_schemas`

## [0.1.1] — 2026-05-27

MVP release.

### Added
- `UnderwritingState` TypedDict + `init_state`
- Domain tools: `compute_dti`, `compute_ltv`, `sanitize_pii`
- `UnderwriterError` exception hierarchy
- Pydantic v2 schemas: `ApplicantIn`, `RunRequest`, `AgentEvent`
- RAG: `build_chroma` script + committed vector store, `load_or_build_store`, `retrieve_policy`
- Six LangGraph agents: credit, income, asset, collateral, critic, decision
- `build_workflow` with supervisor routing
- `stream_run` async iterator wrapping `graph.astream` + SSE formatter
- FastAPI routes: `/api/healthz`, `/api/cases`, `/api/run` (SSE, heartbeat, disconnect handling)
- Vanilla-JS frontend: form, Mermaid graph, tabs, decision card
- Real-LLM e2e tests gated by `OPENAI_API_KEY`
- Dockerfile (HF Space target), `run_local.sh`
- CI: ruff + mypy + pytest matrix 3.11/3.12
- Architecture, deployment, and manual-test docs
- Git LFS for Chroma binaries

[Unreleased]: https://github.com/alanvaa06/Underwriting_Agent/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/alanvaa06/Underwriting_Agent/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/alanvaa06/Underwriting_Agent/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/alanvaa06/Underwriting_Agent/releases/tag/v0.1.1
