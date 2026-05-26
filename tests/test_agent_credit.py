from langchain_community.chat_models.fake import FakeListChatModel

from underwriter.agents.credit import credit_analyst_node
from underwriter.state import init_state
from underwriter.tools import sanitize_pii


def _state_with_sanitized(applicant: dict) -> dict:
    s = init_state(applicant_data=applicant, case_id="T-1")
    s["sanitized_data"] = sanitize_pii(applicant)
    return s


def test_credit_node_returns_credit_analysis_and_chain(strong_applicant_raw):
    llm = FakeListChatModel(
        responses=['{"summary":"FICO 760, zero derogatory","risk_level":"low","key_factors":["high FICO","no late payments"]}']
    )
    state = _state_with_sanitized(strong_applicant_raw)
    delta = credit_analyst_node(state, llm=llm, retriever=None)
    assert "credit_analysis" in delta
    assert "FICO 760" in delta["credit_analysis"]
    assert delta["reasoning_chain"]
    assert any("credit" in step.lower() for step in delta["reasoning_chain"])


def test_credit_node_uses_retriever_when_provided(strong_applicant_raw):
    class FakeRetriever:
        def invoke(self, query: str):
            class Doc:
                page_content = "FICO above 700 qualifies for prime rates."
            return [Doc()]

    llm = FakeListChatModel(responses=['{"summary":"OK","risk_level":"low"}'])
    state = _state_with_sanitized(strong_applicant_raw)
    delta = credit_analyst_node(state, llm=llm, retriever=FakeRetriever())
    assert "credit_analysis" in delta
