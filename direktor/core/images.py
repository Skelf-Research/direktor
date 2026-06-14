"""
Image generation module for Direktor.

This module handles image prompt generation and image creation using FLUX.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from tqdm import tqdm

from .exceptions import ImageGenerationError
from .logger import get_logger
from .settings import get_settings
from .transcript import aggregate_chunks
from .utils import download_file, run_replicate_model

logger = get_logger("images")


def generate_image_prompts(
    transcript: dict[str, Any], temp_dir: str | os.PathLike[str]
) -> list[dict[str, Any]]:
    """Generate image prompts from a transcript using GPT.

    Args:
        transcript: Transcript dictionary with ``chunks`` containing text and
            timestamps.
        temp_dir: Temporary directory for output files.

    Returns:
        List of image prompts with timestamps.
    """
    temp_path = Path(temp_dir)
    prompts_file = temp_path / "image_prompts.json"
    if prompts_file.exists():
        with prompts_file.open(encoding="utf-8") as f:
            data: list[dict[str, Any]] = json.load(f)
            return data

    settings = get_settings()
    raw_chunks = transcript.get("chunks", [])
    aggregated_chunks = aggregate_chunks(
        raw_chunks, target_duration=settings.target_segment_duration
    )

    system_prompt = (
        "You are an AI assistant that generates image prompts based on podcast "
        "transcripts. Generate a single, vivid image prompt that captures the main "
        "theme or most striking visual element from the given text."
    )
    user_template = (
        "Generate a Stable Diffusion generation prompt for the following podcast "
        "transcript segment:\n\nText: {text}\nTimestamp: {start} - {end}"
    )

    all_prompts: list[dict[str, Any]] = []
    for chunk in tqdm(aggregated_chunks, desc="Generating image prompts"):
        response = settings.client.chat.completions.create(
            model=settings.gpt4_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": user_template.format(
                        text=chunk["text"],
                        start=chunk["timestamp"][0],
                        end=chunk["timestamp"][1],
                    ),
                },
            ],
        )
        content = response.choices[0].message.content
        if content is None:
            raise ImageGenerationError("OpenAI returned empty image prompt.")
        all_prompts.append({"time": chunk["timestamp"][0], "prompt": content.strip()})

    with prompts_file.open("w", encoding="utf-8") as f:
        json.dump(all_prompts, f)
    return all_prompts


def generate_images(
    prompts: list[dict[str, Any]], temp_dir: str | os.PathLike[str]
) -> list[Path]:
    """Generate images from prompts using the FLUX model.

    Args:
        prompts: List of image prompts with timestamps.
        temp_dir: Temporary directory for output files.

    Returns:
        List of paths to generated image files.
    """
    temp_path = Path(temp_dir)
    image_dir = temp_path / "images"
    image_dir.mkdir(exist_ok=True)
    image_files: list[Path] = []

    for i, prompt in enumerate(tqdm(prompts, desc="Generating images")):
        image_file = image_dir / f"image_{i}.webp"
        if image_file.exists():
            image_files.append(image_file)
            continue

        input_data: dict[str, Any] = {
            "prompt": prompt["prompt"],
            "num_outputs": 1,
            "aspect_ratio": "16:9",
            "output_format": "webp",
            "output_quality": 80,
        }
        output = run_replicate_model(get_settings().flux_model, input_data)

        # Replicate can return a single URL or a list of URLs.
        url: str = output[0] if isinstance(output, list) else output
        download_file(url, image_file)
        image_files.append(image_file)

    return image_files
