"""
Unified API Layer for ClipScribe

This package provides a unified interface for all external APIs,
eliminating method mismatches and parameter mapping issues.
"""

from .unified_transcriber import (
    UnifiedTranscriberAPI,
    BackendType,
    BackendConfig,
    BackendRegistry,
    ParameterMapper,
    MethodResolver,
    UnifiedErrorHandler,
    MetricsCollector
)

__all__ = [
    "UnifiedTranscriberAPI",
    "BackendType",
    "BackendConfig",
    "BackendRegistry",
    "ParameterMapper",
    "MethodResolver",
    "UnifiedErrorHandler",
    "MetricsCollector"
]
