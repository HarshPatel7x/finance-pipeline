# Finance Pipeline — Progress Tracker

## Week 1 (2026-05-08)
**Goal:** Repo live, README with architecture, Plaid ingestion script running locally.

- [x] Repo created on GitHub
- [x] README with Mermaid architecture diagram
- [x] `.gitignore` — real credentials and PDFs excluded
- [x] `src/models.py` — Transaction dataclass
- [x] `data/sample_transactions.json` — synthetic test data
- [x] `src/ingest.py` — loads sample + Plaid sandbox mode
- [ ] Plaid credentials added to `.env` (do this yourself — not committed)
- [ ] Verified `python -m src.ingest` runs with real Plaid sandbox

**Sessions this week:** 1
**Commits this week:** 1

---

## Week 2 (planned)
- [ ] DynamoDB table created (`transactions`)
- [ ] `src/store.py` — write Transaction records to DynamoDB
- [ ] Rule-based categorizer (`keyword → category` map)
- [ ] End-to-end: fetch → categorize → store → verify in DynamoDB console

---

## Metrics

| Week | Sessions | Commits | Feature shipped |
|------|----------|---------|-----------------|
| 1    | 1        | 1       | Plaid ingestion |

---

## Blockers / Notes
- Need Plaid developer account to test live sandbox (free at dashboard.plaid.com)
- BofA uses OAuth via Plaid — one-time browser flow when switching to `development` env
