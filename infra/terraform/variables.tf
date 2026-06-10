variable "region" {
  description = "AWS region for the finance-pipeline infrastructure"
  type        = string
  default     = "us-east-1"
}

variable "function_name" {
  description = "Name of the existing finance-pipeline Lambda function"
  type        = string
  default     = "finance-pipeline"
}

variable "log_retention_days" {
  description = "CloudWatch retention for the Lambda log group (was unset = never expire)"
  type        = number
  default     = 14
}
