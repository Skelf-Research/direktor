"""
Tests for utility functions.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from direktor.core import utils
from direktor.core.exceptions import ConfigurationError


def test_create_temp_dir(env_vars: dict[str, str], tmp_path: Path) -> None:
    """create_temp_dir should produce a deterministic hashed directory."""
    input_file = tmp_path / "article.txt"
    input_file.write_text("hello world", encoding="utf-8")
    temp_dir = utils.create_temp_dir(input_file)
    assert temp_dir.exists()
    assert temp_dir.name == "5eb63bbbe01eeed093cb22bb8f5acdc3"  # md5("hello world")


def test_split_text(env_vars: dict[str, str]) -> None:
    """split_text should chunk text by token count."""
    text = " ".join(["word"] * 50)
    chunks = utils.split_text(text, max_tokens=10)
    assert len(chunks) > 1


def test_split_into_sentences() -> None:
    """split_into_sentences should split on sentence terminators."""
    text = "First sentence. Second sentence! Third sentence?"
    sentences = utils.split_into_sentences(text)
    assert len(sentences) == 3


def test_group_sentences() -> None:
    """group_sentences should respect the character limit."""
    sentences = ["Short.", "This is ok.", "Tiny."]
    chunks = utils.group_sentences(sentences, max_chars=15)
    assert all(len(chunk) <= 15 for chunk in chunks)


def test_run_subprocess_success() -> None:
    """run_subprocess should return a CompletedProcess for valid commands."""
    result = utils.run_subprocess(["echo", "hello"])
    assert result.returncode == 0
    assert "hello" in result.stdout


def test_run_subprocess_failure() -> None:
    """run_subprocess should raise RuntimeError on command failure."""
    with pytest.raises(RuntimeError):
        utils.run_subprocess(["false"])


def test_upload_to_r2_missing_aws(
    env_vars: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """upload_to_r2 should raise ConfigurationError when AWS config is missing."""
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    reset = getattr(utils.get_settings, "cache_clear", None)
    if reset:
        reset()

    with pytest.raises(ConfigurationError):
        utils.upload_to_r2("/tmp/fake.wav", "fake.wav")


def test_download_file(env_vars: dict[str, str], tmp_path: Path) -> None:
    """download_file should fetch a URL and write it to disk."""
    local_file = tmp_path / "downloaded.webp"

    class _FakeResponse:
        headers = {"content-length": "6"}

        def __enter__(self) -> _FakeResponse:
            return self

        def __exit__(self, *exc: object) -> None:
            return None

        def raise_for_status(self) -> None:
            pass

        def iter_content(self, chunk_size: int) -> list[bytes]:
            return [b"data01"]

    with patch.object(utils.requests, "get", return_value=_FakeResponse()):
        result = utils.download_file("https://example.com/file.webp", local_file)

    assert result == local_file
    assert local_file.read_bytes() == b"data01"
