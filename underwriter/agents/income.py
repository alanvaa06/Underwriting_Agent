"""Income Analyst agent — evaluates employment, income stability, DTI."""

from __future__ import annotations

import json
from typing import Any, Protocol

from langchain_core.language_models import BaseChatModel

from underwriter.agents.base import invoke_agent
from underwriter.state import UnderwritingState
from underwriter.tools import compute_dti


class _Retriever(Protocol):
    def invoke(self, query: str) -> list[Any]: ...


SYSTEM_PROMPT = """You are a Senior Mortgage Income Analyst.
Evaluate the applicant's income stability, employment tenure, and debt-to-income ratio.
Return STRICT JSON with keys:
  - "summary": string, 1-2 sentences
  - "dti": float (0.0 to 1.0)
  - "qualifies": boolean (based on standard QM rule: DTI <= 0.43)
Cite any retrieved policy snippets if relevant.
"""


def income_analyst_node(
    state: UnderwritingState,
    *,
    llm: BaseChatModel,
    retriever: _Retriever | None = None,
) -> dict:
    applicant = state["sanitized_data"]
    emp = applicant.get("employment", {})
    debts = applicant.get("debts", {})

    monthly_income = float(emp.get("monthly_income", 0) or 0)
    total_debt = float(
        debts.get("car_loan", 0) + debts.get("student_loan", 0)
        + debts.get("credit_cards", 0) + debts.get("other", 0)
    )

    computed_dti: float | None
    try:
        computed_dti = compute_dti(total_monthly_debt=total_debt, monthly_income=monthly_income)
    except ValueError:
        computed_dti = None

    policy_context = ""
    if retriever is not None:
        try:
            docs = retriever.invoke("debt-to-income ratio qualified mortgage guidelines")
            policy_context = "\n\nRelevant policy:\n" + "\n---\n".join(d.page_content for d in docs)
        except Exception:
            policy_context = ""

    user_prompt = (
        f"Applicant income profile:\n"
        f"  Employer: {emp.get('employer', 'N/A')}\n"
        f"  Position: {emp.get('position', 'N/A')}\n"
        f"  Tenure (years): {emp.get('years', 0)}\n"
        f"  Monthly income: ${monthly_income:,.0f}\n"
        f"  Type: {emp.get('type', 'N/A')}\n"
        f"  Total monthly debt: ${total_debt:,.0f}\n"
        f"  Computed DTI: {computed_dti if computed_dti is not None else 'N/A'}\n"
        f"{policy_context}\n\nReturn the JSON object now."
    )

    result = invoke_agent(llm, system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)
    summary = result.get("summary", "")

    return {
        "income_analysis": json.dumps(result),
        "reasoning_chain": [f"[income] {summary}"],
    }
