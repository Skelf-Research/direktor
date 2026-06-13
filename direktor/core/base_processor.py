"""
Base classes for stage processors.
"""
import time
import traceback
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type
from dataclasses import dataclass

from .config import get_config, Config
from .logging_config import get_stage_logger, StageLogger
from .nng_queue import get_queue_manager, NNGQueueManager, JobData, JobStatus


@dataclass
class ProcessingResult:
    """Result of stage processing."""
    success: bool
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    duration_seconds: float = 0.0
    retry_recommended: bool = False


class BaseStageProcessor(ABC):
    """Base class for all stage processors."""

    def __init__(self, stage_name: str):
        """Initialize base processor.

        Args:
            stage_name: Name of the processing stage
        """
        self.stage_name = stage_name
        self.config = get_config()
        self.queue_manager = get_queue_manager()

    @abstractmethod
    def process(self, input_data: Dict[str, Any], job_id: str) -> ProcessingResult:
        """Process input data for this stage.

        Args:
            input_data: Input data for processing
            job_id: Unique job identifier

        Returns:
            Processing result
        """
        pass

    def get_next_stage(self) -> Optional[str]:
        """Get the next stage in the pipeline.

        Returns:
            Next stage name or None if this is the final stage
        """
        stage_order = ['script', 'audio', 'transcript', 'prompts', 'images', 'video']
        try:
            current_index = stage_order.index(self.stage_name)
            if current_index < len(stage_order) - 1:
                return stage_order[current_index + 1]
        except ValueError:
            pass
        return None

    def run_worker(self, max_jobs: Optional[int] = None, timeout: int = 30) -> None:
        """Run worker to process jobs from queue.

        Args:
            max_jobs: Maximum number of jobs to process (None for unlimited)
            timeout: Timeout in seconds for waiting for jobs
        """
        logger = get_stage_logger(self.stage_name, "worker")
        logger.info(f"Starting worker for stage {self.stage_name}")

        jobs_processed = 0

        try:
            while max_jobs is None or jobs_processed < max_jobs:
                # Get next job from queue
                job = self.queue_manager.get_next_job(self.stage_name, timeout)

                if job is None:
                    logger.debug(f"No jobs available in {self.stage_name} queue")
                    if max_jobs is not None:
                        break
                    continue

                # Process the job
                self._process_job(job)
                jobs_processed += 1

                logger.info(f"Processed {jobs_processed} job(s)")

        except KeyboardInterrupt:
            logger.info("Worker interrupted by user")
        except Exception as e:
            logger.error(f"Worker error: {e}", exc_info=True)
        finally:
            logger.info(f"Worker finished. Processed {jobs_processed} job(s)")

    def _process_job(self, job: JobData) -> None:
        """Process a single job.

        Args:
            job: Job data to process
        """
        logger = get_stage_logger(self.stage_name, job.job_id)
        logger.stage_start()

        start_time = time.time()

        try:
            # Process the job
            result = self.process(job.input_data, job.job_id)
            duration = time.time() - start_time
            result.duration_seconds = duration

            if result.success:
                # Mark job as completed
                self.queue_manager.complete_job(
                    job.job_id,
                    result.output_data,
                    self.get_next_stage()
                )
                logger.stage_complete(duration)
            else:
                # Mark job as failed
                self.queue_manager.fail_job(
                    job.job_id,
                    result.error_message or "Unknown error",
                    result.retry_recommended
                )
                logger.error(f"Job failed: {result.error_message}")

        except Exception as e:
            duration = time.time() - start_time
            error_message = f"Unexpected error: {str(e)}\n{traceback.format_exc()}"

            self.queue_manager.fail_job(job.job_id, error_message, True)
            logger.stage_error(e)


class ValidationMixin:
    """Mixin for input/output validation."""

    def validate_input(self, input_data: Dict[str, Any], required_fields: list) -> None:
        """Validate input data has required fields.

        Args:
            input_data: Input data to validate
            required_fields: List of required field names

        Raises:
            ValueError: If required fields are missing
        """
        missing_fields = [field for field in required_fields if field not in input_data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

    def validate_file_exists(self, file_path: str) -> None:
        """Validate that a file exists.

        Args:
            file_path: Path to file

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        import os
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")


class FileManagerMixin:
    """Mixin for file management utilities."""

    def get_temp_dir(self, job_id: str) -> str:
        """Get temp directory for job.

        Args:
            job_id: Job identifier

        Returns:
            Path to temp directory
        """
        import os
        temp_dir = os.path.join(self.config.temp_dir_base, job_id[:8])  # Use first 8 chars of job ID
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir

    def get_temp_file_path(self, job_id: str, filename: str) -> str:
        """Get path for temp file.

        Args:
            job_id: Job identifier
            filename: Name of file

        Returns:
            Full path to temp file
        """
        import os
        return os.path.join(self.get_temp_dir(job_id), filename)

    def cleanup_temp_files(self, job_id: str, keep_final_output: bool = True) -> None:
        """Clean up temporary files for job.

        Args:
            job_id: Job identifier
            keep_final_output: Whether to keep final output files
        """
        import os
        import shutil

        temp_dir = self.get_temp_dir(job_id)
        if not os.path.exists(temp_dir):
            return

        if keep_final_output:
            # Keep important output files
            keep_files = ['output.mp4', 'audio.mp3', 'final_script.txt']
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file not in keep_files:
                        try:
                            os.remove(os.path.join(root, file))
                        except OSError:
                            pass
        else:
            # Remove entire directory
            try:
                shutil.rmtree(temp_dir)
            except OSError:
                pass


class ProcessorRegistry:
    """Registry for stage processors."""

    def __init__(self):
        """Initialize processor registry."""
        self._processors: Dict[str, Type[BaseStageProcessor]] = {}

    def register(self, stage_name: str, processor_class: Type[BaseStageProcessor]) -> None:
        """Register a processor for a stage.

        Args:
            stage_name: Name of the stage
            processor_class: Processor class
        """
        self._processors[stage_name] = processor_class

    def get_processor(self, stage_name: str) -> Optional[Type[BaseStageProcessor]]:
        """Get processor class for stage.

        Args:
            stage_name: Name of the stage

        Returns:
            Processor class or None if not found
        """
        return self._processors.get(stage_name)

    def get_available_stages(self) -> list:
        """Get list of available stages.

        Returns:
            List of stage names
        """
        return list(self._processors.keys())

    def create_processor(self, stage_name: str) -> Optional[BaseStageProcessor]:
        """Create processor instance for stage.

        Args:
            stage_name: Name of the stage

        Returns:
            Processor instance or None if not found
        """
        processor_class = self.get_processor(stage_name)
        if processor_class:
            return processor_class(stage_name)
        return None


# Global registry instance
_processor_registry = ProcessorRegistry()


def register_processor(stage_name: str):
    """Decorator to register a processor class.

    Args:
        stage_name: Name of the stage

    Returns:
        Decorator function
    """
    def decorator(cls: Type[BaseStageProcessor]):
        _processor_registry.register(stage_name, cls)
        return cls
    return decorator


def get_processor_registry() -> ProcessorRegistry:
    """Get the global processor registry.

    Returns:
        Global processor registry
    """
    return _processor_registry