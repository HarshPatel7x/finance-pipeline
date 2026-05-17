"""
Report generation: monthly spending summary + debt payoff projection.
Usage: called from ingest.main() after transactions are categorized.
"""
import os
from src.models import Transaction


def monthly_summary(transactions: list[Transaction]) -> dict[str, dict[str, float]]:
    """
    Returns: { "YYYY-MM": { "Food & Drink": 45.20, "Transportation": 12.00, ... } }
    Groups by month then category, summing amounts. Skips pending transactions.
    """
    summary_obj = {}
    for txn in transactions:
        date = txn.date[:7]
        category = txn.category[0]
        amount = txn.amount

        if not txn.pending:
            if date not in summary_obj:
                summary_obj[date] = {category: amount}
            else:
                summary_obj[date][category] = summary_obj[date].get(category, 0) + amount

    return summary_obj


def debt_payoff_projection(
    balance: float,
    annual_rate: float,   # e.g. 0.19 for 19% APR
    monthly_payment: float,
) -> dict:
    """
    Returns: { "months": int, "total_paid": float, "total_interest": float }
    months == -1 means payment doesn't cover interest — balance grows forever.
    """
    monthly_rate = annual_rate / 12
    monthly_interest = monthly_rate * balance

    if monthly_payment <= monthly_interest:
        return {"months": -1, "total_paid": 0, "total_interest": 0}

    initial_balance = balance
    total_paid = 0
    months = 0

    while balance > 0:
        balance = balance * (1 + monthly_rate)
        balance -= monthly_payment
        months += 1
        total_paid += monthly_payment

    total_interest = total_paid - initial_balance

    return {
        "months": months,
        "total_paid": round(total_paid, 2),
        "total_interest": round(total_interest, 2),
    }


def print_report(
    transactions: list[Transaction],
    debt_balance: float | None = None,
    debt_rate: float | None = None,
    debt_payment: float | None = None,
) -> None:
    summary = monthly_summary(transactions)

    print("\n" + "=" * 52)
    print("  MONTHLY SPENDING SUMMARY")
    print("=" * 52)

    for month in sorted(summary.keys()):
        cats = summary[month]
        spending = sum(v for cat, v in cats.items() if cat != "Income")
        income = abs(sum(v for cat, v in cats.items() if cat == "Income"))
        print(f"\n{month}  |  spent ${spending:.2f}  |  income ${income:.2f}")
        for cat, amount in sorted(cats.items(), key=lambda x: -x[1]):
            bar = "█" * max(1, int(amount / 10))
            print(f"  {cat:<20}  ${amount:>8.2f}  {bar}")

    if debt_balance and debt_rate and debt_payment:
        print("\n" + "=" * 52)
        print("  DEBT PAYOFF PROJECTION")
        print("=" * 52)
        result = debt_payoff_projection(debt_balance, debt_rate, debt_payment)
        if result["months"] == -1:
            min_payment = debt_balance * debt_rate / 12
            print(f"\n  ⚠  Payment ${debt_payment:.2f}/mo doesn't cover interest.")
            print(f"     At {debt_rate*100:.1f}% APR you need > ${min_payment:.2f}/mo to make progress.")
        else:
            years, mos = divmod(result["months"], 12)
            time_str = f"{years}y {mos}mo" if years else f"{mos}mo"
            print(f"\n  Balance:         ${debt_balance:>10.2f}")
            print(f"  APR:             {debt_rate * 100:>9.1f}%")
            print(f"  Monthly payment: ${debt_payment:>10.2f}")
            print(f"  Payoff time:     {time_str:>10}")
            print(f"  Total paid:      ${result['total_paid']:>10.2f}")
            print(f"  Total interest:  ${result['total_interest']:>10.2f}")
