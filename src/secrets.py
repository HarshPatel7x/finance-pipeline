"""Shared secret resolution: environment-first, then AWS SSM Parameter Store.

Local dev sets secrets in .env. The deployed Lambda has no such env vars and reads
SecureString parameters from SSM via its execution role -- so secrets never live in
the function configuration or in Terraform state.
"""
import os


def resolve_secret(env_var: str, ssm_name: str) -> str | None:
    """Return a secret from the environment if set, else from SSM (SecureString).

    Degrades to None (with a clear log line) rather than raising, so a missing or
    unreadable parameter never crashes the caller with an opaque boto error.
    """
    value = os.getenv(env_var)
    if value:
        return value
    try:
        import boto3

        ssm = boto3.client("ssm", region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
        return ssm.get_parameter(Name=ssm_name, WithDecryption=True)["Parameter"]["Value"]
    except Exception as e:
        print(f"WARN: could not load {env_var} from SSM ({ssm_name}): {e}")
        return None
