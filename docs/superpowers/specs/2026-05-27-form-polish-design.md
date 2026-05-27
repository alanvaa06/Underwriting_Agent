# Form Polish — Tooltips + Number Formatting

**Date:** 2026-05-27
**Status:** Awaiting user review
**Scope:** v0.1.1 follow-up to MVP. Frontend-only.

---

## 1. Goal

Make the applicant form more approachable for non-mortgage colleagues:

1. **Tooltips** — every form field gets a `?` icon with hover-revealed one-liner explanation.
2. **Number formatting** — dollar inputs show comma-grouped thousands on blur (`12500` → `12,500`).

No backend change. No new deps. Zero impact on `/api/run` payload shape (frontend strips commas before sending).

---

## 2. Tooltip

### Pattern

Inline `<span class="help" data-tip="...">?</span>` placed after each label's text node. Pure CSS hover popover — no JS.

### CSS

```css
.help {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 14px;
  height: 14px;
  margin-left: 4px;
  border-radius: 50%;
  background: rgb(148, 163, 184); /* slate-400 */
  color: white;
  font-size: 10px;
  font-weight: 600;
  cursor: help;
  position: relative;
  vertical-align: middle;
}
.help:hover {
  background: rgb(37, 99, 235); /* blue-600 */
}
.help:hover::after {
  content: attr(data-tip);
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  width: 200px;
  padding: 8px 10px;
  background: rgb(30, 41, 59); /* slate-800 */
  color: white;
  font-size: 11px;
  font-weight: 400;
  line-height: 1.4;
  border-radius: 6px;
  text-align: left;
  white-space: normal;
  z-index: 50;
  pointer-events: none;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.help:hover::before {
  content: '';
  position: absolute;
  bottom: calc(100% + 2px);
  left: 50%;
  transform: translateX(-50%);
  border: 6px solid transparent;
  border-top-color: rgb(30, 41, 59);
  z-index: 51;
}
```

### Content per field (one-liner ≤ 12 words)

| Field | Tooltip |
|---|---|
| Full name | "Borrower's full legal name." |
| FICO score | "Credit score, 300–850. Higher is better." |
| Oldest tradeline (yrs) | "Years since oldest credit line opened." |
| Bankruptcies | "Filings in last 7 years." |
| Foreclosures | "Lost properties in last 7 years." |
| Late payments (12mo) | "Payments 30+ days late, last 12 months." |
| Late payments (24mo) | "Payments 30+ days late, last 24 months." |
| Employer | "Current employer name." |
| Position | "Current job title." |
| Tenure (years) | "Years at current employer." |
| Monthly income ($) | "Gross monthly income before tax." |
| Type | "W2 = salaried. 1099 = contractor." |
| Car loan ($) | "Monthly car payment." |
| Student loan ($) | "Monthly student loan payment." |
| Credit cards ($) | "Minimum monthly credit card payment." |
| Other ($) | "Other recurring monthly debt." |
| Checking ($) | "Checking account balance." |
| Savings ($) | "Savings account balance." |
| Investments ($) | "Brokerage / non-retirement holdings." |
| Retirement ($) | "401k / IRA balance." |
| Purchase price ($) | "Home sale price." |
| Down payment ($) | "Cash paid upfront." |
| Loan amount ($) | "Mortgage principal requested." |
| Term (years) | "Loan repayment duration. 30 most common." |
| Property type | "Single family, condo, townhouse, multi-family." |
| Occupancy | "Primary = live in. Secondary = vacation. Investment = rent out." |
| OpenAI API Key | "Your sk-... key. Sent per-request, never stored." |

---

## 3. Number Formatting

### Inputs affected

12 fields switch from `<input type="number">` to `<input type="text" inputmode="numeric" data-format="money">`:

- monthly_income
- car_loan, student_loan, credit_cards, debt_other
- checking, savings, investments, retirement
- purchase_price, down_payment, loan_amount

### Inputs NOT affected (small integers, no commas)

- credit_score (300–850, 3 digits)
- oldest_tradeline_years (float)
- bankruptcies, foreclosures, late_payments_12mo, late_payments_24mo (single digits)
- years (employment tenure, float)
- term_years (1–40)

### New file: `frontend/format.js`

```javascript
(function () {
  const fmt = new Intl.NumberFormat('en-US');

  function parse(raw) {
    if (raw === '' || raw == null) return null;
    const digits = String(raw).replace(/[^\d.-]/g, '');
    if (digits === '' || digits === '-') return null;
    const n = Number(digits);
    return Number.isFinite(n) ? n : null;
  }

  function formatBlur(e) {
    const n = parse(e.target.value);
    e.target.value = n == null ? '' : fmt.format(n);
  }

  function unformatFocus(e) {
    const n = parse(e.target.value);
    e.target.value = n == null ? '' : String(n);
  }

  function init() {
    document.querySelectorAll('input[data-format="money"]').forEach(el => {
      el.addEventListener('blur', formatBlur);
      el.addEventListener('focus', unformatFocus);
      // initial render if pre-filled
      if (el.value !== '') formatBlur({ target: el });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  window.UnderwriterFormat = { parse };
})();
```

### `app.js` integration

`$n()` helper updated to strip commas before parsing:

```javascript
function $n(name) {
  const v = form.querySelector(`[name="${name}"]`).value;
  if (v === '') return null;
  const stripped = v.replace(/,/g, '');
  return stripped === '' ? null : Number(stripped);
}
```

DTI/LTV recompute on `input` event already calls `$n()` — no further change.

Form `<input type="text">` cannot use HTML5 `required`/`min` validation natively. Mitigation: keep `required` attribute (browser still respects on text inputs for empty-check), drop `min` enforcement (handled by Pydantic on backend). Acceptable for MVP.

---

## 4. Files Changed

| File | Change |
|---|---|
| `frontend/index.html` | 27 tooltip spans added. 12 inputs switched to `type="text" inputmode="numeric" data-format="money"`. New `<script src="/format.js">` before `<script src="/app.js">`. |
| `frontend/styles.css` | `.help`, `.help:hover::after`, `.help:hover::before` rules appended (~50 lines). |
| `frontend/format.js` | NEW. ~40 LoC IIFE. |
| `frontend/app.js` | `$n()` strips commas. No other change. |

---

## 5. Testing

- **No new automated tests.** Frontend has no test framework per MVP scope.
- **Manual check** added to `docs/manual-test-plan.md`:
  - "Hover ? icon — tooltip appears within 100ms with correct text."
  - "Type 12500 in monthly income, click away — shows 12,500. Click in — reverts to 12500."
  - "Submit form — payload sent to /api/run has integer values (not strings with commas). Verify via DevTools network tab."
- Existing `tests/test_api.py` unaffected — payload schema unchanged.

---

## 6. Out of Scope

- Mobile-specific tooltip pattern (tap-to-reveal). Hover-only covers desktop demo audience.
- Currency symbol inside input (`$`). Plain comma grouping only.
- Negative numbers (none of these fields support negatives).
- Locale switching (en-US fixed).
- Field-level inline validation (still happens via Pydantic 422 on submit).

---

## 7. Acceptance Criteria

- [ ] Every form field (incl. API key) has a `?` icon
- [ ] Hovering `?` reveals styled popover within 100ms
- [ ] 12 dollar fields format with commas on blur
- [ ] Clicking back into a formatted field reverts to raw digits
- [ ] Submitting form sends clean integers to `/api/run` (no comma strings)
- [ ] Existing 59 tests still pass (no regression)
- [ ] Manual test plan updated with 3 new checks
