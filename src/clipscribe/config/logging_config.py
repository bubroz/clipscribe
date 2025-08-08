"""Logging configuration for ClipScribe."""

import logging
from pathlib import Path
from typing import Optional, Type, Dict, Any

from rich.logging import RichHandler

def setup_logging(level: str = "INFO", log_dir: Path = Path("logs"), 
                  handler_class: Optional[Type[logging.Handler]] = None,
                  handler_args: Optional[Dict[str, Any]] = None):
    """Set up logging for the application."""
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "clipscribe.log"

    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()
        
    # Create file handler
    file_handler = logging.FileHandler(log_file)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    
    # Create console handler
    if handler_class:
        if handler_args is None:
            handler_args = {}
        console_handler = handler_class(**handler_args)
    else:
        console_handler = RichHandler(
            rich_tracebacks=True,
            tracebacks_show_locals=True
        )
        
    console_formatter = logging.Formatter("%(message)s")
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logging.info("Logging setup complete.")
