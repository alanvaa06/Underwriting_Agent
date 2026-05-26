"""Bridge LangGraph graph.astream → typed AgentEvent async iterator for the SSE endpoint."""

from __future__ import annotations

import time
import uuid
from collections.abc import AsyncIterator
from typing import Any, Protocol

from langchain_core.language_models import BaseChatModel

from app.schemas import AgentEvent, ApplicantIn
from underwriter.graph import build_workflow
from underwriter.state import init_state


class _Retriever(Protocol):
    def invoke(self, query: str) -> list[Any]: ...


_INTERNAL_NODES = frozenset({"initialize", "supervisor"})


async def stream_run(
    *,
    applicant: ApplicantIn,
    llm: BaseChatModel,
    retriever: _Retriever | None,
    case_id: str | None = None,
) -> AsyncIterator[AgentEvent]:
    started = time.time()
    case = case_id or f"run-{uuid.uuid4().hex[:8]}"
    graph = build_workflow(llm=llm, retriever=retriever)

    applicant_dict = applicant.model_dump()
    state = init_state(applicant_data=applicant_dict, case_id=case)

    config = {"configurable": {"thread_id": case}}
    final_state: dict[str, Any] = {}

    async for chunk in graph.astream(state, config=config, stream_mode="updates"):
        for node_name, delta in chunk.items():
            if not isinstance(delta, dict):
                continue
            if node_name not in _INTERNAL_NODES:
                yield AgentEvent(
                    type="agent_start",
                    payload={"agent": node_name},
                    ts=time.time(),
                )
                yield AgentEvent(
                    type="agent_complete",
                    payload={"agent": node_name, "output": _serializable(delta)},
                    ts=time.time(),
                )
            final_state.update(delta)

    yield AgentEvent(
        type="decision",
        payload={
            "decision": final_state.get("final_decision"),
            "risk_score": final_state.get("risk_score"),
            "memo": final_state.get("decision_memo"),
            "reasoning_chain": final_state.get("reasoning_chain", []),
        },
        ts=time.time(),
    )

    yield AgentEvent(
        type="done",
        payload={"total_duration_ms": int((time.time() - started) * 1000), "case_id": case},
        ts=time.time(),
    )


def _serializable(obj: Any) -> Any:
    """Coerce any non-JSON-serializable values (e.g., set, datetime) into JSON-safe forms."""
    if isinstance(obj, dict):
        return {k: _serializable(v) for k, v in obj.items()}
    if isinstance(obj, list | tuple):
        return [_serializable(v) for v in obj]
    if isinstance(obj, set | frozenset):
        return sorted(_serializable(v) for v in obj)
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    return obj
