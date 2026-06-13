# API Reference

## Python API

### Core Functions

```python
from direktor.core.nng_queue import get_queue_manager
from direktor.core.config import get_config
from direktor.core.logging_config import setup_logging

# Initialize system
setup_logging(level="INFO")
config = get_config()
queue_manager = get_queue_manager()
```

### Job Management

#### Create Job

```python
job_id = queue_manager.create_job(
    stage='script',
    input_data={
        'text_content': 'Your article text here...',
        'optimize_content': True
    },
    max_retries=3
)
```

#### Get Job Status

```python
job = queue_manager.get_job_status(job_id)
if job:
    print(f"Status: {job.status.value}")
    print(f"Stage: {job.stage}")
    if job.error_message:
        print(f"Error: {job.error_message}")
```

#### Process Job (Worker)

```python
# Get next job from queue
job = queue_manager.get_next_job('script', timeout_ms=30000)

if job:
    try:
        # Process the job
        result = process_script(job.input_data)

        # Mark as completed
        queue_manager.complete_job(
            job.job_id,
            output_data={'script_content': result},
            next_stage='audio'  # Optional: chain to next stage
        )
    except Exception as e:
        # Mark as failed
        queue_manager.fail_job(
            job.job_id,
            error_message=str(e),
            retry=True
        )
```

### Creating Processors

#### Basic Processor

```python
from direktor.core.base_processor import BaseStageProcessor, ProcessingResult, register_processor
from typing import Dict, Any

@register_processor('my_stage')
class MyProcessor(BaseStageProcessor):
    def process(self, input_data: Dict[str, Any], job_id: str) -> ProcessingResult:
        """Process input data and return result."""
        try:
            # Your processing logic
            output = self.transform_data(input_data)

            return ProcessingResult(
                success=True,
                output_data=output
            )
        except Exception as e:
            return ProcessingResult(
                success=False,
                error_message=str(e),
                retry_recommended=True
            )

    def get_next_stage(self) -> Optional[str]:
        """Return next stage name or None for final stage."""
        return 'next_stage'

    def transform_data(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Custom transformation logic."""
        # Implementation here
        return {'processed': input_data}
```

#### Advanced Processor with Mixins

```python
from direktor.core.base_processor import (
    BaseStageProcessor,
    ProcessingResult,
    ValidationMixin,
    FileManagerMixin,
    register_processor
)

@register_processor('advanced_stage')
class AdvancedProcessor(BaseStageProcessor, ValidationMixin, FileManagerMixin):
    def process(self, input_data: Dict[str, Any], job_id: str) -> ProcessingResult:
        # Validate required fields
        self.validate_input(input_data, ['required_field'])

        # Use file management utilities
        temp_dir = self.get_temp_dir(job_id)
        output_file = self.get_temp_file_path(job_id, 'result.json')

        # Process data
        result = self.complex_processing(input_data)

        # Save result
        with open(output_file, 'w') as f:
            json.dump(result, f)

        return ProcessingResult(
            success=True,
            output_data={
                'result': result,
                'output_file': output_file
            }
        )
```

## Configuration API

### Config Access

```python
from direktor.core.config import get_config

config = get_config()

# Access API keys
openai_key = config.apis.openai_key
replicate_token = config.apis.replicate_token

# Access model configuration
gpt_model = config.models.gpt4_model
max_tokens = config.models.gpt4_max_tokens

# Access AWS configuration
bucket_name = config.aws.bucket_name
endpoint_url = config.aws.endpoint_url

# Access processing configuration
temp_dir = config.temp_dir_base
max_chars = config.max_chunk_chars
```

### Custom Configuration

```python
from direktor.core.config import Config

# Load from custom .env file
config = Config(env_file='/path/to/custom.env')

# Convert to dictionary
config_dict = config.to_dict()

# Get NNG addresses
distributor_addr = config.nng_distributor_address
tracker_addr = config.nng_tracker_address
```

## Logging API

### Basic Logging

```python
from direktor.core.logging_config import setup_logging, get_logger

# Setup logging
setup_logging(level="DEBUG", log_dir="custom_logs")

# Get logger
logger = get_logger()
logger.info("Application started")
logger.error("Something went wrong", exc_info=True)
```

### Stage-specific Logging

```python
from direktor.core.logging_config import get_stage_logger

# Get stage logger with job context
logger = get_stage_logger('script', 'job_12345')

# Log with automatic context
logger.stage_start()
logger.info("Processing started")
logger.warning("API rate limit approaching")
logger.stage_complete(duration_seconds=45.2)
logger.stage_error(exception)
```

## Queue API

### Direct Queue Operations

```python
from direktor.core.nng_queue import NNGDistributor, NNGJobTracker

# Direct distributor usage
distributor = NNGDistributor("tcp://127.0.0.1")

# Push job to specific stage
job_data = {'job_id': 'test', 'stage': 'script', 'data': {...}}
distributor.push_job('script', job_data)

# Pull job from stage
job = distributor.pull_job('script', timeout_ms=1000)

# Job tracker usage
tracker = NNGJobTracker("tcp://127.0.0.1:5560")
tracker.start_server()

# Send requests
response = tracker.send_request({
    'action': 'create_job',
    'job': job_data
})
```

### Queue Statistics

```python
# Get comprehensive statistics
stats = queue_manager.get_queue_stats()

for stage, stage_stats in stats.items():
    print(f"Stage {stage}:")
    print(f"  Total jobs: {stage_stats['total_jobs']}")

    for status, count in stage_stats['status_counts'].items():
        if count > 0:
            print(f"  {status}: {count}")
```

## Utilities API

### File Operations

```python
from direktor.core.utils import (
    download_file,
    get_file_hash,
    sanitize_filename,
    ensure_directory,
    retry_operation
)

# Download file with progress
download_file(
    url="https://example.com/file.zip",
    local_filename="/tmp/download.zip",
    show_progress=True
)

# Get file hash
hash_value = get_file_hash("/path/to/file.txt")

# Sanitize filename
safe_name = sanitize_filename("unsafe/file:name*.txt")  # -> "unsafe_file_name_.txt"

# Ensure directory exists
ensure_directory("/path/to/create")

# Retry operation with exponential backoff
def flaky_operation():
    # Operation that might fail
    response = requests.get("https://api.example.com/data")
    response.raise_for_status()
    return response.json()

result = retry_operation(flaky_operation, max_retries=3, delay=1.0)
```

### Content Processing

```python
from direktor.core.narrative import optimize_content

# Optimize content through multiple AI enhancement stages
original_text = "Your article content here..."
optimized_text = optimize_content(original_text)
```

## Error Handling

### Job Processing Errors

```python
try:
    job_id = queue_manager.create_job('script', input_data)
    print(f"Job created: {job_id}")
except ValueError as e:
    print(f"Invalid input data: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Processor Errors

```python
class MyProcessor(BaseStageProcessor):
    def process(self, input_data: Dict[str, Any], job_id: str) -> ProcessingResult:
        logger = self.get_logger(job_id)

        try:
            self.validate_input(input_data, ['required_field'])
            result = self.do_work(input_data)

            return ProcessingResult(success=True, output_data=result)

        except ValueError as e:
            # Don't retry validation errors
            logger.error(f"Validation error: {e}")
            return ProcessingResult(
                success=False,
                error_message=str(e),
                retry_recommended=False
            )
        except requests.RequestException as e:
            # Retry network errors
            logger.warning(f"Network error: {e}")
            return ProcessingResult(
                success=False,
                error_message=str(e),
                retry_recommended=True
            )
        except Exception as e:
            # Unexpected errors - retry with caution
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return ProcessingResult(
                success=False,
                error_message=str(e),
                retry_recommended=True
            )
```

## Data Structures

### JobData

```python
from direktor.core.nng_queue import JobData, JobStatus

job = JobData(
    job_id="unique_id",
    stage="script",
    status=JobStatus.PENDING,
    input_data={"text": "content"},
    output_data=None,  # Set when completed
    error_message=None,  # Set when failed
    created_at=1234567890.0,
    started_at=None,  # Set when processing starts
    completed_at=None,  # Set when done
    retry_count=0,
    max_retries=3
)

# Serialization
job_dict = job.to_dict()
restored_job = JobData.from_dict(job_dict)
```

### ProcessingResult

```python
from direktor.core.base_processor import ProcessingResult

# Success result
result = ProcessingResult(
    success=True,
    output_data={"generated_content": "..."},
    duration_seconds=45.2
)

# Failure result
result = ProcessingResult(
    success=False,
    error_message="API rate limit exceeded",
    retry_recommended=True,
    duration_seconds=2.1
)
```

## Examples

### Simple Pipeline

```python
from direktor.core.nng_queue import get_queue_manager
from direktor.core.config import get_config

# Initialize
config = get_config()
queue_manager = get_queue_manager()

# Submit job
job_id = queue_manager.create_job(
    stage='script',
    input_data={
        'text_content': open('article.txt').read(),
        'optimize_content': True
    }
)

print(f"Submitted job: {job_id}")

# Monitor progress
import time
while True:
    job = queue_manager.get_job_status(job_id)
    if job:
        print(f"Status: {job.status.value}")
        if job.status.value in ['completed', 'failed']:
            break
    time.sleep(5)
```

### Custom Worker

```python
from direktor.core.base_processor import get_processor_registry

# Get registered processor
registry = get_processor_registry()
processor = registry.create_processor('script')

# Run single job
job = queue_manager.get_next_job('script', timeout_ms=10000)
if job:
    processor._process_job(job)

# Run worker loop
processor.run_worker(max_jobs=10, timeout=30)
```

### Batch Processing

```python
# Submit multiple jobs
job_ids = []
for filename in glob.glob('articles/*.txt'):
    with open(filename, 'r') as f:
        content = f.read()

    job_id = queue_manager.create_job('script', {
        'text_content': content,
        'source_file': filename
    })
    job_ids.append(job_id)

print(f"Submitted {len(job_ids)} jobs")

# Monitor all jobs
completed = 0
while completed < len(job_ids):
    stats = queue_manager.get_queue_stats()
    completed = sum(s['status_counts']['completed'] for s in stats.values())
    print(f"Completed: {completed}/{len(job_ids)}")
    time.sleep(10)
```