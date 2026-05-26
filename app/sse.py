"""SSE wire-format helper. Each event = `event: <type>\ndata: <json>\n\n`."""

import json

from app.schemas import AgentEvent


def format_event(evt: AgentEvent) -> str:
    payload = evt.model_dump()
    data_json = json.dumps(payload, separators=(",", ":"), default=str)
    return f"event: {evt.type}\ndata: {data_json}\n\n"
