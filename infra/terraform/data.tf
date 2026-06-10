# Read-only references.
#
# The Terraform principal (IAM user finance-pipeline-dev) is intentionally read-only on
# IAM, so the execution role is ADOPTED as a data source rather than a managed resource.
# Any drift on a managed IAM resource would turn a clean plan into a denied apply — using
# a data source is both safer and honest about what Terraform actually owns here.
data "aws_iam_role" "lambda" {
  name = "finance-pipeline-lambda-role"
}

# The Transactions table is an upstream dependency created out-of-band; not this module's
# job to manage. Referenced read-only so its ARN is available if needed.
data "aws_dynamodb_table" "transactions" {
  name = "Transactions"
}

data "aws_caller_identity" "current" {}
