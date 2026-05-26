from underwriter.errors import (
    AgentParseError,
    AuthError,
    RAGError,
    RateLimitError,
    TimeoutError,
    UnderwriterError,
)


def test_base_has_code_and_recoverable_default():
    e = UnderwriterError("boom")
    assert e.code == "UNKNOWN"
    assert e.recoverable is False


def test_auth_error_code_and_recoverable_false():
    e = AuthError("bad key")
    assert isinstance(e, UnderwriterError)
    assert e.code == "OPENAI_AUTH"
    assert e.recoverable is False


def test_rate_limit_recoverable():
    e = RateLimitError("429")
    assert e.code == "OPENAI_RATE_LIMIT"
    assert e.recoverable is True


def test_timeout_recoverable():
    e = TimeoutError("slow")
    assert e.code == "OPENAI_TIMEOUT"
    assert e.recoverable is True


def test_rag_error_recoverable():
    e = RAGError("chroma down")
    assert e.code == "RAG_RETRIEVE"
    assert e.recoverable is True


def test_agent_parse_not_recoverable():
    e = AgentParseError("bad json")
    assert e.code == "AGENT_PARSE"
    assert e.recoverable is False


def test_all_errors_are_underwriter_error():
    for cls in [AuthError, RateLimitError, TimeoutError, RAGError, AgentParseError]:
        assert issubclass(cls, UnderwriterError)
