"""
Tests for the command-line interface.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from direktor.cli import main
from direktor.core.pipeline import PipelineResult


def test_cli_missing_file() -> None:
    """CLI should exit with an error when the input file does not exist."""
    assert main(["nonexistent.txt"]) == 1


def test_cli_success(
    env_vars: dict[str, str],
    sample_input: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """CLI should print the output path on success."""
    output_file = tmp_path / "output.mp4"
    result = PipelineResult(
        output_file=output_file,
        temp_dir=tmp_path / "work",
        stages_completed=[
            "script",
            "audio",
            "transcript",
            "image_prompts",
            "images",
            "video",
        ],
    )

    with patch("direktor.cli.run_pipeline", return_value=result):
        exit_code = main([str(sample_input), "--output", str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Video created" in captured.out
    assert str(output_file) in captured.out


def test_cli_failure(
    env_vars: dict[str, str],
    sample_input: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """CLI should print an error message on pipeline failure."""
    result = PipelineResult(error="Something went wrong")

    with patch("direktor.cli.run_pipeline", return_value=result):
        exit_code = main([str(sample_input), "--output", str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Something went wrong" in captured.err


def test_cli_keywords_file(
    env_vars: dict[str, str],
    sample_input: Path,
    tmp_path: Path,
) -> None:
    """CLI should parse keyword overlays from a JSON file."""
    keywords_file = tmp_path / "keywords.json"
    keywords_file.write_text('[["Intro", 0, 5], ["Topic", 5, 10]]', encoding="utf-8")

    result = PipelineResult(
        output_file=tmp_path / "output.mp4",
        temp_dir=tmp_path / "work",
        stages_completed=["video"],
    )

    with patch("direktor.cli.run_pipeline") as mock_pipeline:
        mock_pipeline.return_value = result
        exit_code = main(
            [
                str(sample_input),
                "--keywords-file",
                str(keywords_file),
                "--output",
                str(tmp_path),
            ]
        )

    assert exit_code == 0
    kwargs = mock_pipeline.call_args.kwargs
    assert kwargs["keywords"] == [("Intro", 0.0, 5.0), ("Topic", 5.0, 10.0)]


def test_cli_stage_option(
    env_vars: dict[str, str],
    sample_input: Path,
    tmp_path: Path,
) -> None:
    """CLI should pass the requested stage to the pipeline."""
    result = PipelineResult(
        temp_dir=tmp_path / "work",
        stages_completed=["script"],
    )

    with patch("direktor.cli.run_pipeline") as mock_pipeline:
        mock_pipeline.return_value = result
        exit_code = main([str(sample_input), "--stage", "1", "--no-resume"])

    assert exit_code == 0
    assert mock_pipeline.call_args.kwargs["stage"] == 1
    assert mock_pipeline.call_args.kwargs["resume"] is False
