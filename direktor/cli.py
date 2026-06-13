"""
Modern CLI interface for Direktor with NNG-based distributed processing.
"""
import argparse
import os
import sys
import time
import signal
import atexit
from typing import Optional
from dotenv import load_dotenv

from .core.config import get_config
from .core.logging_config import setup_logging, get_logger
from .core.nng_queue import get_queue_manager, reset_queue_manager
from .core.base_processor import get_processor_registry
from .processors import *  # Import all processors to register them


def setup_environment() -> None:
    """Set up environment and configuration."""
    # Load environment variables
    load_dotenv()

    # Set up logging
    log_level = os.getenv("LOG_LEVEL", "INFO")
    setup_logging(level=log_level)

    # Validate configuration
    try:
        config = get_config()
        logger = get_logger()
        logger.info("Direktor initialized successfully")
    except Exception as e:
        print(f"Configuration error: {e}")
        sys.exit(1)


def cleanup_handler():
    """Cleanup handler for graceful shutdown."""
    try:
        reset_queue_manager()
    except:
        pass


def submit_job(input_file: str, optimize_content: bool = True) -> str:
    """Submit a new job to the processing pipeline.

    Args:
        input_file: Path to input text file
        optimize_content: Whether to optimize content before processing

    Returns:
        Job ID
    """
    logger = get_logger()

    # Validate input file
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    # Read input content
    with open(input_file, 'r', encoding='utf-8') as f:
        text_content = f.read()

    if not text_content.strip():
        raise ValueError("Input file is empty")

    # Submit to queue
    queue_manager = get_queue_manager()
    job_id = queue_manager.create_job(
        stage='script',
        input_data={
            'text_content': text_content,
            'optimize_content': optimize_content,
            'input_file': input_file
        }
    )

    logger.info(f"Job {job_id} submitted successfully")
    print(f"Job submitted: {job_id}")
    print(f"Track progress with: direktor status {job_id}")

    return job_id


def run_worker(stage: str, max_jobs: Optional[int] = None, timeout_ms: int = 30000) -> None:
    """Run a worker for a specific stage.

    Args:
        stage: Stage name to process
        max_jobs: Maximum number of jobs to process (None for unlimited)
        timeout_ms: Timeout in milliseconds for waiting for jobs
    """
    logger = get_logger()
    registry = get_processor_registry()

    # Create processor for stage
    processor = registry.create_processor(stage)
    if not processor:
        logger.error(f"No processor found for stage: {stage}")
        print(f"Error: Unknown stage '{stage}'")
        print(f"Available stages: {registry.get_available_stages()}")
        sys.exit(1)

    logger.info(f"Starting worker for stage: {stage}")
    print(f"🔄 Worker starting for stage: {stage}")
    print(f"⏱️  Timeout: {timeout_ms/1000:.1f}s")

    if max_jobs:
        print(f"📊 Will process max {max_jobs} jobs")

    # Run the worker
    try:
        processor.run_worker(max_jobs=max_jobs, timeout=timeout_ms//1000)
    except KeyboardInterrupt:
        print("\n⏹️  Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker error: {e}")
        print(f"❌ Worker error: {e}")
        sys.exit(1)


def run_tracker() -> None:
    """Run the job tracking server."""
    logger = get_logger()

    print("🗄️  Starting job tracking server...")

    try:
        queue_manager = get_queue_manager()
        print("✅ Job tracker running. Press Ctrl+C to stop.")

        # Keep the tracker running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n⏹️  Job tracker stopped by user")

    except Exception as e:
        logger.error(f"Tracker error: {e}")
        print(f"❌ Tracker error: {e}")
        sys.exit(1)


def check_job_status(job_id: str) -> None:
    """Check the status of a job.

    Args:
        job_id: Job ID to check
    """
    queue_manager = get_queue_manager()
    job = queue_manager.get_job_status(job_id)

    if not job:
        print(f"❌ Job {job_id} not found")
        return

    # Status emoji mapping
    status_emojis = {
        'pending': '⏳',
        'in_progress': '🔄',
        'completed': '✅',
        'failed': '❌',
        'retry': '🔄'
    }

    status_emoji = status_emojis.get(job.status.value, '❓')

    print(f"\n📋 Job Status: {job.job_id}")
    print(f"   Stage: {job.stage}")
    print(f"   Status: {status_emoji} {job.status.value.upper()}")
    print(f"   Created: {time.ctime(job.created_at)}")

    if job.started_at:
        print(f"   Started: {time.ctime(job.started_at)}")

    if job.completed_at:
        print(f"   Completed: {time.ctime(job.completed_at)}")
        duration = job.completed_at - (job.started_at or job.created_at)
        print(f"   Duration: {duration:.2f} seconds")

    if job.error_message:
        print(f"   Error: {job.error_message}")

    if job.retry_count > 0:
        print(f"   Retries: {job.retry_count}/{job.max_retries}")


def show_queue_stats() -> None:
    """Show statistics for all queues."""
    queue_manager = get_queue_manager()
    stats = queue_manager.get_queue_stats()

    print("\n📊 Queue Statistics")
    print("=" * 50)

    stage_emojis = {
        'script': '📝',
        'audio': '🎵',
        'transcript': '📑',
        'prompts': '🎨',
        'images': '🖼️',
        'video': '🎬'
    }

    for stage, stage_stats in stats.items():
        emoji = stage_emojis.get(stage, '📦')
        print(f"\n{emoji} {stage.upper()}:")
        print(f"   Total jobs: {stage_stats['total_jobs']}")

        for status, count in stage_stats['status_counts'].items():
            if count > 0:
                status_emoji = {
                    'pending': '⏳',
                    'in_progress': '🔄',
                    'completed': '✅',
                    'failed': '❌',
                    'retry': '🔄'
                }.get(status, '❓')
                print(f"   {status_emoji} {status}: {count}")


def run_pipeline(input_file: str, watch: bool = False) -> None:
    """Run the complete pipeline for a single job.

    Args:
        input_file: Path to input text file
        watch: Whether to watch job progress
    """
    print("🚀 Starting Direktor pipeline...")

    # Submit job
    job_id = submit_job(input_file)

    if not watch:
        print("\n💡 To watch progress, run: direktor watch")
        return

    print(f"\n👀 Watching job {job_id}...")

    queue_manager = get_queue_manager()
    last_status = None

    try:
        while True:
            job = queue_manager.get_job_status(job_id)
            if not job:
                print("❌ Job not found")
                break

            if job.status.value != last_status:
                status_emojis = {
                    'pending': '⏳',
                    'in_progress': '🔄',
                    'completed': '✅',
                    'failed': '❌',
                    'retry': '🔄'
                }
                emoji = status_emojis.get(job.status.value, '❓')
                print(f"{emoji} {job.stage}: {job.status.value}")
                last_status = job.status.value

            if job.status.value in ['completed', 'failed']:
                break

            time.sleep(2)

        if job and job.status.value == 'completed':
            print("\n🎉 Pipeline completed successfully!")
            if job.output_data and 'video_file' in job.output_data:
                print(f"📹 Video: {job.output_data['video_file']}")
        else:
            print(f"\n💥 Pipeline failed: {job.error_message if job else 'Unknown error'}")

    except KeyboardInterrupt:
        print("\n⏹️  Stopped watching")


def start_all_workers() -> None:
    """Start workers for all stages."""
    stages = ['script', 'audio', 'transcript', 'prompts', 'images', 'video']

    print("🔧 Starting all workers...")
    print("💡 This will run workers for all stages in the background")
    print("⚠️  Make sure the job tracker is running: direktor tracker")

    import subprocess
    import sys

    processes = []

    try:
        for stage in stages:
            cmd = [sys.executable, '-m', 'direktor.cli', 'worker', stage]
            proc = subprocess.Popen(cmd)
            processes.append((stage, proc))
            print(f"✅ Started {stage} worker (PID: {proc.pid})")

        print(f"\n🎯 All {len(stages)} workers started!")
        print("📊 Monitor with: direktor stats")
        print("⏹️  Stop with Ctrl+C")

        # Wait for user interrupt
        try:
            while True:
                time.sleep(1)
                # Check if any worker died
                for stage, proc in processes:
                    if proc.poll() is not None:
                        print(f"⚠️  Worker {stage} stopped unexpectedly")

        except KeyboardInterrupt:
            print("\n⏹️  Stopping all workers...")

    finally:
        # Clean shutdown
        for stage, proc in processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
                print(f"⏹️  Stopped {stage} worker")
            except:
                proc.kill()


def main() -> None:
    """Main CLI entry point."""
    # Register cleanup handler
    atexit.register(cleanup_handler)
    signal.signal(signal.SIGTERM, lambda s, f: cleanup_handler())

    parser = argparse.ArgumentParser(
        description="Direktor - AI-powered distributed video generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Submit a job and watch progress
  direktor submit input.txt --watch

  # Run job tracker (required for distributed processing)
  direktor tracker

  # Run worker for specific stage
  direktor worker script

  # Start all workers
  direktor workers

  # Check job status
  direktor status job_12345678

  # Show queue statistics
  direktor stats
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Submit command
    submit_parser = subparsers.add_parser('submit', help='Submit a new job')
    submit_parser.add_argument('input_file', help='Path to input text file')
    submit_parser.add_argument('--no-optimize', action='store_true',
                              help='Skip content optimization')
    submit_parser.add_argument('--watch', action='store_true',
                              help='Watch job progress')

    # Tracker command
    subparsers.add_parser('tracker', help='Run job tracking server')

    # Worker command
    worker_parser = subparsers.add_parser('worker', help='Run a stage worker')
    worker_parser.add_argument('stage', help='Stage to process',
                              choices=['script', 'audio', 'transcript', 'prompts', 'images', 'video'])
    worker_parser.add_argument('--max-jobs', type=int,
                              help='Maximum number of jobs to process')
    worker_parser.add_argument('--timeout', type=int, default=30,
                              help='Timeout in seconds for waiting for jobs')

    # Workers command (start all)
    subparsers.add_parser('workers', help='Start all workers')

    # Status command
    status_parser = subparsers.add_parser('status', help='Check job status')
    status_parser.add_argument('job_id', help='Job ID to check')

    # Stats command
    subparsers.add_parser('stats', help='Show queue statistics')

    # Pipeline command (submit + run workers)
    pipeline_parser = subparsers.add_parser('pipeline', help='Run complete pipeline')
    pipeline_parser.add_argument('input_file', help='Path to input text file')
    pipeline_parser.add_argument('--watch', action='store_true',
                                help='Watch job progress')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Set up environment
    setup_environment()

    try:
        if args.command == 'submit':
            submit_job(args.input_file, optimize_content=not args.no_optimize)
            if args.watch:
                # Get the job ID from submit and watch it
                pass  # Implementation would need to return job_id from submit

        elif args.command == 'tracker':
            run_tracker()

        elif args.command == 'worker':
            timeout_ms = args.timeout * 1000
            run_worker(args.stage, args.max_jobs, timeout_ms)

        elif args.command == 'workers':
            start_all_workers()

        elif args.command == 'status':
            check_job_status(args.job_id)

        elif args.command == 'stats':
            show_queue_stats()

        elif args.command == 'pipeline':
            run_pipeline(args.input_file, args.watch)

    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled")
        sys.exit(1)
    except Exception as e:
        logger = get_logger()
        logger.error(f"Error: {e}", exc_info=True)
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()