# Week 3 — AWS Lambda + CloudWatch schedule

## The lambda_handler pattern

```python
from src.ingest import main

def lambda_handler(event, context):
    try:
        main()
        print("Success in lambda_handler.")
        return {"statusCode": 200}
    except Exception as e:
        print(f"Error in lambda_handler: {e}")
        return {"statusCode": 500, "body": str(e)}
```

AWS Lambda requires one entry-point function with this exact signature:
`lambda_handler(event, context)`

- `event` — a dict AWS passes in when the function is triggered (CloudWatch schedule sends an empty-ish dict; you're not using it here)
- `context` — AWS runtime info (remaining time, function name, etc.). Not used here either.
- **Return value** — Lambda expects a dict with `statusCode`. `200` = success, `500` = error. CloudWatch logs both outcomes.

The function itself does one thing: call `main()` from `ingest.py`. That's the whole pipeline — fetch from Plaid, categorize, store to DynamoDB. Lambda is just the trigger wrapper.

**Why `print()` instead of a logger?**
`print()` in Lambda automatically goes to CloudWatch Logs. You don't need to set up logging — Lambda captures stdout for you.

---

## deploy.sh — what it does in order

```bash
# 1. Package
rm -rf package lambda.zip
pip3 install -r requirements.txt -t package/   # install deps INTO package/
cp -r src/ package/src/                         # copy your code into package/
cd package && zip -r ../lambda.zip .            # zip everything

# 2. Create or update Lambda
aws lambda update-function-code --zip-file fileb://lambda.zip ...
# (or create-function if it doesn't exist yet)

# 3. CloudWatch daily schedule
aws events put-rule --schedule-expression "rate(1 day)" ...
aws events put-targets --rule finance-pipeline-daily --targets ...
```

**Step 1 — why `-t package/`:**
Normally `pip install` puts packages in your system Python. `-t package/` tells pip to install INTO the `package/` folder instead. When you zip that folder, the Lambda runtime can find the packages next to your code. Without this, Lambda would throw `ModuleNotFoundError` for `plaid`, `boto3`, etc.

**Step 2 — create vs update:**
The script checks if the Lambda already exists (`get-function`). If yes: update the code. If no: create it from scratch. This means you can run `./deploy.sh` repeatedly — it's idempotent.

**Step 3 — CloudWatch rule:**
`rate(1 day)` = run once every 24 hours. `aws events put-targets` wires the rule to your Lambda function — "when this rule fires, invoke THIS Lambda." The `add-permission` call lets EventBridge (the AWS service running CloudWatch rules) actually trigger Lambda — without it, the rule fires but Lambda ignores it.

---

## IAM role — why it exists

Lambda runs as an IAM role (`finance-pipeline-lambda-role`). The role has permissions for:
- **DynamoDB write** — so `store.py` can call `put_item`/`batch_writer`
- **CloudWatch Logs** — so Lambda can write log output
- **Plaid** — Plaid is an external API over HTTPS, no IAM needed

Without the role, `boto3.resource('dynamodb')` would throw an access denied error at runtime. IAM is how AWS answers "who is allowed to do what."

The role ARN is hardcoded in `deploy.sh`:
```
ROLE_ARN="arn:aws:iam::477913828854:role/finance-pipeline-lambda-role"
```
That number (`477913828854`) is your AWS account ID — unique to your account.

---

## Handler string — how AWS finds your code

```
HANDLER="src.lambda_function.lambda_handler"
```

AWS uses dot notation: `module.path.function_name`. This maps to `src/lambda_function.py`, function `lambda_handler`. If you renamed the file or function, you'd update this string.

---

## Timeout and memory

```
--timeout 300       # 5 minutes max
--memory-size 256   # 256 MB RAM
```

Lambda kills the function if it runs longer than `timeout`. 5 minutes is generous for fetching 16 transactions, categorizing, and writing to DynamoDB — should finish in under 30 seconds in practice.

Memory affects both RAM and CPU allocation in Lambda. 256 MB is plenty for this pipeline.

---

## Gotchas

**1 — package/ is .gitignored**
`package/` and `lambda.zip` are build artifacts — they're excluded from git. Run `./deploy.sh` to rebuild them. If you clone a fresh copy, `package/` won't exist until you run the script.

**2 — macOS build → Linux runtime mismatch**
`pip3 install -t package/` on macOS installs macOS-specific wheels. Lambda runs on Linux x86_64. For pure-Python packages (boto3, plaid-python) this is fine — no compiled code. For packages with Rust/C extensions (`anthropic`'s `pydantic_core`), the macOS wheel won't run on Linux. Fix:
```bash
pip3 install --platform manylinux2014_x86_64 --only-binary=:all: -t package/ anthropic
```

**3 — `set -e` at the top of deploy.sh**
Any command that fails causes the script to exit immediately. If `aws lambda update-function-code` fails (e.g., wrong credentials), the CloudWatch step never runs. Intentional — you don't want a partial deploy.

**4 — Plaid sandbox vs production**
Lambda reads `PLAID_ENV` from its environment variables. Make sure it's set in the Lambda console to match what you want (`sandbox` for testing, `production` for real BofA data).
