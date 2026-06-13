"""
NNG-based distributed queue system for Direktor.
"""
import json
import time
import uuid
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional, List, Callable
from enum import Enum
import logging

try:
    import pynng
    NNG_AVAILABLE = True
except ImportError:
    NNG_AVAILABLE = False

from .config import get_config
from .logging_config import get_logger


class JobStatus(Enum):
    """Job status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class JobData:
    """Data structure for job information."""
    job_id: str
    stage: str
    status: JobStatus
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: float = 0.0
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3

    def __post_init__(self):
        if self.created_at == 0.0:
            self.created_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['status'] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobData':
        """Create from dictionary."""
        data['status'] = JobStatus(data['status'])
        return cls(**data)


class NNGDistributor:
    """NNG-based job distributor using PUSH/PULL pattern."""

    def __init__(self, base_address: str = "tcp://127.0.0.1"):
        """Initialize NNG distributor.

        Args:
            base_address: Base address for NNG sockets
        """
        if not NNG_AVAILABLE:
            raise ImportError("pynng package not available. Install with: pip install pynng")

        self.base_address = base_address
        self.port_start = 5550
        self.pushers: Dict[str, pynng.Socket] = {}
        self.pullers: Dict[str, pynng.Socket] = {}
        self.logger = get_logger()
        self._lock = threading.Lock()

    def get_stage_address(self, stage: str, port_offset: int = 0) -> str:
        """Get address for a stage.

        Args:
            stage: Stage name
            port_offset: Additional port offset

        Returns:
            Full address for the stage
        """
        stage_ports = {
            'script': 0,
            'audio': 1,
            'transcript': 2,
            'prompts': 3,
            'images': 4,
            'video': 5
        }
        port = self.port_start + stage_ports.get(stage, 6) + port_offset
        return f"{self.base_address}:{port}"

    def get_pusher(self, stage: str) -> pynng.Socket:
        """Get or create pusher socket for stage.

        Args:
            stage: Stage name

        Returns:
            PUSH socket for the stage
        """
        with self._lock:
            if stage not in self.pushers:
                try:
                    socket = pynng.Push0()
                    address = self.get_stage_address(stage)
                    socket.dial(address)
                    self.pushers[stage] = socket
                    self.logger.debug(f"Created pusher for {stage} at {address}")
                except Exception as e:
                    self.logger.error(f"Failed to create pusher for {stage}: {e}")
                    raise

            return self.pushers[stage]

    def get_puller(self, stage: str) -> pynng.Socket:
        """Get or create puller socket for stage.

        Args:
            stage: Stage name

        Returns:
            PULL socket for the stage
        """
        with self._lock:
            if stage not in self.pullers:
                try:
                    socket = pynng.Pull0()
                    address = self.get_stage_address(stage)
                    socket.listen(address)
                    self.pullers[stage] = socket
                    self.logger.debug(f"Created puller for {stage} at {address}")
                except Exception as e:
                    self.logger.error(f"Failed to create puller for {stage}: {e}")
                    raise

            return self.pullers[stage]

    def push_job(self, stage: str, job_data: Dict[str, Any]) -> None:
        """Push job to stage queue.

        Args:
            stage: Target stage
            job_data: Job data to push
        """
        try:
            pusher = self.get_pusher(stage)
            message = json.dumps(job_data).encode('utf-8')
            pusher.send(message)
            self.logger.debug(f"Pushed job to {stage} queue")
        except Exception as e:
            self.logger.error(f"Failed to push job to {stage}: {e}")
            raise

    def pull_job(self, stage: str, timeout_ms: int = 1000) -> Optional[Dict[str, Any]]:
        """Pull job from stage queue.

        Args:
            stage: Stage to pull from
            timeout_ms: Timeout in milliseconds

        Returns:
            Job data or None if timeout
        """
        try:
            puller = self.get_puller(stage)
            try:
                message = puller.recv(timeout=timeout_ms)
                job_data = json.loads(message.decode('utf-8'))
                self.logger.debug(f"Pulled job from {stage} queue")
                return job_data
            except pynng.Timeout:
                return None
        except Exception as e:
            self.logger.error(f"Failed to pull job from {stage}: {e}")
            raise

    def close(self) -> None:
        """Close all sockets."""
        with self._lock:
            for stage, socket in self.pushers.items():
                try:
                    socket.close()
                except:
                    pass

            for stage, socket in self.pullers.items():
                try:
                    socket.close()
                except:
                    pass

            self.pushers.clear()
            self.pullers.clear()
            self.logger.info("Closed all NNG sockets")


class NNGJobTracker:
    """NNG-based job status tracking using REQ/REP pattern."""

    def __init__(self, base_address: str = "tcp://127.0.0.1:5560"):
        """Initialize job tracker.

        Args:
            base_address: Address for job tracking service
        """
        if not NNG_AVAILABLE:
            raise ImportError("pynng package not available. Install with: pip install pynng")

        self.address = base_address
        self.jobs: Dict[str, JobData] = {}
        self.logger = get_logger()
        self._lock = threading.Lock()
        self._server_socket: Optional[pynng.Socket] = None
        self._client_socket: Optional[pynng.Socket] = None
        self._running = False
        self._server_thread: Optional[threading.Thread] = None

    def start_server(self) -> None:
        """Start job tracking server."""
        if self._running:
            return

        try:
            self._server_socket = pynng.Rep0()
            self._server_socket.listen(self.address)
            self._running = True

            self._server_thread = threading.Thread(target=self._server_loop, daemon=True)
            self._server_thread.start()

            self.logger.info(f"Job tracker server started at {self.address}")
        except Exception as e:
            self.logger.error(f"Failed to start job tracker server: {e}")
            raise

    def _server_loop(self) -> None:
        """Server loop for handling requests."""
        while self._running:
            try:
                if not self._server_socket:
                    break

                message = self._server_socket.recv(timeout=1000)
                request = json.loads(message.decode('utf-8'))

                response = self._handle_request(request)

                response_data = json.dumps(response).encode('utf-8')
                self._server_socket.send(response_data)

            except pynng.Timeout:
                continue
            except Exception as e:
                self.logger.error(f"Error in server loop: {e}")
                if self._running:
                    # Send error response
                    try:
                        error_response = {"error": str(e)}
                        self._server_socket.send(json.dumps(error_response).encode('utf-8'))
                    except:
                        pass

    def _handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle job tracking requests.

        Args:
            request: Request data

        Returns:
            Response data
        """
        with self._lock:
            action = request.get('action')

            if action == 'create_job':
                job_data = JobData.from_dict(request['job'])
                self.jobs[job_data.job_id] = job_data
                return {"status": "created", "job_id": job_data.job_id}

            elif action == 'update_job':
                job_id = request['job_id']
                if job_id in self.jobs:
                    job = self.jobs[job_id]
                    for key, value in request['updates'].items():
                        if key == 'status':
                            job.status = JobStatus(value)
                        else:
                            setattr(job, key, value)
                    return {"status": "updated"}
                return {"error": "Job not found"}

            elif action == 'get_job':
                job_id = request['job_id']
                if job_id in self.jobs:
                    return {"job": self.jobs[job_id].to_dict()}
                return {"error": "Job not found"}

            elif action == 'list_jobs':
                stage = request.get('stage')
                if stage:
                    jobs = [job.to_dict() for job in self.jobs.values() if job.stage == stage]
                else:
                    jobs = [job.to_dict() for job in self.jobs.values()]
                return {"jobs": jobs}

            elif action == 'get_stats':
                stats = {}
                for stage in ['script', 'audio', 'transcript', 'prompts', 'images', 'video']:
                    stage_jobs = [job for job in self.jobs.values() if job.stage == stage]
                    status_counts = {}
                    for status in JobStatus:
                        status_counts[status.value] = len([job for job in stage_jobs if job.status == status])

                    stats[stage] = {
                        'total_jobs': len(stage_jobs),
                        'status_counts': status_counts
                    }
                return {"stats": stats}

            return {"error": "Unknown action"}

    def get_client(self) -> pynng.Socket:
        """Get or create client socket.

        Returns:
            REQ socket for client communication
        """
        if not self._client_socket:
            try:
                self._client_socket = pynng.Req0()
                self._client_socket.dial(self.address)
                self.logger.debug(f"Connected job tracker client to {self.address}")
            except Exception as e:
                self.logger.error(f"Failed to connect job tracker client: {e}")
                raise

        return self._client_socket

    def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send request to job tracker.

        Args:
            request: Request data

        Returns:
            Response data
        """
        try:
            client = self.get_client()

            request_data = json.dumps(request).encode('utf-8')
            client.send(request_data)

            response_data = client.recv(timeout=5000)  # 5 second timeout
            return json.loads(response_data.decode('utf-8'))

        except Exception as e:
            self.logger.error(f"Failed to send job tracker request: {e}")
            raise

    def stop_server(self) -> None:
        """Stop job tracking server."""
        self._running = False

        if self._server_thread:
            self._server_thread.join(timeout=2.0)

        if self._server_socket:
            self._server_socket.close()
            self._server_socket = None

        if self._client_socket:
            self._client_socket.close()
            self._client_socket = None

        self.logger.info("Job tracker server stopped")


class NNGQueueManager:
    """NNG-based queue manager for distributed processing."""

    def __init__(self, distributor_address: str = "tcp://127.0.0.1", tracker_address: str = "tcp://127.0.0.1:5560"):
        """Initialize NNG queue manager.

        Args:
            distributor_address: Base address for job distribution
            tracker_address: Address for job tracking
        """
        self.distributor = NNGDistributor(distributor_address)
        self.tracker = NNGJobTracker(tracker_address)
        self.logger = get_logger()

    def start_tracker_server(self) -> None:
        """Start the job tracking server."""
        self.tracker.start_server()

    def create_job(self, stage: str, input_data: Dict[str, Any], job_id: Optional[str] = None, max_retries: int = 3) -> str:
        """Create and queue a new job.

        Args:
            stage: Target stage name
            input_data: Input data for the stage
            job_id: Optional custom job ID
            max_retries: Maximum retry attempts

        Returns:
            Job ID
        """
        if job_id is None:
            job_id = str(uuid.uuid4())

        job = JobData(
            job_id=job_id,
            stage=stage,
            status=JobStatus.PENDING,
            input_data=input_data,
            max_retries=max_retries
        )

        try:
            # Register job with tracker
            self.tracker.send_request({
                'action': 'create_job',
                'job': job.to_dict()
            })

            # Push to distribution queue
            self.distributor.push_job(stage, job.to_dict())

            self.logger.info(f"Created job {job_id} for stage {stage}")
            return job_id

        except Exception as e:
            self.logger.error(f"Failed to create job {job_id}: {e}")
            raise

    def get_next_job(self, stage: str, timeout_ms: int = 30000) -> Optional[JobData]:
        """Get next job from stage queue.

        Args:
            stage: Stage name to get job from
            timeout_ms: Timeout in milliseconds

        Returns:
            Job data or None if no jobs available
        """
        try:
            job_dict = self.distributor.pull_job(stage, timeout_ms)
            if job_dict:
                job = JobData.from_dict(job_dict)

                # Update job status to IN_PROGRESS
                self.tracker.send_request({
                    'action': 'update_job',
                    'job_id': job.job_id,
                    'updates': {
                        'status': JobStatus.IN_PROGRESS.value,
                        'started_at': time.time()
                    }
                })

                job.status = JobStatus.IN_PROGRESS
                job.started_at = time.time()

                self.logger.info(f"Retrieved job {job.job_id} from stage {stage}")
                return job

            return None

        except Exception as e:
            self.logger.error(f"Failed to get job from stage {stage}: {e}")
            return None

    def complete_job(self, job_id: str, output_data: Dict[str, Any], next_stage: Optional[str] = None) -> None:
        """Mark job as completed and optionally queue for next stage.

        Args:
            job_id: Job ID to complete
            output_data: Output data from completed stage
            next_stage: Optional next stage to queue job for
        """
        try:
            # Update job status
            self.tracker.send_request({
                'action': 'update_job',
                'job_id': job_id,
                'updates': {
                    'status': JobStatus.COMPLETED.value,
                    'output_data': output_data,
                    'completed_at': time.time()
                }
            })

            self.logger.info(f"Completed job {job_id}")

            # Queue for next stage if specified
            if next_stage:
                next_job_id = f"{job_id}_{next_stage}"
                self.create_job(
                    stage=next_stage,
                    input_data=output_data,
                    job_id=next_job_id
                )

        except Exception as e:
            self.logger.error(f"Failed to complete job {job_id}: {e}")
            raise

    def fail_job(self, job_id: str, error_message: str, retry: bool = True) -> None:
        """Mark job as failed and optionally retry.

        Args:
            job_id: Job ID to fail
            error_message: Error description
            retry: Whether to retry the job
        """
        try:
            # Get current job state
            response = self.tracker.send_request({
                'action': 'get_job',
                'job_id': job_id
            })

            if 'error' in response:
                self.logger.error(f"Job {job_id} not found for failure")
                return

            job_data = response['job']
            job = JobData.from_dict(job_data)

            if retry and job.retry_count < job.max_retries:
                # Retry the job
                job.retry_count += 1
                job.status = JobStatus.RETRY
                job.error_message = error_message
                job.started_at = None

                # Update in tracker
                self.tracker.send_request({
                    'action': 'update_job',
                    'job_id': job_id,
                    'updates': {
                        'status': JobStatus.RETRY.value,
                        'retry_count': job.retry_count,
                        'error_message': error_message,
                        'started_at': None
                    }
                })

                # Re-queue the job
                self.distributor.push_job(job.stage, job.to_dict())
                self.logger.warning(f"Retrying job {job_id} (attempt {job.retry_count}/{job.max_retries})")

            else:
                # Mark as permanently failed
                self.tracker.send_request({
                    'action': 'update_job',
                    'job_id': job_id,
                    'updates': {
                        'status': JobStatus.FAILED.value,
                        'error_message': error_message,
                        'completed_at': time.time()
                    }
                })
                self.logger.error(f"Job {job_id} failed permanently: {error_message}")

        except Exception as e:
            self.logger.error(f"Failed to handle job failure for {job_id}: {e}")
            raise

    def get_job_status(self, job_id: str) -> Optional[JobData]:
        """Get job status.

        Args:
            job_id: Job ID to check

        Returns:
            Job data or None if not found
        """
        try:
            response = self.tracker.send_request({
                'action': 'get_job',
                'job_id': job_id
            })

            if 'error' in response:
                return None

            return JobData.from_dict(response['job'])

        except Exception as e:
            self.logger.error(f"Failed to get job status for {job_id}: {e}")
            return None

    def get_queue_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all queues.

        Returns:
            Dictionary with queue statistics
        """
        try:
            response = self.tracker.send_request({'action': 'get_stats'})
            return response.get('stats', {})

        except Exception as e:
            self.logger.error(f"Failed to get queue stats: {e}")
            return {}

    def shutdown(self) -> None:
        """Shutdown the queue manager."""
        self.distributor.close()
        self.tracker.stop_server()
        self.logger.info("NNG queue manager shut down")


# Global queue manager instance
_queue_manager: Optional[NNGQueueManager] = None


def get_queue_manager() -> NNGQueueManager:
    """Get global NNG queue manager instance.

    Returns:
        Global queue manager instance
    """
    global _queue_manager
    if _queue_manager is None:
        config = get_config()
        _queue_manager = NNGQueueManager(
            distributor_address=config.nng_distributor_address,
            tracker_address=config.nng_tracker_address
        )
        # Auto-start tracker server
        _queue_manager.start_tracker_server()
    return _queue_manager


def reset_queue_manager() -> None:
    """Reset global queue manager (mainly for testing)."""
    global _queue_manager
    if _queue_manager:
        _queue_manager.shutdown()
    _queue_manager = None