"""
Test module for Direktor.
"""

import os
import sys

# Add the parent directory to sys.path to import direktor
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_import():
    """Test that we can import the direktor package."""
    import direktor

    assert hasattr(direktor, "generate_video")
    assert hasattr(direktor, "optimize_content")
    assert hasattr(direktor, "__version__")
    assert direktor.__version__ == "0.1.0"


def test_module_imports():
    """Test that individual modules can be imported."""
    from direktor.core import audio, video, transcript, images, utils, pipeline

    # Check audio module
    assert hasattr(audio, "generate_audio")

    # Check video module
    assert hasattr(video, "create_video")

    # Check transcript module
    assert hasattr(transcript, "generate_podcast_script")
    assert hasattr(transcript, "generate_transcript")
    assert hasattr(transcript, "aggregate_chunks")

    # Check images module
    assert hasattr(images, "generate_image_prompts")
    assert hasattr(images, "generate_images")

    # Check utils module
    assert hasattr(utils, "create_temp_dir")
    assert hasattr(utils, "run_replicate_model")
    assert hasattr(utils, "split_text")
    assert hasattr(utils, "download_file")
    assert hasattr(utils, "upload_to_r2")

    # Check pipeline module
    assert hasattr(pipeline, "main")


def test_config_import():
    """Test that config module can be imported."""
    from direktor.core import config

    assert hasattr(config, "validate_env_vars")
    assert hasattr(config, "REQUIRED_ENV_VARS")
    assert hasattr(config, "FONT_PATH")
    assert hasattr(config, "ASSETS_DIR")


def test_narrative_import():
    """Test that narrative module can be imported."""
    from direktor.core import narrative

    assert hasattr(narrative, "optimize_content")


def test_assets_exist():
    """Test that required assets are present."""
    from direktor.core.config import FONT_PATH, ASSETS_DIR

    assert os.path.exists(ASSETS_DIR), f"Assets directory not found: {ASSETS_DIR}"
    assert os.path.exists(FONT_PATH), f"Font file not found: {FONT_PATH}"


def test_cli_import():
    """Test that CLI module can be imported."""
    from direktor import cli

    assert hasattr(cli, "main")


if __name__ == "__main__":
    test_import()
    test_module_imports()
    test_config_import()
    test_narrative_import()
    test_assets_exist()
    test_cli_import()
    print("All tests passed!")
