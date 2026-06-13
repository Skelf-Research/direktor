"""
Stage processors for Direktor pipeline.
"""
from .script_processor import ScriptProcessor
from .audio_processor import AudioProcessor
from .transcript_processor import TranscriptProcessor
from .image_prompt_processor import ImagePromptProcessor
from .image_processor import ImageProcessor
from .video_processor import VideoProcessor

__all__ = [
    'ScriptProcessor',
    'AudioProcessor',
    'TranscriptProcessor',
    'ImagePromptProcessor',
    'ImageProcessor',
    'VideoProcessor'
]