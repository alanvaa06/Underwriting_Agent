# Form Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `?` hover tooltips to every form field and comma-grouped formatting on blur to dollar inputs, per spec `docs/superpowers/specs/2026-05-27-form-polish-design.md`.

**Architecture:** Frontend-only change. Three files modified (`index.html`, `styles.css`, `app.js`) + one new file (`format.js`). No backend touch, no new deps, no payload schema change (commas stripped before submit). Manual test only.

**Tech Stack:** Vanilla JS, CSS, `Intl.NumberFormat('en-US')`. No build step.

---

## File Map

| File | Change |
|---|---|
| `frontend/index.html` | 27 tooltip spans added. 12 inputs switched to `type="text" inputmode="numeric" data-format="money"`. New `<script src="/format.js">` added before `app.js`. |
| `frontend/styles.css` | `.help` + `.help:hover::after` + `.help:hover::before` rules appended (~50 lines). |
| `frontend/format.js` | NEW. ~40 LoC IIFE. Format on blur, unformat on focus. |
| `frontend/app.js` | `$n()` helper strips commas before parsing. |
| `docs/manual-test-plan.md` | 3 new manual checks appended. |

---

## Task Order Rationale

1. **Task 1** — CSS (`.help` styling). Foundation; safe to ship alone (no spans yet → no visual change).
2. **Task 2** — `format.js` standalone module. Self-contained, callable but not yet wired.
3. **Task 3** — `app.js` patch (`$n()` comma strip). Defensive; no UI change yet.
4. **Task 4** — `index.html` rewrite: add 27 tooltip spans + switch 12 inputs to `type="text"` + load `format.js`. Single big edit that activates everything.
5. **Task 5** — manual test plan doc + smoke instructions.

Each task ends with one commit. Push deferred to end (single batched push to main → triggers HF Space rebuild via GitHub sync, which we'll handle separately).

---

## Task 1: Add tooltip CSS to styles.css

**Files:**
- Modify: `frontend/styles.css` (append)

- [x] **Step 1: Append to `frontend/styles.css`**

Open `C:\Proyectos\Underwriter_Agent\frontend\styles.css` and add at the bottom (after existing rules):

```css

/* === Form tooltips === */
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

- [x] **Step 2: Verify CSS syntax by booting the dev server**

```bash
.venv\Scripts\python.exe -m uvicorn app.main:app --port 7860 &
```

Open `http://localhost:7860`. Page should still render (no `.help` spans yet so no visual change). Stop server.

- [x] **Step 3: Commit**

```bash
git add frontend/styles.css
git commit -m "feat(frontend): tooltip popover CSS (.help class)"
```

---

## Task 2: Create frontend/format.js

**Files:**
- Create: `frontend/format.js`

- [x] **Step 1: Write `frontend/format.js`**

Create `C:\Proyectos\Underwriter_Agent\frontend\format.js` with:

```javascript
/* Money input formatter. Format on blur, unformat on focus. */

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

- [x] **Step 2: Verify file loads via node syntax check**

```bash
node -c frontend/format.js
```

Expected: no output, exit 0 (node validates syntax without executing browser-only `document` references — `-c` checks parse only).

If `node` not available, skip — the script is small enough to eyeball.

- [x] **Step 3: Commit**

```bash
git add frontend/format.js
git commit -m "feat(frontend): format.js — money input formatter (blur/focus toggle)"
```

---

## Task 3: Patch app.js $n() to strip commas

**Files:**
- Modify: `frontend/app.js`

- [x] **Step 1: Read current `$n()` function**

Open `C:\Proyectos\Underwriter_Agent\frontend\app.js`. Locate the existing helper at top of IIFE:

```javascript
  function $n(name) {
    const v = form.querySelector(`[name="${name}"]`).value;
    return v === '' ? null : Number(v);
  }
```

- [x] **Step 2: Replace with comma-stripping version**

Use Edit to replace exactly:

```javascript
  function $n(name) {
    const v = form.querySelector(`[name="${name}"]`).value;
    return v === '' ? null : Number(v);
  }
```

with:

```javascript
  function $n(name) {
    const v = form.querySelector(`[name="${name}"]`).value;
    if (v === '') return null;
    const stripped = v.replace(/,/g, '');
    return stripped === '' ? null : Number(stripped);
  }
```

- [x] **Step 3: Boot dev server and verify no regression**

```bash
.venv\Scripts\python.exe -m uvicorn app.main:app --port 7860 &
```

Open `http://localhost:7860`. Type `12500` in Monthly income, then `1200` in Car loan. Watch "Computed DTI" — should display `9.6%` (still works, no commas yet). Stop server.

- [x] **Step 4: Run full pytest suite — confirm no backend regression**

```bash
.venv\Scripts\python.exe -m pytest --ignore=tests/test_e2e.py -q
```

Expected: `59 passed`.

- [x] **Step 5: Commit**

```bash
git add frontend/app.js
git commit -m "feat(frontend): app.js $n() strips commas before parse"
```

---

## Task 4: Update index.html — tooltips + input type swap + format.js script tag

**Files:**
- Modify: `frontend/index.html`

This is the biggest task. Three coordinated edits in one file.

### Step 1: Add `data-format="money"` and switch type on the 12 dollar inputs

- [x] **Edit each of these 12 inputs.** For each one, replace its current `<input ...>` tag with the new shape: change `type="number"` to `type="text" inputmode="numeric"` (remove `min`/`max`/`step` since they don't apply to text), keep `name` and `required` and Tailwind classes, add `data-format="money"`.

Below is one example transformation. Apply the same pattern to all 12 inputs (names listed under the example):

**Before:**
```html
<label class="text-xs">Monthly income ($) <input name="monthly_income" type="number" min="1" required class="w-full mt-1 px-2 py-1 border rounded" /></label>
```

**After (also adds tooltip span — see Step 2):**
```html
<label class="text-xs">Monthly income ($) <span class="help" data-tip="Gross monthly income before tax.">?</span> <input name="monthly_income" type="text" inputmode="numeric" data-format="money" required class="w-full mt-1 px-2 py-1 border rounded" /></label>
```

**The 12 inputs needing this swap (by `name` attribute):**

1. `monthly_income`
2. `car_loan`
3. `student_loan`
4. `credit_cards`
5. `debt_other`
6. `checking`
7. `savings`
8. `investments`
9. `retirement`
10. `purchase_price`
11. `down_payment`
12. `loan_amount`

### Step 2: Add `<span class="help" data-tip="...">?</span>` after every field's label text

- [x] Add tooltip spans inline with each label. Insert immediately before the `<input>` or `<select>` element, with a space separating it from the text node. Exact text per field:

| `name` attr | `data-tip` |
|---|---|
| `api_key` | `Your sk-... key. Sent per-request, never stored.` |
| `name` | `Borrower's full legal name.` |
| `credit_score` | `Credit score, 300–850. Higher is better.` |
| `oldest_tradeline_years` | `Years since oldest credit line opened.` |
| `bankruptcies` | `Filings in last 7 years.` |
| `foreclosures` | `Lost properties in last 7 years.` |
| `late_payments_12mo` | `Payments 30+ days late, last 12 months.` |
| `late_payments_24mo` | `Payments 30+ days late, last 24 months.` |
| `employer` | `Current employer name.` |
| `position` | `Current job title.` |
| `years` | `Years at current employer.` |
| `monthly_income` | `Gross monthly income before tax.` |
| `emp_type` | `W2 = salaried. 1099 = contractor.` |
| `car_loan` | `Monthly car payment.` |
| `student_loan` | `Monthly student loan payment.` |
| `credit_cards` | `Minimum monthly credit card payment.` |
| `debt_other` | `Other recurring monthly debt.` |
| `checking` | `Checking account balance.` |
| `savings` | `Savings account balance.` |
| `investments` | `Brokerage / non-retirement holdings.` |
| `retirement` | `401k / IRA balance.` |
| `purchase_price` | `Home sale price.` |
| `down_payment` | `Cash paid upfront.` |
| `loan_amount` | `Mortgage principal requested.` |
| `term_years` | `Loan repayment duration. 30 most common.` |
| `property_type` | `Single family, condo, townhouse, multi-family.` |
| `occupancy` | `Primary = live in. Secondary = vacation. Investment = rent out.` |

Example transformation for `credit_score` (number input, gets tooltip but NO `data-format` since it's not a dollar field):

**Before:**
```html
<label class="text-xs">FICO score <input name="credit_score" type="number" min="300" max="850" required class="w-full mt-1 px-2 py-1 border rounded" /></label>
```

**After:**
```html
<label class="text-xs">FICO score <span class="help" data-tip="Credit score, 300–850. Higher is better.">?</span> <input name="credit_score" type="number" min="300" max="850" required class="w-full mt-1 px-2 py-1 border rounded" /></label>
```

Example for `api_key` (password input, gets tooltip):

**Before:**
```html
<input type="password" name="api_key" required placeholder="sk-..."
       class="w-full px-3 py-2 border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500" />
```

**After (tooltip lives inside the `<legend>`):**
```html
<legend class="px-2 text-sm font-semibold text-slate-700">OpenAI API Key <span class="help" data-tip="Your sk-... key. Sent per-request, never stored.">?</span></legend>
<input type="password" name="api_key" required placeholder="sk-..."
       class="w-full px-3 py-2 border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500" />
```

Example for `emp_type` (select element):

**Before:**
```html
<label class="text-xs">Type
  <select name="emp_type" class="w-full mt-1 px-2 py-1 border rounded">
    <option value="W2">W2</option><option value="1099">1099</option><option value="self_employed">Self-employed</option>
  </select>
</label>
```

**After:**
```html
<label class="text-xs">Type <span class="help" data-tip="W2 = salaried. 1099 = contractor.">?</span>
  <select name="emp_type" class="w-full mt-1 px-2 py-1 border rounded">
    <option value="W2">W2</option><option value="1099">1099</option><option value="self_employed">Self-employed</option>
  </select>
</label>
```

### Step 3: Load format.js before app.js

- [x] Replace this block at the bottom of `<body>`:

**Before:**
```html
  <script src="/graph.js"></script>
  <script src="/app.js"></script>
```

**After:**
```html
  <script src="/graph.js"></script>
  <script src="/format.js"></script>
  <script src="/app.js"></script>
```

### Step 4: Boot dev server and manually smoke-test

- [x] Run:

```bash
.venv\Scripts\python.exe -m uvicorn app.main:app --port 7860 &
```

Open `http://localhost:7860`. Verify:
- Every form field has a small grey `?` icon next to its label
- Hovering the `?` reveals a dark popover with the tooltip text after ~100ms
- Type `12500` in Monthly income, click outside → input shows `12,500`
- Click back into the field → reverts to `12500`
- Type `1200` in Car loan, blur → `1,200`
- Computed DTI updates correctly (~9.6%)
- Submit form with invalid key (e.g. `xxx`) → red error banner "Enter a valid OpenAI API key..."

Stop server (Ctrl-C or kill the background process).

### Step 5: Commit

- [x] Run:

```bash
git add frontend/index.html
git commit -m "feat(frontend): tooltips on every field + money inputs swap to text+data-format"
```

---

## Task 5: Update docs/manual-test-plan.md

**Files:**
- Modify: `docs/manual-test-plan.md`

- [ ] **Step 1: Append three checks to the existing list**

Open `C:\Proyectos\Underwriter_Agent\docs\manual-test-plan.md`. Add these three items as new checkboxes after the existing 7 items (before any closing line):

```markdown
- [ ] Hover any `?` icon — tooltip popover appears within 100ms with correct text, disappears when cursor moves off
- [ ] In Monthly income, type `12500` and click outside — input displays `12,500`; click back in — reverts to `12500`
- [ ] Submit form with money fields filled — verify in DevTools Network tab that POST `/api/run` body contains integer values (e.g. `12500`), not string `"12,500"`
```

- [ ] **Step 2: Commit**

```bash
git add docs/manual-test-plan.md
git commit -m "docs: manual-test-plan adds 3 checks for tooltips + formatting"
```

---

## Task 6: Push batch to origin/main → triggers HF Space rebuild

**Files:** none

- [ ] **Step 1: Run full pytest one more time to confirm no regression**

```bash
.venv\Scripts\python.exe -m pytest --ignore=tests/test_e2e.py -q
```

Expected: `59 passed`.

- [ ] **Step 2: Push all 5 commits to GitHub**

```bash
git push origin main
```

Expected: 5 commits pushed (CSS, format.js, app.js patch, index.html, manual-test-plan).

- [ ] **Step 3: Force-push to HF Space** (HF doesn't auto-sync from GitHub for our setup; manual push)

```bash
git remote add hf "https://alanvaa:<HF_WRITE_TOKEN>@huggingface.co/spaces/alanvaa/underwriter-agent" 2>/dev/null || true
git push hf main --force
git remote remove hf
```

**SECURITY:** Substitute `<HF_WRITE_TOKEN>` with a freshly generated HF write token. Do NOT commit the URL with embedded token. The `remote remove` at the end clears any persisted credential.

If the existing `hf` remote URL is still in `.git/config` from a prior push, the `git remote add` will fail benign-fail; the `git push hf` will then use whatever URL is currently set.

- [ ] **Step 4: Wait ~3 min for HF Space rebuild, then smoke-test**

```bash
curl -sS "https://alanvaa-underwriter-agent.hf.space/api/healthz"
```

Expected: `{"status":"ok"}` once the new container boots.

Open `https://alanvaa-underwriter-agent.hf.space/` in browser. Verify:
- `?` icons visible on form
- Hover reveals tooltip
- Money fields format on blur

- [ ] **Step 5: Tag the release**

```bash
git tag -a v0.1.1 -m "v0.1.1 — form polish: tooltips + comma formatting"
git push origin v0.1.1
```

---

## Self-Review

**1. Spec coverage:**

| Spec §  | Task |
|---|---|
| §2 Tooltip CSS | Task 1 |
| §2 Tooltip content (27 entries) | Task 4 Step 2 (table of all 27 `name`/`data-tip` pairs) |
| §3 format.js | Task 2 |
| §3 12 input swaps to `type="text"` | Task 4 Step 1 (lists all 12 names) |
| §3 `app.js` `$n()` strip | Task 3 |
| §4 Files Changed | Tasks 1, 2, 3, 4, 5 |
| §5 Testing — manual plan update | Task 5 |
| §5 Testing — backend regression check | Task 3 Step 4 + Task 6 Step 1 |
| §7 Acceptance criteria | Validated in Task 4 Step 4 + Task 6 Step 4 |

All spec sections mapped to a task.

**2. Placeholder scan:**

- `<HF_WRITE_TOKEN>` in Task 6 Step 3 — intentional security placeholder; subagent should pause and ask the controller (main session) for the token rather than substitute themselves.

No other placeholders.

**3. Type consistency:**

- `data-format="money"` attribute used consistently in Task 2 (querySelector) and Task 4 (HTML).
- `data-tip` attribute used consistently in Task 1 (CSS `attr(data-tip)`) and Task 4 (HTML).
- `.help` class used consistently in Task 1 (CSS) and Task 4 (HTML).
- `UnderwriterFormat` global from Task 2 not consumed by any later task (currently unused — could remove, but leaving as a debug hook is fine and YAGNI is satisfied).

All names consistent.

---

**Plan complete and saved to `docs/superpowers/plans/2026-05-27-form-polish.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — fresh subagent per task, two-stage review between tasks, fast iteration.

**2. Inline Execution** — execute tasks in this session using executing-plans, batch with checkpoints.

**Which approach?**
