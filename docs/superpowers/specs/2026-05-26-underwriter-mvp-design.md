# Underwriter Agent MVP — Design Spec

**Date:** 2026-05-26
**Status:** Awaiting user review
**Author:** Alan Vazquez (with Claude Code)
**Repo:** https://github.com/alanvaa06/Underwriting_Agent

---

## 1. Goal

Ship a public, portfolio-grade demo of the multi-agent mortgage underwriting system. Colleagues access a shareable URL, supply their own OpenAI API key, fill an applicant form, and watch a LangGraph workflow execute live (graph viz + per-agent panels + final decision).

Existing assets: `Senior_Mortgage_Underwriting_System_Learners_Notebook.ipynb` (JHU/GreatLearning lab), `underwriting_policies.pdf` (RAG corpus), `mortgage_test_cases.json` (3 personas).

Notebook becomes teaching artifact; production code lives in a clean, modular Python package backed by FastAPI + a static SPA, deployed as a Docker Hugging Face Space.

---

## 2. Decisions Made During Brainstorming

| Decision | Choice |
|---|---|
| Demo scope | Full custom applicant form (empty start, no prefill) |
| Output detail | Decision + per-agent panels + live LangGraph viz |
| Audience / lifespan | Portfolio piece, public |
| Model | Locked to `gpt-4o` |
| Hosting | Docker Hugging Face Space (free CPU tier) |
| Framework | FastAPI backend + vanilla JS SPA frontend |
| Streaming | SSE (not WebSocket) |
| API key handling | Per-request, never stored, no HF secret |
| RAG strategy | Build Chroma once locally, commit to repo, bake into image |

---

## 3. Architecture

### 3.1 Topology

Single Docker container on HF Space, port 7860. FastAPI serves both `/api/*` endpoints and `/` static frontend. No reverse proxy, no separate frontend host.

```
┌──────────── HF Space (Docker, port 7860) ─────────────┐
│                                                       │
│   Static frontend     ◀─SSE─▶  FastAPI app            │
│   (served by FastAPI)          │                      │
│                                ▼                      │
│                          underwriter/ package         │
│                          (state, agents, graph, RAG)  │
│                                │                      │
│                                ▼                      │
│                          Chroma  +  OpenAI API        │
└───────────────────────────────────────────────────────┘
```

### 3.2 Key Decisions

- **Single container, single port** — simplest HF Docker Space layout.
- **SSE over WebSocket** — one-way agent → UI updates, works through HF proxies.
- **API key per request** — frontend sends key in POST body; backend instantiates `ChatOpenAI(api_key=...)` per request. Never stored, never logged.
- **Chroma persistence** — pre-built `data/chroma/` directory committed to repo, baked into image. No runtime embedding cost, no HF Pro tier.
- **No auth, no rate limit** — public Space, user-paid tokens. Disclaimer banner on UI.

### 3.3 SSE Event Protocol

```
event: agent_start       data: {"agent":"credit","ts":...}
event: agent_thinking    data: {"agent":"credit","step":"..."}
event: agent_complete    data: {"agent":"credit","output":{...},"duration_ms":...}
event: graph_transition  data: {"from":"credit","to":"supervisor"}
event: decision          data: {"decision":"APPROVED","risk_score":23,"memo":"..."}
event: error             data: {"code":"OPENAI_AUTH","message":"...","agent":"...","recoverable":false}
event: ping              data: {}   # heartbeat every 10s
event: done              data: {"total_duration_ms":...}
```

---

## 4. Repo Structure

```
underwriter-agent/
├── README.md                       # hero, demo URL, badges, quickstart
├── LICENSE                         # MIT
├── Dockerfile                      # HF Space container
├── requirements.txt                # pinned runtime deps
├── requirements-dev.txt            # pytest, ruff, mypy
├── pyproject.toml                  # package metadata, ruff/mypy config
├── .gitignore                      # .superpowers/, .venv/, __pycache__, etc.
├── .env.example                    # OPENAI_API_KEY=...  (local dev only)
│
├── app/                            # FastAPI shell — routing, SSE, schemas
│   ├── __init__.py
│   ├── main.py                     # app factory + lifespan
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── run.py                  # POST /api/run → SSE stream
│   │   ├── cases.py                # GET /api/cases → bundled examples
│   │   └── health.py               # GET /api/healthz
│   ├── sse.py                      # SSE event formatter
│   └── schemas.py                  # Pydantic: ApplicantIn, RunRequest, AgentEvent
│
├── underwriter/                    # pure domain — no FastAPI, no HTTP
│   ├── __init__.py
│   ├── state.py                    # UnderwritingState TypedDict
│   ├── tools.py                    # DTI, LTV, sanitize_pii
│   ├── rag.py                      # load_or_build_store, retriever
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py                 # shared prompt template, llm factory
│   │   ├── credit.py
│   │   ├── income.py
│   │   ├── asset.py
│   │   ├── collateral.py
│   │   ├── critic.py
│   │   └── decision.py
│   ├── graph.py                    # build_workflow(), supervisor routing
│   └── streaming.py                # AsyncIterator[AgentEvent] wrapper
│
├── frontend/                       # static SPA — no build step
│   ├── index.html
│   ├── styles.css
│   ├── app.js                      # form, SSE consumer, UI dispatch
│   ├── graph.js                    # mermaid render + node highlight
│   └── assets/
│       └── logo.svg
│
├── data/
│   ├── underwriting_policies.pdf
│   ├── test_cases.json
│   └── chroma/                     # pre-built vector store, committed
│
├── tests/
│   ├── conftest.py                 # fake llm, sample applicants, test client
│   ├── test_tools.py
│   ├── test_schemas.py
│   ├── test_agents.py
│   ├── test_graph.py
│   ├── test_api.py
│   ├── test_errors.py
│   └── test_e2e.py                 # skipif not OPENAI_API_KEY
│
├── scripts/
│   ├── build_chroma.py             # PDF → Chroma at data/chroma/
│   └── run_local.sh                # uvicorn dev server
│
├── docs/
│   ├── architecture.md             # mermaid + SSE protocol + module map
│   ├── deployment.md               # HF Space setup
│   ├── manual-test-plan.md         # 7-step pre-deploy checklist
│   └── superpowers/                # specs/, plans/
│
├── notebooks/
│   └── Senior_Mortgage_Underwriting_Walkthrough.ipynb   # archived teaching artifact
│
└── .github/
    └── workflows/
        ├── test.yml                # ruff + pytest + mypy on push/PR
        └── e2e.yml                 # workflow_dispatch, real LLM
```

### 4.1 Boundary Principles

- **`underwriter/` is pure domain** — zero FastAPI, zero HTTP. Importable from any host.
- **`app/` is the FastAPI shell** — routing, SSE plumbing, request validation. No business logic.
- **`frontend/` is static** — no build step. Mermaid + Tailwind via CDN.
- **`scripts/` is ops** — runnable utilities, never imported.
- **Tests mirror source tree.**
- **Existing notebook preserved** as teaching artifact in `notebooks/`.
- **Orphaned `docs/context/*` momentum residue purged** from prior project template.

### 4.2 Per-Agent File Contract

Each `underwriter/agents/{name}.py` exposes one function:

```python
def credit_analyst_node(state: UnderwritingState, *, llm: BaseChatModel) -> dict:
    """Pure node function — takes state, returns state delta. No side effects beyond LLM call."""
    ...
    return {"credit_analysis": ..., "reasoning_chain": [...]}
```

LLM injected (not imported globally) → easy mocking + per-request API key.

---

## 5. Backend Components

### 5.1 `app/main.py` — app factory + lifespan

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.vector_store = rag.load_or_build_store(CHROMA_DIR, PDF_PATH)
    yield

app = FastAPI(lifespan=lifespan, title="Underwriter Agent")
app.include_router(run.router, prefix="/api")
app.include_router(cases.router, prefix="/api")
app.include_router(health.router, prefix="/api")
app.mount("/", StaticFiles(directory="frontend", html=True), name="static")
```

### 5.2 `app/schemas.py` — Pydantic v2

```python
class ApplicantIn(BaseModel):
    name: str
    credit_score: int = Field(ge=300, le=850)
    credit_history: CreditHistory
    employment: Employment
    debts: Debts
    assets: Assets
    property_info: PropertyInfo
    loan: LoanRequest

class RunRequest(BaseModel):
    applicant: ApplicantIn
    api_key: SecretStr
    model: Literal["gpt-4o"] = "gpt-4o"

class AgentEvent(BaseModel):
    type: Literal["agent_start","agent_thinking","agent_complete",
                  "graph_transition","decision","error","ping","done"]
    payload: dict
    ts: float
```

### 5.3 `app/routes/run.py` — SSE endpoint

```python
@router.post("/run")
async def run_underwriting(req: RunRequest, request: Request):
    async def event_gen():
        try:
            llm = build_llm(req.api_key.get_secret_value(), req.model)
            async for evt in streaming.stream_run(req.applicant, llm, request.app.state.vector_store):
                if await request.is_disconnected():
                    break
                yield sse.format(evt)
        except UnderwriterError as e:
            yield sse.format(AgentEvent(type="error", payload={"code": e.code, "message": str(e), "recoverable": e.recoverable}, ts=time()))
        except Exception as e:
            yield sse.format(AgentEvent(type="error", payload={"code":"INTERNAL","message":"Unexpected error","recoverable":False}, ts=time()))
            logger.exception("internal error")
    return StreamingResponse(event_gen(), media_type="text/event-stream",
                             headers={"X-Accel-Buffering":"no", "Cache-Control":"no-cache"})
```

### 5.4 `underwriter/streaming.py`

```python
async def stream_run(applicant, llm, vector_store) -> AsyncIterator[AgentEvent]:
    graph = build_workflow(llm=llm, retriever=vector_store.as_retriever())
    initial_state = init_state(applicant)
    async for chunk in graph.astream(initial_state, stream_mode="updates"):
        for node_name, delta in chunk.items():
            yield AgentEvent(type="agent_start", payload={"agent": node_name}, ts=time())
            yield AgentEvent(type="agent_complete", payload={"agent": node_name, "output": delta}, ts=time())
    final = await graph.aget_state(...)
    yield AgentEvent(type="decision", payload={"decision": final["final_decision"], "risk_score": final["risk_score"], "memo": final["decision_memo"]}, ts=time())
    yield AgentEvent(type="done", payload={"total_duration_ms": ...}, ts=time())
```

### 5.5 RAG — `underwriter/rag.py`

`load_or_build_store(chroma_dir, pdf_path)`:

- If `chroma_dir/chroma.sqlite3` exists → load via `Chroma(persist_directory=...)`
- Else → `PyPDFLoader(pdf_path)` → `RecursiveCharacterTextSplitter(chunk=1000, overlap=200)` → `Chroma.from_documents(..., embedding=OpenAIEmbeddings())`

**Strategy A locked**: build once locally via `scripts/build_chroma.py`, commit `data/chroma/` to repo. Zero runtime embedding cost. PDF is static, no privacy concern.

### 5.6 Concurrency Model

- FastAPI async, uvicorn `workers=1` (free Space has 2 vCPU, 16GB).
- Each request gets own `ChatOpenAI` (per-key isolation).
- Vector store shared read-only via `app.state`.
- `graph.astream` yields per node → natural backpressure to SSE.
- Disconnect detected via `request.is_disconnected()` → break loop, cancel pending LLM call.

---

## 6. Frontend

### 6.1 Layout (desktop ≥1024px)

Two-column: form left (40%), live run right (60%).

- Header: title + tagline + GitHub link
- Banner: "Demo only. Your OpenAI key is used per-request and never stored."
- Left column: collapsible form sections (Borrower, Employment, Debts, Assets, Property & Loan) + API key field + Run button
- Right column: graph viz (mermaid SVG), per-agent tabs (Credit / Income / Asset / Collateral / Critic), decision card

### 6.2 Tech Choices

- **No framework** — vanilla JS, single `app.js` + `graph.js`. Form is static, state simple, zero npm dep.
- **Tailwind via CDN play-mode** — `<script src="https://cdn.tailwindcss.com">`. Zero build.
- **Mermaid.js for graph viz** — render workflow DAG from string, mutate `classDef` per agent event, re-render.
- **SSE via fetch + `response.body.getReader()`** — EventSource doesn't support POST; ~30 LoC manual parser.
- **Form state in plain object** — `buildPayload()` walks form fields → nested JSON matching `ApplicantIn`.

### 6.3 UI States

| State | Form | Graph | Decision | Button |
|---|---|---|---|---|
| Idle | Editable | Grey nodes | Hidden | "Run Underwriting" |
| Validating | Editable, inline errors | Grey | Hidden | "Run Underwriting" |
| Streaming | Locked | Amber (running) / Green (done) per event | Hidden | "Cancel" |
| Done | Unlocked | All green | Animated in | "Run Again" |
| Error | Unlocked | Resets (or red on failing node) | Hidden | "Retry" |

### 6.4 Graph Viz

```javascript
const BASE_GRAPH = `
flowchart TD
  init([Initialize]) --> sup{Supervisor}
  sup --> credit[Credit] --> sup
  sup --> income[Income] --> sup
  sup --> asset[Asset] --> sup
  sup --> collateral[Collateral] --> sup
  sup --> critic[Critic] --> decision[Decision] --> done([Done])
  classDef pending fill:#e5e7eb,stroke:#9ca3af
  classDef running fill:#fef3c7,stroke:#f59e0b,stroke-width:3px
  classDef done    fill:#d1fae5,stroke:#10b981
  classDef error   fill:#fee2e2,stroke:#ef4444
`;

const nodeState = { credit:'pending', income:'pending', asset:'pending', collateral:'pending', critic:'pending', decision:'pending' };

function applyState() {
  const lines = Object.entries(nodeState).map(([k,v]) => `class ${k} ${v}`).join('\n');
  return BASE_GRAPH + '\n' + lines;
}

function onEvent(evt) {
  if (evt.type === 'agent_start')    nodeState[evt.payload.agent] = 'running';
  if (evt.type === 'agent_complete') nodeState[evt.payload.agent] = 'done';
  if (evt.type === 'error')          nodeState[evt.payload.agent] = 'error';
  mermaid.render('graph-svg', applyState()).then(({svg}) => {
    document.getElementById('graph-container').innerHTML = svg;
  });
}
```

### 6.5 Form Sections (collapsible `<details>`)

- **Borrower** — name, FICO, credit_history (bankruptcies, foreclosures, late_payments_12mo/24mo, oldest_tradeline_years)
- **Employment** — employer, position, years, monthly_income, type (W2/1099), gap
- **Debts** — car_loan, student_loan, credit_cards (auto-summed)
- **Assets** — checking, savings, investments, retirement
- **Property & Loan** — purchase_price, down_payment, loan_amount (auto-calc), property_type, occupancy

Auto-computed (DTI, LTV, total_debt) shown read-only beside related inputs, recompute on blur.

---

## 7. Data Flow (Happy Path)

End-to-end ~28s for full run with `gpt-4o`.

1. **t=0** — user clicks Run. Frontend: `validateForm()` → `buildPayload()` → `lockForm()` → `fetch('/api/run', {method:'POST', body: ...})`
2. **t=0.1s** — Backend: Pydantic validates → `build_llm(key)` → returns `StreamingResponse(text/event-stream)`
3. **t=0.2s** — `streaming.stream_run` calls `graph.astream(state, stream_mode='updates')`
4. **t=0.3s** — `initialize` → `supervisor` → `credit`. SSE `agent_start{credit}` → mermaid node amber
5. **t=4.5s** — Credit completes. SSE `agent_complete{credit, output}` → mermaid node green + panel populates
6. Cycle continues: income, asset, collateral, each ~4s
7. **t=20s** — Supervisor → critic. SSE events.
8. **t=25s** — Critic → decision. SSE events.
9. **t=28s** — SSE `decision{APPROVED, risk_score, memo}` → decision card animates in (green/amber/red by outcome)
10. **t=28.1s** — SSE `done{total_duration_ms}` → form unlocks, button → "Run Again". Backend closes stream. State discarded.

### 7.1 State Lifecycle

- **Frontend** — single in-memory object, cleared on Run Again, never persisted
- **Backend** — per-request `UnderwritingState` TypedDict + `MemorySaver` checkpoint, GC'd when request ends
- **Shared** — only `app.state.vector_store` (read-only Chroma handle)
- **No DB, no Redis, no session store.** Refreshing the page kills the run cleanly.

### 7.2 PII Path

`sanitize_pii()` runs **before** any LLM call:

- SSN → `XXX-XX-NNNN` (last 4 only)
- Full name → first name only
- Street address dropped → city + state only
- Phone/email stripped

`state.applicant_data` = raw (for tools that need real numbers). `state.sanitized_data` = scrubbed (passed to LLM prompts). Agents read only sanitized.

### 7.3 Audit Trail

`state.reasoning_chain: Annotated[List[str], "append"]` — each agent appends. Full audit log. Not surfaced in MVP UI; available in `decision` event payload for power users inspecting network.

---

## 8. Error Handling

### 8.1 Error Taxonomy

| Code | Where | Trigger | UI Response |
|---|---|---|---|
| `VALIDATION_CLIENT` | Frontend | Required empty, FICO out of range, negatives | Inline field error, no network call |
| `VALIDATION_SERVER` | FastAPI | Pydantic rejects (defense in depth) | HTTP 422, banner with field path |
| `OPENAI_AUTH` | Backend | Invalid key, revoked key, no billing | SSE error event, red banner |
| `OPENAI_RATE_LIMIT` | Backend | 429 from OpenAI | SSE error event, suggest retry |
| `OPENAI_TIMEOUT` | Backend | LLM call >60s | SSE error event, mark failing agent red |
| `RAG_RETRIEVE` | Backend | Chroma query fails | Agent proceeds without RAG, panel notes "policy retrieval skipped" |
| `AGENT_PARSE` | Backend | LLM output doesn't match expected structure | Retry once with stricter prompt; second failure → error event |
| `CLIENT_DISCONNECT` | Backend | User closes tab | Loop breaks, LLM cancel, no event sent |
| `INTERNAL` | Backend | Catch-all | SSE error event, stderr log with traceback, generic UI message |
| `NETWORK` | Frontend | Fetch abort, SSE drop | Toast, unlock form, "Retry" button |

### 8.2 Exception Hierarchy

```python
class UnderwriterError(Exception):
    code: str
    recoverable: bool = False

class AuthError(UnderwriterError):       code = "OPENAI_AUTH"
class RateLimitError(UnderwriterError):  code = "OPENAI_RATE_LIMIT"; recoverable = True
class TimeoutError(UnderwriterError):    code = "OPENAI_TIMEOUT";    recoverable = True
class RAGError(UnderwriterError):        code = "RAG_RETRIEVE";      recoverable = True
class AgentParseError(UnderwriterError): code = "AGENT_PARSE"
```

### 8.3 Logging

- Structured JSON to stdout (HF Space captures). Fields: `request_id`, `agent`, `event_type`, `duration_ms`, `error_code`.
- **No PII** — only sanitized fields.
- **No API keys** — never log `req.api_key`, never echo in error messages to client.
- **Request ID** — UUID via middleware, propagated through SSE events.

### 8.4 Frontend Resilience

- SSE reader wrapped in try/catch around `reader.read()`.
- **Heartbeat**: backend sends `event: ping` every 10s during long LLM calls (prevents HF proxy timeout).
- If no event for 30s → frontend surfaces `NETWORK`.
- **Cancel** during streaming → `controller.abort()` → backend detects disconnect.

---

## 9. Testing Strategy

### 9.1 Pyramid

| Layer | File | Scope | LLM | Run On |
|---|---|---|---|---|
| Unit — tools | `test_tools.py` | DTI/LTV math, PII sanitizer, type coercion | N/A | Every commit |
| Unit — schemas | `test_schemas.py` | Pydantic validation: FICO range, required, coercion | N/A | Every commit |
| Unit — agents | `test_agents.py` | Each agent in isolation: state + mock LLM → asserts delta shape + `reasoning_chain` append | `FakeListLLM` | Every commit |
| Integration — graph | `test_graph.py` | Full workflow, mocked agents. Routing: supervisor → all specialists → critic → decision → END | `FakeListLLM` | Every commit |
| Integration — API | `test_api.py` | `TestClient`, POST `/api/run`, parse SSE, assert event sequence + decision present | `FakeListLLM` via dep override | Every commit |
| Integration — errors | `test_errors.py` | Each error path: invalid Pydantic, raised `AuthError`, disconnect mid-stream | Mocks raising | Every commit |
| E2E — real LLM | `test_e2e.py` | All 3 bundled cases vs real `gpt-4o`. Strong→APPROVED, Weak→DENIED, Borderline→CONDITIONAL or DENIED | Real `ChatOpenAI` | Manual / nightly, `@pytest.mark.skipif(not OPENAI_API_KEY)` |

### 9.2 Fixtures (`conftest.py`)

- `strong_applicant`, `borderline_applicant`, `weak_applicant` — Pydantic-validated `ApplicantIn` from `data/test_cases.json`
- `fake_llm` — `FakeListLLM` with per-agent canned JSON
- `vector_store` — tiny `Chroma.from_texts([...], FakeEmbeddings(size=128))`
- `client` — `TestClient(app)` with dependency overrides

### 9.3 Coverage Targets

- `underwriter/tools.py` — 100% (pure functions, must be airtight)
- `underwriter/agents/*` — 90%+
- `underwriter/graph.py` — 100% routing logic
- `app/routes/*` — 90%+ (happy path + every documented error code)
- `underwriter/rag.py` — 80%+
- **Overall: 85%+**, enforced via `pytest --cov-fail-under=85`

### 9.4 CI

`.github/workflows/test.yml`:

- Trigger: push, PR to `main`
- Matrix: Python 3.11, 3.12
- Steps: install → `ruff check` → `pytest --cov=underwriter --cov=app --cov-fail-under=85` → `mypy app/ underwriter/` (strict)

`.github/workflows/e2e.yml`: separate, `workflow_dispatch`, uses repo secret `OPENAI_API_KEY`. ~$0.50/run.

### 9.5 Manual Frontend Test Plan

Documented in `docs/manual-test-plan.md`, checked in PR descriptions:

1. Empty form → Run → all required-field errors inline
2. Invalid key → SSE error → red banner
3. Cancel mid-stream → graph stops, form unlocks
4. Strong case full run → APPROVED card (green)
5. Weak case full run → DENIED card (red)
6. Refresh during stream → no zombie state
7. Mobile viewport (375×667) → form stacks, graph scales

---

## 10. Deployment

### 10.1 Dockerfile

```dockerfile
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ ./app/
COPY underwriter/ ./underwriter/
COPY frontend/ ./frontend/
COPY data/ ./data/

EXPOSE 7860
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
```

### 10.2 HF Space Setup

- **SDK**: Docker
- **Hardware**: CPU basic (free, 2vCPU/16GB) — no local model weights
- **Visibility**: Public
- **Repo link**: HF Spaces "Sync from GitHub" → `alanvaa06/Underwriting_Agent`, push to `main` triggers rebuild
- **Secrets**: None
- **README HF metadata**: title, emoji, colorFrom/To, `sdk: docker`, `app_port: 7860`, `pinned: false`

### 10.3 requirements.txt (pinned)

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
pydantic==2.10.4
python-multipart==0.0.20
langgraph==0.2.62
langchain==0.3.14
langchain-openai==0.2.14
langchain-community==0.3.14
langchain-text-splitters==0.3.5
chromadb==0.5.23
pypdf==5.1.0
sse-starlette==2.2.1
```

Dev deps in `requirements-dev.txt`: `pytest`, `pytest-asyncio`, `pytest-cov`, `httpx`, `ruff`, `mypy`.

### 10.4 Local Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
export OPENAI_API_KEY=sk-...
python scripts/build_chroma.py        # one-time, writes data/chroma/
uvicorn app.main:app --reload --port 7860
```

### 10.5 Release Flow

1. Branch `feat/X` → commit → push
2. PR to `main` → CI (ruff + pytest + mypy)
3. Manual frontend test plan checked in PR description
4. Merge → HF Space auto-rebuild (~2-3 min)
5. Smoke test on live URL
6. Tag `v0.1.0` on milestone releases

### 10.6 Operational Posture

- **No SLA** — best-effort demo. Free Space sleeps after 48h idle, ~30s cold start.
- **Operator cost: $0** — user-paid keys, no HF Pro.
- **Observability** — HF Space log viewer for stdout. No external APM.
- **Versioning** — semver in `pyproject.toml`. Tag milestones.

### 10.7 README Outline

1. Hero banner + tagline
2. Badges: CI, Python version, license, HF Spaces "Open in Spaces", GitHub stars
3. Animated GIF / screenshot of full run
4. "Try it live" → HF Space URL prominent
5. How it works — mermaid agent graph + 3 paragraphs
6. Local quickstart (5 commands)
7. Architecture — link to `docs/architecture.md`
8. Tech stack badges (LangGraph, FastAPI, OpenAI, Chroma)
9. Contributing + license + acknowledgments (JHU course)

---

## 11. Out of Scope (Explicitly)

To keep MVP shippable:

- No user accounts, sessions, persistence of runs
- No analytics / usage telemetry
- No multi-language support (English only)
- No alternative LLM providers (OpenAI only, `gpt-4o` only)
- No custom branding theming UI
- No PDF upload (policy corpus is static, baked into image)
- No agent prompt customization UI
- No real PII handling (sanitizer scrubs synthetic test data only; real-world PII compliance is out of scope)
- No frontend automated tests (manual checklist only)
- No HF Pro persistent storage tier

These are candidates for v0.2+ once MVP lands.

---

## 12. Open Questions / Risks

- **HF proxy SSE buffering** — `X-Accel-Buffering: no` header set. If still buffered, may need to switch to chunked Transfer-Encoding workaround or HF Pro tier.
- **LangGraph `astream` stream_mode** — spec assumes `updates`. If granularity insufficient (e.g., need token-level), revisit with `messages` or `custom` modes.
- **Mermaid re-render performance** — full SVG regenerate per event. If flicker visible at <100ms cadence, switch to targeted DOM mutation of existing SVG nodes.
- **AGENT_PARSE retry budget** — set to 1 retry. If brittle in practice, may need structured output via `with_structured_output(Pydantic)` for decision agent specifically.
- **Pre-built Chroma in git** — adds ~MB to repo. If embedding model changes, must rebuild + recommit. Acceptable tradeoff for free deploy.

---

## 13. Acceptance Criteria

MVP is shippable when:

- [ ] Repo structure matches §4. All orphaned context files purged.
- [ ] All 6 agents reimplemented as injectable node functions (§4.2 contract).
- [ ] FastAPI app serves `/`, `/api/run`, `/api/cases`, `/api/healthz`.
- [ ] SSE stream emits all events from §3.3 with correct payload shapes.
- [ ] Frontend renders form with 5 collapsible sections + live graph + per-agent tabs + decision card.
- [ ] All UI states (§6.3) reachable and visually distinct.
- [ ] CI green: ruff, pytest (85% coverage), mypy strict on `app/` + `underwriter/`.
- [ ] All 7 manual frontend tests pass.
- [ ] E2E test passes for all 3 bundled cases against real `gpt-4o`.
- [ ] HF Space deployed, reachable, full run completes from public URL.
- [ ] README has demo URL, GIF, badges, quickstart.

---

**Spec ends here.** Implementation plan to follow in `docs/superpowers/plans/2026-05-26-underwriter-mvp.md` via writing-plans skill.
