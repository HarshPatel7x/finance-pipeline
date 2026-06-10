output "lambda_function_arn" {
  description = "ARN of the adopted Lambda function"
  value       = aws_lambda_function.finance_pipeline.arn
}

output "schedule_rule_arn" {
  description = "ARN of the daily EventBridge rule"
  value       = aws_cloudwatch_event_rule.daily.arn
}

output "log_group_name" {
  description = "Lambda log group now managed by Terraform"
  value       = aws_cloudwatch_log_group.lambda.name
}

output "log_retention_days" {
  description = "Retention Terraform applied to the Lambda log group"
  value       = aws_cloudwatch_log_group.lambda.retention_in_days
}

output "execution_role_arn" {
  description = "ARN of the (read-only referenced) Lambda execution role"
  value       = data.aws_iam_role.lambda.arn
}
