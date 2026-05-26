from app.schemas import AgentEvent
from app.sse import format_event


def test_format_event_emits_two_lines_followed_by_blank():
    evt = AgentEvent(type="agent_start", payload={"agent": "credit"}, ts=1700000000.0)
    out = format_event(evt)
    assert out.startswith("event: agent_start\n")
    assert "data: " in out
    assert out.endswith("\n\n")


def test_format_event_data_is_compact_json():
    evt = AgentEvent(type="decision", payload={"decision": "APPROVED", "risk_score": 23}, ts=1.0)
    out = format_event(evt)
    # one data line, no embedded newlines
    data_line = next(ln for ln in out.split("\n") if ln.startswith("data: "))
    assert "\n" not in data_line[len("data: "):]
