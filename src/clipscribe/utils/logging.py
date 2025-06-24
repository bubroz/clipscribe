"""Logging configuration for ClipScribe.

Provides structured logging with both file and console outputs.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional
import json

from rich.logging import RichHandler
from rich.console import Console


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'video_url'):
            log_data['video_url'] = record.video_url
        if hasattr(record, 'transcript_id'):
            log_data['transcript_id'] = record.transcript_id
        if hasattr(record, 'cost'):
            log_data['cost'] = record.cost
        if hasattr(record, 'duration'):
            log_data['duration'] = record.duration
            
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_data)


def setup_logging(
    log_level: str = "INFO",
    log_dir: Optional[Path] = None,
    console: Optional[Console] = None
) -> None:
    """Configure application logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_dir: Directory for log files (default: logs/)
        console: Rich console for pretty console output
    """
    # Create log directory
    if log_dir is None:
        log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.handlers.clear()
    
    # Console handler with Rich
    if console is None:
        console = Console()
        
    console_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=False,
        markup=True
    )
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    
    # File handler for structured logs
    log_file = log_dir / f"clipscribe_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(StructuredFormatter())
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    
    # Error file handler
    error_file = log_dir / "errors.log"
    error_handler = RotatingFileHandler(
        error_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3
    )
    error_handler.setFormatter(StructuredFormatter())
    error_handler.setLevel(logging.ERROR)
    logger.addHandler(error_handler)
    
    # Log startup
    logger.info(
        "ClipScribe logging initialized",
        extra={
            "log_level": log_level,
            "log_dir": str(log_dir),
            "handlers": ["console", "file", "error"]
        }
    )


class TranscriptionLogger:
    """Context manager for logging transcription operations."""
    
    def __init__(self, video_url: str, logger: Optional[logging.Logger] = None):
        """Initialize transcription logger.
        
        Args:
            video_url: URL of the video being transcribed
            logger: Logger instance (uses root logger if None)
        """
        self.video_url = video_url
        self.logger = logger or logging.getLogger(__name__)
        self.start_time = None
        self.transcript_id = None
        
    def __enter__(self):
        """Start transcription logging."""
        self.start_time = datetime.now()
        self.transcript_id = f"transcript_{self.start_time.strftime('%Y%m%d_%H%M%S')}"
        
        self.logger.info(
            "Starting transcription",
            extra={
                "video_url": self.video_url,
                "transcript_id": self.transcript_id
            }
        )
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Complete transcription logging."""
        duration = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.info(
                "Transcription completed",
                extra={
                    "video_url": self.video_url,
                    "transcript_id": self.transcript_id,
                    "duration": duration
                }
            )
        else:
            self.logger.error(
                f"Transcription failed: {exc_val}",
                extra={
                    "video_url": self.video_url,
                    "transcript_id": self.transcript_id,
                    "duration": duration,
                    "error_type": exc_type.__name__
                },
                exc_info=True
            )
            
        return False  # Don't suppress exceptions
    
    def log_cost(self, cost: float) -> None:
        """Log transcription cost."""
        self.logger.info(
            f"Transcription cost: ${cost:.4f}",
            extra={
                "video_url": self.video_url,
                "transcript_id": self.transcript_id,
                "cost": cost
            }
        ) 