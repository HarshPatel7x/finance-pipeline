terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source = "hashicorp/aws"
      # Pinned tight: a stray `init -upgrade` to a newer 5.x can surface new computed
      # defaults and dirty the clean plan. Bump deliberately, not incidentally.
      version = "~> 5.100"
    }
  }

  # Remote state in S3. State holds the imported Lambda's environment (which includes
  # PLAID_SECRET), so the bucket is encrypted (SSE-AES256) and access is locked down.
  # use_lockfile = S3-native state locking (Terraform >= 1.10) — no DynamoDB lock table needed.
  backend "s3" {
    bucket       = "finance-pipeline-tfstate-477913828854"
    key          = "finance-pipeline/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}
