"""
Tests for the full video generation pipeline.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from direktor.core.pipeline import main as run_pipeline


def _fake_openai_client(content: str) -> MagicMock:
    """Build a mock OpenAI client that returns the given content."""
    client = MagicMock()
    client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=content))]
    )
    return client


def _fake_replicate_prediction(output: Any) -> MagicMock:
    """Build a mock Replicate prediction object."""
    prediction = MagicMock()
    prediction.status = "succeeded"
    prediction.output = output
    return prediction


def _fake_boto3_client() -> MagicMock:
    """Build a mock boto3 S3 client."""
    client = MagicMock()
    client.generate_presigned_url.return_value = "https://example.com/audio.wav?signed"
    return client


def _fake_requests_get(url: str, **kwargs: Any) -> Any:
    """Return a context manager that yields fake image bytes."""
    response = MagicMock()
    response.headers = {"content-length": "4"}
    response.iter_content.return_value = [b"data"]
    return response


def test_full_pipeline(
    env_vars: dict[str, str],
    sample_input: Path,
    tmp_path: Path,
) -> None:
    """Run the full pipeline with all external APIs mocked."""
    openai_client = _fake_openai_client(
        "RoboGPT enables natural language interaction with robots."
    )
    s3_client = _fake_boto3_client()

    transcript_data = {
        "chunks": [
            {
                "text": "RoboGPT enables natural language interaction.",
                "timestamp": [0.0, 5.0],
            },
            {
                "text": "It transforms manufacturing and healthcare.",
                "timestamp": [5.0, 10.0],
            },
        ]
    }

    def _replicate_create(model: str, **kwargs: Any) -> MagicMock:
        if model == env_vars["DISTIL_MODEL"]:
            return _fake_replicate_prediction(transcript_data)
        return _fake_replicate_prediction("https://example.com/output.webp")

    def _subprocess(command: list[str], **kwargs: Any) -> MagicMock:
        working_dir = Path(kwargs.get("cwd") or tmp_path)
        last_arg = command[-1]
        if last_arg.endswith("audio.mp3"):
            (working_dir / "audio.mp3").write_bytes(b"fake audio")
        elif last_arg.endswith(".wav"):
            (working_dir / Path(last_arg).name).write_bytes(b"fake wav")
        elif last_arg.endswith("temp_video.mp4"):
            (working_dir / "temp_video.mp4").write_bytes(b"fake video")
        elif last_arg.endswith("output.mp4"):
            (working_dir / "output.mp4").write_bytes(b"final video")
        return MagicMock(returncode=0, stdout="", stderr="")

    with (
        patch("direktor.core.settings.OpenAI", return_value=openai_client),
        patch(
            "direktor.core.utils.replicate.predictions.create",
            side_effect=_replicate_create,
        ),
        patch("direktor.core.utils.boto3.client", return_value=s3_client),
        patch("direktor.core.utils.requests.get", side_effect=_fake_requests_get),
        patch("direktor.core.audio.run_subprocess", side_effect=_subprocess),
        patch("direktor.core.transcript.run_subprocess", side_effect=_subprocess),
        patch("direktor.core.video.run_subprocess", side_effect=_subprocess),
    ):
        result = run_pipeline(
            sample_input,
            stage=6,
            output_dir=tmp_path / "output",
            temp_dir=tmp_path / "work",
            optimize=False,
        )

    assert result.success
    assert result.output_file is not None
    assert result.output_file.exists()
    assert "video" in result.stages_completed


def test_pipeline_resumes_existing_outputs(
    env_vars: dict[str, str],
    sample_input: Path,
    tmp_path: Path,
) -> None:
    """The pipeline should skip stages whose output files already exist."""
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    (work_dir / "podcast_script.txt").write_text("existing script", encoding="utf-8")
    (work_dir / "audio.mp3").write_bytes(b"existing audio")

    with (
        patch("direktor.core.pipeline.generate_podcast_script") as mock_script,
        patch("direktor.core.pipeline.generate_audio") as mock_audio,
    ):
        result = run_pipeline(
            sample_input,
            stage=2,
            temp_dir=work_dir,
            resume=True,
        )

    mock_script.assert_not_called()
    mock_audio.assert_not_called()
    assert "audio" in result.stages_completed
    assert result.temp_dir == work_dir


def test_pipeline_configuration_error(
    sample_input: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The pipeline should report an error when required env vars are missing."""
    for key in [
        "REPLICATE_API_TOKEN",
        "OPENAI_API_KEY",
        "DISTIL_MODEL",
        "BARK_MODEL",
        "FLUX_MODEL",
        "GPT4_MODEL",
    ]:
        monkeypatch.delenv(key, raising=False)

    result = run_pipeline(sample_input, stage=6, temp_dir=tmp_path / "work")
    assert not result.success
    assert result.error is not None
    assert "Configuration error" in result.error
