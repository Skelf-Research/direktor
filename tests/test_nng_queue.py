"""
Tests for NNG-based queue management system.
"""
import pytest
import json
import time
import threading
from unittest.mock import Mock, patch, MagicMock

from direktor.core.nng_queue import (
    NNGQueueManager,
    NNGDistributor,
    NNGJobTracker,
    JobData,
    JobStatus,
    get_queue_manager,
    reset_queue_manager
)


class MockPyNNGSocket:
    """Mock pynng socket for testing."""

    def __init__(self):
        self.messages = []
        self.responses = []
        self.closed = False
        self.address = None

    def listen(self, address):
        self.address = address

    def dial(self, address):
        self.address = address

    def send(self, message):
        if self.closed:
            raise Exception("Socket closed")
        self.messages.append(message)

    def recv(self, timeout=None):
        if self.closed:
            raise Exception("Socket closed")
        if self.responses:
            return self.responses.pop(0)
        if timeout and timeout > 0:
            import pynng
            raise pynng.Timeout()
        return b'{"test": "message"}'

    def close(self):
        self.closed = True

    def add_response(self, response):
        if isinstance(response, str):
            response = response.encode('utf-8')
        self.responses.append(response)


class TestJobData:
    """Test cases for JobData class."""

    def test_job_data_creation(self):
        """Test JobData creation and initialization."""
        job = JobData(
            job_id="test_job",
            stage="script",
            status=JobStatus.PENDING,
            input_data={"test": "data"}
        )

        assert job.job_id == "test_job"
        assert job.stage == "script"
        assert job.status == JobStatus.PENDING
        assert job.input_data == {"test": "data"}
        assert job.output_data is None
        assert job.error_message is None
        assert job.retry_count == 0
        assert job.max_retries == 3
        assert job.created_at > 0

    def test_job_data_serialization(self):
        """Test JobData serialization and deserialization."""
        original_job = JobData(
            job_id="test_job",
            stage="script",
            status=JobStatus.PENDING,
            input_data={"test": "data"},
            max_retries=5
        )

        # Convert to dict
        job_dict = original_job.to_dict()
        assert job_dict['status'] == 'pending'
        assert job_dict['max_retries'] == 5

        # Convert back from dict
        restored_job = JobData.from_dict(job_dict)
        assert restored_job.job_id == original_job.job_id
        assert restored_job.stage == original_job.stage
        assert restored_job.status == original_job.status
        assert restored_job.input_data == original_job.input_data
        assert restored_job.max_retries == original_job.max_retries


@patch('direktor.core.nng_queue.pynng')
class TestNNGDistributor:
    """Test cases for NNGDistributor."""

    def setup_method(self):
        """Set up test environment."""
        self.mock_sockets = {}

    def create_mock_socket(self, socket_type):
        """Create a mock socket."""
        socket = MockPyNNGSocket()
        return socket

    def test_distributor_initialization(self, mock_pynng):
        """Test NNG distributor initialization."""
        distributor = NNGDistributor("tcp://127.0.0.1")
        assert distributor.base_address == "tcp://127.0.0.1"
        assert distributor.port_start == 5550

    def test_get_stage_address(self, mock_pynng):
        """Test stage address generation."""
        distributor = NNGDistributor("tcp://127.0.0.1")

        assert distributor.get_stage_address("script") == "tcp://127.0.0.1:5550"
        assert distributor.get_stage_address("audio") == "tcp://127.0.0.1:5551"
        assert distributor.get_stage_address("video") == "tcp://127.0.0.1:5555"

    def test_push_job(self, mock_pynng):
        """Test job pushing."""
        mock_pynng.Push0.return_value = self.create_mock_socket("push")

        distributor = NNGDistributor("tcp://127.0.0.1")
        job_data = {"job_id": "test", "stage": "script"}

        distributor.push_job("script", job_data)

        # Verify socket was created and message sent
        mock_pynng.Push0.assert_called_once()

    def test_pull_job(self, mock_pynng):
        """Test job pulling."""
        mock_socket = self.create_mock_socket("pull")
        mock_socket.add_response(json.dumps({"job_id": "test", "stage": "script"}))
        mock_pynng.Pull0.return_value = mock_socket

        distributor = NNGDistributor("tcp://127.0.0.1")
        job_data = distributor.pull_job("script", timeout_ms=1000)

        assert job_data is not None
        assert job_data["job_id"] == "test"
        assert job_data["stage"] == "script"

    def test_pull_job_timeout(self, mock_pynng):
        """Test job pulling with timeout."""
        mock_socket = self.create_mock_socket("pull")
        mock_pynng.Pull0.return_value = mock_socket
        mock_pynng.Timeout = Exception  # Mock the timeout exception

        # Mock timeout
        def mock_recv(timeout=None):
            raise mock_pynng.Timeout()

        mock_socket.recv = mock_recv

        distributor = NNGDistributor("tcp://127.0.0.1")
        job_data = distributor.pull_job("script", timeout_ms=100)

        assert job_data is None


@patch('direktor.core.nng_queue.pynng')
class TestNNGJobTracker:
    """Test cases for NNGJobTracker."""

    def test_job_tracker_initialization(self, mock_pynng):
        """Test job tracker initialization."""
        tracker = NNGJobTracker("tcp://127.0.0.1:5560")
        assert tracker.address == "tcp://127.0.0.1:5560"
        assert not tracker._running

    def test_handle_create_job_request(self, mock_pynng):
        """Test job creation request handling."""
        tracker = NNGJobTracker("tcp://127.0.0.1:5560")

        job_data = {
            "job_id": "test_job",
            "stage": "script",
            "status": "pending",
            "input_data": {"test": "data"},
            "created_at": time.time(),
            "retry_count": 0,
            "max_retries": 3
        }

        request = {
            "action": "create_job",
            "job": job_data
        }

        response = tracker._handle_request(request)

        assert response["status"] == "created"
        assert response["job_id"] == "test_job"
        assert "test_job" in tracker.jobs

    def test_handle_get_job_request(self, mock_pynng):
        """Test job retrieval request handling."""
        tracker = NNGJobTracker("tcp://127.0.0.1:5560")

        # First create a job
        job = JobData(
            job_id="test_job",
            stage="script",
            status=JobStatus.PENDING,
            input_data={"test": "data"}
        )
        tracker.jobs["test_job"] = job

        request = {
            "action": "get_job",
            "job_id": "test_job"
        }

        response = tracker._handle_request(request)

        assert "job" in response
        assert response["job"]["job_id"] == "test_job"
        assert response["job"]["stage"] == "script"

    def test_handle_update_job_request(self, mock_pynng):
        """Test job update request handling."""
        tracker = NNGJobTracker("tcp://127.0.0.1:5560")

        # First create a job
        job = JobData(
            job_id="test_job",
            stage="script",
            status=JobStatus.PENDING,
            input_data={"test": "data"}
        )
        tracker.jobs["test_job"] = job

        request = {
            "action": "update_job",
            "job_id": "test_job",
            "updates": {
                "status": "in_progress",
                "started_at": time.time()
            }
        }

        response = tracker._handle_request(request)

        assert response["status"] == "updated"
        assert tracker.jobs["test_job"].status == JobStatus.IN_PROGRESS

    def test_handle_get_stats_request(self, mock_pynng):
        """Test statistics request handling."""
        tracker = NNGJobTracker("tcp://127.0.0.1:5560")

        # Create some jobs
        jobs = [
            JobData("job1", "script", JobStatus.PENDING, {}),
            JobData("job2", "script", JobStatus.COMPLETED, {}),
            JobData("job3", "audio", JobStatus.IN_PROGRESS, {})
        ]

        for job in jobs:
            tracker.jobs[job.job_id] = job

        request = {"action": "get_stats"}
        response = tracker._handle_request(request)

        assert "stats" in response
        stats = response["stats"]

        assert "script" in stats
        assert "audio" in stats
        assert stats["script"]["total_jobs"] == 2
        assert stats["audio"]["total_jobs"] == 1
        assert stats["script"]["status_counts"]["pending"] == 1
        assert stats["script"]["status_counts"]["completed"] == 1


@patch('direktor.core.nng_queue.pynng')
@patch('direktor.core.nng_queue.get_config')
class TestNNGQueueManager:
    """Test cases for NNGQueueManager."""

    def setup_method(self):
        """Set up test environment."""
        reset_queue_manager()

    def teardown_method(self):
        """Clean up after test."""
        reset_queue_manager()

    def test_queue_manager_initialization(self, mock_get_config, mock_pynng):
        """Test queue manager initialization."""
        mock_config = Mock()
        mock_config.nng_distributor_address = "tcp://127.0.0.1"
        mock_config.nng_tracker_address = "tcp://127.0.0.1:5560"
        mock_get_config.return_value = mock_config

        queue_manager = NNGQueueManager("tcp://127.0.0.1", "tcp://127.0.0.1:5560")

        assert queue_manager.distributor is not None
        assert queue_manager.tracker is not None

    @patch('direktor.core.nng_queue.NNGJobTracker')
    @patch('direktor.core.nng_queue.NNGDistributor')
    def test_create_job(self, mock_distributor_class, mock_tracker_class, mock_get_config, mock_pynng):
        """Test job creation."""
        mock_config = Mock()
        mock_get_config.return_value = mock_config

        # Mock distributor and tracker
        mock_distributor = Mock()
        mock_tracker = Mock()
        mock_distributor_class.return_value = mock_distributor
        mock_tracker_class.return_value = mock_tracker

        # Mock tracker response
        mock_tracker.send_request.return_value = {"status": "created", "job_id": "test_job"}

        queue_manager = NNGQueueManager()
        input_data = {"text_content": "test content"}

        job_id = queue_manager.create_job("script", input_data, job_id="test_job")

        assert job_id == "test_job"
        mock_tracker.send_request.assert_called()
        mock_distributor.push_job.assert_called()

    @patch('direktor.core.nng_queue.NNGJobTracker')
    @patch('direktor.core.nng_queue.NNGDistributor')
    def test_complete_job(self, mock_distributor_class, mock_tracker_class, mock_get_config, mock_pynng):
        """Test job completion."""
        mock_config = Mock()
        mock_get_config.return_value = mock_config

        # Mock distributor and tracker
        mock_distributor = Mock()
        mock_tracker = Mock()
        mock_distributor_class.return_value = mock_distributor
        mock_tracker_class.return_value = mock_tracker

        # Mock tracker response
        mock_tracker.send_request.return_value = {"status": "updated"}

        queue_manager = NNGQueueManager()
        output_data = {"script_content": "generated script"}

        queue_manager.complete_job("test_job", output_data)

        # Verify tracker was called to update job
        mock_tracker.send_request.assert_called()
        call_args = mock_tracker.send_request.call_args[0][0]
        assert call_args["action"] == "update_job"
        assert call_args["job_id"] == "test_job"
        assert call_args["updates"]["status"] == "completed"

    def test_global_queue_manager(self, mock_get_config, mock_pynng):
        """Test global queue manager instance."""
        mock_config = Mock()
        mock_config.nng_distributor_address = "tcp://127.0.0.1"
        mock_config.nng_tracker_address = "tcp://127.0.0.1:5560"
        mock_get_config.return_value = mock_config

        # Reset before test
        reset_queue_manager()

        qm1 = get_queue_manager()
        qm2 = get_queue_manager()

        # Should return same instance
        assert qm1 is qm2

        # Reset and get new instance
        reset_queue_manager()
        qm3 = get_queue_manager()

        # Should be different instance after reset
        assert qm1 is not qm3