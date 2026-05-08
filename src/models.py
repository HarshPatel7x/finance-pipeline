from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Transaction:
    transaction_id: str
    date: str                        # ISO format: YYYY-MM-DD
    name: str                        # merchant name (Plaid-cleaned)
    amount: float                    # positive = money out, negative = money in (Plaid convention)
    account_id: str
    merchant_name: Optional[str] = None
    category: list[str] = field(default_factory=list)
    pending: bool = False

    @property
    def is_debit(self) -> bool:
        return self.amount > 0

    @property
    def is_credit(self) -> bool:
        return self.amount < 0
