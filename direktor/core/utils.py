"""
Utility functions for Direktor.

This module contains helper functions for file operations, API calls, and text processing.
"""

import hashlib
import os
import re
import time
import requests
import boto3
from botocore.client import Config
from halo import Halo
from tqdm import tqdm
import replicate

from .config import (
    encoding,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_ENDPOINT_URL,
    AWS_BUCKET_NAME,
)


def create_temp_dir(input_file):
    """
    Create a temporary directory based on the input file's hash.

    Args:
        input_file: Path to the input file

    Returns:
        Path to the created temporary directory
    """
    with open(input_file, "rb") as f:
        file_hash = hashlib.md5(f.read()).hexdigest()
    temp_dir = os.path.join("temp", file_hash)
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir


def run_replicate_model(model, input_data):
    """
    Run a Replicate model with the given input data.

    Args:
        model: The Replicate model identifier
        input_data: Dictionary of input parameters

    Returns:
        The model output

    Raises:
        Exception: If the prediction fails
    """
    spinner = Halo(text="Running Replicate model", spinner="dots")
    spinner.start()

    prediction = replicate.predictions.create(model=model, input=input_data)

    while prediction.status not in {"succeeded", "failed", "canceled"}:
        time.sleep(1)
        prediction.reload()

    spinner.stop()

    if prediction.status == "succeeded":
        return prediction.output
    else:
        raise Exception(f"Prediction failed with status: {prediction.status}")


def split_text(text, max_tokens):
    """
    Split text into chunks based on token count.

    Args:
        text: The text to split
        max_tokens: Maximum tokens per chunk

    Returns:
        List of text chunks
    """
    tokens = encoding.encode(text)
    chunks = []
    current_chunk = []
    current_length = 0

    for token in tokens:
        if current_length + 1 > max_tokens:
            chunks.append(encoding.decode(current_chunk))
            current_chunk = []
            current_length = 0
        current_chunk.append(token)
        current_length += 1

    if current_chunk:
        chunks.append(encoding.decode(current_chunk))

    return chunks


def split_into_sentences(text):
    """
    Split text into sentences.

    Args:
        text: The text to split

    Returns:
        List of sentences
    """
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return sentences


def group_sentences(sentences, max_chars=100):
    """
    Group sentences into chunks with a maximum character count.

    Args:
        sentences: List of sentences to group
        max_chars: Maximum characters per chunk

    Returns:
        List of grouped text chunks
    """
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_chars:
            current_chunk += sentence + " "
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + " "

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def download_file(url, local_filename):
    """
    Download a file from a URL with progress tracking.

    Args:
        url: The URL to download from
        local_filename: Local path to save the file

    Returns:
        The local filename
    """
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        total_size = int(r.headers.get("content-length", 0))
        block_size = 8192
        with open(local_filename, "wb") as f, tqdm(
            desc=os.path.basename(local_filename),
            total=total_size,
            unit="iB",
            unit_scale=True,
            unit_divisor=1024,
        ) as progress_bar:
            for data in r.iter_content(block_size):
                size = f.write(data)
                progress_bar.update(size)
    return local_filename


def upload_to_r2(file_path, object_name):
    """
    Upload a file to S3-compatible storage (Cloudflare R2).

    Args:
        file_path: Path to the local file
        object_name: Object name in the bucket

    Returns:
        Presigned URL for the uploaded file, or None on failure
    """
    print(AWS_ENDPOINT_URL)
    s3 = boto3.client(
        "s3",
        endpoint_url=AWS_ENDPOINT_URL,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )

    try:
        s3.upload_file(file_path, AWS_BUCKET_NAME, object_name)
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": AWS_BUCKET_NAME, "Key": object_name},
            ExpiresIn=3600,  # 1 hour in seconds
        )
        return url
    except Exception as e:
        print(f"Failed to upload file to R2: {e}")
        return None
