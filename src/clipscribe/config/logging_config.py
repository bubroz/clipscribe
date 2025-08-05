# src/clipscribe/config/logging_config.py
# This file is temporarily reverted to simplify debugging.
# The structlog implementation will be restored after the core
# application bugs are resolved.

import logging
import sys

def setup_logging(log_level: str = "INFO"):
    """
    Set up basic logging for the application.
    """
    logging.basicConfig(
        level=log_level.upper(),
        stream=sys.stderr,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
