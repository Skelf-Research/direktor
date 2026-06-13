"""
Tests for stage processors.
"""
import os
import json
import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open

from direktor.core.base_processor import BaseStageProcessor, ProcessingResult, ProcessorRegistry, register_processor
from direktor.processors.script_processor import ScriptProcessor
from direktor.processors.audio_processor import AudioProcessor


class MockProcessor(BaseStageProcessor):
    """Mock processor for testing base functionality."""

    def process(self, input_data, job_id):
        return ProcessingResult(
            success=True,
            output_data={"result": "mock_output"}
        )


class TestProcessorRegistry:
    """Test cases for ProcessorRegistry."""

    def setup_method(self):
        """Set up test environment."""
        self.registry = ProcessorRegistry()

    def test_register_processor(self):
        """Test processor registration."""
        self.registry.register("test_stage", MockProcessor)

        processor_class = self.registry.get_processor("test_stage")
        assert processor_class == MockProcessor

    def test_get_nonexistent_processor(self):
        """Test getting non-existent processor."""
        processor_class = self.registry.get_processor("nonexistent")
        assert processor_class is None

    def test_get_available_stages(self):
        """Test getting available stages."""
        self.registry.register("stage1", MockProcessor)
        self.registry.register("stage2", MockProcessor)

        stages = self.registry.get_available_stages()
        assert "stage1" in stages
        assert "stage2" in stages

    def test_create_processor(self):
        """Test processor instance creation."""
        self.registry.register("test_stage", MockProcessor)

        processor = self.registry.create_processor("test_stage")
        assert isinstance(processor, MockProcessor)
        assert processor.stage_name == "test_stage"

    def test_create_nonexistent_processor(self):
        """Test creating non-existent processor."""
        processor = self.registry.create_processor("nonexistent")
        assert processor is None

    def test_register_decorator(self):
        """Test register decorator functionality."""
        @register_processor("decorated_stage")
        class DecoratedProcessor(BaseStageProcessor):
            def process(self, input_data, job_id):
                return ProcessingResult(success=True)

        # Should be automatically registered
        from direktor.core.base_processor import get_processor_registry
        registry = get_processor_registry()
        processor_class = registry.get_processor("decorated_stage")
        assert processor_class == DecoratedProcessor


class TestBaseStageProcessor:
    """Test cases for BaseStageProcessor."""

    def setup_method(self):
        """Set up test environment."""
        # Mock configuration and queue manager
        self.mock_config = Mock()
        self.mock_queue_manager = Mock()

        with patch('direktor.core.base_processor.get_config', return_value=self.mock_config):
            with patch('direktor.core.base_processor.get_queue_manager', return_value=self.mock_queue_manager):
                self.processor = MockProcessor("test_stage")

    def test_initialization(self):
        """Test processor initialization."""
        assert self.processor.stage_name == "test_stage"
        assert self.processor.config == self.mock_config
        assert self.processor.queue_manager == self.mock_queue_manager

    def test_get_next_stage(self):
        """Test getting next stage in pipeline."""
        # Test known stages
        script_processor = MockProcessor("script")
        assert script_processor.get_next_stage() == "audio"

        audio_processor = MockProcessor("audio")
        assert audio_processor.get_next_stage() == "transcript"

        video_processor = MockProcessor("video")
        assert video_processor.get_next_stage() is None

        # Test unknown stage
        unknown_processor = MockProcessor("unknown")
        assert unknown_processor.get_next_stage() is None

    @patch('direktor.core.base_processor.get_stage_logger')
    def test_process_job_success(self, mock_get_logger):
        """Test successful job processing."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        # Mock job data
        mock_job = Mock()
        mock_job.job_id = "test_job"
        mock_job.input_data = {"test": "data"}

        # Mock queue manager methods
        self.mock_queue_manager.complete_job = Mock()

        # Process the job
        self.processor._process_job(mock_job)

        # Verify completion was called
        self.mock_queue_manager.complete_job.assert_called_once()
        mock_logger.stage_start.assert_called_once()
        mock_logger.stage_complete.assert_called_once()

    @patch('direktor.core.base_processor.get_stage_logger')
    def test_process_job_failure(self, mock_get_logger):
        """Test job processing failure."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        # Create processor that fails
        class FailingProcessor(BaseStageProcessor):
            def process(self, input_data, job_id):
                return ProcessingResult(
                    success=False,
                    error_message="Test error",
                    retry_recommended=True
                )

        with patch('direktor.core.base_processor.get_config', return_value=self.mock_config):
            with patch('direktor.core.base_processor.get_queue_manager', return_value=self.mock_queue_manager):
                failing_processor = FailingProcessor("test_stage")

        # Mock job data
        mock_job = Mock()
        mock_job.job_id = "test_job"
        mock_job.input_data = {"test": "data"}

        # Mock queue manager methods
        self.mock_queue_manager.fail_job = Mock()

        # Process the job
        failing_processor._process_job(mock_job)

        # Verify failure was called
        self.mock_queue_manager.fail_job.assert_called_once_with(
            "test_job", "Test error", True
        )


@patch.dict('os.environ', {
    'REPLICATE_API_TOKEN': 'test_token',
    'OPENAI_API_KEY': 'test_key',
    'DISTIL_MODEL': 'test_model',
    'BARK_MODEL': 'test_model',
    'FLUX_MODEL': 'test_model',
    'GPT4_MODEL': 'test_model',
    'AWS_ACCESS_KEY_ID': 'test_key',
    'AWS_SECRET_ACCESS_KEY': 'test_secret',
    'AWS_BUCKET_NAME': 'test_bucket'
})
class TestScriptProcessor:
    """Test cases for ScriptProcessor."""

    def setup_method(self):
        """Set up test environment."""
        with patch('direktor.core.base_processor.get_config') as mock_get_config:
            with patch('direktor.core.base_processor.get_queue_manager'):
                # Mock config
                mock_config = Mock()
                mock_config.apis.openai_key = 'test_key'
                mock_config.models.gpt4_model = 'gpt-4'
                mock_config.models.gpt4_max_tokens = 4000
                mock_get_config.return_value = mock_config

                self.processor = ScriptProcessor("script")

    @patch('direktor.processors.script_processor.OpenAI')
    @patch('direktor.processors.script_processor.tiktoken')
    def test_process_success(self, mock_tiktoken, mock_openai):
        """Test successful script processing."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Generated script content"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        # Mock tiktoken
        mock_encoding = Mock()
        mock_encoding.encode.return_value = [1, 2, 3, 4, 5]  # Short token list
        mock_encoding.decode.return_value = "Test content"
        mock_tiktoken.encoding_for_model.return_value = mock_encoding

        # Mock file operations
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('os.path.exists', return_value=False):
                with patch.object(self.processor, 'get_temp_file_path', return_value='test_path.txt'):
                    input_data = {
                        'text_content': 'Test content to process',
                        'optimize_content': False
                    }

                    result = self.processor.process(input_data, 'test_job')

                    assert result.success is True
                    assert 'script_content' in result.output_data
                    assert result.output_data['script_content'] == "Generated script content"

    def test_process_missing_input(self):
        """Test processing with missing input data."""
        input_data = {}  # Missing required 'text_content'

        result = self.processor.process(input_data, 'test_job')

        assert result.success is False
        assert "Missing required fields" in result.error_message

    @patch('direktor.processors.script_processor.optimize_content')
    def test_process_with_optimization(self, mock_optimize):
        """Test processing with content optimization."""
        mock_optimize.return_value = "Optimized content"

        with patch.object(self.processor, '_generate_podcast_script', return_value="Script"):
            with patch('builtins.open', mock_open()):
                with patch.object(self.processor, 'get_temp_file_path', return_value='test_path.txt'):
                    input_data = {
                        'text_content': 'Test content',
                        'optimize_content': True
                    }

                    result = self.processor.process(input_data, 'test_job')

                    mock_optimize.assert_called_once_with('Test content')


@patch.dict('os.environ', {
    'REPLICATE_API_TOKEN': 'test_token',
    'OPENAI_API_KEY': 'test_key',
    'DISTIL_MODEL': 'test_model',
    'BARK_MODEL': 'test_model',
    'FLUX_MODEL': 'test_model',
    'GPT4_MODEL': 'test_model',
    'AWS_ACCESS_KEY_ID': 'test_key',
    'AWS_SECRET_ACCESS_KEY': 'test_secret',
    'AWS_BUCKET_NAME': 'test_bucket'
})
class TestAudioProcessor:
    """Test cases for AudioProcessor."""

    def setup_method(self):
        """Set up test environment."""
        with patch('direktor.core.base_processor.get_config') as mock_get_config:
            with patch('direktor.core.base_processor.get_queue_manager'):
                # Mock config
                mock_config = Mock()
                mock_config.models.bark_model = 'test_bark_model'
                mock_config.max_chunk_chars = 150
                mock_get_config.return_value = mock_config

                self.processor = AudioProcessor("audio")

    def test_process_missing_input(self):
        """Test processing with missing input data."""
        input_data = {}  # Missing required 'script_content'

        result = self.processor.process(input_data, 'test_job')

        assert result.success is False
        assert "Missing required fields" in result.error_message

    @patch('os.path.exists')
    def test_process_cached_audio(self, mock_exists):
        """Test processing with cached audio file."""
        mock_exists.return_value = True

        with patch.object(self.processor, 'get_temp_file_path', return_value='cached_audio.mp3'):
            input_data = {'script_content': 'Test script content'}

            result = self.processor.process(input_data, 'test_job')

            assert result.success is True
            assert 'audio_file' in result.output_data

    def test_split_into_sentences(self):
        """Test sentence splitting functionality."""
        text = "First sentence. Second sentence! Third sentence? Fourth sentence."

        sentences = self.processor._split_into_sentences(text)

        assert len(sentences) == 4
        assert "First sentence" in sentences[0]
        assert "Second sentence" in sentences[1]
        assert "Third sentence" in sentences[2]
        assert "Fourth sentence" in sentences[3]

    def test_group_sentences(self):
        """Test sentence grouping functionality."""
        sentences = ["Short.", "Also short.", "This is a longer sentence that might exceed limits."]

        chunks = self.processor._group_sentences(sentences, max_chars=20)

        # Should group first two short sentences, keep long one separate
        assert len(chunks) >= 2
        assert "Short. Also short." in chunks[0] or ("Short." in chunks[0] and "Also short." in chunks[1])

    def test_get_next_stage(self):
        """Test getting next stage."""
        assert self.processor.get_next_stage() == 'transcript'