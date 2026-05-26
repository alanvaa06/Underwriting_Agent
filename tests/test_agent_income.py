from langchain_community.chat_models.fake import FakeListChatModel

from underwriter.agents.income import income_analyst_node
from underwriter.state import init_state
from underwriter.tools import sanitize_pii


def _state(applicant: dict) -> dict:
    s = init_state(applicant_data=applicant, case_id="T")
    s["sanitized_data"] = sanitize_pii(applicant)
    return s


def test_income_node_returns_income_analysis_with_dti(strong_applicant_raw):
    llm = FakeListChatModel(
        responses=['{"summary":"Stable W2 income, $12500/mo","dti":0.304,"qualifies":true}']
    )
    delta = income_analyst_node(_state(strong_applicant_raw), llm=llm, retriever=None)
    assert "income_analysis" in delta
    assert delta["reasoning_chain"]
    assert any("income" in s.lower() for s in delta["reasoning_chain"])


def test_income_node_handles_missing_employment_gracefully(strong_applicant_raw):
    raw = dict(strong_applicant_raw)
    raw.pop("employment", None)
    llm = FakeListChatModel(responses=['{"summary":"No employment data","dti":0.0,"qualifies":false}'])
    delta = income_analyst_node(_state(raw), llm=llm, retriever=None)
    assert "income_analysis" in delta
