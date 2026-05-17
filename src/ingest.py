"""
Fetches transactions from Plaid (sandbox) or loads from local sample file.
Usage:
  python -m src.ingest              # Plaid sandbox (requires .env)
  python -m src.ingest --sample     # local sample_transactions.json (no credentials needed)
"""
import json
import os
import sys
import time
from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv

from src.categorize import categorize
from src.models import Transaction
from src.report import print_report
from src.store import save_transactions

load_dotenv()

DATA_DIR = Path(__file__).parent.parent / "data"
SAMPLE_FILE = DATA_DIR / "sample_transactions.json"


def load_sample() -> list[Transaction]:
    with open(SAMPLE_FILE) as f:
        rows = json.load(f)
    return [Transaction(**row) for row in rows]


def fetch_from_plaid() -> list[Transaction]:
    import plaid
    from plaid.api import plaid_api
    from plaid.model.country_code import CountryCode
    from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
    from plaid.model.products import Products
    from plaid.model.sandbox_public_token_create_request import SandboxPublicTokenCreateRequest
    from plaid.model.transactions_get_request import TransactionsGetRequest
    from plaid.model.transactions_refresh_request import TransactionsRefreshRequest

    client_id = os.getenv("PLAID_CLIENT_ID")
    secret = os.getenv("PLAID_SECRET")
    env = os.getenv("PLAID_ENV", "sandbox")

    if not client_id or not secret:
        print("ERROR: PLAID_CLIENT_ID and PLAID_SECRET must be set in .env")
        print("Tip: copy .env.example → .env and fill in your credentials.")
        sys.exit(1)

    host = {
        "sandbox": plaid.Environment.Sandbox,
        "production": plaid.Environment.Production,
    }.get(env, plaid.Environment.Sandbox)

    configuration = plaid.Configuration(
        host=host,
        api_key={"clientId": client_id, "secret": secret},
    )
    api_client = plaid.ApiClient(configuration)
    client = plaid_api.PlaidApi(api_client)

    # Sandbox: create a public token directly (bypasses Link UI)
    pt_request = SandboxPublicTokenCreateRequest(
        institution_id="ins_109508",  # Bank of America
        initial_products=[Products("transactions")],
    )
    pt_response = client.sandbox_public_token_create(pt_request)

    # Exchange public token for access token
    exchange_request = ItemPublicTokenExchangeRequest(
        public_token=pt_response["public_token"]
    )
    exchange_response = client.item_public_token_exchange(exchange_request)
    access_token = exchange_response["access_token"]

    # Sandbox: trigger transaction data generation, then wait for it to be ready
    client.transactions_refresh(TransactionsRefreshRequest(access_token=access_token))
    end = date.today()
    start = end - timedelta(days=30)
    tx_request = TransactionsGetRequest(
        access_token=access_token,
        start_date=start,
        end_date=end,
    )

    # Retry up to 3 times — sandbox data takes a moment to generate
    tx_response = None
    for attempt in range(3):
        try:
            tx_response = client.transactions_get(tx_request)
            break
        except Exception as e:
            if "PRODUCT_NOT_READY" in str(e) and attempt < 2:
                print(f"  Sandbox data not ready yet, retrying in 5s... ({attempt + 1}/3)")
                time.sleep(5)
            else:
                raise

    transactions = []
    for t in tx_response["transactions"]:
        transactions.append(
            Transaction(
                transaction_id=t["transaction_id"],
                date=str(t["date"]),
                name=t["name"],
                amount=t["amount"],
                account_id=t["account_id"],
                merchant_name=t.get("merchant_name"),
                category=t.get("category") or [],
                pending=t.get("pending", False),
            )
        )
    return transactions


def print_summary(transactions: list[Transaction]) -> None:
    if not transactions:
        print("No transactions found.")
        return

    dates = [t.date for t in transactions]
    debits = [t.amount for t in transactions if t.is_debit]
    credits = [abs(t.amount) for t in transactions if t.is_credit]

    print(f"\nLoaded {len(transactions)} transactions ({min(dates)} → {max(dates)})")
    print(f"Total debits:  ${sum(debits):>10.2f}")
    print(f"Total credits: ${sum(credits):>10.2f}")
    print(f"Net:           ${sum(credits) - sum(debits):>10.2f}")
    print()

    # Top 5 by amount
    top = sorted([t for t in transactions if t.is_debit], key=lambda t: t.amount, reverse=True)[:5]
    print("Top 5 expenses:")
    for t in top:
        name = t.merchant_name or t.name
        print(f"  {t.date}  {name:<30}  ${t.amount:.2f}")


def main() -> None:
    use_sample = "--sample" in sys.argv or not os.getenv("PLAID_CLIENT_ID")
    dry_run = "--no-save" in sys.argv

    if use_sample:
        print("Mode: local sample data")
        transactions = load_sample()
    else:
        print("Mode: Plaid sandbox")
        transactions = fetch_from_plaid()

    for txn in transactions:
        txn.category = [categorize(txn)]

    print_summary(transactions)

    debt_balance = float(os.getenv("DEBT_BALANCE") or 0)
    debt_rate = float(os.getenv("DEBT_ANNUAL_RATE") or 0)
    debt_payment = float(os.getenv("DEBT_MONTHLY_PAYMENT") or 0)
    print_report(
        transactions,
        debt_balance=debt_balance or None,
        debt_rate=debt_rate or None,
        debt_payment=debt_payment or None,
    )

    if dry_run:
        print("Skipping DynamoDB save (--no-save).")
    else:
        saved = save_transactions(transactions)
        print(f"Saved {saved} transactions to DynamoDB.")


if __name__ == "__main__":
    main()
