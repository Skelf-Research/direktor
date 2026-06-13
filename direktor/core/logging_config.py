"""
Logging configuration for Direktor.
"""
import logging
import logging.handlers
import os
import sys
from typing import Optional
from pathlib import Path


class DirektorLogger:
    """Centralized logging configuration for Direktor."""

    def __init__(self,
                 name: str = "direktor",
                 level: str = "INFO",
                 log_file: Optional[str] = None,
                 log_dir: str = "logs"):
        """Initialize logger configuration.

        Args:
            name: Logger name
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional log file name. If None, uses {name}.log
            log_dir: Directory for log files
        """
        self.name = name
        self.level = getattr(logging, level.upper())
        self.log_dir = Path(log_dir)
        self.log_file = log_file or f"{name}.log"

        # Create logs directory if it doesn't exist
        self.log_dir.mkdir(exist_ok=True)

        self._setup_logger()

    def _setup_logger(self) -> None:
        """Set up logger with console and file handlers."""
        # Get or create logger
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(self.level)

        # Clear existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        self.logger.addHandler(console_handler)

        # File handler with rotation
        file_path = self.log_dir / self.log_file
        file_handler = logging.handlers.RotatingFileHandler(
            file_path,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        file_handler.setLevel(self.level)
        file_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(file_handler)

        # Error file handler
        error_file_path = self.log_dir / f"{self.name}_errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_file_path,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(error_handler)

    def get_logger(self) -> logging.Logger:
        """Get the configured logger instance."""
        return self.logger

    def set_level(self, level: str) -> None:
        """Change logging level.

        Args:
            level: New logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        new_level = getattr(logging, level.upper())
        self.logger.setLevel(new_level)
        self.level = new_level


class StageLogger:
    """Logger for individual processing stages."""

    def __init__(self, stage_name: str, job_id: str, base_logger: logging.Logger):
        """Initialize stage logger.

        Args:
            stage_name: Name of the processing stage
            job_id: Unique job identifier
            base_logger: Base logger instance
        """
        self.stage_name = stage_name
        self.job_id = job_id
        self.logger = base_logger

    def info(self, message: str) -> None:
        """Log info message with stage context."""
        self.logger.info(f"[{self.stage_name}:{self.job_id}] {message}")

    def warning(self, message: str) -> None:
        """Log warning message with stage context."""
        self.logger.warning(f"[{self.stage_name}:{self.job_id}] {message}")

    def error(self, message: str, exc_info: bool = False) -> None:
        """Log error message with stage context."""
        self.logger.error(f"[{self.stage_name}:{self.job_id}] {message}", exc_info=exc_info)

    def debug(self, message: str) -> None:
        """Log debug message with stage context."""
        self.logger.debug(f"[{self.stage_name}:{self.job_id}] {message}")

    def critical(self, message: str) -> None:
        """Log critical message with stage context."""
        self.logger.critical(f"[{self.stage_name}:{self.job_id}] {message}")

    def stage_start(self) -> None:
        """Log stage start."""
        self.info(f"Starting {self.stage_name} processing")

    def stage_complete(self, duration_seconds: float) -> None:
        """Log stage completion."""
        self.info(f"Completed {self.stage_name} processing in {duration_seconds:.2f}s")

    def stage_error(self, error: Exception) -> None:
        """Log stage error."""
        self.error(f"Error in {self.stage_name} processing: {str(error)}", exc_info=True)


# Global logger instance
_logger_instance: Optional[DirektorLogger] = None


def setup_logging(level: str = "INFO",
                  log_dir: str = "logs",
                  log_file: Optional[str] = None) -> logging.Logger:
    """Set up global logging configuration.

    Args:
        level: Logging level
        log_dir: Directory for log files
        log_file: Optional custom log file name

    Returns:
        Configured logger instance
    """
    global _logger_instance

    # Get level from environment if not provided
    if level == "INFO":
        level = os.getenv("LOG_LEVEL", "INFO")

    _logger_instance = DirektorLogger(
        level=level,
        log_dir=log_dir,
        log_file=log_file
    )

    return _logger_instance.get_logger()


def get_logger() -> logging.Logger:
    """Get the global logger instance.

    Returns:
        Global logger instance

    Raises:
        RuntimeError: If logging hasn't been set up yet
    """
    if _logger_instance is None:
        # Auto-setup with defaults if not already configured
        return setup_logging()
    return _logger_instance.get_logger()


def get_stage_logger(stage_name: str, job_id: str) -> StageLogger:
    """Get a stage-specific logger.

    Args:
        stage_name: Name of the processing stage
        job_id: Unique job identifier

    Returns:
        Stage logger instance
    """
    base_logger = get_logger()
    return StageLogger(stage_name, job_id, base_logger)


def reset_logging() -> None:
    """Reset global logging (mainly for testing)."""
    global _logger_instance
    if _logger_instance:
        # Close all handlers
        for handler in _logger_instance.logger.handlers:
            handler.close()
        _logger_instance.logger.handlers.clear()
    _logger_instance = None