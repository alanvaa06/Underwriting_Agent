# Section Notes — Free-Text Context per Form Section

**Date:** 2026-05-27
**Status:** Awaiting user review
**Scope:** v0.2.0. Backend schema + agent prompts + frontend form. PII sanitizer extended.

---

## 1. Goal

Let the user attach free-text explanatory context to each form section. Each specialist agent reads the notes for its section alongside structured fields, so things like "bonus is recurring per HR letter dated 2025-01-15" or "gap year was for caregiving" surface in the agent's reasoning instead of being lost.

5 inline textareas — one per existing collapsible form section. Notes flow through PII sanitization before reaching any LLM.

---

## 2. Decisions Made During Brainstorming

| Decision | Choice |
|---|---|
| Number of notes textareas | 5 (one per form section) |
| Placement | Inline inside each `<details>` collapsible section, below structured fields |
| Schema placement | Nested `notes: str` field on each Pydantic sub-model |
| Char limit | 2000 per field |
| Agent routing | Fixed by section → agent mapping (no user-controlled routing) |
| Sanitizer | Light regex pass over notes for SSN + email patterns (defense in depth) |

---

## 3. Section → Agent Mapping

| Form section | Pydantic sub-model | Notes field | Read by agent(s) |
|---|---|---|---|
| Borrower | `CreditHistory` | `credit_history.notes` | `credit` |
| Employment | `Employment` | `employment.notes` | `income` |
| Debts | `Debts` | `debts.notes` | `income` |
| Assets | `Assets` | `assets.notes` | `asset` |
| Property & Loan | `PropertyInfo` | `property_info.notes` | `collateral` |

`income` reads both `employment.notes` and `debts.notes` (it already consumes both sub-models for DTI).

Critic and Decision agents do not read notes directly — they see them transitively via specialist analyses (JSON-encoded in `state.<role>_analysis`).

---

## 4. Backend Changes

### 4.1 `app/schemas.py`

Add `notes: str = Field(default="", max_length=2000)` to:

```python
class CreditHistory(BaseModel):
    # ... existing fields ...
    notes: str = Field(default="", max_length=2000)


class Employment(BaseModel):
    # ... existing fields ...
    notes: str = Field(default="", max_length=2000)


class Debts(BaseModel):
    # ... existing fields ...
    notes: str = Field(default="", max_length=2000)


class Assets(BaseModel):
    # ... existing fields ...
    notes: str = Field(default="", max_length=2000)


class PropertyInfo(BaseModel):
    # ... existing fields ...
    notes: str = Field(default="", max_length=2000)
```

All optional (default empty string). Backward compatible — existing payloads without `notes` validate fine.

**Note on existing fields:** `CreditHistory.credit_notes` and `Employment.employment_gap` / `gap_explanation` already exist and are preserved unchanged. The new `notes` field is additive — both old and new fields can coexist in the same payload, and agents read both.

### 4.2 `underwriter/tools.py` — extend `sanitize_pii`

After existing SSN/name/address/phone/email scrubbing, add a recursive pass that walks all string values at any depth and applies:

```python
import re

_SSN_NOTES_RE = re.compile(r"\b(\d{3})-(\d{2})-(\d{4})\b")
_EMAIL_NOTES_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")


def _scrub_string(s: str) -> str:
    s = _SSN_NOTES_RE.sub(lambda m: f"XXX-XX-{m.group(3)}", s)
    s = _EMAIL_NOTES_RE.sub("[email]", s)
    return s


def _scrub_deep(obj):
    if isinstance(obj, str):
        return _scrub_string(obj)
    if isinstance(obj, dict):
        return {k: _scrub_deep(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_scrub_deep(v) for v in obj]
    return obj
```

Modify `sanitize_pii(applicant)`: after the existing top-level scrubbing, return `_scrub_deep(out)` instead of `out`. Catches PII embedded in `notes` fields anywhere in the structure.

Behavior preserved for current tests — strings without SSN/email patterns pass through unchanged.

### 4.3 Agent prompt updates

Each of the 4 specialist agents includes its `notes` field in the user prompt block, formatted as a separate line/section. Empty string → renders as "Notes: (none)".

**Pattern (credit agent example):**

In `underwriter/agents/credit.py`, the `user_prompt` string gets one new line appended:

```python
notes = credit.get("notes", "").strip() or "(none)"
# ... existing prompt construction ...
user_prompt = (
    f"Applicant credit profile:\n"
    f"  FICO: {applicant.get('credit_score')}\n"
    # ... existing lines ...
    f"  Recent inquiries (6mo): {credit.get('inquiries_6mo', 0)}\n"
    f"\nUnderwriter notes: {notes}\n"
    f"{policy_context}\n\nReturn the JSON object now."
)
```

Same pattern for `income` (reads BOTH `employment.notes` AND `debts.notes` — render as two separate blocks), `asset` (reads `assets.notes`), `collateral` (reads `property_info.notes`).

`critic` and `decision` agents unchanged. They see notes implicitly via the JSON-encoded analyses.

---

## 5. Frontend Changes

### 5.1 `frontend/index.html`

Inside each of the 5 `<details>` sections, after the structured-fields grid, add:

```html
<div class="mt-3">
  <label class="text-xs flex items-center justify-between">
    <span>Notes <span class="help" data-tip="Free-text context for this section. The agent reads it alongside structured fields.">?</span></span>
    <span class="text-slate-400 text-[10px]" data-counter="<section>_notes">0 / 2000</span>
  </label>
  <textarea name="<section>_notes" rows="3" maxlength="2000"
            placeholder="e.g., 'Bonus is recurring per HR letter dated 2025-01-15'"
            class="w-full mt-1 px-2 py-1 border rounded text-xs font-mono"></textarea>
</div>
```

`<section>` is one of: `credit`, `employment`, `debts`, `assets`, `property`.

Placeholder text per section (concrete example):
- credit: `"e.g., 'Late payment in March 2024 was due to a banking error, resolved.'"`
- employment: `"e.g., 'Promotion to Senior Engineer effective Jan 2025, salary increased 18%.'"`
- debts: `"e.g., 'Student loan in deferment until 2026; payment shown is post-deferment estimate.'"`
- assets: `"e.g., 'Retirement balance includes vested employer match; vested as of 2024-12-31.'"`
- property: `"e.g., 'Appraisal pending; purchase price reflects accepted offer 2025-02-10.'"`

### 5.2 `frontend/app.js`

Two changes:

1. **`buildPayload()` extends each sub-object** with the notes value:

```javascript
applicant: {
  // ...
  credit_history: {
    // ... existing fields ...
    notes: $('credit_notes'),
  },
  employment: {
    // ... existing fields ...
    notes: $('employment_notes'),
  },
  debts: {
    // ... existing fields ...
    notes: $('debts_notes'),
  },
  assets: {
    // ... existing fields ...
    notes: $('assets_notes'),
  },
  property_info: {
    // ... existing fields ...
    notes: $('property_notes'),
  },
  // loan unchanged
}
```

2. **Live character counter** on each `<textarea data-counter>` — single delegated listener at form level:

```javascript
form.addEventListener('input', (e) => {
  if (e.target.tagName === 'TEXTAREA' && e.target.name.endsWith('_notes')) {
    const counter = form.querySelector(`[data-counter="${e.target.name}"]`);
    if (counter) counter.textContent = `${e.target.value.length} / 2000`;
  }
});
```

---

## 6. Testing

### 6.1 `tests/test_schemas.py`

Add three tests:

```python
def test_credit_history_accepts_notes():
    h = CreditHistory.model_validate({
        "bankruptcies": 0, "foreclosures": 0, "late_payments_12mo": 0,
        "late_payments_24mo": 0, "oldest_tradeline_years": 5,
        "notes": "Late payment was banking error.",
    })
    assert h.notes == "Late payment was banking error."


def test_notes_default_empty_string():
    h = CreditHistory.model_validate({
        "bankruptcies": 0, "foreclosures": 0, "late_payments_12mo": 0,
        "late_payments_24mo": 0, "oldest_tradeline_years": 5,
    })
    assert h.notes == ""


def test_notes_rejects_over_2000_chars():
    with pytest.raises(ValidationError):
        CreditHistory.model_validate({
            "bankruptcies": 0, "foreclosures": 0, "late_payments_12mo": 0,
            "late_payments_24mo": 0, "oldest_tradeline_years": 5,
            "notes": "x" * 2001,
        })
```

### 6.2 `tests/test_tools.py`

Add three tests for deep-scrub:

```python
def test_sanitize_pii_scrubs_ssn_in_nested_notes():
    out = sanitize_pii({"credit_history": {"notes": "SSN was 999-88-7777 reported wrong."}})
    assert out["credit_history"]["notes"] == "SSN was XXX-XX-7777 reported wrong."


def test_sanitize_pii_scrubs_email_in_nested_notes():
    out = sanitize_pii({"employment": {"notes": "HR contact: jane@example.com confirmed."}})
    assert out["employment"]["notes"] == "HR contact: [email] confirmed."


def test_sanitize_pii_passes_clean_notes_unchanged():
    msg = "Promotion to Senior Engineer effective Jan 2025."
    out = sanitize_pii({"employment": {"notes": msg}})
    assert out["employment"]["notes"] == msg
```

### 6.3 Per-agent tests

`tests/test_agent_credit.py`, `test_agent_income.py`, `test_agent_asset.py`, `test_agent_collateral.py` each gain one test verifying that when the relevant `notes` field is populated, the underlying prompt contains the note string. Use a custom fake LLM that records the prompts it received:

```python
class _RecordingLLM:
    def __init__(self, response):
        self.captured_prompts = []
        self.response = response

    def invoke(self, messages):
        self.captured_prompts.append([m.content for m in messages])
        class _Msg:
            content = self.response
        return _Msg()


def test_credit_node_includes_notes_in_prompt(strong_applicant_raw):
    raw = {**strong_applicant_raw}
    raw["credit_history"] = {**raw["credit_history"], "notes": "Late payment was banking error."}
    state = init_state(applicant_data=raw, case_id="T")
    state["sanitized_data"] = sanitize_pii(raw)
    llm = _RecordingLLM('{"summary":"OK","risk_level":"low"}')
    credit_analyst_node(state, llm=llm, retriever=None)
    user_prompt = llm.captured_prompts[0][1]  # [system, user]
    assert "banking error" in user_prompt
```

Pattern repeats per agent with appropriate notes field + section.

### 6.4 No frontend automated tests

Manual checks added to `docs/manual-test-plan.md`:

- "Type 1500-char string into Borrower notes. Counter shows `1500 / 2000` in real time."
- "Type 2001 chars — counter caps at 2000 (browser-enforced via `maxlength`). Submit succeeds with 2000."
- "Type `SSN 123-45-6789` into any notes box, submit, run with real key — confirm agent panels don't echo full SSN (last-4 only)."

---

## 7. Files Changed

| File | Change |
|---|---|
| `app/schemas.py` | 5 new `notes` fields (one per sub-model) |
| `underwriter/tools.py` | `sanitize_pii` extends with `_scrub_deep` recursive SSN/email pass |
| `underwriter/agents/credit.py` | Prompt includes `credit_history.notes` |
| `underwriter/agents/income.py` | Prompt includes `employment.notes` + `debts.notes` |
| `underwriter/agents/asset.py` | Prompt includes `assets.notes` |
| `underwriter/agents/collateral.py` | Prompt includes `property_info.notes` |
| `frontend/index.html` | 5 `<textarea>` blocks added (one per `<details>` section) |
| `frontend/app.js` | `buildPayload()` adds notes to each sub-object; live counter listener |
| `tests/test_schemas.py` | 3 new tests (notes accept/default/limit) |
| `tests/test_tools.py` | 3 new tests (deep scrub SSN/email/clean) |
| `tests/test_agent_credit.py` | 1 new test (notes in prompt) |
| `tests/test_agent_income.py` | 1 new test (notes in prompt) |
| `tests/test_agent_asset.py` | 1 new test (notes in prompt) |
| `tests/test_agent_collateral.py` | 1 new test (notes in prompt) |
| `docs/manual-test-plan.md` | 3 new manual checks |

---

## 8. Out of Scope

- Per-agent routing checkboxes (user-controlled which agent sees which note). Section→agent mapping fixed.
- Dedicated critic-override notes textarea.
- Notes for the Decision agent specifically.
- Markdown rendering inside textareas.
- File upload (PDF, JSON, applicant docs) — separate spec.
- Notes persistence across runs / session storage.
- Auto-suggest notes based on field values.
- Translation / localization of placeholder text.

---

## 9. Acceptance Criteria

- [ ] All 5 sub-models accept optional `notes` (default `""`, max 2000 chars)
- [ ] `sanitize_pii` redacts SSN + email patterns in any nested string at any depth
- [ ] Each of 4 specialist prompts includes its section's notes when present
- [ ] Frontend has 5 inline textareas with `?` tooltip + live char counter
- [ ] Form submits successfully with notes — backend receives them in correct sub-objects
- [ ] Existing 59 tests still pass
- [ ] 10 new automated tests pass (3 schema + 3 sanitizer + 4 agent-prompt)
- [ ] 3 new manual checks documented
