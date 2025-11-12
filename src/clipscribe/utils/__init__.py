"""
ClipScribe utilities package.

Provides utility functions and classes for video processing, progress tracking,
performance monitoring, batch processing.
"""

from .batch_progress import BatchProgress
from .file_utils import calculate_sha256

# Lazy-load PerformanceDashboard (requires streamlit - dev dependency)
# from .performance_dashboard import PerformanceDashboard
from .filename import (
    create_output_filename,
    create_output_structure,
    create_structured_filename,
    extract_platform_from_url,
    extract_video_id_from_url,
    sanitize_filename,
)
from .logger_setup import setup_logging
from .performance import PerformanceMonitor
from .progress import ClipScribeProgress, console, progress_tracker
from .prompt_cache import GrokPromptCache, get_prompt_cache

# from .web_research import WebResearchIntegrator  # Removed - uses Gemini

__all__ = [
    "setup_logging",
    "ClipScribeProgress",
    "progress_tracker",
    "console",
    "BatchProgress",
    "PerformanceMonitor",
    # "PerformanceDashboard",  # Dev-only (requires streamlit)
    "create_output_filename",
    "sanitize_filename",
    "extract_platform_from_url",
    "extract_video_id_from_url",
    "create_structured_filename",
    "create_output_structure",
    "calculate_sha256",
    "GrokPromptCache",
    "get_prompt_cache",
    # "WebResearchIntegrator",  # Removed - uses Gemini
]
