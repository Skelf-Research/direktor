"""
Direktor core modules.

This package contains the core functionality for the Direktor video
generation pipeline.
"""

from .audio import generate_audio
from .config import validate_env_vars
from .images import generate_image_prompts, generate_images
from .narrative import optimize_content
from .pipeline import PipelineResult, main
from .settings import Settings, get_settings, reset_settings
from .transcript import aggregate_chunks, generate_podcast_script, generate_transcript
from .utils import create_temp_dir, download_file, run_replicate_model, upload_to_r2
from .video import create_video

__all__ = [
    # Settings
    "Settings",
    "get_settings",
    "reset_settings",
    # Config
    "validate_env_vars",
    # Utils
    "create_temp_dir",
    "run_replicate_model",
    "download_file",
    "upload_to_r2",
    # Audio
    "generate_audio",
    # Transcript
    "generate_podcast_script",
    "generate_transcript",
    "aggregate_chunks",
    # Images
    "generate_image_prompts",
    "generate_images",
    # Video
    "create_video",
    # Pipeline
    "PipelineResult",
    "main",
    # Narrative
    "optimize_content",
]
