"""
Application settings for Direktor.

Uses Pydantic Settings to load configuration from environment variables and
``.env`` files with validation, type coercion, and lazy initialization.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from openai import OpenAI
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from tiktoken import encoding_for_model
from tiktoken.core import Encoding


class Settings(BaseSettings):
    """Centralized, validated settings for the Direktor pipeline."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API tokens
    replicate_api_token: str
    openai_api_key: str

    # Model identifiers
    distil_model: str
    bark_model: str
    flux_model: str
    gpt4_model: str = "gpt-4o"
    gpt4_max_tokens: int = 8000

    # S3-compatible storage (R2/Backblaze/etc.)
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_endpoint_url: str | None = None
    aws_bucket_name: str | None = None
    aws_region_name: str = "auto"

    # Processing behavior
    temp_dir_base: str = "temp"
    max_chunk_chars: int = 150
    target_segment_duration: int = 30

    # Logging
    log_level: str = "INFO"

    @field_validator("log_level")
    @classmethod
    def _validate_log_level(cls, value: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = value.upper()
        if upper not in allowed:
            raise ValueError(
                f"Invalid log level '{value}'. Must be one of: {', '.join(sorted(allowed))}"
            )
        return upper

    def required_env_vars(self) -> list[str]:
        """Return the list of required environment variable names."""
        return [
            "REPLICATE_API_TOKEN",
            "OPENAI_API_KEY",
            "DISTIL_MODEL",
            "BARK_MODEL",
            "FLUX_MODEL",
            "GPT4_MODEL",
        ]

    def ensure_valid(self) -> None:
        """Validate that all required settings are present."""
        missing = [
            name
            for name in self.required_env_vars()
            if not getattr(self, name.lower(), None)
        ]
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}. "
                "Please set these in your .env file or environment."
            )

    @property
    def client(self) -> OpenAI:
        """Lazy OpenAI client initialized from the API key."""
        if self.openai_api_key is None:
            raise ValueError("OPENAI_API_KEY is not set.")
        return OpenAI(api_key=self.openai_api_key)

    @property
    def encoding(self) -> Encoding:
        """Lazy tiktoken encoder for the configured GPT model."""
        if self.gpt4_model is None:
            raise ValueError("GPT4_MODEL is not set.")
        return encoding_for_model(self.gpt4_model)

    @property
    def assets_dir(self) -> Path:
        """Path to the bundled assets directory."""
        return Path(__file__).resolve().parent.parent / "assets"

    @property
    def font_path(self) -> Path:
        """Path to the bundled title font."""
        return self.assets_dir / "mexcellent_3d.ttf"

    @property
    def replicate_token(self) -> str:
        """Alias for ``replicate_api_token`` used in module code."""
        return self.replicate_api_token


@lru_cache
def get_settings() -> Settings:
    """Return the cached, validated application settings."""
    # Pydantic Settings reads values from the environment / .env file, so the
    # apparent missing constructor arguments are resolved at runtime.
    settings: Settings = Settings()  # type: ignore[call-arg]
    settings.ensure_valid()
    # Ensure replicate library sees the token if it reads the env var directly.
    if settings.replicate_api_token:
        os.environ["REPLICATE_API_TOKEN"] = settings.replicate_api_token
    return settings


def reset_settings() -> None:
    """Reset the cached settings instance (useful mainly in tests)."""
    get_settings.cache_clear()
