# infra/terraform — Infrastructure as Code for finance-pipeline

This module brings the finance-pipeline's already-running AWS infrastructure under Terraform.

The stack was originally stood up by [`deploy.sh`](../../deploy.sh) (imperative AWS CLI calls).
This module **adopts** that live infrastructure into Terraform (brownfield import) and adds one
genuinely new managed change — log retention — without disturbing the daily pipeline.

## What Terraform manages here

| Resource | How | Notes |
|----------|-----|-------|
| `aws_lambda_function.finance_pipeline` | **imported** | Config only (runtime, memory, timeout, handler, role, logging). Code + secret env are `ignore_changes` — owned by `deploy.sh`. |
| `aws_cloudwatch_event_rule.daily` | **imported** | `rate(1 day)` schedule. `prevent_destroy`. |
| `aws_cloudwatch_event_target.lambda` | **imported** | Wires the rule to the Lambda. |
| `aws_lambda_permission.allow_eventbridge` | **imported** | Lets EventBridge invoke the Lambda. |
| `aws_cloudwatch_log_group.lambda` | **imported + changed** | Applies **14-day retention** (was: never expire). The real `apply`. |
| `aws_iam_role.lambda` | `data` (read-only) | The principal is read-only on IAM; the role is referenced, not managed. |
| `aws_dynamodb_table.transactions` | `data` (read-only) | Upstream dependency, out of scope to manage. |

## State

- **Backend:** S3 (`finance-pipeline-tfstate-477913828854`, key `finance-pipeline/terraform.tfstate`).
  The backend sets `encrypt = true`, so Terraform writes the state object SSE-encrypted — this is
  verifiable from the config. Bucket-level default encryption (AES256), versioning, and
  public-access-block were configured at bucket creation, but the least-privilege
  `finance-pipeline-dev` principal is intentionally **denied** `s3:GetEncryptionConfiguration` /
  `GetBucketVersioning`, so they aren't re-readable from here — verify from an admin identity if needed.
- **Locking:** S3-native (`use_lockfile = true`, Terraform ≥ 1.10) — no DynamoDB lock table.
- **Why state is sensitive:** importing the Lambda pulled its environment into state. `PLAID_SECRET`
  has since been moved to SSM (see **Secrets** below), removed from the Lambda env, and scrubbed from
  current state via `terraform apply -refresh-only`. The object is still written encrypted
  (`encrypt = true`) and `*.tfstate` gitignored as a precaution (older state versions may retain
  rotated/dead values).

## Drift handling

`deploy.sh` still ships Lambda **code** out-of-band (`update-function-code`) on every deploy. So the
function's code hash legitimately changes outside Terraform. `ignore_changes = [filename,
source_code_hash, environment, layers]` tells Terraform not to fight that — it manages configuration,
not the code artifact or secrets. Run `terraform plan` any time to detect drift on the parts Terraform
*does* own.

## Usage

```bash
cd infra/terraform
terraform init      # configures the S3 backend
terraform plan      # adopted resources show "No changes"; log group shows retention 14
terraform apply     # applies the log-retention change
```

Auth: the local `finance-pipeline-dev` IAM user (full Lambda/EventBridge/DynamoDB, read-only IAM,
S3 read/write on the state bucket only). In a team/prod setup this would be OIDC role-assumption in
CI rather than a long-lived user — not wired here (solo project).

## Secrets (managed out-of-band)

Both runtime secrets are **SSM Parameter Store SecureString** params, read by the Lambda at runtime
via its execution role (env-first, SSM fallback — see `src/secrets.py`):

| Parameter | Used by |
|-----------|---------|
| `/finance-pipeline/plaid_secret` | `src/ingest.py` (Plaid auth) |
| `/finance-pipeline/anthropic_api_key` | `src/claude_categorize.py` (Claude) |

The params and the `finance-pipeline-ssm-read` inline policy on the Lambda role (scoped to exactly
those two ARNs, `ssm:GetParameter` only) are created **out-of-band by an admin** — deliberately NOT
managed by this module. The `finance-pipeline-dev` principal is read-only on IAM and lacks
`ssm:PutParameter`, so managing them here would force IAM/SSM writes it can't make and turn a clean
plan into a denied apply (same reason the role is a read-only `data` source).

**A fresh deploy must recreate them** (admin identity):

```bash
aws ssm put-parameter --name /finance-pipeline/plaid_secret      --type SecureString --key-id alias/aws/ssm --value '<PLAID_SECRET>'      --region us-east-1
aws ssm put-parameter --name /finance-pipeline/anthropic_api_key --type SecureString --key-id alias/aws/ssm --value '<ANTHROPIC_API_KEY>' --region us-east-1
aws iam put-role-policy --role-name finance-pipeline-lambda-role --policy-name finance-pipeline-ssm-read \
  --policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"ssm:GetParameter","Resource":["arn:aws:ssm:us-east-1:477913828854:parameter/finance-pipeline/plaid_secret","arn:aws:ssm:us-east-1:477913828854:parameter/finance-pipeline/anthropic_api_key"]}]}'
```

Without these the Lambda degrades: Plaid auth fails (run errors) and Claude falls back to keyword-only.

## What I'd improve next

- Add a CI plan check via OIDC so drift is caught on every PR.
