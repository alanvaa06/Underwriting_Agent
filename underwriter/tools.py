"""Pure computational + PII-scrubbing helpers shared across agents."""

import copy
import re
from typing import Any


def compute_dti(*, total_monthly_debt: float, monthly_income: float) -> float:
    if monthly_income <= 0:
        raise ValueError("monthly income must be positive")
    if total_monthly_debt < 0:
        raise ValueError("monthly debt cannot be negative")
    return total_monthly_debt / monthly_income


def compute_ltv(*, loan_amount: float, property_value: float) -> float:
    if property_value <= 0:
        raise ValueError("property value must be positive")
    if loan_amount < 0:
        raise ValueError("loan amount cannot be negative")
    return loan_amount / property_value


_SSN_RE = re.compile(r"^\d{3}-\d{2}-(\d{4})$")
_PII_DROP_KEYS = frozenset({"phone", "email"})

_SSN_NOTES_RE = re.compile(r"\b(\d{3})-(\d{2})-(\d{4})\b")
_EMAIL_NOTES_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")


def _scrub_string(s: str) -> str:
    s = _SSN_NOTES_RE.sub(lambda m: f"XXX-XX-{m.group(3)}", s)
    s = _EMAIL_NOTES_RE.sub("[email]", s)
    return s


def _scrub_deep(obj: Any) -> Any:
    if isinstance(obj, str):
        return _scrub_string(obj)
    if isinstance(obj, dict):
        return {k: _scrub_deep(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_scrub_deep(v) for v in obj]
    return obj


def sanitize_pii(applicant: dict[str, Any]) -> dict[str, Any]:
    """Return a deep copy with SSN/name/address scrubbed and phone/email removed."""
    out = copy.deepcopy(applicant)

    if "ssn" in out and isinstance(out["ssn"], str):
        m = _SSN_RE.match(out["ssn"])
        if m:
            out["ssn"] = f"XXX-XX-{m.group(1)}"

    if "name" in out and isinstance(out["name"], str):
        out["name"] = out["name"].split()[0]

    if "address" in out and isinstance(out["address"], str):
        # take last two comma-separated components, drop ZIP from state if present
        parts = [p.strip() for p in out["address"].split(",")]
        if len(parts) >= 3:
            city = parts[-2]
            state_zip = parts[-1].split()
            state = state_zip[0] if state_zip else parts[-1]
            out["address"] = f"{city}, {state}"

    for k in _PII_DROP_KEYS:
        out.pop(k, None)

    return _scrub_deep(out)
