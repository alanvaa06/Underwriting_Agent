from underwriter.state import init_state


def test_init_state_populates_applicant_and_defaults():
    raw = {"name": "Sarah Johnson", "credit_score": 760}
    state = init_state(applicant_data=raw, case_id="MTG-001")

    assert state["case_id"] == "MTG-001"
    assert state["applicant_data"] == raw
    assert state["sanitized_data"] == {}  # populated later by sanitize_pii
    assert state["credit_analysis"] is None
    assert state["income_analysis"] is None
    assert state["asset_analysis"] is None
    assert state["collateral_analysis"] is None
    assert state["critic_review"] is None
    assert state["decision_memo"] is None
    assert state["final_decision"] is None
    assert state["risk_score"] is None
    assert state["analysis_complete"] is False
    assert state["human_review_required"] is False
    assert state["human_review_completed"] is False
    assert state["bias_flags"] == []
    assert state["policy_violations"] == []
    assert state["reasoning_chain"] == []
    assert state["timestamp"]   # iso string
