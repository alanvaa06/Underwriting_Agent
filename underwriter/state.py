"""LangGraph workflow state schema + initializer."""

import operator
from datetime import UTC, datetime
from typing import Annotated, Any, TypedDict


class UnderwritingState(TypedDict):
    case_id: str
    applicant_data: dict[str, Any]
    sanitized_data: dict[str, Any]

    credit_analysis: str | None
    income_analysis: str | None
    asset_analysis: str | None
    collateral_analysis: str | None

    critic_review: str | None
    decision_memo: str | None
    final_decision: str | None
    risk_score: int | None

    next_agent: str | None
    analysis_complete: bool
    human_review_required: bool
    human_review_completed: bool
    human_notes: str | None

    bias_flags: list[str]
    policy_violations: list[str]

    reasoning_chain: Annotated[list[str], operator.add]
    timestamp: str


def init_state(*, applicant_data: dict[str, Any], case_id: str) -> UnderwritingState:
    return UnderwritingState(
        case_id=case_id,
        applicant_data=applicant_data,
        sanitized_data={},
        credit_analysis=None,
        income_analysis=None,
        asset_analysis=None,
        collateral_analysis=None,
        critic_review=None,
        decision_memo=None,
        final_decision=None,
        risk_score=None,
        next_agent=None,
        analysis_complete=False,
        human_review_required=False,
        human_review_completed=False,
        human_notes=None,
        bias_flags=[],
        policy_violations=[],
        reasoning_chain=[],
        timestamp=datetime.now(UTC).isoformat(),
    )
