import pytest
from langchain_community.chat_models.fake import FakeListChatModel

from underwriter.agents.critic import critic_node
from underwriter.state import init_state
from underwriter.tools import sanitize_pii


def _state_with_analyses(applicant: dict) -> dict:
    s = init_state(applicant_data=applicant, case_id="T")
    s["sanitized_data"] = sanitize_pii(applicant)
    s["credit_analysis"] = '{"summary":"FICO 760, low risk","risk_level":"low"}'
    s["income_analysis"] = '{"summary":"Stable","dti":0.304,"qualifies":true}'
    s["asset_analysis"] = '{"summary":"Strong reserves","sufficient":true}'
    s["collateral_analysis"] = '{"summary":"LTV 80%","acceptable":true}'
    return s


@pytest.mark.asyncio
async def test_critic_node_returns_critic_review(strong_applicant_raw):
    llm = FakeListChatModel(
        responses=['{"summary":"All four pillars aligned","concerns":[],"recommendation":"approve"}']
    )
    delta = await critic_node(_state_with_analyses(strong_applicant_raw), llm=llm)
    assert "critic_review" in delta
    assert any("critic" in s.lower() for s in delta["reasoning_chain"])
    assert "usage" in delta
    assert "critic" in delta["usage"]
