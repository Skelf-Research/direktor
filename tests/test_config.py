"""
Tests for configuration management.
"""
import os
import pytest
from unittest.mock import patch, MagicMock

from direktor.core.config import Config, get_config, reset_config


class TestConfig:
    """Test cases for Config class."""

    def setup_method(self):
        """Set up test environment."""
        reset_config()

    def teardown_method(self):
        """Clean up after test."""
        reset_config()

    @patch.dict(os.environ, {
        'REPLICATE_API_TOKEN': 'test_replicate_token',
        'OPENAI_API_KEY': 'test_openai_key',
        'DISTIL_MODEL': 'test_distil_model',
        'BARK_MODEL': 'test_bark_model',
        'FLUX_MODEL': 'test_flux_model',
        'GPT4_MODEL': 'test_gpt4_model',
        'AWS_ACCESS_KEY_ID': 'test_access_key',
        'AWS_SECRET_ACCESS_KEY': 'test_secret_key',
        'AWS_BUCKET_NAME': 'test_bucket'
    })
    def test_config_initialization(self):
        """Test successful configuration initialization."""
        config = Config()

        assert config.apis.replicate_token == 'test_replicate_token'
        assert config.apis.openai_key == 'test_openai_key'
        assert config.models.distil_model == 'test_distil_model'
        assert config.models.bark_model == 'test_bark_model'
        assert config.models.flux_model == 'test_flux_model'
        assert config.models.gpt4_model == 'test_gpt4_model'
        assert config.aws.access_key_id == 'test_access_key'
        assert config.aws.secret_access_key == 'test_secret_key'
        assert config.aws.bucket_name == 'test_bucket'

    def test_config_missing_required_vars(self):
        """Test configuration with missing required variables."""
        with pytest.raises(ValueError, match="Missing required environment variables"):
            Config()

    @patch.dict(os.environ, {
        'REPLICATE_API_TOKEN': 'test_replicate_token',
        'OPENAI_API_KEY': 'test_openai_key',
        'DISTIL_MODEL': 'test_distil_model',
        'BARK_MODEL': 'test_bark_model',
        'FLUX_MODEL': 'test_flux_model',
        'GPT4_MODEL': 'test_gpt4_model',
        'AWS_ACCESS_KEY_ID': 'test_access_key',
        'AWS_SECRET_ACCESS_KEY': 'test_secret_key',
        'AWS_BUCKET_NAME': 'test_bucket',
        'GPT4_MAX_TOKENS': '4000',
        'TEMP_DIR_BASE': 'custom_temp',
        'NNG_DISTRIBUTOR_ADDRESS': 'tcp://192.168.1.100',
        'NNG_TRACKER_ADDRESS': 'tcp://192.168.1.100:5560'
    })
    def test_config_optional_values(self):
        """Test configuration with optional values."""
        config = Config()

        assert config.models.gpt4_max_tokens == 4000
        assert config.temp_dir_base == 'custom_temp'
        assert config.nng_distributor_address == 'tcp://192.168.1.100'
        assert config.nng_tracker_address == 'tcp://192.168.1.100:5560'

    @patch.dict(os.environ, {
        'REPLICATE_API_TOKEN': 'test_replicate_token',
        'OPENAI_API_KEY': 'test_openai_key',
        'DISTIL_MODEL': 'test_distil_model',
        'BARK_MODEL': 'test_bark_model',
        'FLUX_MODEL': 'test_flux_model',
        'GPT4_MODEL': 'test_gpt4_model',
        'AWS_ACCESS_KEY_ID': 'test_access_key',
        'AWS_SECRET_ACCESS_KEY': 'test_secret_key',
        'AWS_BUCKET_NAME': 'test_bucket'
    })
    def test_stage_address_generation(self):
        """Test stage address generation."""
        config = Config()

        assert config.get_stage_address('script') == 'tcp://127.0.0.1:5550'
        assert config.get_stage_address('audio') == 'tcp://127.0.0.1:5551'

    @patch.dict(os.environ, {
        'REPLICATE_API_TOKEN': 'test_replicate_token',
        'OPENAI_API_KEY': 'test_openai_key',
        'DISTIL_MODEL': 'test_distil_model',
        'BARK_MODEL': 'test_bark_model',
        'FLUX_MODEL': 'test_flux_model',
        'GPT4_MODEL': 'test_gpt4_model',
        'AWS_ACCESS_KEY_ID': 'test_access_key',
        'AWS_SECRET_ACCESS_KEY': 'test_secret_key',
        'AWS_BUCKET_NAME': 'test_bucket'
    })
    def test_config_to_dict(self):
        """Test configuration serialization to dictionary."""
        config = Config()
        config_dict = config.to_dict()

        assert 'models' in config_dict
        assert 'aws' in config_dict
        assert 'processing' in config_dict
        assert 'nng' in config_dict

        assert config_dict['models']['gpt4_model'] == 'test_gpt4_model'
        assert config_dict['aws']['bucket_name'] == 'test_bucket'

    @patch.dict(os.environ, {
        'REPLICATE_API_TOKEN': 'test_replicate_token',
        'OPENAI_API_KEY': 'test_openai_key',
        'DISTIL_MODEL': 'test_distil_model',
        'BARK_MODEL': 'test_bark_model',
        'FLUX_MODEL': 'test_flux_model',
        'GPT4_MODEL': 'test_gpt4_model',
        'AWS_ACCESS_KEY_ID': 'test_access_key',
        'AWS_SECRET_ACCESS_KEY': 'test_secret_key',
        'AWS_BUCKET_NAME': 'test_bucket'
    })
    def test_global_config_instance(self):
        """Test global configuration instance management."""
        config1 = get_config()
        config2 = get_config()

        # Should return same instance
        assert config1 is config2

        # Reset and get new instance
        reset_config()
        config3 = get_config()

        # Should be different instance after reset
        assert config1 is not config3