"""
Tests for the Pydantic Settings configuration.
"""

from __future__ import annotations

import os

import pytest

from direktor.core.settings import Settings, get_settings, reset_settings


def test_settings_loads_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings should load required values from environment variables."""
    monkeypatch.setenv("REPLICATE_API_TOKEN", "r-token")
    monkeypatch.setenv("OPENAI_API_KEY", "o-token")
    monkeypatch.setenv("DISTIL_MODEL", "distil")
    monkeypatch.setenv("BARK_MODEL", "bark")
    monkeypatch.setenv("FLUX_MODEL", "flux")
    monkeypatch.setenv("GPT4_MODEL", "gpt-4o")

    settings = get_settings()
    assert settings.replicate_api_token == "r-token"
    assert settings.openai_api_key == "o-token"
    assert settings.gpt4_model == "gpt-4o"
    assert settings.gpt4_max_tokens == 8000


def test_settings_validates_missing_vars() -> None:
    """Missing required settings should raise a clear error."""
    settings = Settings(  # type: ignore[call-arg]
        replicate_api_token="x",
        openai_api_key="x",
        distil_model="x",
        bark_model="",
        flux_model="x",
        gpt4_model="x",
    )
    with pytest.raises(ValueError, match="Missing required environment variables"):
        settings.ensure_valid()


def test_settings_log_level_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Invalid log levels should be rejected."""
    monkeypatch.setenv("REPLICATE_API_TOKEN", "r-token")
    monkeypatch.setenv("OPENAI_API_KEY", "o-token")
    monkeypatch.setenv("DISTIL_MODEL", "distil")
    monkeypatch.setenv("BARK_MODEL", "bark")
    monkeypatch.setenv("FLUX_MODEL", "flux")
    monkeypatch.setenv("GPT4_MODEL", "gpt-4o")
    monkeypatch.setenv("LOG_LEVEL", "invalid")

    reset_settings()
    with pytest.raises(ValueError, match="Invalid log level"):
        get_settings()


def test_replicate_token_propagated_to_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_settings should set REPLICATE_API_TOKEN in the environment."""
    monkeypatch.setenv("OPENAI_API_KEY", "o-token")
    monkeypatch.setenv("DISTIL_MODEL", "distil")
    monkeypatch.setenv("BARK_MODEL", "bark")
    monkeypatch.setenv("FLUX_MODEL", "flux")
    monkeypatch.setenv("GPT4_MODEL", "gpt-4o")
    monkeypatch.setenv("REPLICATE_API_TOKEN", "r-token")

    reset_settings()
    settings = get_settings()
    assert os.environ.get("REPLICATE_API_TOKEN") == settings.replicate_api_token
