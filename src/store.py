import os
from decimal import Decimal

import boto3
from dotenv import load_dotenv

from src.models import Transaction

load_dotenv()

_table = None


def _get_table():
    global _table
    if _table is None:
        dynamodb = boto3.resource(
            'dynamodb',
            region_name=os.getenv('AWS_DEFAULT_REGION'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        )
        _table = dynamodb.Table('Transactions')
    return _table


def to_dynamo_item(txn: Transaction) -> dict:
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


def save_transaction(txn: Transaction) -> None:
    _get_table().put_item(Item=to_dynamo_item(txn))


def save_transactions(txns: list[Transaction]) -> int:
    table = _get_table()
    with table.batch_writer() as batch:
        for txn in txns:
            batch.put_item(Item=to_dynamo_item(txn))
    return len(txns)
