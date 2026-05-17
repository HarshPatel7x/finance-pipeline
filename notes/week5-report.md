# Week 5 — Report Output

## Dict accumulation — the pattern you needed

Wrong (what you wrote first):
```python
summary_obj[date].update({"Food & Drink": 8.00})
# .update() replaces existing keys — $5 is gone, $8 overwrites it
```

Right — Option A (explicit):
```python
if category in summary_obj[date]:
    summary_obj[date][category] += amount
else:
    summary_obj[date][category] = amount
```

Right — Option B (idiomatic, one line):
```python
summary_obj[date][category] = summary_obj[date].get(category, 0) + amount
```

`.get(key, default)` returns the existing value if the key exists, or `default` if not.
First time you see "Food & Drink": `0 + 5.00 = 5.00`. Second time: `5.00 + 8.00 = 13.00`.

**The rule:** whenever you're summing into a dict, use `.get(key, 0) + value`. It's one
of the 5 most common Python patterns — worth having in muscle memory.

---

## Debt payoff — the math

Each month, two things happen in order:
1. Interest accrues on the current balance: `balance *= (1 + monthly_rate)`
2. You make a payment: `balance -= monthly_payment`

Order matters — banks charge interest first, then apply payment. Flipping the order
understates interest slightly.

```python
monthly_rate = annual_rate / 12        # 0.19 / 12 = 0.01583 for 19% APR
monthly_interest = monthly_rate * balance

# Edge case: if payment < interest, balance grows every month — infinite loop
if monthly_payment <= monthly_interest:
    return {"months": -1, ...}

while balance > 0:
    balance = balance * (1 + monthly_rate)  # interest accrues
    balance -= monthly_payment              # payment applied
    months += 1
    total_paid += monthly_payment

total_interest = total_paid - initial_balance
```

`total_interest = total_paid - initial_balance` — what you paid minus what you borrowed.
Everything on top of the principal is interest.

**Gotcha:** the last payment slightly overpays (balance goes a few cents negative).
`total_paid` is overstated by less than one payment. Acceptable for personal finance;
production apps would do `payment = min(monthly_payment, balance)` on the final month.

---

## Where each function lives

```
src/report.py           monthly_summary()         — groups + sums by month/category
                        debt_payoff_projection()  — months to payoff + interest cost
                        print_report()            — formats both to stdout
src/ingest.py           main()                    — calls print_report() after categorize loop
.env                    DEBT_BALANCE              — your current debt balance
                        DEBT_ANNUAL_RATE          — e.g. 0.19 for 19% APR
                        DEBT_MONTHLY_PAYMENT      — how much you pay per month
```

If debt vars are blank in `.env`, the debt section is skipped silently.

---

## Bugs caught in review

1. **`.update()` overwrites** — first attempt used `.update()` on existing date key, which
   replaced previous category amounts instead of summing them.
2. **No pending guard** — spec said skip `txn.pending == True`; missing from first draft.
3. **Double-divide by 100** — `annual_rate` is already a decimal (0.19, not 19).
   `monthly_interest / 100` made the edge case check nearly unreachable.
4. **`if` instead of `while`** — debt loop ran exactly once, not until payoff.
5. **`month` typo** — return used undefined `month` instead of `months`.
