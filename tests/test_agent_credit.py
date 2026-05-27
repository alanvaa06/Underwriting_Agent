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


class _RecordingLLM:
    def __init__(self, response: str):
        self.captured_prompts = []
        self.response = response

    def invoke(self, messages):
        self.captured_prompts.append([m.content for m in messages])

        class _Msg:
            content = self.response

        return _Msg()


def test_credit_node_includes_notes_in_prompt(strong_applicant_raw):
    raw = dict(strong_applicant_raw)
    raw["credit_history"] = {**raw["credit_history"], "notes": "Late payment was banking error."}
    state = init_state(applicant_data=raw, case_id="T")
    state["sanitized_data"] = sanitize_pii(raw)
    llm = _RecordingLLM('{"summary":"OK","risk_level":"low"}')
    credit_analyst_node(state, llm=llm, retriever=None)
    user_prompt = llm.captured_prompts[0][1]
    assert "banking error" in user_prompt
