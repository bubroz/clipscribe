"""Logging configuration for ClipScribe.

Uses structlog to provide structured logging with rich console output.
"""

import logging
import structlog
from ..config.logging_config import setup_logging

def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a logger instance.

    Args:
        name: The name of the logger.

    Returns:
        A structlog logger instance.
    """
    return structlog.get_logger(name)
