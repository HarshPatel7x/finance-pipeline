# Track C — Instrumentation rep (2026-05-22)

Apply-phase polish: making the categorizer observable. `categorize()` returns a
structured `CategorizationResult` (category + which path produced it + token
cost), and `run_summary()` rolls one run's results into metrics.

## Concept — instrumentation
Making an opaque process report on itself. The categorizer was a black box: a
category came out, nothing else. Now each categorization emits a record and one
function aggregates them. Why it earns its keep: a missing API key once degraded
every Claude call to "Other" silently — instrumentation makes that visible in the
run output. Résumé line: "instrumented the categorizer to track keyword-vs-LLM
split and token cost per run."

## The record pattern — `CategorizationResult`
A 4-field dataclass beats a 4-tuple: `result.input_tokens` reads clearly,
`result[2]` does not. The repo already does this with `Transaction`.

## Bugs caught (first categorize() attempt)
1. **Generator-expression scope.** In `any(kw in text for kw in keywords)`, `kw`
   exists ONLY inside that generator expression. Referencing `kw` on the next
   line → `NameError`. Comprehensions and generators get their own scope; the
   loop variable does not leak out.
2. **`if / else / break` short-circuit.** An `else: ... break` attached to the
   `if` exits the rule loop after the FIRST rule — so only rule #1 is ever
   checked and everything else force-routes to the LLM. The keyword fallback
   belongs AFTER the loop finishes with no match, not inside it.

## Python has no "garbage values"
That is a C / C++ idea. In Python a name or dict key either exists with a real
value or does not exist — and accessing a missing one RAISES (`NameError`,
`KeyError`); it never hands back junk. `dict["k"] += 1` on a missing key →
`KeyError`, an immediate crash, not silent wrong math. Python fails loud, at the
exact line. Handling a maybe-missing key: pre-initialize, `dict.get(k, 0)`, or
`collections.defaultdict(int)`.

## run_summary — aggregation
Single pass, accumulate into a pre-initialized dict, O(n) time, O(1) space.
Note: an `if x > 0:` guard before `total += x` is redundant — `+= 0` is a no-op.

## Process lesson
When a task feels sprawling and you feel lost, re-anchor BEFORE writing code:
"what one thing am I producing — which file, which function?" ~40 minutes went
into the wrong file this session for want of that 30-second check.
