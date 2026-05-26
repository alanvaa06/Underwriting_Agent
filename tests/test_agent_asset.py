from langchain_community.chat_models.fake import FakeListChatModel

from underwriter.agents.asset import asset_analyst_node
from underwriter.state import init_state
from underwriter.tools import sanitize_pii


def _state(applicant: dict) -> dict:
    s = init_state(applicant_data=applicant, case_id="T")
    s["sanitized_data"] = sanitize_pii(applicant)
    return s


def test_asset_node_returns_asset_analysis(strong_applicant_raw):
    llm = FakeListChatModel(
        responses=['{"summary":"Strong liquid reserves","reserves_months":12,"sufficient":true}']
    )
    delta = asset_analyst_node(_state(strong_applicant_raw), llm=llm, retriever=None)
    assert "asset_analysis" in delta
    assert any("asset" in s.lower() for s in delta["reasoning_chain"])
