# Finance Pipeline — Progress Tracker

## Week 1 (2026-05-08)
**Goal:** Repo live, README with architecture, Plaid ingestion script running locally.

- [x] Repo created on GitHub
- [x] README with Mermaid architecture diagram
- [x] `.gitignore` — real credentials and PDFs excluded
- [x] `src/models.py` — Transaction dataclass
- [x] `data/sample_transactions.json` — synthetic test data
- [x] `src/ingest.py` — loads sample + Plaid sandbox mode
- [x] Plaid credentials added to `.env` (gitignored, not committed)
- [x] Verified `python -m src.ingest` runs with real Plaid sandbox — 16 transactions loaded

**Sessions this week:** 1
**Commits this week:** 1

---

## Week 2 (2026-05-08)
**Goal:** DynamoDB write layer + rule-based categorizer wired into pipeline.

- [x] DynamoDB table created (`transactions`)
- [x] `src/store.py` — write Transaction records to DynamoDB via `batch_writer`
- [x] Rule-based categorizer (`keyword → category` map) in `src/categorize.py`
- [x] End-to-end: fetch → categorize → store → verified in DynamoDB console

---

## Week 3 (2026-05-11)
**Goal:** Lambda deployment + daily CloudWatch schedule.

- [x] `src/lambda_function.py` — handler wraps `main()` from ingest
- [x] `deploy.sh` — pip-installs deps into `package/`, zips, creates/updates Lambda function
- [x] IAM role + DynamoDB write + CloudWatch Logs permissions
- [x] CloudWatch rule `finance-pipeline-daily` at `rate(1 day)`

---

## Week 4 (2026-05-13)
**Goal:** Claude API fallback categorization for unknown transactions.

- [x] `src/claude_categorize.py` — Anthropic SDK wrapper, model `claude-haiku-4-5-20251001`, temperature 0
- [x] `src/categorize.py` — calls Claude fallback when keyword rules return "Other"
- [x] Missing `ANTHROPIC_API_KEY` → silent degrade to "Other" (no crash, CI stays green)
- [x] Any Claude failure (timeout / HTTP error / bad response) → degrade to "Other"
- [x] `requirements.txt` + `.env.example` + `README.md` updated

---

## Metrics

| Week | Sessions | Commits | Feature shipped |
|------|----------|---------|-----------------|
| 1    | 1        | 1       | Plaid ingestion |
| 2    | —        | 2       | DynamoDB + keyword categorize |
| 3    | —        | 1       | Lambda + daily schedule |
| 4    | —        | 1       | Claude fallback categorize |

---

## Blockers / Notes
- Need Plaid developer account to test live sandbox (free at dashboard.plaid.com)
- BofA uses OAuth via Plaid — one-time browser flow when switching to `development` env
- Lambda deployment (`deploy.sh`) builds on macOS; `anthropic`'s `pydantic_core` dep is Rust-compiled. If Lambda cold-starts fail with `ImportError`, rebuild `package/` with `--platform manylinux2014_x86_64 --only-binary=:all:` or use Docker.
