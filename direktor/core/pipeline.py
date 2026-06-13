"""
Main pipeline orchestration for Direktor.

This module coordinates all stages of the video generation pipeline.
"""

import json
import os

from .config import validate_env_vars
from .utils import create_temp_dir
from .audio import generate_audio
from .transcript import generate_podcast_script, generate_transcript
from .images import generate_image_prompts, generate_images
from .video import create_video
from .narrative import optimize_content


def main(input_file, stage=6, keywords=None):
    """
    Main pipeline function that orchestrates all stages of video generation.

    The pipeline has 6 stages:
    1. Generate podcast script from input text
    2. Generate audio from the script
    3. Generate transcript from the audio
    4. Generate image prompts from the transcript
    5. Generate images from the prompts
    6. Create the final video

    Args:
        input_file: Path to the input text file
        stage: Stage to run up to (1-6). Previous outputs must exist for stages > 1.
        keywords: Optional list of (keyword, start_time, end_time) tuples for video overlays

    Returns:
        None
    """
    # Check if required environment variables are set
    try:
        validate_env_vars()
    except EnvironmentError as e:
        print(f"Error: {e}")
        return

    temp_dir = create_temp_dir(input_file)

    with open(input_file, "r") as f:
        input_text = f.read()

    # Apply content optimization if this is the first stage
    if stage <= 1:
        print("Optimizing content...")
        try:
            input_text = optimize_content(input_text)
        except Exception as e:
            print(f"Warning: Content optimization failed: {e}. Proceeding with original text.")

    if stage <= 1:
        print("Stage 1: Generating podcast script...")
        podcast_script = generate_podcast_script(input_text, temp_dir)
        return
    else:
        with open(os.path.join(temp_dir, "podcast_script.txt"), "r") as f:
            podcast_script = f.read()

    if stage <= 2:
        print("Stage 2: Generating audio...")
        audio_file = generate_audio(podcast_script, temp_dir)
        return
    else:
        audio_file = os.path.join(temp_dir, "audio.mp3")

    if stage <= 3:
        print("Stage 3: Generating transcript...")
        transcript = generate_transcript(audio_file, temp_dir)
        return
    else:
        with open(os.path.join(temp_dir, "transcript.json"), "r") as f:
            transcript = json.load(f)

    if stage <= 4:
        print("Stage 4: Generating image prompts...")
        image_prompts = generate_image_prompts(transcript, temp_dir)
        return
    else:
        with open(os.path.join(temp_dir, "image_prompts.json"), "r") as f:
            image_prompts = json.load(f)

    if stage <= 5:
        print("Stage 5: Generating images...")
        image_files = generate_images(image_prompts, temp_dir)
        return
    else:
        image_dir = os.path.join(temp_dir, "images")
        image_files = [
            os.path.join(image_dir, f)
            for f in os.listdir(image_dir)
            if f.endswith(".webp")
        ]

    if stage <= 6:
        print("Stage 6: Creating video...")
        if keywords is None:
            keywords = [
                ("Direktor", 0, 5),
                ("AI Video", 5, 10),
                ("Automation", 10, 15),
            ]
        output_file = create_video(
            audio_file, image_files, image_prompts, temp_dir, keywords
        )
        print(f"Video created: {output_file}")
    else:
        print(f"All stages completed. Video should be in {temp_dir}")

    print("Done!")
