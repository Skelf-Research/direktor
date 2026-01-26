"""
Direktor core modules.

This package contains the core functionality for the Direktor video generation pipeline.
"""

from .config import client, encoding, validate_env_vars
from .utils import create_temp_dir, run_replicate_model, download_file, upload_to_r2
from .audio import generate_audio
from .transcript import generate_podcast_script, generate_transcript, aggregate_chunks
from .images import generate_image_prompts, generate_images
from .video import create_video
from .pipeline import main
from .narrative import optimize_content

__all__ = [
    # Config
    "client",
    "encoding",
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
    "main",
    # Narrative
    "optimize_content",
]
