import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routes import run as run_module
from underwriter.errors import AuthError, RateLimitError


def _strong_payload() -> dict:
    cases = json.loads((Path(__file__).resolve().parents[1] / "data" / "test_cases.json").read_text(encoding="utf-8"))["test_cases"]
    applicant = dict(cases[0])
    # Apply same normalization as tests/test_api.py
    if "property" in applicant and "property_info" not in applicant:
        prop = dict(applicant.pop("property"))
        # Normalize property_type strings to schema literals
        ptype_map = {
            "Single Family Home": "single_family",
            "Single Family": "single_family",
            "Condo": "condo",
            "Townhouse": "townhouse",
            "Multi-family": "multi_family",
            "Multi Family": "multi_family",
        }
        if "type" in prop and "property_type" not in prop:
            prop["property_type"] = ptype_map.get(prop.pop("type"), "single_family")
        if "occupancy" in prop:
            occ_map = {"Primary": "primary", "Secondary": "secondary", "Investment": "investment"}
            prop["occupancy"] = occ_map.get(prop["occupancy"], prop["occupancy"]).lower()
        if "purchase_price" not in prop:
            prop["purchase_price"] = prop.get("appraised_value") or 500000
        applicant["property_info"] = prop
    if "loan" in applicant:
        loan = dict(applicant["loan"])
        if "amount" in loan and "loan_amount" not in loan:
            loan["loan_amount"] = loan.pop("amount")
        if "term_years" not in loan:
            loan["term_years"] = 30
        applicant["loan"] = loan
    return {"applicant": applicant, "api_key": "sk-test-fake", "model": "gpt-4o"}


def _parse_sse(lines):
    cur_event, cur_data = None, []
    for raw in lines:
        line = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        if line.startswith("event: "):
            cur_event = line[len("event: "):]
        elif line.startswith("data: "):
            cur_data.append(line[len("data: "):])
        elif line == "":
            if cur_event and cur_data:
                yield json.loads("\n".join(cur_data))
            cur_event, cur_data = None, []


def _client_with_failing_stream(monkeypatch: pytest.MonkeyPatch, exc: Exception) -> TestClient:
    async def fake_stream_run(*args, **kwargs):
        raise exc
        yield  # pragma: no cover — make this an async generator

    monkeypatch.setattr(run_module, "stream_run", fake_stream_run)
    monkeypatch.setattr(run_module, "_retriever_from_state", lambda _: None)
    monkeypatch.setattr(run_module, "build_llm", lambda api_key, model: object())
    from app.ratelimit import RateLimiter
    monkeypatch.setattr(run_module, "_limiter", RateLimiter(max_requests=10_000, window_seconds=60.0))
    c = TestClient(app)
    c.app.state.vector_store = None
    return c


def test_auth_error_emits_sse_error_event_and_halts(monkeypatch):
    client = _client_with_failing_stream(monkeypatch, AuthError("Invalid API key"))
    with client.stream("POST", "/api/run", json=_strong_payload()) as r:
        events = list(_parse_sse(r.iter_lines()))
    err = next(e for e in events if e["type"] == "error")
    assert err["payload"]["code"] == "OPENAI_AUTH"
    assert err["payload"]["recoverable"] is False


def test_rate_limit_error_marks_recoverable(monkeypatch):
    client = _client_with_failing_stream(monkeypatch, RateLimitError("429"))
    with client.stream("POST", "/api/run", json=_strong_payload()) as r:
        events = list(_parse_sse(r.iter_lines()))
    err = next(e for e in events if e["type"] == "error")
    assert err["payload"]["code"] == "OPENAI_RATE_LIMIT"
    assert err["payload"]["recoverable"] is True


def test_unexpected_exception_becomes_internal_error_event(monkeypatch):
    client = _client_with_failing_stream(monkeypatch, RuntimeError("boom"))
    with client.stream("POST", "/api/run", json=_strong_payload()) as r:
        events = list(_parse_sse(r.iter_lines()))
    err = next(e for e in events if e["type"] == "error")
    assert err["payload"]["code"] == "INTERNAL"
    # message must NOT include the raw exception text — sanitized
    assert "boom" not in err["payload"]["message"]
