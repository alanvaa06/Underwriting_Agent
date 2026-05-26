# Deployment

## Hugging Face Spaces

1. Create a new Space on https://huggingface.co/new-space:
   - Owner: your HF account
   - Space name: `underwriter-agent`
   - SDK: **Docker**
   - Hardware: **CPU basic** (free)
   - Visibility: Public
2. On the new Space's "Settings" tab → "Repository sync" → connect to GitHub repo `alanvaa06/Underwriting_Agent`.
3. Every push to `main` triggers a rebuild (~2-3 minutes).
4. **Secrets**: leave empty. User-supplied keys are passed in request bodies at runtime.
5. Add this metadata block at the **top** of `README.md` so HF parses it (HF requires YAML frontmatter):

```yaml
---
title: Underwriter Agent
emoji: 🏠
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---
```

## Local Docker

```bash
docker build -t underwriter-agent:dev .
docker run --rm -p 7860:7860 underwriter-agent:dev
# open http://localhost:7860
```

## Release Flow

1. Branch `feat/X` → commit → push
2. PR → CI (ruff + pytest + mypy on Python 3.11 and 3.12)
3. Run manual frontend tests (see `manual-test-plan.md`)
4. Merge to `main` → HF Space auto-rebuilds
5. Smoke test on live URL
6. Tag `v0.1.0` on milestone releases

## Operational Posture

- **No SLA.** Free Space sleeps after 48h idle, ~30s cold start.
- **Cost to operator: $0** — no HF Pro tier, user-paid OpenAI tokens.
- **Logs**: HF Space log viewer (stdout). No external APM.
- **Versioning**: semver in `pyproject.toml`; tag milestones.
