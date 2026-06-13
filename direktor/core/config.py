"""
Configuration management for Direktor.
"""
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class ModelConfig:
    """Configuration for AI models."""
    distil_model: str
    bark_model: str
    flux_model: str
    gpt4_model: str
    gpt4_max_tokens: int


@dataclass
class AWSConfig:
    """Configuration for AWS/R2 storage."""
    access_key_id: str
    secret_access_key: str
    endpoint_url: str
    bucket_name: str
    region_name: str = "auto"


@dataclass
class APIConfig:
    """Configuration for external APIs."""
    replicate_token: str
    openai_key: str


class Config:
    """Central configuration management for Direktor."""

    def __init__(self, env_file: Optional[str] = None):
        """Initialize configuration from environment variables.

        Args:
            env_file: Path to .env file. If None, looks for .env in current directory.
        """
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()

        self._validate_required_vars()

        # Initialize configuration sections
        self.models = ModelConfig(
            distil_model=os.getenv("DISTIL_MODEL"),
            bark_model=os.getenv("BARK_MODEL"),
            flux_model=os.getenv("FLUX_MODEL"),
            gpt4_model=os.getenv("GPT4_MODEL"),
            gpt4_max_tokens=int(os.getenv("GPT4_MAX_TOKENS", 8000))
        )

        self.aws = AWSConfig(
            access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            endpoint_url=os.getenv("AWS_ENDPOINT_URL", "https://s3.us-west-000.backblazeb2.com"),
            bucket_name=os.getenv("AWS_BUCKET_NAME")
        )

        self.apis = APIConfig(
            replicate_token=os.getenv("REPLICATE_API_TOKEN"),
            openai_key=os.getenv("OPENAI_API_KEY")
        )

        # Processing configuration
        self.temp_dir_base = os.getenv("TEMP_DIR_BASE", "temp")
        self.max_chunk_chars = int(os.getenv("MAX_CHUNK_CHARS", 150))
        self.target_segment_duration = int(os.getenv("TARGET_SEGMENT_DURATION", 30))

        # NNG configuration for distributed processing
        self.nng_distributor_address = os.getenv("NNG_DISTRIBUTOR_ADDRESS", "tcp://127.0.0.1")
        self.nng_tracker_address = os.getenv("NNG_TRACKER_ADDRESS", "tcp://127.0.0.1:5560")

    def _validate_required_vars(self) -> None:
        """Validate that all required environment variables are set."""
        required_vars = [
            "REPLICATE_API_TOKEN",
            "OPENAI_API_KEY",
            "DISTIL_MODEL",
            "BARK_MODEL",
            "FLUX_MODEL",
            "GPT4_MODEL",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "AWS_BUCKET_NAME"
        ]

        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}. "
                "Please set these in your .env file."
            )

    def get_stage_address(self, stage: str) -> str:
        """Get NNG address for a specific stage.

        Args:
            stage: Stage name (e.g., 'script', 'audio', 'transcript', etc.)

        Returns:
            Full NNG address for the stage
        """
        stage_ports = {
            'script': 5550,
            'audio': 5551,
            'transcript': 5552,
            'prompts': 5553,
            'images': 5554,
            'video': 5555
        }
        base = self.nng_distributor_address.rstrip('/')
        port = stage_ports.get(stage, 5556)
        return f"{base}:{port}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization."""
        return {
            "models": {
                "distil_model": self.models.distil_model,
                "bark_model": self.models.bark_model,
                "flux_model": self.models.flux_model,
                "gpt4_model": self.models.gpt4_model,
                "gpt4_max_tokens": self.models.gpt4_max_tokens
            },
            "aws": {
                "endpoint_url": self.aws.endpoint_url,
                "bucket_name": self.aws.bucket_name,
                "region_name": self.aws.region_name
            },
            "processing": {
                "temp_dir_base": self.temp_dir_base,
                "max_chunk_chars": self.max_chunk_chars,
                "target_segment_duration": self.target_segment_duration
            },
            "nng": {
                "distributor_address": self.nng_distributor_address,
                "tracker_address": self.nng_tracker_address
            }
        }


# Global configuration instance
_config: Optional[Config] = None


def get_config(env_file: Optional[str] = None) -> Config:
    """Get global configuration instance.

    Args:
        env_file: Path to .env file for initialization

    Returns:
        Global configuration instance
    """
    global _config
    if _config is None:
        _config = Config(env_file)
    return _config


def reset_config() -> None:
    """Reset global configuration (mainly for testing)."""
    global _config
    _config = None