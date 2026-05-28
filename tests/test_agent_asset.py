import pytest
from langchain_community.chat_models.fake import FakeListChatModel

from underwriter.agents.asset import asset_analyst_node
from underwriter.state import init_state
from underwriter.tools import sanitize_pii


def _state(applicant: dict) -> dict:
    s = init_state(applicant_data=applicant, case_id="T")
    s["sanitized_data"] = sanitize_pii(applicant)
    return s


@pytest.mark.asyncio
async def test_asset_node_returns_asset_analysis(strong_applicant_raw):
    llm = FakeListChatModel(
        responses=['{"summary":"Strong liquid reserves","reserves_months":12,"sufficient":true}']
    )
    delta = await asset_analyst_node(_state(strong_applicant_raw), llm=llm, retriever=None)
    assert "asset_analysis" in delta
    assert any("asset" in s.lower() for s in delta["reasoning_chain"])
    assert "usage" in delta
    assert "asset" in delta["usage"]


class _RecordingLLM:
    def __init__(self, response: str):
        self.captured_prompts = []
        self.response = response

    async def ainvoke(self, messages, **kwargs):
        self.captured_prompts.append([m.content for m in messages])

        class _Msg:
            content = self.response
            usage_metadata = {"input_tokens": 0, "output_tokens": 0}

        return _Msg()


@pytest.mark.asyncio
async def test_asset_node_includes_notes_in_prompt(strong_applicant_raw):
    raw = dict(strong_applicant_raw)
    raw["assets"] = {**raw["assets"], "notes": "Retirement includes vested employer match."}
    state = init_state(applicant_data=raw, case_id="T")
    state["sanitized_data"] = sanitize_pii(raw)
    llm = _RecordingLLM('{"summary":"OK","reserves_months":12,"sufficient":true}')
    await asset_analyst_node(state, llm=llm, retriever=None)
    user_prompt = llm.captured_prompts[0][1]
    assert "vested employer match" in user_prompt
