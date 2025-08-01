"""Logging configuration for ClipScribe.

Uses structlog to provide structured logging with rich console output.
"""

import structlog
from ..config.logging_config import setup_logging

# Set up logging on module import
setup_logging()

def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a logger instance.
    """
    return structlog.get_logger(name)
