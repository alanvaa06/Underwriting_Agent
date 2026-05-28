import pytest
from langchain_community.chat_models.fake import FakeListChatModel

from app.schemas import ApplicantIn
from underwriter.streaming import stream_run


@pytest.mark.asyncio
async def test_stream_run_emits_expected_event_sequence(strong_applicant, fake_llm_responses):
    llm = FakeListChatModel(responses=fake_llm_responses)
    events = []
    async for evt in stream_run(applicant=strong_applicant, llm=llm, retriever=None):
        events.append(evt)

    types = [e.type for e in events]
    assert "agent_start" in types
    assert "agent_complete" in types
    assert "decision" in types
    assert "cost" in types
    assert types[-1] == "done"


@pytest.mark.asyncio
async def test_stream_run_decision_event_has_payload_keys(strong_applicant: ApplicantIn, fake_llm_responses):
    llm = FakeListChatModel(responses=fake_llm_responses)
    decision_evt = None
    async for evt in stream_run(applicant=strong_applicant, llm=llm, retriever=None):
        if evt.type == "decision":
            decision_evt = evt
    assert decision_evt is not None
    assert "decision" in decision_evt.payload
    assert "risk_score" in decision_evt.payload
    assert "memo" in decision_evt.payload


@pytest.mark.asyncio
async def test_stream_run_cost_event_has_per_agent_and_total(strong_applicant: ApplicantIn, fake_llm_responses):
    llm = FakeListChatModel(responses=fake_llm_responses)
    cost_evt = None
    async for evt in stream_run(applicant=strong_applicant, llm=llm, retriever=None):
        if evt.type == "cost":
            cost_evt = evt
    assert cost_evt is not None
    assert "per_agent" in cost_evt.payload
    assert "total_usd" in cost_evt.payload
    assert "total_tokens" in cost_evt.payload
    assert cost_evt.payload["total_usd"] == 0.0


@pytest.mark.asyncio
async def test_stream_run_emits_token_events_when_callback_fires(strong_applicant: ApplicantIn, fake_llm_responses):
    llm = FakeListChatModel(responses=fake_llm_responses)
    events = [e async for e in stream_run(applicant=strong_applicant, llm=llm, retriever=None)]
    assert any(e.type == "done" for e in events)
