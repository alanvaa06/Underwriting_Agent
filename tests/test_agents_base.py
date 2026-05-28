import pytest
from langchain_community.chat_models.fake import FakeListChatModel

from underwriter.agents.base import build_llm, invoke_agent


def test_build_llm_returns_chat_model_with_key_and_model():
    llm = build_llm(api_key="sk-test", model="gpt-4o")
    assert llm.__class__.__name__ == "ChatOpenAI"


def test_build_llm_enables_streaming():
    llm = build_llm(api_key="sk-test", model="gpt-4o")
    assert getattr(llm, "streaming", False) is True


@pytest.mark.asyncio
async def test_invoke_agent_parses_json_and_returns_usage():
    llm = FakeListChatModel(responses=['{"summary":"ok","risk_level":"low"}'])
    parsed, usage = await invoke_agent(llm, system_prompt="X", user_prompt="Y")
    assert parsed == {"summary": "ok", "risk_level": "low"}
    assert "input_tokens" in usage and "output_tokens" in usage


@pytest.mark.asyncio
async def test_invoke_agent_strips_code_fences():
    llm = FakeListChatModel(responses=["```json\n{\"k\":1}\n```"])
    parsed, _usage = await invoke_agent(llm, system_prompt="X", user_prompt="Y")
    assert parsed == {"k": 1}


@pytest.mark.asyncio
async def test_invoke_agent_raises_agent_parse_error_on_bad_json():
    from underwriter.errors import AgentParseError

    llm = FakeListChatModel(responses=["not json"])
    with pytest.raises(AgentParseError):
        await invoke_agent(llm, system_prompt="X", user_prompt="Y")


@pytest.mark.asyncio
async def test_invoke_agent_usage_zero_when_metadata_missing():
    llm = FakeListChatModel(responses=['{"k":1}'])
    _, usage = await invoke_agent(llm, system_prompt="X", user_prompt="Y")
    assert usage == {"input_tokens": 0, "output_tokens": 0}
