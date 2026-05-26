"""Liveness probe. Returns 200 OK + JSON status."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}
