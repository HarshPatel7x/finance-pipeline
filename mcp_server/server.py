"""One-tool MCP server over the finance-pipeline categorizer.

Local dev tooling: runs over stdio so an MCP client (e.g. Claude Code, via the
repo's .mcp.json) can call the pipeline's categorize() as a tool. Deliberately
small — one tool, no registry, no auth, no HTTP transport. This module never
ships in the Lambda bundle (deploy.sh packages only requirements.txt + src/).
"""
import sys
from datetime import date
from pathlib import Path
from typing import TypedDict

# The server may be spawned with any cwd (Claude Code uses the directory it was
# launched from), so anchor imports to the repo root rather than the cwd.
_REPO_ROOT = str(Path(__file__).resolve().parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from mcp.server.fastmcp import FastMCP  # noqa: E402

from src.categorize import categorize as _categorize  # noqa: E402
from src.models import Transaction  # noqa: E402

mcp = FastMCP("finance-pipeline")


class CategorizationOutput(TypedDict):
    """Typed result so FastMCP emits an output schema + structured content."""
    category: str
    source: str
    input_tokens: int
    output_tokens: int


@mcp.tool()
def categorize(
    name: str, merchant: str | None = None, amount: float = 0.0
) -> CategorizationOutput:
    """Categorize a financial transaction into one of the pipeline's categories.

    Runs the pipeline's real categorizer: keyword rules first (free), then the
    Claude Haiku fallback for anything the rules don't match. Without an
    Anthropic key the fallback degrades gracefully to category "Other".

    Args:
        name: The transaction description, e.g. "STARBUCKS #123".
        merchant: Optional cleaned merchant name, e.g. "Starbucks".
        amount: Transaction amount (positive = money out, Plaid convention).

    Returns:
        category: one of Food & Drink, Transportation, Shopping, Entertainment,
            Health, Income, Transfer, Other.
        source: "keyword" (rule hit) or "claude" (LLM fallback).
        input_tokens / output_tokens: Claude usage (0 on the keyword path).
    """
    # The pipeline's Transaction requires id/date/account fields that have no
    # meaning for an ad-hoc tool call — fill them with explicit placeholders.
    txn = Transaction(
        transaction_id="mcp-tool-call",
        date=date.today().isoformat(),
        name=name,
        amount=amount,
        account_id="mcp-tool-call",
        merchant_name=merchant,
    )
    result = _categorize(txn)
    return {
        "category": result.category,
        "source": result.source,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
    }


if __name__ == "__main__":
    mcp.run()  # stdio transport
