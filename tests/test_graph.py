from langchain_community.chat_models.fake import FakeListChatModel

from underwriter.graph import build_workflow
from underwriter.state import init_state
from underwriter.tools import sanitize_pii


def test_workflow_runs_end_to_end_with_fake_llm(strong_applicant_raw, fake_llm_responses):
    llm = FakeListChatModel(responses=fake_llm_responses)
    graph = build_workflow(llm=llm, retriever=None)

    state = init_state(applicant_data=strong_applicant_raw, case_id="GRAPH-TEST-1")
    state["sanitized_data"] = sanitize_pii(strong_applicant_raw)

    final = graph.invoke(state, config={"configurable": {"thread_id": "test-graph-1"}})

    assert final["final_decision"] in {"APPROVED", "CONDITIONAL_APPROVAL", "DENIED"}
    assert final["risk_score"] is not None
    assert final["decision_memo"]
    assert final["analysis_complete"] is True
    # All four specialists ran
    assert final["credit_analysis"]
    assert final["income_analysis"]
    assert final["asset_analysis"]
    assert final["collateral_analysis"]
    assert final["critic_review"]


def test_workflow_compiles_without_error():
    llm = FakeListChatModel(responses=[])
    graph = build_workflow(llm=llm, retriever=None)
    assert graph is not None
