import pytest
from pydantic import ValidationError

from app.schemas import (
    AgentEvent,
    ApplicantIn,
    Debts,
    RunRequest,
)


def _valid_applicant_dict() -> dict:
    return {
        "name": "Sarah Johnson",
        "credit_score": 760,
        "credit_history": {
            "bankruptcies": 0,
            "foreclosures": 0,
            "late_payments_12mo": 0,
            "late_payments_24mo": 0,
            "oldest_tradeline_years": 15,
        },
        "employment": {
            "employer": "Tech Solutions Inc",
            "position": "Senior Software Engineer",
            "years": 6.5,
            "monthly_income": 12500,
            "type": "W2",
        },
        "debts": {
            "car_loan": 1200,
            "student_loan": 800,
            "credit_cards": 1800,
        },
        "assets": {
            "checking": 85000,
            "savings": 100000,
            "investments": 0,
            "retirement": 0,
        },
        "property_info": {
            "purchase_price": 800000,
            "property_type": "single_family",
            "occupancy": "primary",
        },
        "loan": {
            "loan_amount": 640000,
            "down_payment": 160000,
            "term_years": 30,
        },
    }


def test_applicant_in_accepts_valid_payload():
    a = ApplicantIn.model_validate(_valid_applicant_dict())
    assert a.name == "Sarah Johnson"
    assert a.credit_score == 760
    assert a.employment.monthly_income == 12500


def test_applicant_in_rejects_fico_below_300():
    bad = _valid_applicant_dict()
    bad["credit_score"] = 250
    with pytest.raises(ValidationError):
        ApplicantIn.model_validate(bad)


def test_applicant_in_rejects_fico_above_850():
    bad = _valid_applicant_dict()
    bad["credit_score"] = 900
    with pytest.raises(ValidationError):
        ApplicantIn.model_validate(bad)


def test_applicant_in_rejects_missing_employment():
    bad = _valid_applicant_dict()
    del bad["employment"]
    with pytest.raises(ValidationError):
        ApplicantIn.model_validate(bad)


def test_debts_total_property():
    d = Debts(car_loan=1200, student_loan=800, credit_cards=1800)
    assert d.total_monthly == 3800


def test_run_request_api_key_is_secret():
    payload = {
        "applicant": _valid_applicant_dict(),
        "api_key": "sk-test-1234567890",
    }
    r = RunRequest.model_validate(payload)
    assert r.api_key.get_secret_value() == "sk-test-1234567890"
    assert "sk-test-1234567890" not in repr(r)


def test_run_request_default_model_is_gpt_4o():
    payload = {"applicant": _valid_applicant_dict(), "api_key": "sk-x"}
    r = RunRequest.model_validate(payload)
    assert r.model == "gpt-4o"


def test_run_request_rejects_other_models():
    payload = {"applicant": _valid_applicant_dict(), "api_key": "sk-x", "model": "gpt-3.5"}
    with pytest.raises(ValidationError):
        RunRequest.model_validate(payload)


def test_agent_event_serializes_to_dict():
    e = AgentEvent(type="agent_start", payload={"agent": "credit"}, ts=1700000000.0)
    d = e.model_dump()
    assert d["type"] == "agent_start"
    assert d["payload"] == {"agent": "credit"}
    assert d["ts"] == 1700000000.0


def test_agent_event_rejects_unknown_type():
    with pytest.raises(ValidationError):
        AgentEvent(type="not_a_type", payload={}, ts=0.0)


def test_credit_history_accepts_notes():
    from app.schemas import CreditHistory
    h = CreditHistory.model_validate({
        "bankruptcies": 0, "foreclosures": 0, "late_payments_12mo": 0,
        "late_payments_24mo": 0, "oldest_tradeline_years": 5,
        "notes": "Late payment was banking error.",
    })
    assert h.notes == "Late payment was banking error."


def test_notes_default_empty_string():
    from app.schemas import CreditHistory
    h = CreditHistory.model_validate({
        "bankruptcies": 0, "foreclosures": 0, "late_payments_12mo": 0,
        "late_payments_24mo": 0, "oldest_tradeline_years": 5,
    })
    assert h.notes == ""


def test_notes_rejects_over_2000_chars():
    from app.schemas import CreditHistory
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        CreditHistory.model_validate({
            "bankruptcies": 0, "foreclosures": 0, "late_payments_12mo": 0,
            "late_payments_24mo": 0, "oldest_tradeline_years": 5,
            "notes": "x" * 2001,
        })
