"""
Shared fixtures and configuration for Direktor tests.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import tiktoken

from direktor.core.settings import reset_settings


@pytest.fixture(scope="session", autouse=True)
def _warm_tiktoken_cache() -> None:
    """Load tiktoken encodings once so tests don't need network access."""
    tiktoken.encoding_for_model("gpt-4o")


@pytest.fixture(autouse=True)
def _reset_settings_cache() -> None:
    """Clear the settings singleton between tests."""
    reset_settings()


@pytest.fixture
def env_vars(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Provide a minimal set of required environment variables."""
    values = {
        "REPLICATE_API_TOKEN": "test-replicate-token",
        "OPENAI_API_KEY": "test-openai-key",
        "DISTIL_MODEL": "test-distil-model",
        "BARK_MODEL": "test-bark-model",
        "FLUX_MODEL": "test-flux-model",
        "GPT4_MODEL": "gpt-4o",
        "AWS_ACCESS_KEY_ID": "test-aws-key",
        "AWS_SECRET_ACCESS_KEY": "test-aws-secret",
        "AWS_ENDPOINT_URL": "https://test.s3.example.com",
        "AWS_BUCKET_NAME": "test-bucket",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    return values


@pytest.fixture
def sample_input(tmp_path: Path) -> Path:
    """Create a small sample input text file."""
    path = tmp_path / "input.txt"
    path.write_text(
        "RoboGPT is transforming industries and shaping the future of "
        "human-robot collaboration.",
        encoding="utf-8",
    )
    return path


@pytest.fixture
def mock_openai_response() -> dict[str, Any]:
    """Return a mock OpenAI chat completion response."""
    return {
        "choices": [
            {
                "message": {
                    "content": "RoboGPT enables natural language interaction with robots."
                }
            }
        ]
    }


@pytest.fixture
def mock_replicate_output() -> str:
    """Return a mock Replicate output URL."""
    return "https://example.com/output.webp"
