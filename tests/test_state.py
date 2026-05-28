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


def test_init_state_usage_defaults_to_empty_dict():
    state = init_state(applicant_data={"name": "X"}, case_id="T")
    assert state["usage"] == {}


def test_merge_usage_combines_two_dicts():
    from underwriter.state import _merge_usage
    left = {"credit": {"input_tokens": 100, "output_tokens": 50}}
    right = {"income": {"input_tokens": 200, "output_tokens": 80}}
    out = _merge_usage(left, right)
    assert out == {
        "credit": {"input_tokens": 100, "output_tokens": 50},
        "income": {"input_tokens": 200, "output_tokens": 80},
    }


def test_merge_usage_right_wins_on_key_collision():
    from underwriter.state import _merge_usage
    left = {"credit": {"input_tokens": 100, "output_tokens": 50}}
    right = {"credit": {"input_tokens": 999, "output_tokens": 999}}
    assert _merge_usage(left, right) == right
