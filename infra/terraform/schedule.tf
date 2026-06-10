# EventBridge (CloudWatch Events) daily schedule — adopted (imported) from deploy.sh.
# This is the serverless scheduling layer Terraform fully manages.
resource "aws_cloudwatch_event_rule" "daily" {
  name                = "finance-pipeline-daily"
  schedule_expression = "rate(1 day)"
  state               = "ENABLED"

  lifecycle {
    prevent_destroy = true # protect the live daily pipeline from accidental teardown
  }
}

resource "aws_cloudwatch_event_target" "lambda" {
  rule      = aws_cloudwatch_event_rule.daily.name
  target_id = "1"
  arn       = aws_lambda_function.finance_pipeline.arn

  lifecycle {
    # A -target'd destroy of just this would silently stop the daily run (rule fires,
    # nothing invoked) without tripping the rule's own guard. Protect it too.
    prevent_destroy = true
  }
}

# Lets EventBridge invoke the Lambda — adopted from deploy.sh's add-permission call.
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "finance-pipeline-schedule"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.finance_pipeline.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily.arn

  lifecycle {
    prevent_destroy = true # removing this would revoke EventBridge's invoke rights
  }
}
