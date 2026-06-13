"""
Utility functions for Direktor.
"""
import os
import hashlib
import requests
from typing import Optional
from tqdm import tqdm


def create_temp_dir(input_file: str, base_dir: str = "temp") -> str:
    """Create temporary directory based on input file hash.

    Args:
        input_file: Path to input file
        base_dir: Base directory for temp files

    Returns:
        Path to created temp directory
    """
    with open(input_file, 'rb') as f:
        file_hash = hashlib.md5(f.read()).hexdigest()
    temp_dir = os.path.join(base_dir, file_hash)
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir


def download_file(url: str, local_filename: str, show_progress: bool = True) -> str:
    """Download file from URL with optional progress bar.

    Args:
        url: URL to download from
        local_filename: Local file path to save to
        show_progress: Whether to show download progress

    Returns:
        Path to downloaded file
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(local_filename), exist_ok=True)

    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        total_size = int(r.headers.get('content-length', 0))
        block_size = 8192

        if show_progress and total_size > 0:
            with open(local_filename, 'wb') as f, tqdm(
                desc=os.path.basename(local_filename),
                total=total_size,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
            ) as progress_bar:
                for data in r.iter_content(block_size):
                    size = f.write(data)
                    progress_bar.update(size)
        else:
            with open(local_filename, 'wb') as f:
                for data in r.iter_content(block_size):
                    f.write(data)

    return local_filename


def get_file_hash(file_path: str) -> str:
    """Get MD5 hash of file.

    Args:
        file_path: Path to file

    Returns:
        MD5 hash as hex string
    """
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing/replacing invalid characters.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    import re
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing whitespace and dots
    filename = filename.strip(' .')
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    return filename


def ensure_directory(path: str) -> str:
    """Ensure directory exists, creating if necessary.

    Args:
        path: Directory path

    Returns:
        Directory path
    """
    os.makedirs(path, exist_ok=True)
    return path


def get_file_size(file_path: str) -> int:
    """Get file size in bytes.

    Args:
        file_path: Path to file

    Returns:
        File size in bytes
    """
    try:
        return os.path.getsize(file_path)
    except OSError:
        return 0


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def validate_url(url: str) -> bool:
    """Validate if string is a valid URL.

    Args:
        url: URL string to validate

    Returns:
        True if valid URL, False otherwise
    """
    import re
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None


def retry_operation(func, max_retries: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)):
    """Retry an operation with exponential backoff.

    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries
        exceptions: Tuple of exceptions to catch

    Returns:
        Function result

    Raises:
        Last exception if all retries fail
    """
    import time
    import random

    for attempt in range(max_retries + 1):
        try:
            return func()
        except exceptions as e:
            if attempt == max_retries:
                raise

            # Exponential backoff with jitter
            wait_time = delay * (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait_time)

    # Should never reach here
    raise RuntimeError("Retry operation failed unexpectedly")