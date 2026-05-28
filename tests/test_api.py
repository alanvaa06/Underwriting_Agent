import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from langchain_community.chat_models.fake import FakeListChatModel

from app.main import app
from app.routes import run as run_module


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, fake_llm_responses: list[str]) -> TestClient:
    # Disable Chroma load (lifespan tries to embed). Tests stub it.
    monkeypatch.setattr(run_module, "_retriever_from_state", lambda _: None)
    # Replace build_llm so no real OpenAI call
    monkeypatch.setattr(
        run_module,
        "build_llm",
        lambda api_key, model: FakeListChatModel(responses=fake_llm_responses),
    )
    with TestClient(app) as c:
        c.app.state.vector_store = None
        yield c


def test_healthz(client: TestClient):
    r = client.get("/api/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_cases_returns_bundled(client: TestClient):
    r = client.get("/api/cases")
    assert r.status_code == 200
    data = r.json()
    assert "cases" in data
    assert len(data["cases"]) >= 1
    assert all("case_id" in c and "name" in c and "applicant" in c for c in data["cases"])
    # applicant payload is ApplicantIn-shaped after server-side normalization
    first = data["cases"][0]["applicant"]
    assert "credit_history" in first
    assert "property_info" in first
    assert "loan_amount" in first["loan"]


def _strong_payload() -> dict:
    cases = json.loads((Path(__file__).resolve().parents[1] / "data" / "test_cases.json").read_text(encoding="utf-8"))["test_cases"]
    applicant = dict(cases[0])
    # Remap property → property_info
    if "property" in applicant and "property_info" not in applicant:
        applicant["property_info"] = applicant.pop("property")
    # Normalize property_type to schema literals
    if "property_info" in applicant:
        pi = dict(applicant["property_info"])
        _type_map = {
            "single family home": "single_family",
            "single family": "single_family",
            "condo": "condo",
            "townhouse": "townhouse",
            "multi family": "multi_family",
        }
        raw_type = pi.get("type", "single_family").lower().strip()
        pi["type"] = _type_map.get(raw_type, "single_family")
        # purchase_price required; use appraised_value fallback
        if "purchase_price" not in pi and "appraised_value" in pi:
            pi["purchase_price"] = pi["appraised_value"]
        applicant["property_info"] = pi
    # Remap loan amount → loan_amount
    if "loan" in applicant and isinstance(applicant["loan"], dict):
        loan = dict(applicant["loan"])
        if "amount" in loan and "loan_amount" not in loan:
            loan["loan_amount"] = loan.pop("amount")
        if "term_years" not in loan:
            loan["term_years"] = 30
        applicant["loan"] = loan
    return {"applicant": applicant, "api_key": "sk-test-fake", "model": "gpt-4o"}


def test_run_endpoint_streams_events_and_emits_decision(client: TestClient):
    with client.stream("POST", "/api/run", json=_strong_payload()) as r:
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/event-stream")
        events = list(_parse_sse(r.iter_lines()))

    types = [e["type"] for e in events]
    assert "agent_start" in types
    assert "agent_complete" in types
    assert "decision" in types
    assert types[-1] == "done"

    decision = next(e for e in events if e["type"] == "decision")
    assert decision["payload"]["decision"] in {"APPROVED", "CONDITIONAL_APPROVAL", "DENIED"}


def test_run_endpoint_returns_pydantic_422_on_bad_input(client: TestClient):
    bad = {"applicant": {"name": "X"}, "api_key": "sk-x"}  # missing required fields
    r = client.post("/api/run", json=bad)
    assert r.status_code == 422


def _parse_sse(lines):
    """Parse iter_lines() output into list of {"type": ..., "payload": ..., "ts": ...} dicts."""
    current_event = None
    current_data = []
    for raw in lines:
        line = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        if line.startswith("event: "):
            current_event = line[len("event: "):]
        elif line.startswith("data: "):
            current_data.append(line[len("data: "):])
        elif line == "":
            if current_event and current_data:
                payload = json.loads("\n".join(current_data))
                yield payload
            current_event, current_data = None, []
