"""Returns the bundled example applicants. Frontend uses these for the mock-data button."""

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter()

_CASES_PATH = Path(__file__).resolve().parents[2] / "data" / "test_cases.json"

_PTYPE_MAP = {
    "Single Family Home": "single_family",
    "Single Family": "single_family",
    "Condo": "condo",
    "Townhouse": "townhouse",
    "Multi-family": "multi_family",
    "Multi Family": "multi_family",
}
_OCC_MAP = {"Primary": "primary", "Secondary": "secondary", "Investment": "investment"}


def _normalize(raw: dict[str, Any]) -> dict[str, Any]:
    """Adapt legacy test_cases.json shape to ApplicantIn schema."""
    applicant = dict(raw)
    if "property" in applicant and "property_info" not in applicant:
        prop = dict(applicant.pop("property"))
        if "type" in prop and "property_type" not in prop:
            prop["property_type"] = _PTYPE_MAP.get(prop.pop("type"), "single_family")
        if "occupancy" in prop:
            prop["occupancy"] = _OCC_MAP.get(prop["occupancy"], str(prop["occupancy"]).lower())
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
    return applicant


@router.get("/cases")
async def list_cases() -> dict:
    if not _CASES_PATH.exists():
        raise HTTPException(status_code=500, detail="test_cases.json not found in data/")
    payload = json.loads(_CASES_PATH.read_text(encoding="utf-8"))
    cases = payload.get("test_cases", [])
    return {
        "cases": [
            {
                "case_id": c.get("case_id"),
                "name": c.get("name", "Unknown"),
                "applicant": _normalize(c),
            }
            for c in cases
        ]
    }
