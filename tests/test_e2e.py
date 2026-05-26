"""End-to-end with real gpt-4o. Skipped unless OPENAI_API_KEY is set.
Runs all three bundled cases. Asserts coarse expectations on the decision."""

import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

OPENAI_KEY = os.getenv("OPENAI_API_KEY")

pytestmark = pytest.mark.skipif(not OPENAI_KEY, reason="OPENAI_API_KEY not set")


def _payload(case_idx: int) -> dict:
    cases = json.loads((Path(__file__).resolve().parents[1] / "data" / "test_cases.json").read_text(encoding="utf-8"))["test_cases"]
    applicant = dict(cases[case_idx])
    if "property" in applicant and "property_info" not in applicant:
        prop = dict(applicant.pop("property"))
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
    return {"applicant": applicant, "api_key": OPENAI_KEY, "model": "gpt-4o"}


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


@pytest.fixture(scope="module")
def real_client() -> TestClient:
    with TestClient(app) as c:
        yield c


def _decision(events: list[dict]) -> str:
    decision_evt = next(e for e in events if e["type"] == "decision")
    return decision_evt["payload"]["decision"]


def test_strong_applicant_approved(real_client: TestClient):
    with real_client.stream("POST", "/api/run", json=_payload(0)) as r:
        events = list(_parse_sse(r.iter_lines()))
    assert _decision(events) == "APPROVED"


def test_weak_applicant_denied(real_client: TestClient):
    with real_client.stream("POST", "/api/run", json=_payload(2)) as r:
        events = list(_parse_sse(r.iter_lines()))
    assert _decision(events) == "DENIED"


def test_borderline_applicant_conditional_or_denied(real_client: TestClient):
    with real_client.stream("POST", "/api/run", json=_payload(1)) as r:
        events = list(_parse_sse(r.iter_lines()))
    assert _decision(events) in {"CONDITIONAL_APPROVAL", "DENIED"}
