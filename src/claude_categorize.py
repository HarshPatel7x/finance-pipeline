from anthropic import Anthropic

from src.models import Transaction, CategorizationResult
from src.secrets import resolve_secret

ANTHROPIC_API_KEY_SSM = "/finance-pipeline/anthropic_api_key"

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
    # Cache only on SUCCESS: a container that started before the SSM parameter
    # existed will re-resolve and self-heal on its next call, rather than caching
    # the failure for the container's lifetime. (One SSM read per container when
    # healthy; cheap repeated reads only while genuinely degraded.)
    global _client
    if _client is not None:
        return _client
    key = resolve_secret("ANTHROPIC_API_KEY", ANTHROPIC_API_KEY_SSM)
    if not key:
        return None
    try:
        _client = Anthropic(api_key=key)
        return _client
    except Exception:
        return None


def classify(txn: Transaction) -> CategorizationResult:
    """LLM fallback categorizer. Always reports source='claude'; token counts
    are 0 when the API key is missing or the call fails (degrades to 'Other')."""
    client = _get_client()
    if client is None:
        return CategorizationResult(category="Other", source="claude")
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
        category = text if text in _ALLOWED else "Other"
        return CategorizationResult(
            category=category,
            source="claude",
            input_tokens=resp.usage.input_tokens,
            output_tokens=resp.usage.output_tokens,
        )
    except Exception:
        return CategorizationResult(category="Other", source="claude")
