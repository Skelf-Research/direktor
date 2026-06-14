"""
Transcript generation module for Direktor.

This module handles podcast script generation and audio transcription.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from tqdm import tqdm

from .exceptions import TranscriptGenerationError
from .logger import get_logger
from .settings import get_settings
from .utils import run_replicate_model, run_subprocess, split_text, upload_to_r2

logger = get_logger("transcript")


def generate_podcast_script(input_text: str, temp_dir: str | os.PathLike[str]) -> str:
    """Generate a podcast script from input text using GPT.

    Args:
        input_text: The text to convert into a podcast script.
        temp_dir: Temporary directory for output files.

    Returns:
        The generated podcast script.
    """
    temp_path = Path(temp_dir)
    script_file = temp_path / "podcast_script.txt"
    if script_file.exists():
        return script_file.read_text(encoding="utf-8")

    settings = get_settings()
    chunks = split_text(input_text, settings.gpt4_max_tokens - 1000)
    script_parts: list[str] = []

    system_prompt = (
        "You are an AI assistant that creates engaging single-person podcast "
        "scripts from input text."
    )
    user_template = (
        "Create an engaging single-person podcast script based on the following "
        "text. Do not add any additional text like host names, pauses, or sound "
        "effects:\n\n{text}"
    )

    for chunk in tqdm(chunks, desc="Generating podcast script"):
        response = settings.client.chat.completions.create(
            model=settings.gpt4_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_template.format(text=chunk)},
            ],
        )
        content = response.choices[0].message.content
        if content is None:
            raise TranscriptGenerationError("OpenAI returned empty content for script.")
        script_parts.append(content)

    script = " ".join(script_parts)
    script_file.write_text(script, encoding="utf-8")
    return script


def aggregate_chunks(
    chunks: list[dict[str, Any]], target_duration: int = 30
) -> list[dict[str, Any]]:
    """Aggregate transcript chunks into segments of approximately target duration.

    Args:
        chunks: List of transcript chunks with ``text`` and ``timestamp`` keys.
            Each timestamp is a ``[start, end]`` pair in seconds.
        target_duration: Target duration in seconds for each segment.

    Returns:
        List of aggregated chunks.
    """
    aggregated: list[dict[str, Any]] = []
    current_text = ""
    current_start: float | None = None
    current_end: float | None = None

    for chunk in chunks:
        text = chunk.get("text", "")
        timestamp = chunk.get("timestamp", [0.0, 0.0])
        start = float(timestamp[0])
        end = float(timestamp[1])

        if current_start is None:
            current_start = start

        if current_end is not None and end - current_start > target_duration:
            aggregated.append(
                {
                    "text": current_text.strip(),
                    "timestamp": [current_start, current_end],
                }
            )
            current_text = text
            current_start = start
            current_end = end
        else:
            current_text = f"{current_text} {text}".strip()
            current_end = end

    if current_text and current_start is not None and current_end is not None:
        aggregated.append(
            {"text": current_text.strip(), "timestamp": [current_start, current_end]}
        )

    return aggregated


def generate_transcript(
    audio_file: str | os.PathLike[str], temp_dir: str | os.PathLike[str]
) -> dict[str, Any]:
    """Generate a transcript from an audio file using Whisper.

    Args:
        audio_file: Path to the audio file.
        temp_dir: Temporary directory for intermediate files.

    Returns:
        Transcript dictionary with chunks and timestamps.

    Raises:
        TranscriptGenerationError: If transcription fails.
    """
    temp_path = Path(temp_dir)
    transcript_file = temp_path / "transcript.json"
    if transcript_file.exists():
        with transcript_file.open(encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)
            return data

    audio_path = Path(audio_file)
    file_hash = hashlib.md5(audio_path.read_bytes()).hexdigest()
    wav_file = temp_path / f"{file_hash}.wav"

    try:
        run_subprocess(
            [
                "ffmpeg",
                "-i",
                str(audio_path),
                "-acodec",
                "pcm_s16le",
                "-ar",
                "16000",
                str(wav_file),
            ],
            cwd=temp_path,
        )

        aws_object_name = f"{file_hash}.wav"
        audio_url = upload_to_r2(wav_file, aws_object_name)

        input_data = {
            "audio": audio_url,
            "task": "transcribe",
            "language": "english",
            "timestamp": "chunk",
        }
        transcript: dict[str, Any] = run_replicate_model(
            get_settings().distil_model, input_data
        )

        with transcript_file.open("w", encoding="utf-8") as f:
            json.dump(transcript, f)

        return transcript
    except Exception as e:
        raise TranscriptGenerationError(f"Failed to generate transcript: {e}") from e
    finally:
        try:
            wav_file.unlink()
        except OSError:
            logger.warning("Could not remove temporary WAV file %s", wav_file)
