"""LangGraph workflow: initialize → supervisor → 4 specialists → critic → decision → END."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol

from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from underwriter.agents.asset import asset_analyst_node
from underwriter.agents.collateral import collateral_analyst_node
from underwriter.agents.credit import credit_analyst_node
from underwriter.agents.critic import critic_node
from underwriter.agents.decision import decision_node
from underwriter.agents.income import income_analyst_node
from underwriter.state import UnderwritingState
from underwriter.tools import sanitize_pii


class _Retriever(Protocol):
    def invoke(self, query: str) -> list[Any]: ...


_SPECIALISTS = ("credit", "income", "asset", "collateral")
_ANALYSIS_KEYS = {
    "credit": "credit_analysis",
    "income": "income_analysis",
    "asset": "asset_analysis",
    "collateral": "collateral_analysis",
}


def _initialize_node(state: UnderwritingState) -> dict:
    return {
        "sanitized_data": sanitize_pii(state["applicant_data"]),
        "reasoning_chain": ["[init] applicant data sanitized"],
    }


def _supervisor_node(_state: UnderwritingState) -> dict:
    return {}


def _route_from_supervisor(state: UnderwritingState) -> str:
    for s in _SPECIALISTS:
        if state.get(_ANALYSIS_KEYS[s]) is None:
            return s
    return "critic"


def build_workflow(
    *,
    llm: BaseChatModel,
    retriever: _Retriever | None,
    callback_factory: Callable[[str], Any] | None = None,
) -> Any:
    """Compile the underwriting graph. Optional callback_factory(agent_name) → AsyncCallbackHandler
    is applied per-agent via llm.with_config(callbacks=[...]) for token streaming."""

    def with_cb(agent_name: str) -> Any:
        if callback_factory is None:
            return llm
        return llm.with_config(callbacks=[callback_factory(agent_name)])

    async def credit_node(s: UnderwritingState) -> dict:
        return await credit_analyst_node(s, llm=with_cb("credit"), retriever=retriever)

    async def income_node(s: UnderwritingState) -> dict:
        return await income_analyst_node(s, llm=with_cb("income"), retriever=retriever)

    async def asset_node(s: UnderwritingState) -> dict:
        return await asset_analyst_node(s, llm=with_cb("asset"), retriever=retriever)

    async def collateral_node(s: UnderwritingState) -> dict:
        return await collateral_analyst_node(s, llm=with_cb("collateral"), retriever=retriever)

    async def critic_wrap(s: UnderwritingState) -> dict:
        return await critic_node(s, llm=with_cb("critic"))

    async def decision_wrap(s: UnderwritingState) -> dict:
        return await decision_node(s, llm=with_cb("decision"))

    workflow = StateGraph(UnderwritingState)
    workflow.add_node("initialize", _initialize_node)
    workflow.add_node("supervisor", _supervisor_node)
    workflow.add_node("credit", credit_node)
    workflow.add_node("income", income_node)
    workflow.add_node("asset", asset_node)
    workflow.add_node("collateral", collateral_node)
    workflow.add_node("critic", critic_wrap)
    workflow.add_node("decision", decision_wrap)

    workflow.set_entry_point("initialize")
    workflow.add_edge("initialize", "supervisor")
    workflow.add_conditional_edges(
        "supervisor",
        _route_from_supervisor,
        {"credit": "credit", "income": "income", "asset": "asset",
         "collateral": "collateral", "critic": "critic"},
    )
    workflow.add_edge("credit", "supervisor")
    workflow.add_edge("income", "supervisor")
    workflow.add_edge("asset", "supervisor")
    workflow.add_edge("collateral", "supervisor")
    workflow.add_edge("critic", "decision")
    workflow.add_edge("decision", END)

    return workflow.compile(checkpointer=MemorySaver())
