# Development Guide

## Project Structure

```
direktor/
├── direktor/
│   ├── cli.py                  # CLI interface
│   ├── core/                   # Core system components
│   │   ├── config.py           # Configuration management
│   │   ├── logging_config.py   # Logging setup
│   │   ├── nng_queue.py        # NNG-based queuing
│   │   ├── base_processor.py   # Base processor classes
│   │   ├── narrative.py        # Content optimization
│   │   └── utils.py            # Utility functions
│   └── processors/             # Processing stages
│       ├── script_processor.py
│       ├── audio_processor.py
│       ├── transcript_processor.py
│       ├── image_prompt_processor.py
│       ├── image_processor.py
│       └── video_processor.py
├── tests/                      # Test suite
├── docs/                       # Documentation
└── pyproject.toml             # Dependencies and config
```

## Development Setup

```bash
# Clone and setup
git clone https://github.com/user/direktor.git
cd direktor

# Install with development dependencies
poetry install

# Set up environment
cp direktor/sample.env .env
# Edit .env with your API keys

# Run tests
poetry run pytest tests/ -v

# Start development system
poetry run direktor tracker &
poetry run direktor workers &
```

## Creating New Processors

### Basic Processor

```python
from direktor.core.base_processor import BaseStageProcessor, ProcessingResult, register_processor

@register_processor('my_stage')
class MyProcessor(BaseStageProcessor):
    def process(self, input_data: Dict[str, Any], job_id: str) -> ProcessingResult:
        try:
            # Your processing logic here
            result = self.do_work(input_data)

            return ProcessingResult(
                success=True,
                output_data={'result': result}
            )
        except Exception as e:
            return ProcessingResult(
                success=False,
                error_message=str(e),
                retry_recommended=True
            )

    def get_next_stage(self) -> str:
        return 'next_stage_name'
```

### Processor with Validation

```python
from direktor.core.base_processor import BaseStageProcessor, ValidationMixin, FileManagerMixin

@register_processor('validated_stage')
class ValidatedProcessor(BaseStageProcessor, ValidationMixin, FileManagerMixin):
    def process(self, input_data: Dict[str, Any], job_id: str) -> ProcessingResult:
        # Validate required inputs
        self.validate_input(input_data, ['required_field', 'another_field'])

        # Use file management utilities
        temp_dir = self.get_temp_dir(job_id)
        output_file = self.get_temp_file_path(job_id, 'output.txt')

        # Process and save
        result = self.process_data(input_data)
        with open(output_file, 'w') as f:
            f.write(result)

        return ProcessingResult(
            success=True,
            output_data={'output_file': output_file}
        )
```

### API Integration Processor

```python
import requests
from direktor.core.utils import retry_operation

@register_processor('api_stage')
class APIProcessor(BaseStageProcessor):
    def process(self, input_data: Dict[str, Any], job_id: str) -> ProcessingResult:
        logger = self.get_logger(job_id)

        def api_call():
            response = requests.post(
                'https://api.example.com/process',
                json=input_data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()

        try:
            # Retry API calls automatically
            result = retry_operation(api_call, max_retries=3)
            logger.info("API call successful")

            return ProcessingResult(
                success=True,
                output_data=result
            )
        except Exception as e:
            logger.error(f"API call failed: {e}")
            return ProcessingResult(
                success=False,
                error_message=str(e),
                retry_recommended=True
            )
```

## Testing

### Unit Tests

```python
import pytest
from unittest.mock import Mock, patch
from direktor.processors.my_processor import MyProcessor

class TestMyProcessor:
    def setup_method(self):
        with patch('direktor.core.base_processor.get_config'):
            with patch('direktor.core.base_processor.get_queue_manager'):
                self.processor = MyProcessor('my_stage')

    def test_process_success(self):
        input_data = {'data': 'test'}
        result = self.processor.process(input_data, 'test_job')

        assert result.success is True
        assert 'result' in result.output_data

    @patch('direktor.processors.my_processor.external_api')
    def test_process_with_mock(self, mock_api):
        mock_api.return_value = {'processed': 'data'}

        input_data = {'data': 'test'}
        result = self.processor.process(input_data, 'test_job')

        assert result.success is True
        mock_api.assert_called_once()
```

### Integration Tests

```python
import tempfile
import os
from direktor.core.nng_queue import NNGQueueManager, NNGJobTracker

class TestIntegration:
    def test_full_pipeline(self):
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup test environment
            os.environ['TEMP_DIR_BASE'] = temp_dir

            # Create job
            queue_manager = NNGQueueManager()
            job_id = queue_manager.create_job('script', {'text': 'test'})

            # Process job
            job = queue_manager.get_next_job('script')
            assert job is not None
            assert job.job_id == job_id
```

## Configuration

### Adding New Config Options

```python
# In direktor/core/config.py
@dataclass
class ProcessingConfig:
    """Processing configuration options."""
    temp_dir_base: str
    max_chunk_chars: int
    target_segment_duration: int
    new_option: str = "default_value"  # Add new option

class Config:
    def __init__(self):
        # ...existing code...
        self.processing = ProcessingConfig(
            temp_dir_base=os.getenv("TEMP_DIR_BASE", "temp"),
            max_chunk_chars=int(os.getenv("MAX_CHUNK_CHARS", 150)),
            target_segment_duration=int(os.getenv("TARGET_SEGMENT_DURATION", 30)),
            new_option=os.getenv("NEW_OPTION", "default_value")
        )
```

### Environment Variable Validation

```python
def _validate_required_vars(self) -> None:
    """Validate that all required environment variables are set."""
    required_vars = [
        "OPENAI_API_KEY",
        "REPLICATE_API_TOKEN",
        # Add new required variables
        "NEW_REQUIRED_VAR"
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
```

## CLI Extensions

### Adding New Commands

```python
# In direktor/cli.py
def new_command() -> None:
    """Implementation of new command."""
    print("Executing new command...")

def main() -> None:
    # ...existing parser setup...

    # Add new command
    new_parser = subparsers.add_parser('new', help='New command')
    new_parser.add_argument('--option', help='Command option')

    # ...existing command handling...

    elif args.command == 'new':
        new_command()
```

### Custom Worker Types

```python
def run_custom_worker(worker_type: str, config_file: str) -> None:
    """Run custom worker with specific configuration."""
    # Load custom configuration
    with open(config_file, 'r') as f:
        custom_config = json.load(f)

    # Create and run custom processor
    processor = create_custom_processor(worker_type, custom_config)
    processor.run_worker()
```

## Debugging

### Enable Debug Logging

```bash
export LOG_LEVEL=DEBUG
direktor tracker &
direktor worker script
```

### Debug Specific Job

```python
# Add to processor for debugging
def process(self, input_data: Dict[str, Any], job_id: str) -> ProcessingResult:
    logger = self.get_logger(job_id)

    # Debug input
    logger.debug(f"Input data: {input_data}")

    try:
        result = self.do_processing(input_data)
        logger.debug(f"Processing result: {result}")

        return ProcessingResult(success=True, output_data=result)
    except Exception as e:
        logger.debug(f"Processing failed", exc_info=True)
        raise
```

### Network Debugging

```bash
# Monitor NNG traffic
netstat -tulpn | grep 555

# Test connectivity
telnet localhost 5560

# Debug NNG sockets
export NNG_DEBUG=1
direktor tracker
```

## Performance Optimization

### Profiling

```python
import cProfile
import pstats

def profile_processor():
    profiler = cProfile.Profile()
    profiler.enable()

    # Run your processor
    processor.process(input_data, job_id)

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)
```

### Memory Optimization

```python
import gc
import psutil
import os

def monitor_memory():
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    print(f"Memory usage: {memory_mb:.1f} MB")

def cleanup_memory():
    gc.collect()  # Force garbage collection
    # Clear large objects
    del large_data_structure
```

### Batch Processing

```python
@register_processor('batch_stage')
class BatchProcessor(BaseStageProcessor):
    def run_worker(self, max_jobs: Optional[int] = None, timeout: int = 30) -> None:
        """Custom worker that processes jobs in batches."""
        batch = []
        batch_size = 5

        while True:
            job = self.queue_manager.get_next_job(self.stage_name, timeout)
            if job:
                batch.append(job)

                if len(batch) >= batch_size:
                    self.process_batch(batch)
                    batch = []
            else:
                if batch:  # Process remaining jobs
                    self.process_batch(batch)
                    batch = []
                break

    def process_batch(self, jobs: List[JobData]) -> None:
        """Process multiple jobs together for efficiency."""
        # Batch processing logic
        for job in jobs:
            # Process job
            result = self.process_single(job)
            self.queue_manager.complete_job(job.job_id, result)
```

## Contributing

### Code Style

```bash
# Format code
black direktor/ tests/

# Check style
flake8 direktor/ tests/

# Type checking
mypy direktor/
```

### Commit Guidelines

```
feat: add new processor for X
fix: resolve memory leak in Y
docs: update deployment guide
test: add integration tests for Z
refactor: simplify queue management
```

### Pull Request Process

1. Fork repository
2. Create feature branch
3. Add tests for new functionality
4. Update documentation
5. Run full test suite
6. Submit pull request

### Release Process

```bash
# Update version
poetry version minor

# Run tests
poetry run pytest tests/ -v

# Build package
poetry build

# Publish (maintainers only)
poetry publish
```

## Architecture Decisions

### Why NNG Over Redis?

- **Zero Dependencies**: No external services to manage
- **High Performance**: Direct TCP communication
- **Built-in Patterns**: PUSH/PULL and REQ/REP messaging
- **Automatic Recovery**: Connection handling and retry logic

### Why Separate Processors?

- **Modularity**: Easy to test and maintain individual stages
- **Scalability**: Different resource requirements per stage
- **Flexibility**: Can run different stages on different machines
- **Reliability**: Failure in one stage doesn't affect others

### Design Principles

1. **Simple Abstractions**: Easy to understand and extend
2. **Fail Fast**: Validate inputs early and clearly
3. **Observable**: Comprehensive logging and monitoring
4. **Recoverable**: Automatic retry and error handling
5. **Scalable**: Horizontal scaling without code changes