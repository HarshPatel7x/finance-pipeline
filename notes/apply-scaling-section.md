# Apply Phase — Architecture Diagram + "What I'd do at scale"

Session: 2026-05-20

## Architecture correction (done)

The README mermaid diagram had `categorize.py` and `report.py` reading from /
writing to DynamoDB. The code does neither — verified against `src/`:

- `categorize.py` and `report.py` do not import `boto3`; only `store.py` does.
- `ingest.main()` runs one in-memory pass: fetch -> categorize (in memory) ->
  print report (in memory) -> ONE DynamoDB batch-write at the end.
- DynamoDB is a write-only sink: written once per run, read zero times.

Diagram fixed: `categorize.py` and `report.py` now connect through `ingest.py`;
DynamoDB has one arrow in, zero out.

## Scale-section reference — the four tools

For the "What I'd do at scale" README section. Each entry = what breaks in THIS
pipeline -> what to add -> why.

- **Snowflake** — store. DynamoDB is key-value: no JOINs / GROUP BY, can't do
  analytical queries. Snowflake = cloud data warehouse, separates storage from
  compute. At scale: analytics moves to Snowflake; DynamoDB stays the
  operational store; data is loaded Dynamo -> Snowflake.
- **dbt** — transform. `report.py`'s `monthly_summary()` aggregation runs in
  memory. At scale that logic becomes a dbt model: tested, version-controlled
  SQL running inside Snowflake. dbt does not call APIs (categorization stays
  out of dbt).
- **Airflow / MWAA** — orchestration. CloudWatch is a timer; it can't express
  step dependencies, retries, or backfills. At scale the one fused Lambda
  splits into steps (ingest / categorize / load / transform); Airflow runs
  them as a DAG.
- **Kinesis** — processing model. Pipeline is batch (daily run). At scale, IF
  real-time were needed (instant fraud/budget alerts, high volume), Kinesis
  streams events for processing on arrival. Batch is correct for the current
  scope — present Kinesis as conditional.

## Section status / next session

- [x] Architecture diagram corrected.
- [x] "What I'd do at scale" — all 4 entries drafted, reframed forward-looking.
- [x] Polish pass — DONE 2026-05-20 S2. Indentation resolved by switching
      `###` headings to a numbered list (4-space indent under a list item is
      paragraph text, not a code block). Spelling + grammar + daily-not-monthly
      all fixed and grep-clean.
- [ ] Metrics: transactions processed, cost per run, categorization accuracy.
      BLOCKED ON instrumentation — see below.

## Metrics — instrumentation rep (next session, 2026-05-21)

The pipeline can't self-report yet: `categorize()` returns only a category
string (can't tell keyword vs Claude vs degraded), and `claude_categorize.py`
discards `resp.usage` (no token cost). Honest metrics need a small change:
- `categorize()` returns `(category, source)` where source is keyword/claude/degraded.
- `claude_categorize.classify()` surfaces token usage from `resp.usage`.
- A run-summary line: `Categorized: N keyword · N Claude · N tokens · ~$X`.
Track C split: user writes the summary function; Claude scaffolds the
return-type plumbing through categorize.py / claude_categorize.py / ingest.py.

Confirmed 2026-05-20 S2: `ANTHROPIC_API_KEY` was missing from `.env` — the Claude
fallback silently degraded every non-keyword txn to "Other". Key now added;
categorizer verified working (Other $685 -> $254, Transfer $371).
