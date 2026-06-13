"""
Audio generation module for Direktor.

This module handles text-to-speech conversion using the BARK model.
"""

import logging
import os
import subprocess

from .config import BARK_MODEL
from .utils import run_replicate_model, split_into_sentences, group_sentences, download_file

logging.basicConfig(filename="audio_generation.log", level=logging.ERROR)


def generate_audio(text, temp_dir):
    """
    Generate audio from text using the BARK text-to-speech model.

    Args:
        text: The text to convert to speech
        temp_dir: Temporary directory for output files

    Returns:
        Path to the generated audio file, or None on failure
    """
    audio_file = os.path.join(temp_dir, "audio.mp3")
    if os.path.exists(audio_file):
        return audio_file

    # Split the text into sentences and group them into chunks
    sentences = split_into_sentences(text)
    chunks = group_sentences(sentences, max_chars=150)

    all_audio_files = []
    failed_chunks = []

    for i, chunk in enumerate(chunks):
        chunk_audio_file = f"audio_chunk_{i}.mp3"
        full_chunk_audio_path = os.path.join(temp_dir, chunk_audio_file)

        input_data = {
            "text": chunk,
            "alpha": 0.3,
            "beta": 0.7,
            "diffusion_steps": 10,
            "embedding_scale": 1.5,
            "seed": 0,
        }

        try:
            output = run_replicate_model(BARK_MODEL, input_data)
            download_file(output, full_chunk_audio_path)
            all_audio_files.append(chunk_audio_file)
        except Exception as e:
            logging.error(f"Failed to generate audio for chunk {i}: {str(e)}")
            logging.error(f"Chunk text: {chunk}")
            logging.error(f"Input parameters: {input_data}")
            failed_chunks.append(i)

    # Remove failed chunks from the list
    successful_chunks = []
    successful_audio_files = []
    for i, (chunk, audio_file_name) in enumerate(zip(chunks, all_audio_files)):
        if i not in failed_chunks:
            successful_chunks.append(chunk)
            successful_audio_files.append(audio_file_name)

    # If there's more than one successful chunk, concatenate them
    if len(successful_audio_files) > 1:
        concat_list_file = "concat_list.txt"
        full_concat_list_path = os.path.join(temp_dir, concat_list_file)
        with open(full_concat_list_path, "w") as f:
            for audio_file_name in successful_audio_files:
                f.write(f"file '{audio_file_name}'\n")

        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", concat_list_file,
                    "-c", "copy",
                    "audio.mp3",
                ],
                check=True,
                cwd=temp_dir,
            )
        except subprocess.CalledProcessError as e:
            logging.error(f"FFmpeg concatenation failed: {str(e)}")
            return None

        # Clean up individual chunk files
        for chunk_file in successful_audio_files:
            try:
                os.remove(os.path.join(temp_dir, chunk_file))
            except OSError as e:
                logging.warning(f"Could not remove chunk file {chunk_file}: {str(e)}")
        try:
            os.remove(full_concat_list_path)
        except OSError as e:
            logging.warning(f"Could not remove concat list file: {str(e)}")

    elif len(successful_audio_files) == 1:
        # If there's only one chunk, just rename it
        try:
            os.rename(
                os.path.join(temp_dir, successful_audio_files[0]), audio_file
            )
        except OSError as e:
            logging.error(f"Failed to rename audio file: {str(e)}")
            return None
    else:
        logging.error("No audio chunks were successfully generated.")
        return None

    return audio_file
