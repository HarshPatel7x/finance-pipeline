# Week 6 — Architecture doc + "How I Built This"

**Session:** 2026-05-18 (pulled forward from Tue 2026-05-19)
**Mode:** Vasudev Mode 2 Teach → user writes draft
**Time:** ~44 min (at cap)
**Tier:** Self Okay / My Okay — match ✓

---

## Concept taught: shape of a portfolio "how I built this" section

Three principles for a section a hiring manager skims in 90 seconds:

1. **Decisions, not narration.** Each paragraph: *choice + rejected alternative + why-fit + tradeoff*. Diary narration ("I did X, then Y") tells the reader nothing they couldn't get from `git log`.
2. **Failures + tradeoffs visible.** Sanitized resumes smell wrong. One real failure + how it was bounded = senior signal. Junior README = no failures.
3. **Constraint-anchored opener.** Open with the 3-4 constraints that drove every decision (single-user, ~50 txns/month, free-tier ceiling, Plaid as data source). Decisions flow from constraints, not from feature lists.

## Teach-back result

Q: Rewrite the Claude API choice in decision-shape — choice, rejected, why.

First answer (Mostly there): named choice + gestured at rejected, but no tradeoff and "hard-coded few categories" was vague (not naming "rule-based keyword map").

Rewrite drill (Crisp): "free-text with many variations and a long tail no rule-based keyword map can accommodate. The cost is latency network call per transaction vs. dict look ups, works at 50 txns/month → $0.001/txn Claude Haiku but not at 50K txns/month."

Senior signal: naming the **scale break point** (50/month works, 50K/month doesn't). The Crisp answer landed only after the explicit "name the tradeoff" drill — pattern is still mechanism-correct, why-fit/tradeoff lagging without prompting.

## Draft output

5-paragraph §How I Built This added to README. Covered: Plaid, DynamoDB, Lambda+CloudWatch, Claude API, silent-degrade fallback.

### What landed
- DynamoDB paragraph: clean choice + 2 alts rejected + 4 why-fit reasons + tradeoff named.
- Claude API paragraph: Crisp (the polished teach-back rewrite).
- Self-tier honest — user named four gaps cold (Plaid pricing unknown, DynamoDB rationale read-once-and-repeated, CloudWatch bluffed, AWS-availability the only cost surfaced).

### What missed
- **No constraint-anchored opener.** Principle 3 fully skipped — doc jumps cold into Plaid.
- **Failure-recovery only half-covered.** Silent-degrade is a fallback pattern, not framed as a failure-recovery story. The Lambda Rust-compile gotcha (documented in PROGRESS.md Blockers) is real failure-recovery and not in the README.
- **Plaid paragraph skeletal:** "consistent format with designed model" is fuzzy; doesn't name normalization, OAuth-handling, webhook-able real-time data.
- **Lambda paragraph:** CloudWatch reasoning is "synergy" — confirmed bluff per self-tier.
- **Copy quality:** 7+ typos in 10 lines, 2 broken sentences. Not interview-ready.

## Pattern note

EI lateral spread continues, fourth hit today:
- DSA Container retry: bottleneck Crisp / dominance Mostly-there
- SQL Dept-Highest-Salary retry: EI Vague
- Project doc teach-back: Mostly-there → Crisp on explicit rewrite drill
- Project doc full write: 4 paragraphs Mostly/Vague (without drill scaffolding)

Lesson: the "why-fit + tradeoff" reasoning lands when the drill is explicit. Without scaffolding, defaults to mechanism narration. Reps needed at unguided-prose level.

## Queued

**Tomorrow (Tuesday 2026-05-19, Track C continuation):**
1. Mode 2 Teach (30 min): Plaid pricing tiers + DynamoDB single-table design tradeoffs + CloudWatch Events vs. EventBridge (cron syntax, retry semantics, actual value over local cron).
2. User rewrites §How I Built This from scratch with constraints opener + Lambda Rust-compile failure-recovery (15 min).

Track A: Longest Substring Without Repeating Characters retry (was overdue per observer A11 2026-05-15).
Track B: Python Data Manipulation Week 3 start (pandas — read CSV, group/aggregate).
