# Section Notes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let users attach free-text context to each of the 5 form sections; each specialist agent reads its section's notes alongside structured data. PII sanitizer extended to scrub SSN/email patterns at any depth. Per spec `docs/superpowers/specs/2026-05-27-section-notes-design.md`.

**Architecture:** Backend adds `notes: str` (max 2000 chars) to 5 Pydantic sub-models. `sanitize_pii` extends with recursive deep-scrub for SSN + email regex. 4 specialist agent prompts include their notes field. Frontend adds 5 inline `<textarea>` blocks with live char counter. No new deps, no schema migration (additive, backward compatible).

**Tech Stack:** Pydantic v2, Python regex, vanilla JS, existing FakeListChatModel for agent tests, new tiny `_RecordingLLM` helper for prompt-capture tests.

---

## File Map

| File | Change |
|---|---|
| `app/schemas.py` | 5 new `notes: str = Field(default="", max_length=2000)` fields |
| `underwriter/tools.py` | `sanitize_pii` extends with `_scrub_deep` (recursive SSN + email regex) |
| `underwriter/agents/credit.py` | Prompt includes `credit_history.notes` |
| `underwriter/agents/income.py` | Prompt includes `employment.notes` + `debts.notes` |
| `underwriter/agents/asset.py` | Prompt includes `assets.notes` |
| `underwriter/agents/collateral.py` | Prompt includes `property_info.notes` |
| `frontend/index.html` | 5 `<textarea>` blocks (one per `<details>` section) |
| `frontend/app.js` | `buildPayload()` extends 5 sub-objects with notes; live counter listener |
| `tests/test_schemas.py` | 3 new tests |
| `tests/test_tools.py` | 3 new tests |
| `tests/test_agent_credit.py` | 1 new test + new `_RecordingLLM` helper |
| `tests/test_agent_income.py` | 1 new test |
| `tests/test_agent_asset.py` | 1 new test |
| `tests/test_agent_collateral.py` | 1 new test |
| `docs/manual-test-plan.md` | 3 new manual checks |

---

## Task Order

1. **Task 1** — Schema additions (5 notes fields) + 3 schema tests. Foundation.
2. **Task 2** — Sanitizer deep-scrub + 3 sanitizer tests.
3. **Task 3** — Agent prompt updates (4 agents) + 4 prompt-capture tests. Uses `_RecordingLLM` helper.
4. **Task 4** — Frontend: 5 textareas + buildPayload extension + char counter.
5. **Task 5** — Manual test plan doc append.
6. **Task 6** — Smoke + push GitHub + push HF Space + tag v0.2.0.

Each task ends with one commit. Push deferred to Task 6.

---

## Task 1: Schemas — add notes field to 5 sub-models

**Files:**
- Modify: `app/schemas.py`
- Modify: `tests/test_schemas.py`

- [x] **Step 1: Write the 3 failing tests**

Open `C:\Proyectos\Underwriter_Agent\tests\test_schemas.py`. Append these tests at the end:

```python
def test_credit_history_accepts_notes():
    from app.schemas import CreditHistory
    h = CreditHistory.model_validate({
        "bankruptcies": 0, "foreclosures": 0, "late_payments_12mo": 0,
        "late_payments_24mo": 0, "oldest_tradeline_years": 5,
        "notes": "Late payment was banking error.",
    })
    assert h.notes == "Late payment was banking error."


def test_notes_default_empty_string():
    from app.schemas import CreditHistory
    h = CreditHistory.model_validate({
        "bankruptcies": 0, "foreclosures": 0, "late_payments_12mo": 0,
        "late_payments_24mo": 0, "oldest_tradeline_years": 5,
    })
    assert h.notes == ""


def test_notes_rejects_over_2000_chars():
    from app.schemas import CreditHistory
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        CreditHistory.model_validate({
            "bankruptcies": 0, "foreclosures": 0, "late_payments_12mo": 0,
            "late_payments_24mo": 0, "oldest_tradeline_years": 5,
            "notes": "x" * 2001,
        })
```

- [x] **Step 2: Run tests — verify fail**

```bash
.venv\Scripts\python.exe -m pytest tests/test_schemas.py::test_credit_history_accepts_notes tests/test_schemas.py::test_notes_default_empty_string tests/test_schemas.py::test_notes_rejects_over_2000_chars -v
```

Expected: 3 FAIL with `AttributeError: 'CreditHistory' object has no attribute 'notes'` or similar (depending on which line fails first).

- [x] **Step 3: Add notes field to 5 sub-models**

Edit `C:\Proyectos\Underwriter_Agent\app\schemas.py`. For each of the 5 sub-model classes, append a new line at the END of the class body (after all existing fields, before any methods like `total_monthly`):

For `CreditHistory` — add at end:
```python
    notes: str = Field(default="", max_length=2000)
```

For `Employment` — add at end:
```python
    notes: str = Field(default="", max_length=2000)
```

For `Debts` — add BEFORE the `total_monthly` `@property`:
```python
    notes: str = Field(default="", max_length=2000)
```

For `Assets` — add at end:
```python
    notes: str = Field(default="", max_length=2000)
```

For `PropertyInfo` — add at end:
```python
    notes: str = Field(default="", max_length=2000)
```

- [x] **Step 4: Run tests — verify pass + full suite green**

```bash
.venv\Scripts\python.exe -m pytest tests/test_schemas.py -v
```

Expected: all schema tests pass (13 total — 10 existing + 3 new).

```bash
.venv\Scripts\python.exe -m pytest --ignore=tests/test_e2e.py -q
```

Expected: `62 passed` (59 prior + 3 new).

- [x] **Step 5: Commit**

```bash
git add app/schemas.py tests/test_schemas.py
git commit -m "feat(schemas): optional notes (max 2000) on 5 sub-models"
```

**DO NOT push.**

---

## Task 2: Sanitizer — recursive deep-scrub for SSN + email

**Files:**
- Modify: `underwriter/tools.py`
- Modify: `tests/test_tools.py`

- [x] **Step 1: Write the 3 failing tests**

Open `C:\Proyectos\Underwriter_Agent\tests\test_tools.py`. Append:

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

- [x] **Step 2: Run tests — verify fail**

```bash
.venv\Scripts\python.exe -m pytest tests/test_tools.py::test_sanitize_pii_scrubs_ssn_in_nested_notes tests/test_tools.py::test_sanitize_pii_scrubs_email_in_nested_notes tests/test_tools.py::test_sanitize_pii_passes_clean_notes_unchanged -v
```

Expected: 2 FAIL (SSN + email tests — current sanitizer doesn't recurse). Clean-passthrough test should PASS trivially since current sanitizer leaves nested dicts alone.

- [x] **Step 3: Extend sanitize_pii with deep scrub**

Open `C:\Proyectos\Underwriter_Agent\underwriter\tools.py`. Add these two compiled regexes and the helper at module level (after `_PII_DROP_KEYS`):

```python
_SSN_NOTES_RE = re.compile(r"\b(\d{3})-(\d{2})-(\d{4})\b")
_EMAIL_NOTES_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")


def _scrub_string(s: str) -> str:
    s = _SSN_NOTES_RE.sub(lambda m: f"XXX-XX-{m.group(3)}", s)
    s = _EMAIL_NOTES_RE.sub("[email]", s)
    return s


def _scrub_deep(obj: Any) -> Any:
    if isinstance(obj, str):
        return _scrub_string(obj)
    if isinstance(obj, dict):
        return {k: _scrub_deep(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_scrub_deep(v) for v in obj]
    return obj
```

Then modify the `sanitize_pii` function's last line from:

```python
    return out
```

to:

```python
    return _scrub_deep(out)
```

- [x] **Step 4: Run tests — verify pass + full suite green**

```bash
.venv\Scripts\python.exe -m pytest tests/test_tools.py -v
```

Expected: 14 PASS (11 existing + 3 new).

```bash
.venv\Scripts\python.exe -m pytest --ignore=tests/test_e2e.py -q
```

Expected: `65 passed`.

**Watch for regression:** the existing `test_sanitize_pii_redacts_ssn_to_last_four` test passes a top-level `ssn` key. With deep-scrub now running AFTER the top-level scrub, the top-level value (already `XXX-XX-6789`) will be re-processed but the regex pattern `\d{3}-\d{2}-\d{4}` doesn't match `XXX-XX-6789` so it passes through unchanged. Same for the address handling: top-level scrubbed `"San Francisco, CA"` doesn't match any regex. Good — no double-scrub bug.

- [x] **Step 5: Commit**

```bash
git add underwriter/tools.py tests/test_tools.py
git commit -m "feat(tools): sanitize_pii deep-scrub SSN + email in nested strings"
```

**DO NOT push.**

---

## Task 3: Agent prompts — include notes in 4 specialists

**Files:**
- Modify: `underwriter/agents/credit.py`
- Modify: `underwriter/agents/income.py`
- Modify: `underwriter/agents/asset.py`
- Modify: `underwriter/agents/collateral.py`
- Modify: `tests/test_agent_credit.py` (new helper + test)
- Modify: `tests/test_agent_income.py`
- Modify: `tests/test_agent_asset.py`
- Modify: `tests/test_agent_collateral.py`

- [x] **Step 1: Write all 4 failing tests**

Each test file gets a `_RecordingLLM` helper class + one new test. The helper captures the prompts the agent sent so we can assert the notes string appears in them.

For `tests/test_agent_credit.py`, append at the end:

```python
class _RecordingLLM:
    def __init__(self, response: str):
        self.captured_prompts = []
        self.response = response

    def invoke(self, messages):
        self.captured_prompts.append([m.content for m in messages])

        class _Msg:
            content = self.response

        return _Msg()


def test_credit_node_includes_notes_in_prompt(strong_applicant_raw):
    raw = dict(strong_applicant_raw)
    raw["credit_history"] = {**raw["credit_history"], "notes": "Late payment was banking error."}
    state = init_state(applicant_data=raw, case_id="T")
    state["sanitized_data"] = sanitize_pii(raw)
    llm = _RecordingLLM('{"summary":"OK","risk_level":"low"}')
    credit_analyst_node(state, llm=llm, retriever=None)
    user_prompt = llm.captured_prompts[0][1]
    assert "banking error" in user_prompt
```

For `tests/test_agent_income.py`, append at the end:

```python
class _RecordingLLM:
    def __init__(self, response: str):
        self.captured_prompts = []
        self.response = response

    def invoke(self, messages):
        self.captured_prompts.append([m.content for m in messages])

        class _Msg:
            content = self.response

        return _Msg()


def test_income_node_includes_employment_and_debts_notes_in_prompt(strong_applicant_raw):
    raw = dict(strong_applicant_raw)
    raw["employment"] = {**raw["employment"], "notes": "Promotion effective Jan 2025."}
    raw["debts"] = {**raw["debts"], "notes": "Student loan in deferment."}
    state = init_state(applicant_data=raw, case_id="T")
    state["sanitized_data"] = sanitize_pii(raw)
    llm = _RecordingLLM('{"summary":"OK","dti":0.3,"qualifies":true}')
    income_analyst_node(state, llm=llm, retriever=None)
    user_prompt = llm.captured_prompts[0][1]
    assert "Promotion effective Jan 2025" in user_prompt
    assert "Student loan in deferment" in user_prompt
```

For `tests/test_agent_asset.py`, append at the end:

```python
class _RecordingLLM:
    def __init__(self, response: str):
        self.captured_prompts = []
        self.response = response

    def invoke(self, messages):
        self.captured_prompts.append([m.content for m in messages])

        class _Msg:
            content = self.response

        return _Msg()


def test_asset_node_includes_notes_in_prompt(strong_applicant_raw):
    raw = dict(strong_applicant_raw)
    raw["assets"] = {**raw["assets"], "notes": "Retirement includes vested employer match."}
    state = init_state(applicant_data=raw, case_id="T")
    state["sanitized_data"] = sanitize_pii(raw)
    llm = _RecordingLLM('{"summary":"OK","reserves_months":12,"sufficient":true}')
    asset_analyst_node(state, llm=llm, retriever=None)
    user_prompt = llm.captured_prompts[0][1]
    assert "vested employer match" in user_prompt
```

For `tests/test_agent_collateral.py`, append at the end:

```python
class _RecordingLLM:
    def __init__(self, response: str):
        self.captured_prompts = []
        self.response = response

    def invoke(self, messages):
        self.captured_prompts.append([m.content for m in messages])

        class _Msg:
            content = self.response

        return _Msg()


def test_collateral_node_includes_notes_in_prompt(strong_applicant_raw):
    raw = dict(strong_applicant_raw)
    # Handle legacy 'property' key OR 'property_info' key — the conftest adapter normalizes for ApplicantIn, but the raw dict here goes through sanitize_pii directly so we use whichever key exists in the test fixture
    section_key = "property_info" if "property_info" in raw else "property"
    raw[section_key] = {**raw[section_key], "notes": "Appraisal pending, offer 2025-02-10."}
    state = init_state(applicant_data=raw, case_id="T")
    state["sanitized_data"] = sanitize_pii(raw)
    llm = _RecordingLLM('{"summary":"OK","ltv":0.80,"acceptable":true}')
    collateral_analyst_node(state, llm=llm, retriever=None)
    user_prompt = llm.captured_prompts[0][1]
    assert "Appraisal pending" in user_prompt
```

- [x] **Step 2: Run all 4 tests — verify fail**

```bash
.venv\Scripts\python.exe -m pytest tests/test_agent_credit.py::test_credit_node_includes_notes_in_prompt tests/test_agent_income.py::test_income_node_includes_employment_and_debts_notes_in_prompt tests/test_agent_asset.py::test_asset_node_includes_notes_in_prompt tests/test_agent_collateral.py::test_collateral_node_includes_notes_in_prompt -v
```

Expected: all 4 FAIL — assertion error (notes string not in prompt because agents don't include it yet).

- [x] **Step 3: Update credit.py — include notes**

Open `C:\Proyectos\Underwriter_Agent\underwriter\agents\credit.py`. Find the `user_prompt = (` block. Replace it entirely with:

```python
    notes = credit.get("notes", "").strip() or "(none)"

    user_prompt = (
        f"Applicant credit profile:\n"
        f"  FICO: {applicant.get('credit_score')}\n"
        f"  Bankruptcies: {credit.get('bankruptcies', 0)}\n"
        f"  Foreclosures: {credit.get('foreclosures', 0)}\n"
        f"  Late payments (12mo): {credit.get('late_payments_12mo', 0)}\n"
        f"  Late payments (24mo): {credit.get('late_payments_24mo', 0)}\n"
        f"  Oldest tradeline (years): {credit.get('oldest_tradeline_years', 0)}\n"
        f"  Recent inquiries (6mo): {credit.get('inquiries_6mo', 0)}\n"
        f"\nUnderwriter notes: {notes}\n"
        f"{policy_context}\n\nReturn the JSON object now."
    )
```

- [x] **Step 4: Update income.py — include notes from BOTH employment + debts**

Open `C:\Proyectos\Underwriter_Agent\underwriter\agents\income.py`. Find the `user_prompt = (` block. Replace it entirely with:

```python
    emp_notes = emp.get("notes", "").strip() or "(none)"
    debt_notes = debts.get("notes", "").strip() or "(none)"

    user_prompt = (
        f"Applicant income profile:\n"
        f"  Employer: {emp.get('employer', 'N/A')}\n"
        f"  Position: {emp.get('position', 'N/A')}\n"
        f"  Tenure (years): {emp.get('years', 0)}\n"
        f"  Monthly income: ${monthly_income:,.0f}\n"
        f"  Type: {emp.get('type', 'N/A')}\n"
        f"  Total monthly debt: ${total_debt:,.0f}\n"
        f"  Computed DTI: {computed_dti if computed_dti is not None else 'N/A'}\n"
        f"\nUnderwriter notes (employment): {emp_notes}\n"
        f"Underwriter notes (debts): {debt_notes}\n"
        f"{policy_context}\n\nReturn the JSON object now."
    )
```

- [x] **Step 5: Update asset.py — include notes**

Open `C:\Proyectos\Underwriter_Agent\underwriter\agents\asset.py`. Find the `user_prompt = (` block. Replace it entirely with:

```python
    notes = assets.get("notes", "").strip() or "(none)"

    user_prompt = (
        f"Applicant asset profile:\n"
        f"  Checking: ${assets.get('checking', 0):,.0f}\n"
        f"  Savings: ${assets.get('savings', 0):,.0f}\n"
        f"  Investments: ${assets.get('investments', 0):,.0f}\n"
        f"  Retirement: ${assets.get('retirement', 0):,.0f}\n"
        f"  Liquid total: ${liquid:,.0f}\n"
        f"  Grand total: ${total:,.0f}\n"
        f"  Requested loan: ${loan.get('loan_amount', 0):,.0f}\n"
        f"  Down payment: ${loan.get('down_payment', 0):,.0f}\n"
        f"  Purchase price: ${prop.get('purchase_price', 0):,.0f}\n"
        f"\nUnderwriter notes: {notes}\n"
        f"{policy_context}\n\nReturn the JSON object now."
    )
```

- [x] **Step 6: Update collateral.py — include notes**

Open `C:\Proyectos\Underwriter_Agent\underwriter\agents\collateral.py`. Find the `user_prompt = (` block. Replace it entirely with:

```python
    notes = prop.get("notes", "").strip() or "(none)"

    user_prompt = (
        f"Property collateral profile:\n"
        f"  Type: {prop.get('property_type', 'N/A')}\n"
        f"  Occupancy: {prop.get('occupancy', 'N/A')}\n"
        f"  Purchase price: ${purchase_price:,.0f}\n"
        f"  Appraised value: ${appraised:,.0f}\n"
        f"  Loan amount: ${loan_amount:,.0f}\n"
        f"  Computed LTV: {computed_ltv if computed_ltv is not None else 'N/A'}\n"
        f"\nUnderwriter notes: {notes}\n"
        f"{policy_context}\n\nReturn the JSON object now."
    )
```

- [x] **Step 7: Run all 4 new tests + full suite — verify pass**

```bash
.venv\Scripts\python.exe -m pytest tests/test_agent_credit.py tests/test_agent_income.py tests/test_agent_asset.py tests/test_agent_collateral.py -v
```

Expected: all green (existing + 4 new = previous count + 4).

```bash
.venv\Scripts\python.exe -m pytest --ignore=tests/test_e2e.py -q
```

Expected: `69 passed`.

- [x] **Step 8: Commit**

```bash
git add underwriter/agents/credit.py underwriter/agents/income.py underwriter/agents/asset.py underwriter/agents/collateral.py tests/test_agent_credit.py tests/test_agent_income.py tests/test_agent_asset.py tests/test_agent_collateral.py
git commit -m "feat(agents): credit/income/asset/collateral prompts include section notes"
```

**DO NOT push.**

---

## Task 4: Frontend — 5 textareas + buildPayload + counter

**Files:**
- Modify: `frontend/index.html`
- Modify: `frontend/app.js`

- [x] **Step 1: Add 5 textareas to frontend/index.html**

Open `C:\Proyectos\Underwriter_Agent\frontend\index.html`. Inside each of the 5 `<details>` sections, immediately AFTER the closing `</div>` of the structured-fields grid and BEFORE the closing `</details>` tag (or before the existing "Computed DTI/LTV" `<p>` if present), insert one block per section:

**Inside the Borrower section, after the grid div:**
```html
        <div class="mt-3">
          <label class="text-xs flex items-center justify-between">
            <span>Notes <span class="help" data-tip="Free-text context for this section. The agent reads it alongside structured fields.">?</span></span>
            <span class="text-slate-400 text-[10px]" data-counter="credit_notes">0 / 2000</span>
          </label>
          <textarea name="credit_notes" rows="3" maxlength="2000"
                    placeholder="e.g., 'Late payment in March 2024 was due to a banking error, resolved.'"
                    class="w-full mt-1 px-2 py-1 border rounded text-xs font-mono"></textarea>
        </div>
```

**Inside the Employment section:**
```html
        <div class="mt-3">
          <label class="text-xs flex items-center justify-between">
            <span>Notes <span class="help" data-tip="Free-text context for this section. The agent reads it alongside structured fields.">?</span></span>
            <span class="text-slate-400 text-[10px]" data-counter="employment_notes">0 / 2000</span>
          </label>
          <textarea name="employment_notes" rows="3" maxlength="2000"
                    placeholder="e.g., 'Promotion to Senior Engineer effective Jan 2025, salary increased 18%.'"
                    class="w-full mt-1 px-2 py-1 border rounded text-xs font-mono"></textarea>
        </div>
```

**Inside the Debts section, AFTER the existing "Computed DTI" `<p>` line:**
```html
        <div class="mt-3">
          <label class="text-xs flex items-center justify-between">
            <span>Notes <span class="help" data-tip="Free-text context for this section. The agent reads it alongside structured fields.">?</span></span>
            <span class="text-slate-400 text-[10px]" data-counter="debts_notes">0 / 2000</span>
          </label>
          <textarea name="debts_notes" rows="3" maxlength="2000"
                    placeholder="e.g., 'Student loan in deferment until 2026; payment shown is post-deferment estimate.'"
                    class="w-full mt-1 px-2 py-1 border rounded text-xs font-mono"></textarea>
        </div>
```

**Inside the Assets section:**
```html
        <div class="mt-3">
          <label class="text-xs flex items-center justify-between">
            <span>Notes <span class="help" data-tip="Free-text context for this section. The agent reads it alongside structured fields.">?</span></span>
            <span class="text-slate-400 text-[10px]" data-counter="assets_notes">0 / 2000</span>
          </label>
          <textarea name="assets_notes" rows="3" maxlength="2000"
                    placeholder="e.g., 'Retirement balance includes vested employer match; vested as of 2024-12-31.'"
                    class="w-full mt-1 px-2 py-1 border rounded text-xs font-mono"></textarea>
        </div>
```

**Inside the Property & Loan section, AFTER the existing "Computed LTV" `<p>` line:**
```html
        <div class="mt-3">
          <label class="text-xs flex items-center justify-between">
            <span>Notes <span class="help" data-tip="Free-text context for this section. The agent reads it alongside structured fields.">?</span></span>
            <span class="text-slate-400 text-[10px]" data-counter="property_notes">0 / 2000</span>
          </label>
          <textarea name="property_notes" rows="3" maxlength="2000"
                    placeholder="e.g., 'Appraisal pending; purchase price reflects accepted offer 2025-02-10.'"
                    class="w-full mt-1 px-2 py-1 border rounded text-xs font-mono"></textarea>
        </div>
```

- [x] **Step 2: Extend buildPayload() in frontend/app.js**

Open `C:\Proyectos\Underwriter_Agent\frontend\app.js`. Find the `buildPayload()` function. Add a `notes` line to each of the 5 sub-objects. Replace the existing `applicant: { ... }` block with this exact version:

```javascript
      applicant: {
        name: $('name'),
        credit_score: $n('credit_score'),
        credit_history: {
          bankruptcies: $n('bankruptcies') || 0,
          foreclosures: $n('foreclosures') || 0,
          late_payments_12mo: $n('late_payments_12mo') || 0,
          late_payments_24mo: $n('late_payments_24mo') || 0,
          oldest_tradeline_years: $n('oldest_tradeline_years') || 0,
          notes: $('credit_notes'),
        },
        employment: {
          employer: $('employer'),
          position: $('position'),
          years: $n('years'),
          monthly_income: $n('monthly_income'),
          type: $('emp_type'),
          notes: $('employment_notes'),
        },
        debts: {
          car_loan: $n('car_loan') || 0,
          student_loan: $n('student_loan') || 0,
          credit_cards: $n('credit_cards') || 0,
          other: $n('debt_other') || 0,
          notes: $('debts_notes'),
        },
        assets: {
          checking: $n('checking') || 0,
          savings: $n('savings') || 0,
          investments: $n('investments') || 0,
          retirement: $n('retirement') || 0,
          notes: $('assets_notes'),
        },
        property_info: {
          purchase_price: $n('purchase_price'),
          property_type: $('property_type'),
          occupancy: $('occupancy'),
          notes: $('property_notes'),
        },
        loan: {
          loan_amount: $n('loan_amount'),
          down_payment: $n('down_payment') || 0,
          term_years: $n('term_years') || 30,
        },
      },
```

- [x] **Step 3: Add the live character counter listener**

In `frontend/app.js`, find the existing `form.addEventListener('input', recomputeDtiLtv);` line. Add this block immediately AFTER it:

```javascript
  form.addEventListener('input', (e) => {
    if (e.target.tagName === 'TEXTAREA' && e.target.name && e.target.name.endsWith('_notes')) {
      const counter = form.querySelector(`[data-counter="${e.target.name}"]`);
      if (counter) counter.textContent = `${e.target.value.length} / 2000`;
    }
  });
```

- [x] **Step 4: Verify HTML element counts**

```bash
.venv\Scripts\python.exe -c "import re; src=open('frontend/index.html').read(); n_ta=len(re.findall(r'<textarea name=\"\\w+_notes\"', src)); n_ctr=len(re.findall(r'data-counter=\"\\w+_notes\"', src)); print(f'textareas:{n_ta} counters:{n_ctr}'); assert n_ta==5 and n_ctr==5"
```

Expected: `textareas:5 counters:5`

- [x] **Step 5: Run full backend suite — confirm no regression**

```bash
.venv\Scripts\python.exe -m pytest --ignore=tests/test_e2e.py -q
```

Expected: `69 passed`.

- [x] **Step 6: Commit**

```bash
git add frontend/index.html frontend/app.js
git commit -m "feat(frontend): 5 section-notes textareas with char counter"
```

**DO NOT push.**

---

## Task 5: Manual test plan doc

**Files:**
- Modify: `docs/manual-test-plan.md`

- [ ] **Step 1: Append 3 new checks**

Open `C:\Proyectos\Underwriter_Agent\docs\manual-test-plan.md`. Append these BEFORE any "If any box fails" footer line:

```markdown
- [ ] Type a 1500-char string into Borrower notes textarea — counter shows `1500 / 2000` in real time as you type
- [ ] Try to paste 2500 chars into any notes textarea — browser-enforced `maxlength` caps it at 2000; submit succeeds with 2000-char string
- [ ] Type `SSN 123-45-6789 and email test@example.com` into any notes box, submit, run with real key — Credit/Income/Asset/Collateral agent panel output should contain `XXX-XX-6789` and `[email]` (NOT the raw values)
```

- [ ] **Step 2: Commit**

```bash
git add docs/manual-test-plan.md
git commit -m "docs: manual-test-plan adds 3 checks for section notes"
```

**DO NOT push.**

---

## Task 6: Push + tag v0.2.0

**Files:** none

- [ ] **Step 1: Run full pytest — confirm 69 green**

```bash
.venv\Scripts\python.exe -m pytest --ignore=tests/test_e2e.py -q
```

Expected: `69 passed`.

- [ ] **Step 2: Run ruff + mypy**

```bash
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m mypy app/ underwriter/
```

Expected: both clean.

- [ ] **Step 3: Push to GitHub**

```bash
git push origin main
```

Expected: 5 commits pushed (Tasks 1-5).

- [ ] **Step 4: Push to HF Space**

The HF remote URL embeds a write token. **Main session handles this push** — the subagent should report the GitHub push succeeded and HALT, letting the controller (main session) perform the HF push with the token directly:

```bash
# (run by main session, not subagent)
git push "https://alanvaa:<HF_WRITE_TOKEN>@huggingface.co/spaces/alanvaa/underwriter-agent" main
```

Substitute `<HF_WRITE_TOKEN>` with a freshly issued token at run time.

- [ ] **Step 5: Smoke test on HF Space (after ~3 min build)**

```bash
until curl -sS "https://alanvaa-underwriter-agent.hf.space/" | grep -q 'name="credit_notes"'; do sleep 5; done && echo "credit_notes textarea live on HF"
```

Expected: prints `credit_notes textarea live on HF` within a few minutes.

- [ ] **Step 6: Tag v0.2.0 and push tag**

```bash
git tag -a v0.2.0 -m "v0.2.0 — section notes: free-text context per form section"
git push origin v0.2.0
```

---

## Self-Review

**1. Spec coverage:**

| Spec § | Task |
|---|---|
| §3 Section→agent mapping | Task 3 (each agent's prompt change) |
| §4.1 Schema additions | Task 1 |
| §4.2 sanitize_pii deep scrub | Task 2 |
| §4.3 Agent prompt updates | Task 3 |
| §5.1 Frontend textareas | Task 4 Step 1 |
| §5.2 buildPayload + counter | Task 4 Steps 2-3 |
| §6.1 Schema tests | Task 1 Step 1 |
| §6.2 Sanitizer tests | Task 2 Step 1 |
| §6.3 Per-agent prompt tests | Task 3 Step 1 |
| §6.4 Manual test plan | Task 5 |
| §7 File matrix | Tasks 1-5 each cover their files |
| §9 Acceptance criteria | Validated by Task 6 pytest + ruff + mypy + smoke |

All spec sections mapped.

**2. Placeholder scan:**

- `<HF_WRITE_TOKEN>` in Task 6 Step 4 — intentional security placeholder, runtime substitution by main session.

No "TBD", "TODO", "implement later", "similar to Task N" patterns.

**3. Type consistency:**

- `notes` field name used identically in schema (Task 1), sanitizer test data (Task 2), agent prompt construction (Task 3), frontend textarea names (Task 4 — `credit_notes`/`employment_notes`/`debts_notes`/`assets_notes`/`property_notes`), and buildPayload (Task 4 Step 2).
- Frontend textarea `name="property_notes"` maps to `property_info.notes` in the submitted payload — consistent with backend schema where the sub-model is `PropertyInfo`.
- `_RecordingLLM.invoke(messages)` returns object with `.content` attribute — matches what `invoke_agent` in `underwriter/agents/base.py` expects.
- Counter naming: textarea `name="credit_notes"` ↔ `<span data-counter="credit_notes">` — handler looks up `[data-counter="${e.target.name}"]`.

All names consistent.

---

**Plan complete and saved to `docs/superpowers/plans/2026-05-27-section-notes.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — fresh subagent per task, two-stage review between tasks, fast iteration.

**2. Inline Execution** — execute tasks in this session using executing-plans, batch with checkpoints.

**Which approach?**
