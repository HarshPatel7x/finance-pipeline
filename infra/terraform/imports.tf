# Config-driven import blocks (Terraform >= 1.5).
#
# These adopt the already-running, bash-deployed infrastructure into Terraform state.
# Goal: after init, `terraform plan` shows NO changes for the four adopted resources
# (proof of faithful adoption) and exactly ONE change for the log group (retention 14d).
#
# Import blocks are inert once a resource is in state, but are kept here as documentation
# of how the brownfield adoption was performed.

import {
  to = aws_lambda_function.finance_pipeline
  id = "finance-pipeline"
}

import {
  to = aws_cloudwatch_event_rule.daily
  id = "finance-pipeline-daily"
}

import {
  to = aws_cloudwatch_event_target.lambda
  id = "finance-pipeline-daily/1"
}

import {
  to = aws_lambda_permission.allow_eventbridge
  id = "finance-pipeline/finance-pipeline-schedule"
}

import {
  to = aws_cloudwatch_log_group.lambda
  id = "/aws/lambda/finance-pipeline"
}
