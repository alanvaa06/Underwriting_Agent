"""SSE streaming endpoint. Runs the full underwriting workflow, yields AgentEvent stream."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.schemas import AgentEvent, RunRequest
from app.sse import format_event
from underwriter.agents.base import build_llm
from underwriter.errors import UnderwriterError
from underwriter.streaming import stream_run

logger = logging.getLogger(__name__)
router = APIRouter()

_PING_INTERVAL_S = 10.0


@router.post("/run")
async def run_underwriting(req: RunRequest, request: Request) -> StreamingResponse:
    async def event_gen():
        retriever = _retriever_from_state(request.app.state)

        try:
            llm = build_llm(api_key=req.api_key.get_secret_value(), model=req.model)
        except Exception as exc:
            yield format_event(_error_event("OPENAI_AUTH", f"Failed to build LLM client: {exc}", False))
            return

        last_ping = time.monotonic()
        try:
            async for evt in stream_run(applicant=req.applicant, llm=llm, retriever=retriever):
                if await request.is_disconnected():
                    logger.info("client disconnected mid-stream")
                    return
                # heartbeat
                if time.monotonic() - last_ping > _PING_INTERVAL_S:
                    yield format_event(AgentEvent(type="ping", payload={}, ts=time.time()))
                    last_ping = time.monotonic()
                yield format_event(evt)
        except UnderwriterError as exc:
            yield format_event(_error_event(exc.code, str(exc), exc.recoverable))
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.exception("internal error in run stream")
            yield format_event(_error_event("INTERNAL", "Unexpected error", False))
            _ = exc  # avoid linter complaint; details only go to stderr

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )


def _retriever_from_state(app_state: Any):
    store = getattr(app_state, "vector_store", None)
    if store is None:
        return None
    return store.as_retriever(search_kwargs={"k": 4})


def _error_event(code: str, message: str, recoverable: bool) -> AgentEvent:
    return AgentEvent(
        type="error",
        payload={"code": code, "message": message, "recoverable": recoverable},
        ts=time.time(),
    )
