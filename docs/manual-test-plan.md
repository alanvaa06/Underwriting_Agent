# Manual Frontend Test Plan

Run before every deploy to `main`. Tick each box in the PR description.

- [ ] Empty form → click Run → inline error: "Enter a valid OpenAI API key" (network call not made)
- [ ] Invalid key (e.g., `sk-bad`) → submit → SSE error event → red banner shows `OPENAI_AUTH`
- [ ] Click Cancel during streaming → graph animation stops, form unlocks within 1s
- [ ] Strong applicant full run → APPROVED card (green border), risk score visible, memo populated
- [ ] Weak applicant full run → DENIED card (red border)
- [ ] Refresh page during stream → no zombie state, fresh page loads cleanly, no console errors
- [ ] Mobile viewport (375×667) → form sections stack vertically, graph SVG scales to width, no horizontal scroll

If any box fails: do not merge. Fix and re-test.
