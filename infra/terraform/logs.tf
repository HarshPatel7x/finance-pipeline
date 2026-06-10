# Lambda log group.
#
# The group existed with NO retention set (logs never expire — a real cost/compliance
# smell). Terraform adopts it and applies a 14-day retention policy. This is the genuine,
# demonstrable `terraform apply` change in this module: a real config change to live infra
# that Terraform now owns end-to-end (it can recreate the group from zero).
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = var.log_retention_days
}
