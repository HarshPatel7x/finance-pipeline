import os

from anthropic import Anthropic

from src.models import Transaction

_MODEL = "claude-haiku-4-5-20251001"
_ALLOWED = {
    "Food & Drink", "Transportation", "Shopping", "Entertainment",
    "Health", "Income", "Transfer", "Other",
}
_PROMPT_TEMPLATE = (
    "Transaction: {name} | merchant: {merchant} | amount: {amount}\n"
    "Pick ONE category from this exact list: "
    "Food & Drink, Transportation, Shopping, Entertainment, Health, Income, Transfer, Other.\n"
    "Reply with the category name only, no punctuation, no explanation."
)

_client: Anthropic | None = None


def _get_client() -> Anthropic | None:
    global _client
    if _client is not None:
        return _client
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        return None
    try:
        _client = Anthropic(api_key=key)
        return _client
    except Exception:
        return None


def classify(txn: Transaction) -> str:
    client = _get_client()
    if client is None:
        return "Other"
    prompt = _PROMPT_TEMPLATE.format(
        name=txn.name,
        merchant=txn.merchant_name or "n/a",
        amount=txn.amount,
    )
    try:
        resp = client.messages.create(
            model=_MODEL,
            max_tokens=20,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp.content[0].text.strip()
        return text if text in _ALLOWED else "Other"
    except Exception:
        return "Other"
