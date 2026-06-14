"""
Custom exceptions for Direktor.
"""

from __future__ import annotations


class DirektorError(Exception):
    """Base exception for all Direktor errors."""


class ConfigurationError(DirektorError):
    """Raised when configuration is missing or invalid."""


class PipelineError(DirektorError):
    """Raised when the video generation pipeline fails."""


class AudioGenerationError(PipelineError):
    """Raised when audio generation fails."""


class TranscriptGenerationError(PipelineError):
    """Raised when transcript generation fails."""


class ImageGenerationError(PipelineError):
    """Raised when image generation fails."""


class VideoCreationError(PipelineError):
    """Raised when video creation fails."""


class SubprocessError(DirektorError):
    """Raised when an external subprocess command fails."""
