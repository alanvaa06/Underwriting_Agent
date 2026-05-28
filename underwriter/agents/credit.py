"""Credit Analyst agent — evaluates FICO, history, derogatory items."""

from __future__ import annotations

import json
from typing import Any, Protocol

from langchain_core.language_models import BaseChatModel

from underwriter.agents.base import invoke_agent
from underwriter.state import UnderwritingState


class _Retriever(Protocol):
    def invoke(self, query: str) -> list[Any]: ...


SYSTEM_PROMPT = """You are a Senior Mortgage Credit Analyst.
Evaluate the applicant's credit profile: FICO score, payment history, derogatory items, tradeline depth.
Return STRICT JSON with keys:
  - "summary": string, 1-2 sentences
  - "risk_level": one of "low", "medium", "high"
  - "key_factors": list of short strings (max 5)
Cite any retrieved policy snippets in your summary if relevant.
"""


async def credit_analyst_node(
    state: UnderwritingState,
    *,
    llm: BaseChatModel,
    retriever: _Retriever | None = None,
) -> dict:
    applicant = state["sanitized_data"]
    credit = applicant.get("credit_history", {})

    policy_context = ""
    if retriever is not None:
        try:
            docs = retriever.invoke(
                f"credit score {applicant.get('credit_score')} guidelines"
            )
            policy_context = "\n\nRelevant policy:\n" + "\n---\n".join(d.page_content for d in docs)
        except Exception:
            policy_context = ""

    notes = credit.get("notes", "").strip() or "(none)"

    user_prompt = (
        f"Applicant credit profile:\n"
        f"  FICO: {applicant.get('credit_score')}\n"
        f"  Bankruptcies: {credit.get('bankruptcies', 0)}\n"
        f"  Foreclosures: {credit.get('foreclosures', 0)}\n"
        f"  Late payments (12mo): {credit.get('late_payments_12mo', 0)}\n"
        f"  Late payments (24mo): {credit.get('late_payments_24mo', 0)}\n"
        f"  Oldest tradeline (years): {credit.get('oldest_tradeline_years', 0)}\n"
        f"  Recent inquiries (6mo): {credit.get('inquiries_6mo', 0)}\n"
        f"\nUnderwriter notes: {notes}\n"
        f"{policy_context}\n\nReturn the JSON object now."
    )

    parsed, usage = await invoke_agent(llm, system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)
    summary = parsed.get("summary", "")

    return {
        "credit_analysis": json.dumps(parsed),
        "reasoning_chain": [f"[credit] {summary}"],
        "usage": {"credit": usage},
    }
