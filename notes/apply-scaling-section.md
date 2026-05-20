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
- [x] "What I'd do at scale" — all 4 entries drafted (Store, Transform,
      Orchestration, Processing), reframed forward-looking ("at scale -> X").
- [ ] Polish pass on the section before PR:
      - Markdown: remove the 4-space indentation under each `###` heading —
        indented lines render as code blocks on GitHub. Flush everything left.
      - Spelling: Dyanmo->DynamoDB, seperate->separate, manged->managed,
        alyer->layer, ceavet->caveat, simmilar->similar, motintor->monitor,
        lamda->Lambda.
      - Store + Transform each have one broken/inverted sentence ("DynamoDB
        the need of ingesting"; "it is necesary for this project's scale").
        Reword so each clearly says the current tool is *sufficient* now.
      - Transform says "monthly ingested transaction" — pipeline runs daily.
- [ ] Metrics: transactions processed, cost per run, categorization accuracy.

Fix note: the pipeline runs once per 24h (CloudWatch schedule), not monthly —
the monthly *report* is the output; the *run* cadence is daily.
