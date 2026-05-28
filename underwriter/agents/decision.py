"""Decision agent — emits final APPROVED / CONDITIONAL_APPROVAL / DENIED + risk score + memo."""

from __future__ import annotations

from langchain_core.language_models import BaseChatModel

from underwriter.agents.base import invoke_agent
from underwriter.errors import AgentParseError
from underwriter.state import UnderwritingState

_VALID_DECISIONS = frozenset({"APPROVED", "CONDITIONAL_APPROVAL", "DENIED"})

SYSTEM_PROMPT = """You are the final Mortgage Decision Authority.
Based on the four specialist analyses and the critic's review, render a final decision.
Return STRICT JSON with EXACTLY these keys:
  - "decision": one of "APPROVED", "CONDITIONAL_APPROVAL", "DENIED" (uppercase, exact spelling)
  - "risk_score": int 0-100 (0 = lowest risk, 100 = highest)
  - "memo": string, 2-4 sentences explaining the rationale and any conditions
"""


async def decision_node(state: UnderwritingState, *, llm: BaseChatModel) -> dict:
    user_prompt = (
        f"All inputs:\n\n"
        f"CREDIT: {state.get('credit_analysis') or 'N/A'}\n\n"
        f"INCOME: {state.get('income_analysis') or 'N/A'}\n\n"
        f"ASSET: {state.get('asset_analysis') or 'N/A'}\n\n"
        f"COLLATERAL: {state.get('collateral_analysis') or 'N/A'}\n\n"
        f"CRITIC: {state.get('critic_review') or 'N/A'}\n\n"
        f"Return the JSON object now."
    )

    parsed, usage = await invoke_agent(llm, system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)

    decision = parsed.get("decision")
    if decision not in _VALID_DECISIONS:
        raise AgentParseError(
            f"Decision agent returned invalid 'decision' value: {decision!r}. "
            f"Must be one of {sorted(_VALID_DECISIONS)}."
        )

    risk_raw = parsed.get("risk_score", 50)
    try:
        risk_score = int(risk_raw)
    except (TypeError, ValueError):
        risk_score = 50
    risk_score = max(0, min(100, risk_score))

    memo = str(parsed.get("memo", ""))

    return {
        "final_decision": decision,
        "risk_score": risk_score,
        "decision_memo": memo,
        "analysis_complete": True,
        "reasoning_chain": [f"[decision] {decision} (risk={risk_score})"],
        "usage": {"decision": usage},
    }
