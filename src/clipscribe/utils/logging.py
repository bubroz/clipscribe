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
import os

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


def setup_logging(level: str = None) -> None:
    """
    Configure logging for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    # Get log level from environment or parameter
    if level is None:
        level = os.getenv('CLIPSCRIBE_LOG_LEVEL', 'INFO')
    
    # Convert string to logging level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers
    root_logger.handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(numeric_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Also set level for specific loggers
    logging.getLogger('clipscribe').setLevel(numeric_level)


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