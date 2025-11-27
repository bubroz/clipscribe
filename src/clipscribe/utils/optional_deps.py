"""Optional dependency management for ClipScribe.

This module provides lazy loading and graceful fallbacks for optional dependencies
to reduce memory footprint and installation requirements for basic functionality.
"""

import importlib
from typing import Any, Dict, Optional


class OptionalDependencyError(ImportError):
    """Raised when an optional dependency is not available."""

    pass


class OptionalDependencyManager:
    """Manages optional dependencies with lazy loading and fallbacks."""

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._error_cache: Dict[str, str] = {}

    def import_optional(
        self, module_name: str, fallback: Optional[Any] = None, error_msg: Optional[str] = None
    ) -> Any:
        """Import an optional module with fallback.

        Args:
            module_name: Name of the module to import
            fallback: Fallback value if import fails
            error_msg: Custom error message

        Returns:
            The imported module or fallback

        Raises:
            OptionalDependencyError: If no fallback provided and import fails
        """
        if module_name in self._cache:
            return self._cache[module_name]

        if module_name in self._error_cache:
            if fallback is not None:
                return fallback
            raise OptionalDependencyError(self._error_cache[module_name])

        try:
            module = importlib.import_module(module_name)
            self._cache[module_name] = module
            return module
        except ImportError as e:
            error = error_msg or f"Optional dependency '{module_name}' is not installed. {str(e)}"
            self._error_cache[module_name] = error

            if fallback is not None:
                return fallback
            raise OptionalDependencyError(error)

    def has_dependency(self, module_name: str) -> bool:
        """Check if an optional dependency is available."""
        try:
            self.import_optional(module_name)
            return True
        except OptionalDependencyError:
            return False

    def require_dependency(self, module_name: str, purpose: str = "") -> Any:
        """Require an optional dependency, raising error if not available."""
        purpose_msg = f" Required for {purpose}." if purpose else ""
        return self.import_optional(
            module_name,
            error_msg=f"Dependency '{module_name}' is required but not installed.{purpose_msg}",
        )


# Global instance
optional_deps = OptionalDependencyManager()


# Convenience functions for common optional dependencies
def get_torch():
    """Get PyTorch with fallback."""
    return optional_deps.import_optional("torch", fallback=None)


def get_transformers():
    """Get transformers library with fallback."""
    return optional_deps.import_optional("transformers", fallback=None)


def get_spacy():
    """Get spaCy with fallback."""
    return optional_deps.import_optional("spacy", fallback=None)


def get_gliner():
    """Get GLiNER with fallback."""
    return optional_deps.import_optional("gliner", fallback=None)


def get_plotly():
    """Get plotly with fallback."""
    return optional_deps.import_optional("plotly", fallback=None)


def get_pdfkit():
    """Get pdfkit with fallback."""
    return optional_deps.import_optional("pdfkit", fallback=None)


def get_google_cloud_storage():
    """Get Google Cloud Storage client with fallback."""
    return optional_deps.import_optional("google.cloud.storage", fallback=None)


def get_google_cloud_aiplatform():
    """Get Google Cloud AI Platform with fallback."""
    return optional_deps.import_optional("google.cloud.aiplatform", fallback=None)


def get_redis():
    """Get Redis client with fallback."""
    return optional_deps.import_optional("redis", fallback=None)


def get_rq():
    """Get RQ (Redis Queue) with fallback."""
    return optional_deps.import_optional("rq", fallback=None)


def get_textual():
    """Get Textual TUI framework with fallback."""
    return optional_deps.import_optional("textual", fallback=None)


def get_streamlit():
    """Get Streamlit with fallback."""
    return optional_deps.import_optional("streamlit", fallback=None)


def get_fastapi():
    """Get FastAPI with fallback."""
    return optional_deps.import_optional("fastapi", fallback=None)


def get_uvicorn():
    """Get Uvicorn with fallback."""
    return optional_deps.import_optional("uvicorn", fallback=None)


# Feature availability checks
def has_ml_features() -> bool:
    """Check if ML features (spacy, transformers, torch) are available."""
    return all(
        [
            optional_deps.has_dependency("spacy"),
            optional_deps.has_dependency("transformers"),
            optional_deps.has_dependency("torch"),
        ]
    )


def has_enterprise_features() -> bool:
    """Check if enterprise features (GCP services) are available."""
    return all(
        [
            optional_deps.has_dependency("google.cloud.storage"),
            optional_deps.has_dependency("google.cloud.aiplatform"),
        ]
    )


def has_api_features() -> bool:
    """Check if API features (FastAPI, Redis) are available."""
    return all(
        [
            optional_deps.has_dependency("fastapi"),
            optional_deps.has_dependency("redis"),
            optional_deps.has_dependency("rq"),
        ]
    )


def has_viz_features() -> bool:
    """Check if visualization features are available."""
    return all([optional_deps.has_dependency("plotly"), optional_deps.has_dependency("pdfkit")])


def has_tui_features() -> bool:
    """Check if TUI features are available."""
    return optional_deps.has_dependency("textual")


def has_web_features() -> bool:
    """Check if web interface features are available."""
    return optional_deps.has_dependency("streamlit")
