"""Shared pytest fixtures. Imported automatically by all tests in tests/."""

import json
from pathlib import Path

import pytest
from langchain_community.chat_models.fake import FakeListChatModel

from app.schemas import ApplicantIn

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


@pytest.fixture(scope="session")
def test_cases_raw() -> list[dict]:
    return json.loads((DATA_DIR / "test_cases.json").read_text(encoding="utf-8"))["test_cases"]


@pytest.fixture(scope="session")
def strong_applicant_raw(test_cases_raw: list[dict]) -> dict:
    """First case in test_cases.json — high FICO, stable income."""
    return test_cases_raw[0]


@pytest.fixture(scope="session")
def borderline_applicant_raw(test_cases_raw: list[dict]) -> dict:
    return test_cases_raw[1]


@pytest.fixture(scope="session")
def weak_applicant_raw(test_cases_raw: list[dict]) -> dict:
    return test_cases_raw[2]


def _to_applicant_in(raw: dict) -> ApplicantIn:
    """Adapt the legacy notebook JSON shape into ApplicantIn. test_cases.json must contain
    keys: name, credit_score, credit_history, employment, debts, assets, property_info, loan.
    If older shape uses 'property' instead of 'property_info', remap here.
    If loan uses 'amount' instead of 'loan_amount', remap here."""
    payload = dict(raw)
    if "property" in payload and "property_info" not in payload:
        payload["property_info"] = payload.pop("property")
    # Remap legacy loan shape: {amount, down_payment, ...} → {loan_amount, down_payment, term_years}
    if "loan" in payload and isinstance(payload["loan"], dict):
        loan = dict(payload["loan"])
        if "amount" in loan and "loan_amount" not in loan:
            loan["loan_amount"] = loan.pop("amount")
        if "term_years" not in loan:
            loan["term_years"] = 30
        payload["loan"] = loan
    return ApplicantIn.model_validate(payload)


@pytest.fixture
def strong_applicant(strong_applicant_raw: dict) -> ApplicantIn:
    return _to_applicant_in(strong_applicant_raw)


@pytest.fixture
def borderline_applicant(borderline_applicant_raw: dict) -> ApplicantIn:
    return _to_applicant_in(borderline_applicant_raw)


@pytest.fixture
def weak_applicant(weak_applicant_raw: dict) -> ApplicantIn:
    return _to_applicant_in(weak_applicant_raw)


@pytest.fixture
def fake_llm_responses() -> list[str]:
    """Canned per-agent JSON, in workflow order: credit, income, asset, collateral, critic, decision."""
    return [
        '{"summary":"FICO 760, oldest tradeline 15y, zero derogatory. LOW risk.","risk_level":"low"}',
        '{"summary":"W2 Senior Engineer, $12500/mo stable. Qualifies.","dti":0.304}',
        '{"summary":"Liquid $185k + $0 invest/retirement. Strong reserves.","reserves_months":12}',
        '{"summary":"Single-family primary, $800k purchase, LTV 80%. Standard.","ltv":0.80}',
        '{"summary":"Specialists aligned. No conflicting signals.","concerns":[]}',
        '{"decision":"APPROVED","risk_score":23,"memo":"Strong applicant. All four pillars green."}',
    ]


@pytest.fixture
def fake_llm(fake_llm_responses: list[str]) -> FakeListChatModel:
    return FakeListChatModel(responses=fake_llm_responses)
