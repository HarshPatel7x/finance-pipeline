# Week 2 — DynamoDB / boto3

## The put_item pattern

```python
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('Transactions')

table.put_item(Item={
    'transaction_id': 'txn_abc123',  # partition key — must always be present
    'date': '2026-05-08',
    'name': 'Whole Foods Market',
    'amount': Decimal('45.67'),      # NOT float — always Decimal(str(value))
})
```

Three steps: `boto3.resource` connects to AWS → `.Table(...)` points at the table →
`.put_item(Item={...})` writes. If item exists, it is **fully replaced** — not merged.

## to_dynamo_item — Transaction dataclass → DynamoDB dict

```python
def to_dynamo_item(txn):
    item = {
        'transaction_id': txn.transaction_id,
        'date': txn.date,
        'name': txn.name,
        'amount': Decimal(str(txn.amount)),
        'account_id': txn.account_id,
        'category': txn.category,
        'pending': txn.pending,
    }
    if txn.merchant_name is not None:
        item['merchant_name'] = txn.merchant_name
    return item
```

## What is boto3 and import os

**boto3** is Amazon's official Python library for talking to AWS. Any time Python needs to
read from or write to DynamoDB, S3, etc., it goes through boto3. Without it you'd be writing
raw HTTPS requests yourself.

**`import os`** gives access to the operating system's environment variables.
`os.getenv('AWS_ACCESS_KEY_ID')` reads the value from `.env` (loaded by `load_dotenv()`
one line earlier). Credentials never get hardcoded into source code — they live in `.env`.

## What boto3.resource('dynamodb') returns

`boto3.resource('dynamodb')` returns a `DynamoDB.ServiceResource` — a Python-friendly
handle to your AWS DynamoDB account. From it, `.Table('Transactions')` gives you a handle
to a specific table. This is the **high-level interface** (works with Python objects).

The alternative is `boto3.client('dynamodb')` — lower-level, raw JSON, more verbose.
Always prefer `.resource` for application code.

## batch_writer — bulk writes

```python
with table.batch_writer() as batch:
    for txn in txns:
        batch.put_item(Item=to_dynamo_item(txn))
return len(txns)
```

`batch_writer()` is like a shopping cart — you add items inside the `with` block, and
when the block closes boto3 automatically sends them to DynamoDB in chunks of 25.
Much faster than calling `put_item` once per transaction (16 calls → 1 batch).

## Gotchas

**1 — float vs Decimal (critical)**
DynamoDB rejects Python `float`. Always wrap: `Decimal(str(txn.amount))`.
Never `Decimal(45.67)` — floating point precision corrupts the value.

**2 — None values (critical)**
DynamoDB rejects `None` as an attribute value. Optional fields must be
conditionally added:
```python
if txn.merchant_name is not None:
    item['merchant_name'] = txn.merchant_name
```
Passing `None` directly throws at runtime.

**3 — Pylance false positive on `.Table()`**
Pylance shows "Cannot access attribute 'Table'" on `dynamodb.Table('Transactions')`.
This is a false positive — boto3 builds its API dynamically at runtime so Pylance can't
infer the return type of `boto3.resource()`. The code runs correctly. Fix:
```
python3 -m pip install 'boto3-stubs[dynamodb]'
```
Add `boto3-stubs[dynamodb]` to requirements.txt. Gives Pylance real type info for DynamoDB.

**4 — Shadowing built-ins (style)**
Never name a variable `dict`, `list`, `str`, `int`, or `bool` — these are
Python built-ins. Using them as variable names hides the built-in within
that scope. Use `item`, `record`, `result` instead.
