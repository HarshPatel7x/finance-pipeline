from src.claude_categorize import classify as _claude_classify
from src.models import Transaction, CategorizationResult

_RULES: list[tuple[str, list[str]]] = [
    ("Food & Drink",    ["restaurant", "cafe", "coffee", "mcdonald", "starbucks", "chipotle",
                         "pizza", "sushi", "doordash", "ubereats", "grubhub", "whole foods",
                         "trader joe", "grocery", "market"]),
    ("Transportation",  ["uber", "lyft", "taxi", "transit", "parking", "gas station",
                         "shell", "chevron", "bp ", "exxon", "airline", "delta", "united"]),
    ("Shopping",        ["amazon", "walmart", "target", "costco", "bestbuy", "best buy",
                         "apple store", "nike", "zara", "h&m"]),
    ("Entertainment",   ["netflix", "spotify", "hulu", "disney", "cinema", "theater",
                         "ticketmaster", "steam", "playstation"]),
    ("Health",          ["pharmacy", "cvs", "walgreens", "doctor", "dental", "hospital",
                         "clinic", "gym", "fitness"]),
    ("Income",          ["payroll", "direct deposit", "salary", "venmo credit", "zelle credit"]),
    ("Transfer",        ["transfer", "zelle", "venmo", "paypal", "wire"]),
]


def categorize(txn: Transaction) -> CategorizationResult:
    text = f"{txn.name} {txn.merchant_name or ''}".lower()
    for category, keywords in _RULES:
        if any(kw in text for kw in keywords):
            return CategorizationResult(category=category, source="keyword")
    # no keyword rule matched → LLM fallback (classify() owns source + tokens)
    return _claude_classify(txn)
