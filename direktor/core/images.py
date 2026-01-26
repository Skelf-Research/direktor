"""
Image generation module for Direktor.

This module handles image prompt generation and image creation using FLUX.
"""

import json
import os

from openai import OpenAI
from tqdm import tqdm

from .config import GPT4_MODEL, FLUX_MODEL
from .utils import run_replicate_model, download_file
from .transcript import aggregate_chunks


def generate_image_prompts(transcript, temp_dir):
    """
    Generate image prompts from a transcript using GPT.

    Args:
        transcript: Transcript dictionary with chunks and timestamps
        temp_dir: Temporary directory for output files

    Returns:
        List of image prompts with timestamps
    """
    prompts_file = os.path.join(temp_dir, "image_prompts.json")
    if os.path.exists(prompts_file):
        with open(prompts_file, "r") as f:
            return json.load(f)

    client = OpenAI()
    all_prompts = []

    # Aggregate chunks to approximately 30-second segments
    aggregated_chunks = aggregate_chunks(transcript["chunks"], target_duration=30)

    for chunk in tqdm(aggregated_chunks, desc="Generating image prompts"):
        response = client.chat.completions.create(
            model=GPT4_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI assistant that generates image prompts based on podcast transcripts. Generate a single, vivid image prompt that captures the main theme or most striking visual element from the given text.",
                },
                {
                    "role": "user",
                    "content": f"Generate an stable diffusion generation prompt for the following podcast transcript segment:\n\nText: {chunk['text']}\nTimestamp: {chunk['timestamp'][0]} - {chunk['timestamp'][1]}",
                },
            ],
        )

        prompt = response.choices[0].message.content.strip()
        all_prompts.append({"time": chunk["timestamp"][0], "prompt": prompt})

    with open(prompts_file, "w") as f:
        json.dump(all_prompts, f)

    return all_prompts


def generate_images(prompts, temp_dir):
    """
    Generate images from prompts using the FLUX model.

    Args:
        prompts: List of image prompts with timestamps
        temp_dir: Temporary directory for output files

    Returns:
        List of paths to generated image files
    """
    image_dir = os.path.join(temp_dir, "images")
    os.makedirs(image_dir, exist_ok=True)
    image_files = []

    for i, prompt in enumerate(tqdm(prompts, desc="Generating images")):
        image_file = os.path.join(image_dir, f"image_{i}.webp")
        if os.path.exists(image_file):
            image_files.append(image_file)
            continue

        input_data = {
            "prompt": prompt["prompt"],
            "num_outputs": 1,
            "aspect_ratio": "16:9",
            "output_format": "webp",
            "output_quality": 80,
            "seed": 0,
            "disable_safety_checker": True,
        }
        output = run_replicate_model(FLUX_MODEL, input_data)
        image_file = download_file(output[0], image_file)
        image_files.append(image_file)

    return image_files
