"""
Transcript generation module for Direktor.

This module handles podcast script generation and audio transcription.
"""

import hashlib
import json
import os
import subprocess

from tqdm import tqdm

from .config import client, GPT4_MODEL, GPT4_MAX_TOKENS, DISTIL_MODEL
from .utils import split_text, run_replicate_model, upload_to_r2


def generate_podcast_script(input_text, temp_dir):
    """
    Generate a podcast script from input text using GPT.

    Args:
        input_text: The text to convert into a podcast script
        temp_dir: Temporary directory for output files

    Returns:
        The generated podcast script
    """
    script_file = os.path.join(temp_dir, "podcast_script.txt")
    if os.path.exists(script_file):
        with open(script_file, "r") as f:
            return f.read()

    chunks = split_text(input_text, GPT4_MAX_TOKENS - 1000)
    script_parts = []

    for chunk in tqdm(chunks, desc="Generating podcast script"):
        response = client.chat.completions.create(
            model=GPT4_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI assistant that creates engaging single-person podcast scripts from input text.",
                },
                {
                    "role": "user",
                    "content": f"Create an engaging single-person podcast script based on the following text, please do not add any additional text like host, pauses etc.:\n\n{chunk}",
                },
            ],
        )
        script_parts.append(response.choices[0].message.content)

    script = " ".join(script_parts)
    with open(script_file, "w") as f:
        f.write(script)
    return script


def aggregate_chunks(chunks, target_duration=30):
    """
    Aggregate transcript chunks into segments of approximately target duration.

    Args:
        chunks: List of transcript chunks with timestamps
        target_duration: Target duration in seconds for each segment

    Returns:
        List of aggregated chunks
    """
    aggregated_chunks = []
    current_chunk = {"text": "", "timestamp": [chunks[0]["timestamp"][0], 0]}

    for chunk in chunks:
        if chunk["timestamp"][1] - current_chunk["timestamp"][0] > target_duration:
            current_chunk["timestamp"][1] = chunk["timestamp"][0]
            aggregated_chunks.append(current_chunk)
            current_chunk = {"text": chunk["text"], "timestamp": chunk["timestamp"]}
        else:
            current_chunk["text"] += " " + chunk["text"]
            current_chunk["timestamp"][1] = chunk["timestamp"][1]

    if current_chunk["text"]:
        aggregated_chunks.append(current_chunk)

    return aggregated_chunks


def generate_transcript(audio_file, temp_dir):
    """
    Generate a transcript from an audio file using Whisper.

    Args:
        audio_file: Path to the audio file
        temp_dir: Temporary directory for intermediate files

    Returns:
        Transcript dictionary with chunks and timestamps, or None on failure
    """
    transcript_file = os.path.join(temp_dir, "transcript.json")
    if os.path.exists(transcript_file):
        with open(transcript_file, "r") as f:
            return json.load(f)

    # Generate a hash for the audio file name
    with open(audio_file, "rb") as f:
        file_hash = hashlib.md5(f.read()).hexdigest()

    # Convert audio to WAV format
    wav_file = os.path.join(temp_dir, f"{file_hash}.wav")
    subprocess.run(
        [
            "ffmpeg",
            "-i", audio_file,
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            wav_file,
        ],
        check=True,
    )

    # Upload WAV file to Cloudflare R2
    aws_object_name = f"{file_hash}.wav"
    audio_url = upload_to_r2(wav_file, aws_object_name)

    if not audio_url:
        print("Failed to upload audio file to R2. Cannot generate transcript.")
        return None

    input_data = {
        "audio": audio_url,
        "task": "transcribe",
        "language": "english",
        "timestamp": "chunk",
    }
    transcript = run_replicate_model(DISTIL_MODEL, input_data)

    with open(transcript_file, "w") as f:
        json.dump(transcript, f)

    # Clean up the temporary WAV file
    os.remove(wav_file)

    return transcript
