"""Shared LLM factory + JSON-extraction wrapper used by every agent node."""

from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from underwriter.errors import AgentParseError

_FENCE_RE = re.compile(r"^```(?:json)?\s*(.+?)\s*```$", re.DOTALL)


def build_llm(*, api_key: str, model: str = "gpt-4o") -> BaseChatModel:
    """Construct a per-request streaming ChatOpenAI. Key never persisted past this call."""
    return ChatOpenAI(
        api_key=api_key,  # type: ignore[arg-type]
        model=model,
        temperature=0.1,
        timeout=60,
        streaming=True,
    )


async def invoke_agent(
    llm: BaseChatModel, *, system_prompt: str, user_prompt: str
) -> tuple[dict[str, Any], dict[str, int]]:
    """Invoke LLM async, return (parsed_json, usage). Raises AgentParseError on bad JSON."""
    msg = await llm.ainvoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
    raw = msg.content if isinstance(msg.content, str) else str(msg.content)
    raw = raw.strip()

    m = _FENCE_RE.match(raw)
    if m:
        raw = m.group(1).strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        raise AgentParseError(f"Failed to parse JSON from LLM: {e}. Raw: {raw[:200]}") from e

    raw_usage = getattr(msg, "usage_metadata", None) or {}
    usage = {
        "input_tokens": int(raw_usage.get("input_tokens", 0) or 0),
        "output_tokens": int(raw_usage.get("output_tokens", 0) or 0),
    }
    return parsed, usage
