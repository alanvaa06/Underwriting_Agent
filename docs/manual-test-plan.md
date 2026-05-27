# Manual Frontend Test Plan

Run before every deploy to `main`. Tick each box in the PR description.

- [ ] Empty form → click Run → inline error: "Enter a valid OpenAI API key" (network call not made)
- [ ] Invalid key (e.g., `sk-bad`) → submit → SSE error event → red banner shows `OPENAI_AUTH`
- [ ] Click Cancel during streaming → graph animation stops, form unlocks within 1s
- [ ] Strong applicant full run → APPROVED card (green border), risk score visible, memo populated
- [ ] Weak applicant full run → DENIED card (red border)
- [ ] Refresh page during stream → no zombie state, fresh page loads cleanly, no console errors
- [ ] Mobile viewport (375×667) → form sections stack vertically, graph SVG scales to width, no horizontal scroll
- [ ] Hover any `?` icon — tooltip popover appears within 100ms with correct text, disappears when cursor moves off
- [ ] In Monthly income, type `12500` and click outside — input displays `12,500`; click back in — reverts to `12500`
- [ ] Submit form with money fields filled — verify in DevTools Network tab that POST `/api/run` body contains integer values (e.g. `12500`), not string `"12,500"`

- [ ] Type a 1500-char string into Borrower notes textarea — counter shows `1500 / 2000` in real time as you type
- [ ] Try to paste 2500 chars into any notes textarea — browser-enforced `maxlength` caps it at 2000; submit succeeds with 2000-char string
- [ ] Type `SSN 123-45-6789 and email test@example.com` into any notes box, submit, run with real key — Credit/Income/Asset/Collateral agent panel output should contain `XXX-XX-6789` and `[email]` (NOT the raw values)

If any box fails: do not merge. Fix and re-test.
