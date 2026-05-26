"""Typed exception hierarchy mapped to SSE error codes in app/routes/run.py."""


class UnderwriterError(Exception):
    code: str = "UNKNOWN"
    recoverable: bool = False


class AuthError(UnderwriterError):
    code = "OPENAI_AUTH"
    recoverable = False


class RateLimitError(UnderwriterError):
    code = "OPENAI_RATE_LIMIT"
    recoverable = True


class TimeoutError(UnderwriterError):  # noqa: A001 — intentional shadow, namespaced via import
    code = "OPENAI_TIMEOUT"
    recoverable = True


class RAGError(UnderwriterError):
    code = "RAG_RETRIEVE"
    recoverable = True


class AgentParseError(UnderwriterError):
    code = "AGENT_PARSE"
    recoverable = False
