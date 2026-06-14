"""
Audio generation module for Direktor.

This module handles text-to-speech conversion using the BARK model via
Replicate.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .exceptions import AudioGenerationError
from .logger import get_logger
from .settings import get_settings
from .utils import (
    download_file,
    group_sentences,
    run_replicate_model,
    run_subprocess,
    split_into_sentences,
)

logger = get_logger("audio")


def generate_audio(text: str, temp_dir: str | os.PathLike[str]) -> Path:
    """Generate audio from text using the BARK text-to-speech model.

    Args:
        text: The text to convert to speech.
        temp_dir: Temporary directory for output files.

    Returns:
        Path to the generated audio file.

    Raises:
        AudioGenerationError: If audio generation fails completely.
    """
    temp_path = Path(temp_dir)
    audio_file = temp_path / "audio.mp3"
    if audio_file.exists():
        logger.info("Audio already exists: %s", audio_file)
        return audio_file

    sentences = split_into_sentences(text)
    chunks = group_sentences(sentences, max_chars=get_settings().max_chunk_chars)

    all_audio_files: list[str] = []
    failed_chunks: list[int] = []

    for i, chunk in enumerate(chunks):
        chunk_audio_file = f"audio_chunk_{i}.mp3"
        full_chunk_audio_path = temp_path / chunk_audio_file

        input_data: dict[str, Any] = {
            "text": chunk,
            "alpha": 0.3,
            "beta": 0.7,
            "diffusion_steps": 10,
            "embedding_scale": 1.5,
            "seed": 0,
        }

        try:
            output = run_replicate_model(get_settings().bark_model, input_data)
            download_file(output, full_chunk_audio_path)
            all_audio_files.append(chunk_audio_file)
        except Exception:
            logger.exception("Failed to generate audio for chunk %d", i)
            failed_chunks.append(i)

    successful_audio_files = [
        file_name
        for i, file_name in enumerate(all_audio_files)
        if i not in failed_chunks
    ]

    if not successful_audio_files:
        raise AudioGenerationError("No audio chunks were successfully generated.")

    if len(successful_audio_files) == 1:
        source = temp_path / successful_audio_files[0]
        source.rename(audio_file)
        return audio_file

    concat_list_path = temp_path / "concat_list.txt"
    concat_list_path.write_text(
        "".join(f"file '{name}'\n" for name in successful_audio_files),
        encoding="utf-8",
    )

    try:
        run_subprocess(
            [
                "ffmpeg",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_list_path),
                "-c",
                "copy",
                str(audio_file),
            ],
            cwd=temp_path,
        )
    except Exception as e:
        raise AudioGenerationError(f"FFmpeg concatenation failed: {e}") from e
    finally:
        for chunk_file in successful_audio_files:
            try:
                (temp_path / chunk_file).unlink()
            except OSError:
                logger.warning("Could not remove chunk file %s", chunk_file)
        try:
            concat_list_path.unlink()
        except OSError:
            logger.warning("Could not remove concat list file")

    return audio_file
