# Lambda — adopted (imported) from the bash-deployed stack (deploy.sh).
#
# Terraform manages the function's CONFIGURATION (runtime, memory, timeout, handler, role,
# logging). The code artifact and the secret environment variables are deliberately NOT
# managed here: deploy.sh ships code out-of-band, and the env holds PLAID_SECRET. Both are
# excluded via ignore_changes so Terraform never overwrites live code or pulls secrets into
# the plan. `filename` points at a committed placeholder only to satisfy the schema.
resource "aws_lambda_function" "finance_pipeline" {
  function_name = var.function_name
  role          = data.aws_iam_role.lambda.arn
  handler       = "src.lambda_function.lambda_handler"
  runtime       = "python3.12"
  architectures = ["x86_64"]
  memory_size   = 256
  timeout       = 300
  package_type  = "Zip"

  filename = "${path.module}/dummy.zip" # placeholder; real code via deploy.sh (ignored below)

  ephemeral_storage {
    size = 512
  }

  logging_config {
    log_format = "Text"
    log_group  = "/aws/lambda/${var.function_name}"
  }

  tracing_config {
    mode = "PassThrough"
  }

  lifecycle {
    # Code + secrets are owned by deploy.sh / AWS, not Terraform.
    ignore_changes = [
      filename,
      source_code_hash,
      environment,
      layers,
    ]
    prevent_destroy = true
  }
}
