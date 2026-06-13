"""
Configuration and constants for Direktor.

This module handles all environment variable loading and API client initialization.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI
import tiktoken

# Load environment variables from .env file
load_dotenv()

# API Tokens
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
if REPLICATE_API_TOKEN:
    os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Model Configuration
DISTIL_MODEL = os.getenv("DISTIL_MODEL")
BARK_MODEL = os.getenv("BARK_MODEL")
FLUX_MODEL = os.getenv("FLUX_MODEL")
GPT4_MODEL = os.getenv("GPT4_MODEL")
GPT4_MAX_TOKENS = int(os.getenv("GPT4_MAX_TOKENS", 8000))

# AWS/S3 Configuration (for Cloudflare R2 or other S3-compatible storage)
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL", "https://s3.us-west-000.backblazeb2.com")
AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Initialize tokenizer for text splitting
encoding = tiktoken.encoding_for_model(GPT4_MODEL) if GPT4_MODEL else None

# Asset paths
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
FONT_PATH = os.path.join(ASSETS_DIR, "mexcellent_3d.ttf")

# Required environment variables for validation
REQUIRED_ENV_VARS = [
    "REPLICATE_API_TOKEN",
    "OPENAI_API_KEY",
    "DISTIL_MODEL",
    "BARK_MODEL",
    "FLUX_MODEL",
    "GPT4_MODEL",
]


def validate_env_vars():
    """Check if all required environment variables are set."""
    missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing_vars:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing_vars)}. "
            "Please set these variables in your .env file."
        )
    return True
