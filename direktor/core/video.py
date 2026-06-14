"""
Video creation module for Direktor.

This module handles combining audio and images into the final video.
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from PIL import Image

from .config import FONT_PATH
from .exceptions import VideoCreationError
from .logger import get_logger
from .utils import run_subprocess

logger = get_logger("video")


def _convert_to_png(image_file: Path, temp_dir: Path) -> Path:
    """Convert a WebP image to PNG for compatibility with FFmpeg."""
    if image_file.suffix.lower() != ".webp":
        return image_file

    png_file = temp_dir / f"{image_file.stem}.png"
    try:
        with Image.open(image_file) as img:
            img.save(png_file, "PNG")
        return png_file
    except Exception as e:
        logger.warning("Failed to convert %s to PNG: %s", image_file, e)
        return image_file


def _build_concat_file(
    image_files: Sequence[Path],
    image_prompts: Sequence[dict[str, Any]],
    concat_file: Path,
) -> None:
    """Build an FFmpeg concat demuxer file.

    Durations are derived from the prompt timestamps. The last image is held
    for a negligible duration because the concat demuxer requires a final entry.
    """
    lines: list[str] = []
    for i, (image_file, prompt) in enumerate(
        zip(image_files, image_prompts, strict=False)
    ):
        # Use absolute paths with safe=0 so the concat file is unambiguous.
        lines.append(f"file '{image_file.as_posix()}'")
        duration = (
            float(prompt["time"])
            if i == 0
            else float(prompt["time"]) - float(image_prompts[i - 1]["time"])
        )
        lines.append(f"duration {duration:.3f}")

    if image_files:
        lines.append(f"file '{image_files[-1].as_posix()}'")
        lines.append("duration 0.1")

    concat_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _build_drawtext_filter(
    keywords: Sequence[tuple[str, float, float]], font_path: Path
) -> str:
    """Build an FFmpeg drawtext filter string from keyword tuples."""
    filters: list[str] = []
    for keyword, start_time, end_time in keywords:
        escaped = keyword.replace("'", "\\'")
        filters.append(
            f"drawtext=fontfile={font_path}:fontsize=24:fontcolor=white:"
            f"box=1:boxcolor=black@0.5:boxborderw=5:x=(w-tw)/2:y=h-th-20:"
            f"text='{escaped}':enable='between(t,{start_time},{end_time})'"
        )
    return ",".join(filters)


def create_video(
    audio_file: str | os.PathLike[str],
    image_files: Sequence[str | os.PathLike[str]],
    image_prompts: Sequence[dict[str, Any]],
    temp_dir: str | os.PathLike[str],
    keywords: Sequence[tuple[str, float, float]] | None = None,
) -> Path:
    """Create a video from audio and images with optional keyword overlays.

    Args:
        audio_file: Path to the audio file.
        image_files: List of paths to image files.
        image_prompts: List of image prompts with timestamps.
        temp_dir: Temporary directory for intermediate files.
        keywords: Optional sequence of ``(keyword, start_time, end_time)``
            tuples for overlays.

    Returns:
        Path to the output video file.

    Raises:
        VideoCreationError: If FFmpeg fails or inputs are inconsistent.
    """
    temp_path = Path(temp_dir)
    audio_path = Path(audio_file)
    output_file = temp_path / "output.mp4"

    if output_file.exists():
        logger.info("Video already exists: %s", output_file)
        return output_file

    if len(image_files) != len(image_prompts):
        raise VideoCreationError(
            f"Number of images ({len(image_files)}) does not match number of "
            f"prompts ({len(image_prompts)})."
        )

    png_images = [_convert_to_png(Path(img), temp_path) for img in image_files]
    concat_file = temp_path / "concat.txt"
    temp_video = temp_path / "temp_video.mp4"

    try:
        _build_concat_file(png_images, image_prompts, concat_file)

        run_subprocess(
            [
                "ffmpeg",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_file),
                "-vsync",
                "vfr",
                "-pix_fmt",
                "yuv420p",
                "-vf",
                "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
                str(temp_video),
            ],
            cwd=temp_path,
        )

        drawtext_filter = _build_drawtext_filter(keywords or [], Path(FONT_PATH))
        output_command = [
            "ffmpeg",
            "-i",
            str(temp_video),
            "-i",
            str(audio_path),
            "-c:a",
            "aac",
            "-shortest",
            str(output_file),
        ]
        if drawtext_filter:
            output_command[-4:-4] = ["-filter_complex", drawtext_filter]

        run_subprocess(output_command, cwd=temp_path)
    except Exception as e:
        raise VideoCreationError(f"Video creation failed: {e}") from e
    finally:
        for path in [concat_file, temp_video]:
            try:
                path.unlink()
            except OSError:
                logger.warning("Could not remove temporary file %s", path)
        for png_file in png_images:
            if png_file.suffix.lower() == ".png" and png_file not in [
                Path(img) for img in image_files
            ]:
                try:
                    png_file.unlink()
                except OSError:
                    logger.warning("Could not remove converted image %s", png_file)

    logger.info("Video created: %s", output_file)
    return output_file
