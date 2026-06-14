"""
Main pipeline orchestration for Direktor.

This module coordinates all stages of the video generation pipeline.
"""

from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from .audio import generate_audio
from .config import validate_env_vars
from .images import generate_image_prompts, generate_images
from .logger import get_logger
from .narrative import optimize_content
from .transcript import generate_podcast_script, generate_transcript
from .utils import create_temp_dir
from .video import create_video

logger = get_logger("pipeline")

ProgressCallback = Callable[[str, int], None]

DEFAULT_KEYWORDS: list[tuple[str, float, float]] = [
    ("Direktor", 0.0, 5.0),
    ("AI Video", 5.0, 10.0),
    ("Automation", 10.0, 15.0),
]


@dataclass
class PipelineResult:
    """Result of running the Direktor pipeline."""

    output_file: Path | None = None
    temp_dir: Path | None = None
    stages_completed: list[str] = field(default_factory=list)
    error: str | None = None

    @property
    def success(self) -> bool:
        """Return True if the pipeline completed without an error."""
        return self.error is None


def _notify(callback: ProgressCallback | None, message: str, stage: int) -> None:
    """Invoke the progress callback if one was provided."""
    logger.info("Stage %d: %s", stage, message)
    if callback is not None:
        callback(message, stage)


def main(
    input_file: str | Path,
    stage: int = 6,
    keywords: list[tuple[str, float, float]] | None = None,
    *,
    output_dir: str | Path | None = None,
    temp_dir: str | Path | None = None,
    clean: bool = False,
    resume: bool = True,
    optimize: bool = True,
    progress_callback: ProgressCallback | None = None,
) -> PipelineResult:
    """Run the Direktor video generation pipeline.

    The pipeline has 6 stages:
        1. Generate podcast script from input text
        2. Generate audio from the script
        3. Generate transcript from the audio
        4. Generate image prompts from the transcript
        5. Generate images from the prompts
        6. Create the final video

    Args:
        input_file: Path to the input text file.
        stage: Stage to run up to (1-6). Previous outputs must exist for
            stages greater than 1.
        keywords: Optional list of ``(keyword, start_time, end_time)`` tuples
            for video overlays.
        output_dir: Directory for the final output. Defaults to the temporary
            working directory.
        temp_dir: Temporary working directory. Defaults to a hashed directory
            under the configured ``temp_dir_base``.
        clean: If True, remove the temporary working directory before starting.
        resume: If True, skip stages whose output files already exist.
        optimize: If True, run narrative optimization on the input text.
        progress_callback: Optional callable ``(message, stage)`` invoked at
            each stage.

    Returns:
        A :class:`PipelineResult` describing the outcome.
    """
    try:
        validate_env_vars()
    except (OSError, ValueError) as e:
        return PipelineResult(error=f"Configuration error: {e}")

    input_path = Path(input_file)
    working_dir = Path(temp_dir) if temp_dir else create_temp_dir(input_path)

    if clean and working_dir.exists():
        shutil.rmtree(working_dir)

    working_dir.mkdir(parents=True, exist_ok=True)

    output_dir_path = Path(output_dir) if output_dir else working_dir
    output_dir_path.mkdir(parents=True, exist_ok=True)

    input_text = input_path.read_text(encoding="utf-8")
    stages_completed: list[str] = []

    try:
        # Stage 1: Optimize content and generate podcast script
        if stage >= 1:
            _notify(progress_callback, "Optimizing content and generating script", 1)
            script_file = working_dir / "podcast_script.txt"
            if resume and script_file.exists():
                logger.info("Resuming: podcast script already exists")
            else:
                if optimize:
                    try:
                        input_text = optimize_content(input_text)
                    except Exception as e:
                        logger.warning("Content optimization failed: %s", e)
                generate_podcast_script(input_text, working_dir)
            stages_completed.append("script")

        # Stage 2: Generate audio
        if stage >= 2:
            _notify(progress_callback, "Generating audio", 2)
            audio_file = working_dir / "audio.mp3"
            if resume and audio_file.exists():
                logger.info("Resuming: audio file already exists")
            else:
                podcast_script = script_file.read_text(encoding="utf-8")
                generate_audio(podcast_script, working_dir)
            stages_completed.append("audio")

        # Stage 3: Generate transcript
        if stage >= 3:
            _notify(progress_callback, "Generating transcript", 3)
            transcript_file = working_dir / "transcript.json"
            if resume and transcript_file.exists():
                logger.info("Resuming: transcript already exists")
            else:
                generate_transcript(audio_file, working_dir)
            stages_completed.append("transcript")

        # Stage 4: Generate image prompts
        if stage >= 4:
            _notify(progress_callback, "Generating image prompts", 4)
            prompts_file = working_dir / "image_prompts.json"
            if resume and prompts_file.exists():
                logger.info("Resuming: image prompts already exists")
            else:
                with transcript_file.open(encoding="utf-8") as f:
                    transcript = json.load(f)
                generate_image_prompts(transcript, working_dir)
            stages_completed.append("image_prompts")

        # Stage 5: Generate images
        if stage >= 5:
            _notify(progress_callback, "Generating images", 5)
            image_dir = working_dir / "images"
            if resume and image_dir.exists() and any(image_dir.glob("*.webp")):
                logger.info("Resuming: images already exist")
            else:
                with prompts_file.open(encoding="utf-8") as f:
                    image_prompts = json.load(f)
                generate_images(image_prompts, working_dir)
            stages_completed.append("images")

        # Stage 6: Create video
        if stage >= 6:
            _notify(progress_callback, "Creating final video", 6)
            final_output = output_dir_path / "output.mp4"
            if resume and final_output.exists():
                logger.info("Resuming: final video already exists")
            else:
                with prompts_file.open(encoding="utf-8") as f:
                    image_prompts = json.load(f)
                image_files = sorted(
                    [path for path in image_dir.glob("*.webp") if path.is_file()]
                )
                overlay_keywords = keywords or DEFAULT_KEYWORDS
                output_file = create_video(
                    audio_file,
                    image_files,
                    image_prompts,
                    working_dir,
                    overlay_keywords,
                )
                shutil.copy2(output_file, final_output)
            stages_completed.append("video")
            return PipelineResult(
                output_file=final_output,
                temp_dir=working_dir,
                stages_completed=stages_completed,
            )

    except Exception as e:
        logger.exception("Pipeline failed at stage %d", len(stages_completed) + 1)
        return PipelineResult(
            temp_dir=working_dir,
            stages_completed=stages_completed,
            error=f"Pipeline failed: {e}",
        )

    return PipelineResult(temp_dir=working_dir, stages_completed=stages_completed)
