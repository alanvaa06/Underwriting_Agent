"""Asset Analyst agent — verifies liquid reserves + down payment sourcing."""

from __future__ import annotations

import json
from typing import Any, Protocol

from langchain_core.language_models import BaseChatModel

from underwriter.agents.base import invoke_agent
from underwriter.state import UnderwritingState


class _Retriever(Protocol):
    def invoke(self, query: str) -> list[Any]: ...


SYSTEM_PROMPT = """You are a Senior Mortgage Asset Analyst.
Evaluate the applicant's liquid reserves, down payment capacity, and asset diversification.
Return STRICT JSON with keys:
  - "summary": string, 1-2 sentences
  - "reserves_months": int (months of PITI covered by liquid assets, your estimate)
  - "sufficient": boolean (true if reserves + down payment cover the requested loan terms)
"""


def asset_analyst_node(
    state: UnderwritingState,
    *,
    llm: BaseChatModel,
    retriever: _Retriever | None = None,
) -> dict:
    applicant = state["sanitized_data"]
    assets = applicant.get("assets", {})
    loan = applicant.get("loan", {})
    prop = applicant.get("property_info", applicant.get("property", {}))

    liquid = float(assets.get("checking", 0) + assets.get("savings", 0))
    total = liquid + float(assets.get("investments", 0) + assets.get("retirement", 0))

    policy_context = ""
    if retriever is not None:
        try:
            docs = retriever.invoke("reserve requirements down payment sourcing")
            policy_context = "\n\nRelevant policy:\n" + "\n---\n".join(d.page_content for d in docs)
        except Exception:
            policy_context = ""

    notes = assets.get("notes", "").strip() or "(none)"

    user_prompt = (
        f"Applicant asset profile:\n"
        f"  Checking: ${assets.get('checking', 0):,.0f}\n"
        f"  Savings: ${assets.get('savings', 0):,.0f}\n"
        f"  Investments: ${assets.get('investments', 0):,.0f}\n"
        f"  Retirement: ${assets.get('retirement', 0):,.0f}\n"
        f"  Liquid total: ${liquid:,.0f}\n"
        f"  Grand total: ${total:,.0f}\n"
        f"  Requested loan: ${loan.get('loan_amount', 0):,.0f}\n"
        f"  Down payment: ${loan.get('down_payment', 0):,.0f}\n"
        f"  Purchase price: ${prop.get('purchase_price', 0):,.0f}\n"
        f"\nUnderwriter notes: {notes}\n"
        f"{policy_context}\n\nReturn the JSON object now."
    )

    result = invoke_agent(llm, system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)
    summary = result.get("summary", "")

    return {
        "asset_analysis": json.dumps(result),
        "reasoning_chain": [f"[asset] {summary}"],
    }
