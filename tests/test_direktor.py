"""
High-level smoke tests for the Direktor package.
"""

from __future__ import annotations

import os

import direktor
from direktor import cli
from direktor.core import (
    audio,
    config,
    images,
    narrative,
    pipeline,
    transcript,
    utils,
    video,
)


def test_package_import() -> None:
    """Test that the top-level package exposes the expected symbols."""
    assert hasattr(direktor, "generate_video")
    assert hasattr(direktor, "optimize_content")
    assert hasattr(direktor, "__version__")
    assert direktor.__version__ == "0.1.0"


def test_module_imports() -> None:
    """Test that individual modules expose their public API."""
    assert hasattr(audio, "generate_audio")
    assert hasattr(video, "create_video")
    assert hasattr(transcript, "generate_podcast_script")
    assert hasattr(transcript, "generate_transcript")
    assert hasattr(transcript, "aggregate_chunks")
    assert hasattr(images, "generate_image_prompts")
    assert hasattr(images, "generate_images")
    assert hasattr(utils, "create_temp_dir")
    assert hasattr(utils, "run_replicate_model")
    assert hasattr(utils, "split_text")
    assert hasattr(utils, "download_file")
    assert hasattr(utils, "upload_to_r2")
    assert hasattr(pipeline, "main")


def test_config_import() -> None:
    """Test that the config module exposes validation helpers and paths."""
    assert hasattr(config, "validate_env_vars")
    assert hasattr(config, "REQUIRED_ENV_VARS")
    assert hasattr(config, "FONT_PATH")
    assert hasattr(config, "ASSETS_DIR")


def test_narrative_import() -> None:
    """Test that the narrative module is importable."""
    assert hasattr(narrative, "optimize_content")


def test_assets_exist() -> None:
    """Test that required assets are present."""
    assert os.path.exists(config.ASSETS_DIR), (
        f"Assets directory not found: {config.ASSETS_DIR}"
    )
    assert os.path.exists(config.FONT_PATH), f"Font file not found: {config.FONT_PATH}"


def test_cli_import() -> None:
    """Test that the CLI module is importable."""
    assert hasattr(cli, "main")
