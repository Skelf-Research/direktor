"""
Configuration and constants for Direktor.

This module re-exports the validated application settings for backward
compatibility. New code should import from :mod:`direktor.core.settings`
directly.
"""

from __future__ import annotations

from pathlib import Path

from openai import OpenAI
from tiktoken import Encoding

from .settings import Settings, get_settings

# -----------------------------------------------------------------------------
# Backward-compatible module-level re-exports
# -----------------------------------------------------------------------------


def _settings() -> Settings:
    """Lazy accessor used by all re-exported module-level values."""
    return get_settings()


# API tokens
REPLICATE_API_TOKEN: str = ""
OPENAI_API_KEY: str = ""

# Model configuration
DISTIL_MODEL: str = ""
BARK_MODEL: str = ""
FLUX_MODEL: str = ""
GPT4_MODEL: str = ""
GPT4_MAX_TOKENS: int = 8000

# AWS/S3 configuration
AWS_ACCESS_KEY_ID: str | None = None
AWS_SECRET_ACCESS_KEY: str | None = None
AWS_ENDPOINT_URL: str | None = None
AWS_BUCKET_NAME: str | None = None
AWS_REGION_NAME: str = "auto"

# Asset paths
ASSETS_DIR: Path = Path(__file__).resolve().parent.parent / "assets"
FONT_PATH: Path = ASSETS_DIR / "mexcellent_3d.ttf"

# API clients / utilities (initialized lazily on first access)
client: OpenAI | None = None
encoding: Encoding | None = None

# Required environment variables for validation
REQUIRED_ENV_VARS = [
    "REPLICATE_API_TOKEN",
    "OPENAI_API_KEY",
    "DISTIL_MODEL",
    "BARK_MODEL",
    "FLUX_MODEL",
    "GPT4_MODEL",
]


def validate_env_vars() -> bool:
    """Check if all required environment variables are set."""
    settings = _settings()
    settings.ensure_valid()
    return True


# -----------------------------------------------------------------------------
# Module-level initialization on import is intentionally avoided.
# The first call to get_settings() or validate_env_vars() triggers loading.
# -----------------------------------------------------------------------------
