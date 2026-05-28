"""Collateral Analyst agent — evaluates property type, occupancy, LTV."""

from __future__ import annotations

import json
from typing import Any, Protocol

from langchain_core.language_models import BaseChatModel

from underwriter.agents.base import invoke_agent
from underwriter.state import UnderwritingState
from underwriter.tools import compute_ltv


class _Retriever(Protocol):
    def invoke(self, query: str) -> list[Any]: ...


SYSTEM_PROMPT = """You are a Senior Mortgage Collateral Analyst.
Evaluate the property as collateral: type, occupancy, value, LTV ratio.
Return STRICT JSON with keys:
  - "summary": string, 1-2 sentences
  - "ltv": float (0.0 to 1.5)
  - "acceptable": boolean (true if property + LTV meet standard guidelines, LTV <= 0.97 owner-occupied)
"""


async def collateral_analyst_node(
    state: UnderwritingState,
    *,
    llm: BaseChatModel,
    retriever: _Retriever | None = None,
) -> dict:
    applicant = state["sanitized_data"]
    prop = applicant.get("property_info", applicant.get("property", {}))
    loan = applicant.get("loan", {})

    purchase_price = float(prop.get("purchase_price", 0) or 0)
    appraised = float(prop.get("appraised_value") or purchase_price)
    loan_amount = float(loan.get("loan_amount", 0) or 0)
    valuation = max(appraised, 1)

    computed_ltv: float | None
    try:
        computed_ltv = compute_ltv(loan_amount=loan_amount, property_value=valuation)
    except ValueError:
        computed_ltv = None

    policy_context = ""
    if retriever is not None:
        try:
            docs = retriever.invoke("loan to value LTV property type occupancy guidelines")
            policy_context = "\n\nRelevant policy:\n" + "\n---\n".join(d.page_content for d in docs)
        except Exception:
            policy_context = ""

    notes = prop.get("notes", "").strip() or "(none)"

    user_prompt = (
        f"Property collateral profile:\n"
        f"  Type: {prop.get('property_type', 'N/A')}\n"
        f"  Occupancy: {prop.get('occupancy', 'N/A')}\n"
        f"  Purchase price: ${purchase_price:,.0f}\n"
        f"  Appraised value: ${appraised:,.0f}\n"
        f"  Loan amount: ${loan_amount:,.0f}\n"
        f"  Computed LTV: {computed_ltv if computed_ltv is not None else 'N/A'}\n"
        f"\nUnderwriter notes: {notes}\n"
        f"{policy_context}\n\nReturn the JSON object now."
    )

    parsed, usage = await invoke_agent(llm, system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)
    summary = parsed.get("summary", "")

    return {
        "collateral_analysis": json.dumps(parsed),
        "reasoning_chain": [f"[collateral] {summary}"],
        "usage": {"collateral": usage},
    }
