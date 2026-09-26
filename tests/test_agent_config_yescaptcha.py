# -*- coding: utf-8 -*-
import pytest
from pydantic import ValidationError

from hcaptcha_challenger.agent.config import AgentConfig


def test_agent_config_default_provider_requires_gemini_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("YESCAPTCHA_CLIENT_KEY", raising=False)

    with pytest.raises(ValidationError) as exc_info:
        AgentConfig(_env_file=None, REASONING_PROVIDER="gemini", GEMINI_API_KEY="")
    assert "GEMINI_API_KEY is required" in str(exc_info.value)


def test_agent_config_yescaptcha_provider_requires_yescaptcha_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("YESCAPTCHA_CLIENT_KEY", raising=False)

    with pytest.raises(ValidationError) as exc_info:
        AgentConfig(_env_file=None, REASONING_PROVIDER="yescaptcha", YESCAPTCHA_CLIENT_KEY="")
    assert "YESCAPTCHA_CLIENT_KEY is required" in str(exc_info.value)


def test_agent_config_yescaptcha_valid(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    config = AgentConfig(
        _env_file=None,
        REASONING_PROVIDER="yescaptcha",
        YESCAPTCHA_CLIENT_KEY="test_yescaptcha_key_12345",
    )
    assert config.REASONING_PROVIDER == "yescaptcha"
    assert config.YESCAPTCHA_CLIENT_KEY.get_secret_value() == "test_yescaptcha_key_12345"
    # Ensure secret is masked in repr/str
    assert "test_yescaptcha_key_12345" not in repr(config.YESCAPTCHA_CLIENT_KEY)
    assert "test_yescaptcha_key_12345" not in str(config.YESCAPTCHA_CLIENT_KEY)


def test_agent_config_invalid_provider():
    with pytest.raises(ValidationError):
        AgentConfig(_env_file=None, REASONING_PROVIDER="invalid_provider")
