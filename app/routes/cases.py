"""Returns the bundled example applicants. Frontend uses these as "load template" presets."""

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter()

_CASES_PATH = Path(__file__).resolve().parents[2] / "data" / "test_cases.json"


@router.get("/cases")
async def list_cases() -> dict:
    if not _CASES_PATH.exists():
        raise HTTPException(status_code=500, detail="test_cases.json not found in data/")
    payload = json.loads(_CASES_PATH.read_text(encoding="utf-8"))
    cases = payload.get("test_cases", [])
    return {
        "cases": [
            {"case_id": c.get("case_id"), "name": c.get("name", "Unknown")}
            for c in cases
        ]
    }
