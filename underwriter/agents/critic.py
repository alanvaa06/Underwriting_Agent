"""Critic agent — cross-checks the four specialist analyses for consistency."""

from __future__ import annotations

import json

from langchain_core.language_models import BaseChatModel

from underwriter.agents.base import invoke_agent
from underwriter.state import UnderwritingState


SYSTEM_PROMPT = """You are a Senior Mortgage Underwriting Critic.
You receive analyses from four specialist agents (credit, income, asset, collateral).
Identify conflicts, gaps, weak reasoning, or bias.
Return STRICT JSON with keys:
  - "summary": string, 1-2 sentences
  - "concerns": list of short strings (max 5)
  - "recommendation": one of "approve", "conditional", "deny"
"""


def critic_node(state: UnderwritingState, *, llm: BaseChatModel) -> dict:
    user_prompt = (
        f"Specialist analyses:\n\n"
        f"CREDIT: {state.get('credit_analysis') or 'N/A'}\n\n"
        f"INCOME: {state.get('income_analysis') or 'N/A'}\n\n"
        f"ASSET: {state.get('asset_analysis') or 'N/A'}\n\n"
        f"COLLATERAL: {state.get('collateral_analysis') or 'N/A'}\n\n"
        f"Return the JSON object now."
    )

    result = invoke_agent(llm, system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)
    summary = result.get("summary", "")

    return {
        "critic_review": json.dumps(result),
        "reasoning_chain": [f"[critic] {summary}"],
    }
