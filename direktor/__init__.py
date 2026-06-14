"""
Direktor - A Python library for transforming text content into engaging podcast-style videos.

This package provides tools to convert text articles into podcast-style videos with
synchronized visuals and narration.
"""

__version__ = "0.1.0"
__author__ = "Dipankar Sarkar"
__email__ = "me@dipankar.name"

# Import main functions for easier access
# Expose individual modules for advanced usage
from .core import audio, images, transcript, utils, video
from .core.narrative import optimize_content
from .core.pipeline import main as generate_video

__all__ = [
    "generate_video",
    "optimize_content",
    "audio",
    "video",
    "transcript",
    "images",
    "utils",
]
