"""Bridge LangGraph graph.astream → typed AgentEvent async iterator. Supports per-agent
token streaming via LangChain AsyncCallbackHandler + asyncio.Queue."""

from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import AsyncIterator
from typing import Any, Protocol

from langchain_core.callbacks.base import AsyncCallbackHandler
from langchain_core.language_models import BaseChatModel

from app.schemas import AgentEvent, ApplicantIn
from underwriter.graph import build_workflow
from underwriter.pricing import compute_cost
from underwriter.state import init_state


class _Retriever(Protocol):
    def invoke(self, query: str) -> list[Any]: ...


_INTERNAL_NODES = frozenset({"initialize", "supervisor"})
_SENTINEL: Any = object()


def _make_token_callback(agent_name: str, queue: asyncio.Queue) -> AsyncCallbackHandler:
    class _Cb(AsyncCallbackHandler):
        async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:  # type: ignore[override]
            await queue.put(AgentEvent(
                type="token",
                payload={"agent": agent_name, "token": token},
                ts=time.time(),
            ))

    return _Cb()


def _cost_payload(usage_by_agent: dict[str, dict]) -> dict:
    per_agent: dict[str, dict] = {}
    total_usd = 0.0
    total_tokens = 0
    for name, u in usage_by_agent.items():
        usd = compute_cost(u)
        per_agent[name] = {
            "input_tokens": u.get("input_tokens", 0),
            "output_tokens": u.get("output_tokens", 0),
            "usd": round(usd, 6),
        }
        total_usd += usd
        total_tokens += u.get("input_tokens", 0) + u.get("output_tokens", 0)
    return {
        "per_agent": per_agent,
        "total_usd": round(total_usd, 6),
        "total_tokens": total_tokens,
    }


def _serializable(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _serializable(v) for k, v in obj.items()}
    if isinstance(obj, list | tuple):
        return [_serializable(v) for v in obj]
    if isinstance(obj, set | frozenset):
        return sorted(_serializable(v) for v in obj)
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    return obj


async def stream_run(
    *,
    applicant: ApplicantIn,
    llm: BaseChatModel,
    retriever: _Retriever | None,
    case_id: str | None = None,
) -> AsyncIterator[AgentEvent]:
    started = time.time()
    case = case_id or f"run-{uuid.uuid4().hex[:8]}"

    queue: asyncio.Queue = asyncio.Queue()
    final_state: dict[str, Any] = {}

    graph = build_workflow(
        llm=llm,
        retriever=retriever,
        callback_factory=lambda name: _make_token_callback(name, queue),
    )

    applicant_dict = applicant.model_dump()
    state = init_state(applicant_data=applicant_dict, case_id=case)
    config = {"configurable": {"thread_id": case}}

    async def run_graph() -> None:
        try:
            async for chunk in graph.astream(state, config=config, stream_mode="updates"):
                for node_name, delta in chunk.items():
                    if not isinstance(delta, dict):
                        continue
                    if node_name not in _INTERNAL_NODES:
                        await queue.put(AgentEvent(
                            type="agent_start",
                            payload={"agent": node_name},
                            ts=time.time(),
                        ))
                        await queue.put(AgentEvent(
                            type="agent_complete",
                            payload={"agent": node_name, "output": _serializable(delta)},
                            ts=time.time(),
                        ))
                    for k, v in delta.items():
                        if k == "usage" and isinstance(v, dict):
                            final_state.setdefault("usage", {}).update(v)
                        else:
                            final_state[k] = v
        finally:
            await queue.put(_SENTINEL)

    graph_task = asyncio.create_task(run_graph())

    while True:
        evt = await queue.get()
        if evt is _SENTINEL:
            break
        yield evt

    await graph_task  # surface any exceptions

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
        type="cost",
        payload=_cost_payload(final_state.get("usage", {})),
        ts=time.time(),
    )

    yield AgentEvent(
        type="done",
        payload={"total_duration_ms": int((time.time() - started) * 1000), "case_id": case},
        ts=time.time(),
    )
