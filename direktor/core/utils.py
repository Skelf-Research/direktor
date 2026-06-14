"""
Utility functions for Direktor.

This module contains helper functions for file operations, API calls, text
processing, and subprocess execution.
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import boto3
import replicate
import requests
from botocore.client import Config
from halo import Halo
from tenacity import retry, stop_after_attempt, wait_exponential_jitter
from tqdm import tqdm

from .exceptions import ConfigurationError
from .logger import get_logger
from .settings import get_settings

logger = get_logger("utils")


def create_temp_dir(
    input_file: str | os.PathLike[str], base_dir: str | None = None
) -> Path:
    """Create a temporary directory based on the input file's hash.

    Args:
        input_file: Path to the input file.
        base_dir: Base directory for temporary files. Defaults to the
            ``temp_dir_base`` setting.

    Returns:
        Path to the created temporary directory.
    """
    path = Path(input_file)
    file_hash = hashlib.md5(path.read_bytes()).hexdigest()
    base = base_dir or get_settings().temp_dir_base
    temp_dir = Path(base) / file_hash
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=1, max=30),
    reraise=True,
)
def run_replicate_model(
    model: str, input_data: dict[str, Any], *, show_spinner: bool = True
) -> Any:
    """Run a Replicate model with the given input data.

    Args:
        model: The Replicate model identifier.
        input_data: Dictionary of input parameters.
        show_spinner: Whether to show a Halo spinner in the terminal.

    Returns:
        The model output.

    Raises:
        RuntimeError: If the prediction fails or is canceled.
    """
    spinner: Halo | None = None
    if show_spinner:
        spinner = Halo(text="Running Replicate model", spinner="dots")
        spinner.start()

    try:
        prediction = replicate.predictions.create(model=model, input=input_data)

        while prediction.status not in {"succeeded", "failed", "canceled"}:
            time.sleep(1)
            prediction.reload()

        if prediction.status == "succeeded":
            return prediction.output
        raise RuntimeError(f"Prediction failed with status: {prediction.status}")
    finally:
        if spinner is not None:
            spinner.stop()


def split_text(text: str, max_tokens: int) -> list[str]:
    """Split text into chunks based on token count.

    Args:
        text: The text to split.
        max_tokens: Maximum tokens per chunk.

    Returns:
        List of text chunks.
    """
    enc = get_settings().encoding
    tokens = enc.encode(text)
    chunks: list[str] = []
    current_chunk: list[int] = []
    current_length = 0

    for token in tokens:
        if current_length + 1 > max_tokens:
            chunks.append(enc.decode(current_chunk))
            current_chunk = []
            current_length = 0
        current_chunk.append(token)
        current_length += 1

    if current_chunk:
        chunks.append(enc.decode(current_chunk))

    return chunks


def split_into_sentences(text: str) -> list[str]:
    """Split text into sentences.

    Args:
        text: The text to split.

    Returns:
        List of sentences.
    """
    return re.split(r"(?<=[.!?])\s+", text)


def group_sentences(sentences: Sequence[str], max_chars: int = 100) -> list[str]:
    """Group sentences into chunks with a maximum character count.

    Args:
        sentences: List of sentences to group.
        max_chars: Maximum characters per chunk.

    Returns:
        List of grouped text chunks.
    """
    chunks: list[str] = []
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


def download_file(url: str, local_filename: str | os.PathLike[str]) -> Path:
    """Download a file from a URL with progress tracking.

    Args:
        url: The URL to download from.
        local_filename: Local path to save the file.

    Returns:
        Path to the downloaded file.

    Raises:
        requests.HTTPError: If the download fails.
    """
    local_path = Path(local_filename)
    local_path.parent.mkdir(parents=True, exist_ok=True)

    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        total_size = int(r.headers.get("content-length", 0))
        block_size = 8192
        with (
            open(local_path, "wb") as f,
            tqdm(
                desc=local_path.name,
                total=total_size,
                unit="iB",
                unit_scale=True,
                unit_divisor=1024,
            ) as progress_bar,
        ):
            for data in r.iter_content(block_size):
                size = f.write(data)
                progress_bar.update(size)

    return local_path


def upload_to_r2(file_path: str | os.PathLike[str], object_name: str) -> str:
    """Upload a file to S3-compatible storage and return a presigned URL.

    Args:
        file_path: Path to the local file.
        object_name: Object name in the bucket.

    Returns:
        Presigned URL for the uploaded file.

    Raises:
        ConfigurationError: If AWS credentials are incomplete.
    """
    settings = get_settings()
    if not all(
        [
            settings.aws_access_key_id,
            settings.aws_secret_access_key,
            settings.aws_endpoint_url,
            settings.aws_bucket_name,
        ]
    ):
        raise ConfigurationError(
            "AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_ENDPOINT_URL, and "
            "AWS_BUCKET_NAME must be set to upload files to S3-compatible storage."
        )

    s3 = boto3.client(
        "s3",
        endpoint_url=settings.aws_endpoint_url,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        config=Config(signature_version="s3v4"),
        region_name=settings.aws_region_name,
    )

    s3.upload_file(str(file_path), settings.aws_bucket_name, object_name)
    url: str = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.aws_bucket_name, "Key": object_name},
        ExpiresIn=3600,
    )
    return url


def run_subprocess(
    command: Sequence[str],
    cwd: str | os.PathLike[str] | None = None,
    timeout: float = 300,
    **kwargs: Any,
) -> subprocess.CompletedProcess[str]:
    """Run a subprocess command safely with captured output.

    Args:
        command: Command and arguments to execute.
        cwd: Working directory for the subprocess.
        timeout: Maximum allowed duration in seconds.
        **kwargs: Extra arguments passed to ``subprocess.run``.

    Returns:
        The completed process result.

    Raises:
        RuntimeError: If the command fails or times out.
    """
    logger.debug("Running subprocess command: %s", " ".join(command))
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            **kwargs,
        )
    except subprocess.CalledProcessError as e:
        logger.error("Subprocess failed: %s", e)
        logger.error("stdout: %s", e.stdout)
        logger.error("stderr: %s", e.stderr)
        raise RuntimeError(
            f"Command {' '.join(command)!r} failed with exit code {e.returncode}: {e.stderr}"
        ) from e
    except subprocess.TimeoutExpired as e:
        logger.error("Subprocess timed out after %s seconds: %s", timeout, command)
        raise RuntimeError(
            f"Command {' '.join(command)!r} timed out after {timeout} seconds"
        ) from e
    return result
