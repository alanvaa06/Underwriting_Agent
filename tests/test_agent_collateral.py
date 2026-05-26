from langchain_community.chat_models.fake import FakeListChatModel

from underwriter.agents.collateral import collateral_analyst_node
from underwriter.state import init_state
from underwriter.tools import sanitize_pii


def _state(applicant: dict) -> dict:
    s = init_state(applicant_data=applicant, case_id="T")
    s["sanitized_data"] = sanitize_pii(applicant)
    return s


def test_collateral_node_returns_collateral_analysis_with_ltv(strong_applicant_raw):
    llm = FakeListChatModel(
        responses=['{"summary":"Single-family primary, LTV 80%","ltv":0.80,"acceptable":true}']
    )
    delta = collateral_analyst_node(_state(strong_applicant_raw), llm=llm, retriever=None)
    assert "collateral_analysis" in delta
    assert any("collateral" in s.lower() for s in delta["reasoning_chain"])
