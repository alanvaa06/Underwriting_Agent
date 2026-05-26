
from langchain_community.chat_models.fake import FakeListChatModel

from underwriter.agents.base import build_llm, invoke_agent


def test_build_llm_returns_chat_model_with_key_and_model():
    llm = build_llm(api_key="sk-test", model="gpt-4o")
    assert llm.__class__.__name__ == "ChatOpenAI"


def test_invoke_agent_parses_json_response():
    llm = FakeListChatModel(responses=['{"summary":"ok","risk_level":"low"}'])
    out = invoke_agent(llm, system_prompt="You are X.", user_prompt="Analyze Y.")
    assert out == {"summary": "ok", "risk_level": "low"}


def test_invoke_agent_strips_code_fences():
    llm = FakeListChatModel(responses=["```json\n{\"k\":1}\n```"])
    out = invoke_agent(llm, system_prompt="X", user_prompt="Y")
    assert out == {"k": 1}


def test_invoke_agent_raises_agent_parse_error_on_bad_json():
    from underwriter.errors import AgentParseError

    llm = FakeListChatModel(responses=["not json"])
    try:
        invoke_agent(llm, system_prompt="X", user_prompt="Y")
        raise AssertionError("expected AgentParseError")
    except AgentParseError as e:
        assert "JSON" in str(e) or "parse" in str(e).lower()
