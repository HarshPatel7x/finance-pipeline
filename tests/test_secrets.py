"""Tests for the shared secret resolver and the self-healing Anthropic client."""
from unittest import mock

import src.claude_categorize as cc
import src.secrets as secrets


def test_resolve_secret_env_first(monkeypatch):
    monkeypatch.setenv("MY_SECRET", "from-env")
    # When the env var is set, SSM is never consulted.
    assert secrets.resolve_secret("MY_SECRET", "/finance-pipeline/whatever") == "from-env"


def test_resolve_secret_ssm_fallback(monkeypatch):
    monkeypatch.delenv("MY_SECRET", raising=False)
    fake_ssm = mock.Mock()
    fake_ssm.get_parameter.return_value = {"Parameter": {"Value": "from-ssm"}}
    fake_boto3 = mock.Mock()
    fake_boto3.client.return_value = fake_ssm
    with mock.patch.dict("sys.modules", {"boto3": fake_boto3}):
        assert secrets.resolve_secret("MY_SECRET", "/x/y") == "from-ssm"
    fake_ssm.get_parameter.assert_called_once_with(Name="/x/y", WithDecryption=True)


def test_resolve_secret_degrades_to_none(monkeypatch):
    monkeypatch.delenv("MY_SECRET", raising=False)
    fake_boto3 = mock.Mock()
    fake_boto3.client.side_effect = Exception("no creds")
    with mock.patch.dict("sys.modules", {"boto3": fake_boto3}):
        # An unreadable parameter degrades to None instead of raising.
        assert secrets.resolve_secret("MY_SECRET", "/x/y") is None


def test_get_client_self_heals(monkeypatch):
    # Regression guard for the sticky-failure bug: a container that starts with
    # no key must NOT cache the failure for its lifetime.
    cc._client = None
    monkeypatch.setattr(cc, "resolve_secret", lambda *a, **k: None)
    assert cc._get_client() is None
    assert cc._client is None  # failure not cached

    # Once the parameter/role grant are in place, the next call self-heals.
    monkeypatch.setattr(cc, "resolve_secret", lambda *a, **k: "sk-test")
    monkeypatch.setattr(cc, "Anthropic", lambda api_key=None: "CLIENT")
    assert cc._get_client() == "CLIENT"
    assert cc._client == "CLIENT"  # success cached
    cc._client = None  # reset module global for other tests
