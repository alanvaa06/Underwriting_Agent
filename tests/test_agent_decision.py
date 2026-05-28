import pytest
from langchain_community.chat_models.fake import FakeListChatModel

from underwriter.agents.decision import decision_node
from underwriter.state import init_state
from underwriter.tools import sanitize_pii


def _state_with_all(applicant: dict) -> dict:
    s = init_state(applicant_data=applicant, case_id="T")
    s["sanitized_data"] = sanitize_pii(applicant)
    s["credit_analysis"] = '{"summary":"FICO 760","risk_level":"low"}'
    s["income_analysis"] = '{"summary":"Stable","dti":0.304,"qualifies":true}'
    s["asset_analysis"] = '{"summary":"Strong","sufficient":true}'
    s["collateral_analysis"] = '{"summary":"LTV 80%","acceptable":true}'
    s["critic_review"] = '{"summary":"OK","recommendation":"approve"}'
    return s


@pytest.mark.asyncio
async def test_decision_node_returns_final_decision_memo_and_risk_score(strong_applicant_raw):
    llm = FakeListChatModel(
        responses=['{"decision":"APPROVED","risk_score":23,"memo":"Strong applicant across all pillars."}']
    )
    delta = await decision_node(_state_with_all(strong_applicant_raw), llm=llm)
    assert delta["final_decision"] == "APPROVED"
    assert delta["risk_score"] == 23
    assert "memo" in delta["decision_memo"].lower() or "applicant" in delta["decision_memo"].lower()
    assert delta["analysis_complete"] is True
    assert "usage" in delta
    assert "decision" in delta["usage"]


@pytest.mark.asyncio
async def test_decision_node_rejects_invalid_decision_string(strong_applicant_raw):
    from underwriter.errors import AgentParseError

    llm = FakeListChatModel(
        responses=['{"decision":"MAYBE","risk_score":50,"memo":"unclear"}']
    )
    try:
        await decision_node(_state_with_all(strong_applicant_raw), llm=llm)
        raise AssertionError("expected AgentParseError")
    except AgentParseError as e:
        assert "decision" in str(e).lower()


@pytest.mark.asyncio
async def test_decision_node_clamps_risk_score_to_0_100(strong_applicant_raw):
    llm = FakeListChatModel(
        responses=['{"decision":"DENIED","risk_score":150,"memo":"high risk"}']
    )
    delta = await decision_node(_state_with_all(strong_applicant_raw), llm=llm)
    assert 0 <= delta["risk_score"] <= 100
