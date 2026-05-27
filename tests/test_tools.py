import pytest

from underwriter.tools import compute_dti, compute_ltv, sanitize_pii


def test_compute_dti_simple():
    assert compute_dti(total_monthly_debt=3800, monthly_income=12500) == pytest.approx(0.304, abs=1e-3)


def test_compute_dti_zero_income_raises():
    with pytest.raises(ValueError, match="income must be positive"):
        compute_dti(total_monthly_debt=1000, monthly_income=0)


def test_compute_dti_negative_debt_raises():
    with pytest.raises(ValueError, match="debt cannot be negative"):
        compute_dti(total_monthly_debt=-100, monthly_income=5000)


def test_compute_ltv_simple():
    assert compute_ltv(loan_amount=400_000, property_value=500_000) == pytest.approx(0.80, abs=1e-3)


def test_compute_ltv_zero_property_raises():
    with pytest.raises(ValueError, match="property value must be positive"):
        compute_ltv(loan_amount=100_000, property_value=0)


def test_sanitize_pii_redacts_ssn_to_last_four():
    applicant = {"name": "Sarah Johnson", "ssn": "123-45-6789", "email": "x@y.com"}
    out = sanitize_pii(applicant)
    assert out["ssn"] == "XXX-XX-6789"


def test_sanitize_pii_keeps_first_name_only():
    out = sanitize_pii({"name": "Sarah Johnson"})
    assert out["name"] == "Sarah"


def test_sanitize_pii_drops_street_address_keeps_city_state():
    applicant = {"address": "1234 Oak Street, San Francisco, CA 94102"}
    out = sanitize_pii(applicant)
    assert out["address"] == "San Francisco, CA"


def test_sanitize_pii_strips_phone_and_email():
    applicant = {"phone": "555-234-5678", "email": "a@b.com"}
    out = sanitize_pii(applicant)
    assert "phone" not in out
    assert "email" not in out


def test_sanitize_pii_preserves_non_pii_keys():
    applicant = {"name": "Sarah Johnson", "credit_score": 760, "debts": {"car_loan": 1200}}
    out = sanitize_pii(applicant)
    assert out["credit_score"] == 760
    assert out["debts"] == {"car_loan": 1200}


def test_sanitize_pii_does_not_mutate_input():
    applicant = {"ssn": "123-45-6789", "name": "Sarah Johnson"}
    sanitize_pii(applicant)
    assert applicant["ssn"] == "123-45-6789"
    assert applicant["name"] == "Sarah Johnson"


def test_sanitize_pii_scrubs_ssn_in_nested_notes():
    out = sanitize_pii({"credit_history": {"notes": "SSN was 999-88-7777 reported wrong."}})
    assert out["credit_history"]["notes"] == "SSN was XXX-XX-7777 reported wrong."


def test_sanitize_pii_scrubs_email_in_nested_notes():
    out = sanitize_pii({"employment": {"notes": "HR contact: jane@example.com confirmed."}})
    assert out["employment"]["notes"] == "HR contact: [email] confirmed."


def test_sanitize_pii_passes_clean_notes_unchanged():
    msg = "Promotion to Senior Engineer effective Jan 2025."
    out = sanitize_pii({"employment": {"notes": msg}})
    assert out["employment"]["notes"] == msg
