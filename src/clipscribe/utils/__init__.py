"""
ClipScribe utilities package.

Provides utility functions and classes for video processing, progress tracking,
performance monitoring, batch processing.
"""

from .logging import setup_logging
from .progress import ClipScribeProgress, progress_tracker, console
from .batch_progress import BatchProgress
from .performance import PerformanceMonitor
from .performance_dashboard import PerformanceDashboard
from .filename import (
    create_output_filename,
    sanitize_filename,
    extract_platform_from_url,
    extract_video_id_from_url,
    create_structured_filename,
    create_output_structure,
)
from .file_utils import calculate_sha256
# from .web_research import WebResearchIntegrator  # Removed - uses Gemini

__all__ = [
    "setup_logging",
    "ClipScribeProgress",
    "progress_tracker",
    "console",
    "BatchProgress",
    "PerformanceMonitor",
    "PerformanceDashboard",
    "create_output_filename",
    "sanitize_filename",
    "extract_platform_from_url",
    "extract_video_id_from_url",
    "create_structured_filename",
    "create_output_structure",
    "calculate_sha256",
    # "WebResearchIntegrator",  # Removed - uses Gemini
]
