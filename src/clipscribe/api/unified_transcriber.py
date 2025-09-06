"""
Unified Transcriber API - Solves Critical Issue #1: API Method Mismatches

This module provides a single, unified interface for all transcription backends,
eliminating method signature differences and parameter mapping issues.

Key Features:
- Automatic parameter mapping across backends
- Method resolution with fallback chains
- Unified error handling and metrics
- Zero method mismatch failures
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Callable, Union, Type
from dataclasses import dataclass, field
from enum import Enum
import inspect
from datetime import datetime

from ..models import VideoIntelligence, VideoTranscript, VideoMetadata

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionResult:
    """
    Unified result format for the API abstraction layer.

    This provides a consistent interface regardless of backend.
    """
    transcript: str
    entities: List[Dict[str, Any]] = field(default_factory=list)
    relationships: List[Dict[str, Any]] = field(default_factory=list)
    key_points: List[Dict[str, Any]] = field(default_factory=list)
    summary: str = ""
    backend: str = "unknown"
    processing_cost: float = 0.0
    processing_time: float = 0.0

    def to_video_intelligence(self, metadata: Dict[str, Any]) -> VideoIntelligence:
        """
        Convert to VideoIntelligence format for compatibility.

        Args:
            metadata: Video metadata

        Returns:
            VideoIntelligence object
        """
        # Create VideoMetadata
        video_metadata = VideoMetadata(
            video_id=metadata.get("video_id", "unknown"),
            url=metadata.get("url"),
            title=metadata.get("title"),
            channel=metadata.get("channel", "unknown"),
            channel_id=metadata.get("channel_id", "unknown"),
            published_at=metadata.get("published_at", datetime.now()),
            duration=metadata.get("duration", 0),
            description=metadata.get("description")
        )

        # Create VideoTranscript
        video_transcript = VideoTranscript(
            full_text=self.transcript,
            segments=[]  # Could be enhanced later
        )

        # Convert entities to EnhancedEntity format
        from ..models import EnhancedEntity
        enhanced_entities = []
        for entity_data in self.entities:
            enhanced_entities.append(EnhancedEntity(
                name=entity_data.get("name", entity_data.get("entity", "Unknown")),
                type=entity_data.get("type", "UNKNOWN"),
                extraction_sources=entity_data.get("extraction_sources", ["unified_api"]),
                mention_count=entity_data.get("mention_count", entity_data.get("mentions", 1)),
                properties=entity_data
            ))

        # Convert relationships
        from ..models import Relationship
        relationships = []
        for rel_data in self.relationships:
            relationships.append(Relationship(
                subject=rel_data.get("subject", ""),
                predicate=rel_data.get("predicate", ""),
                object=rel_data.get("object", ""),
                confidence=rel_data.get("confidence", 0.5),
                evidence=rel_data.get("evidence")
            ))

        # Convert key points
        from ..models import KeyPoint
        keypoints = []
        for kp_data in self.key_points:
            keypoints.append(KeyPoint(
                text=kp_data.get("text", kp_data.get("point", "")),
                importance=kp_data.get("importance", 0.5),
                context=kp_data.get("context")
            ))

        return VideoIntelligence(
            metadata=video_metadata,
            transcript=video_transcript,
            entities=enhanced_entities,
            relationships=relationships,
            key_points=keypoints,
            summary=self.summary,
            processing_cost=self.processing_cost,
            processing_time=self.processing_time
        )


class BackendType(Enum):
    """Supported transcription backends."""
    # GEMINI = "gemini"  # Removed - using Voxtral-Grok
    VERTEX = "vertex"
    GROK = "grok"
    MOCK = "mock"


@dataclass
class BackendConfig:
    """Configuration for a transcription backend."""
    backend_type: BackendType
    name: str
    class_path: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    health_check_interval: int = 60  # seconds


@dataclass
class BackendHealth:
    """Health status of a backend."""
    backend_type: BackendType
    last_check: float
    is_healthy: bool
    error_count: int
    last_error: Optional[str] = None
    response_time: float = 0.0


class BackendRegistry:
    """
    Registry for managing transcription backends.

    Handles backend registration, health monitoring, and failover.
    """

    def __init__(self):
        self.backends: Dict[BackendType, Any] = {}
        self.health_status: Dict[BackendType, BackendHealth] = {}
        self.configs: Dict[BackendType, BackendConfig] = {}

    def register_backend(
        self,
        backend_type: BackendType,
        backend_class: Type,
        config: BackendConfig
    ) -> None:
        """
        Register a new backend with the registry.

        Args:
            backend_type: Type of backend
            backend_class: Backend class to instantiate
            config: Configuration for the backend
        """
        try:
            # Instantiate the backend
            backend_instance = backend_class(**config.parameters)

            # Register it
            self.backends[backend_type] = backend_instance
            self.configs[backend_type] = config

            # Initialize health status
            self.health_status[backend_type] = BackendHealth(
                backend_type=backend_type,
                last_check=time.time(),
                is_healthy=True,
                error_count=0
            )

            logger.info(f"Registered backend: {backend_type.value}")

        except Exception as e:
            logger.error(f"Failed to register backend {backend_type.value}: {e}")
            self.health_status[backend_type] = BackendHealth(
                backend_type=backend_type,
                last_check=time.time(),
                is_healthy=False,
                error_count=1,
                last_error=str(e)
            )

    def get_backend(self, backend_type: BackendType) -> Optional[Any]:
        """
        Get a backend instance by type.

        Args:
            backend_type: Type of backend to retrieve

        Returns:
            Backend instance if available and healthy, None otherwise
        """
        if backend_type not in self.backends:
            return None

        health = self.health_status.get(backend_type)
        if not health or not health.is_healthy:
            return None

        return self.backends[backend_type]

    def list_available_backends(self) -> List[BackendType]:
        """
        List all available (healthy) backends.

        Returns:
            List of available backend types
        """
        available = []
        for backend_type, health in self.health_status.items():
            if health.is_healthy:
                available.append(backend_type)
        return available

    def update_health(self, backend_type: BackendType, is_healthy: bool, error: Optional[str] = None) -> None:
        """
        Update health status of a backend.

        Args:
            backend_type: Backend to update
            is_healthy: Whether the backend is healthy
            error: Error message if unhealthy
        """
        if backend_type in self.health_status:
            health = self.health_status[backend_type]
            health.last_check = time.time()
            health.is_healthy = is_healthy

            if not is_healthy:
                health.error_count += 1
                health.last_error = error
            else:
                health.error_count = 0
                health.last_error = None

    def get_health_status(self, backend_type: BackendType) -> Optional[BackendHealth]:
        """Get health status for a backend."""
        return self.health_status.get(backend_type)


class ParameterMapper:
    """
    Intelligent parameter mapping across different backends.

    Handles parameter name differences, type conversions, and default values.
    """

    def __init__(self):
        # Parameter mapping definitions
        self.mappings = self._load_parameter_mappings()
        self.validators = self._load_validators()
        self.type_converters = self._load_type_converters()

    def _load_parameter_mappings(self) -> Dict[BackendType, Dict[str, str]]:
        """Load parameter name mappings for each backend."""
        return {
            BackendType.VERTEX: {
                "file_path": "gcs_uri",
                "audio_path": "video_path",
                "media_file": "content_uri",
                "duration_seconds": "duration",
                "metadata": "metadata",
                "language_code": "language"
            },
            BackendType.GROK: {
                "audio_path": "audio_file",
                "video_file": "input_file",
                "duration_seconds": "duration",
                "metadata": "metadata",
                "language_code": "lang",
                "file_path": "audio_file",
                "duration": "duration",
                "language": "lang"
            },
            BackendType.MOCK: {
                # Mock uses unified parameter names
            }
        }

    def _load_validators(self) -> Dict[BackendType, Dict[str, Callable]]:
        """Load parameter validators for each backend."""
        return {
            BackendType.GEMINI: {
                "file_path": self._validate_path,
                "duration_seconds": self._validate_duration
            },
            BackendType.VERTEX: {
                "gcs_uri": self._validate_gcs_uri,
                "duration": self._validate_duration
            },
            BackendType.GROK: {
                "content_path": self._validate_path,
                "length": self._validate_duration
            }
        }

    def _load_type_converters(self) -> Dict[str, Callable]:
        """Load type conversion functions."""
        return {
            "path_to_str": lambda x: str(x) if hasattr(x, '__str__') else x,
            "str_to_path": lambda x: Path(x) if isinstance(x, str) else x,
            "int_to_str": lambda x: str(x) if isinstance(x, int) else x,
            "str_to_int": lambda x: int(x) if isinstance(x, str) and x.isdigit() else x
        }

    def map_parameters(
        self,
        backend_type: BackendType,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Map parameters to backend-specific format.

        Args:
            backend_type: Target backend type
            params: Original parameters

        Returns:
            Mapped parameters for the backend
        """
        mapped_params = {}
        mapping = self.mappings.get(backend_type, {})

        for key, value in params.items():
            # Check if parameter needs mapping
            if key in mapping:
                new_key = mapping[key]

                # Apply validation if available
                if new_key in self.validators.get(backend_type, {}):
                    validator = self.validators[backend_type][new_key]
                    value = validator(value)

                mapped_params[new_key] = value
            elif backend_type == BackendType.GEMINI and key == "metadata":
                # Legacy Gemini handling - backend removed
                continue
            elif key in ["backend_preference", "force_backend"]:
                # Filter out API control parameters - these shouldn't go to backends
                continue
            else:
                # Keep original parameter if no mapping (for other backends)
                mapped_params[key] = value

        return mapped_params

    def _validate_path(self, path: Any) -> str:
        """Validate and convert path parameters."""
        if hasattr(path, '__str__'):
            return str(path)
        elif isinstance(path, str):
            return path
        else:
            raise ValueError(f"Invalid path parameter: {path}")

    def _validate_duration(self, duration: Any) -> int:
        """Validate duration parameters."""
        if isinstance(duration, (int, float)):
            return int(duration)
        elif isinstance(duration, str) and duration.isdigit():
            return int(duration)
        else:
            raise ValueError(f"Invalid duration parameter: {duration}")

    def _validate_gcs_uri(self, uri: str) -> str:
        """Validate GCS URI format."""
        if isinstance(uri, str):
            # Allow both GCS URIs and local paths for flexibility
            if uri.startswith("gs://") or uri.startswith("/"):
                return uri
            else:
                raise ValueError(f"Invalid GCS URI: {uri}")
        else:
            raise ValueError(f"Invalid GCS URI: {uri}")


class MethodResolver:
    """
    Resolves appropriate methods for different backends.

    Handles method name differences and signature inspection.
    """

    def __init__(self):
        self.method_priority = [
            "transcribe",
            "transcribe_audio",
            "transcribe_video",
            "process",
            "analyze",
            "extract"
        ]

    def resolve_method(
        self,
        backend: Any,
        operation: str = "transcribe"
    ) -> Optional[Callable]:
        """
        Resolve the appropriate method for an operation.

        Args:
            backend: Backend instance
            operation: Type of operation (transcribe, extract, etc.)

        Returns:
            Resolved method if found, None otherwise
        """
        # First try the primary operation method
        method_name = operation
        if hasattr(backend, method_name):
            method = getattr(backend, method_name)
            if self._is_compatible_method(method):
                return method

        # Fall back to method priority list
        for method_name in self.method_priority:
            if hasattr(backend, method_name):
                method = getattr(backend, method_name)
                if self._is_compatible_method(method):
                    logger.info(f"Resolved method {method_name} for operation {operation}")
                    return method

        return None

    def _is_compatible_method(self, method: Callable) -> bool:
        """
        Check if a method is compatible for transcription.

        Args:
            method: Method to check

        Returns:
            True if method is compatible
        """
        try:
            # Check if it's a bound method (has __self__ attribute)
            if hasattr(method, '__self__'):
                return True

            # Check signature for unbound methods
            sig = inspect.signature(method)
            params = list(sig.parameters.keys())

            # Must have at least one parameter (self for instance methods)
            if len(params) == 0:
                return False

            # Check for async capability
            if asyncio.iscoroutinefunction(method):
                return True

            # Allow sync methods too
            return True

        except Exception as e:
            logger.warning(f"Method inspection failed: {e}")
            return False


class UnifiedErrorHandler:
    """
    Unified error handling across all backends.

    Provides consistent error types and recovery strategies.
    """

    def __init__(self):
        self.error_mappings = self._load_error_mappings()
        self.recovery_strategies = self._load_recovery_strategies()

    def _load_error_mappings(self) -> Dict[str, str]:
        """Map backend-specific errors to unified types."""
        return {
            # Legacy Gemini error handling
            "InvalidArgument": "INVALID_PARAMETERS",
            "ResourceExhausted": "RATE_LIMIT_EXCEEDED",
            "PermissionDenied": "AUTHENTICATION_FAILED",

            # Vertex errors
            "google.api_core.exceptions.InvalidArgument": "INVALID_PARAMETERS",
            "google.api_core.exceptions.ResourceExhausted": "RATE_LIMIT_EXCEEDED",

            # Grok errors
            "httpx.HTTPStatusError": "API_ERROR",
            "httpx.TimeoutException": "TIMEOUT_ERROR",

            # Generic errors
            "TimeoutError": "TIMEOUT_ERROR",
            "ConnectionError": "CONNECTIVITY_ERROR",
            "ValueError": "VALIDATION_ERROR"
        }

    def _load_recovery_strategies(self) -> Dict[str, Callable]:
        """Load recovery strategies for different error types."""
        return {
            "RATE_LIMIT_EXCEEDED": self._retry_with_backoff,
            "TIMEOUT_ERROR": self._retry_with_timeout,
            "CONNECTIVITY_ERROR": self._retry_with_backoff,
            "API_ERROR": self._switch_backend
        }

    def handle_error(
        self,
        error: Exception,
        backend_type: BackendType,
        original_params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle an error with appropriate recovery strategy.

        Args:
            error: The error that occurred
            backend_type: Backend where error occurred
            original_params: Original parameters
            context: Additional context

        Returns:
            Error handling result with recovery strategy
        """
        error_type = self._classify_error(error)
        recovery_strategy = self.recovery_strategies.get(error_type, self._default_recovery)

        try:
            result = recovery_strategy(error, backend_type, original_params, context)
            logger.info(f"Applied recovery strategy {recovery_strategy.__name__} for {error_type}")
            return result
        except Exception as recovery_error:
            logger.error(f"Recovery strategy failed: {recovery_error}")
            return {
                "error": "RECOVERY_FAILED",
                "original_error": str(error),
                "recovery_error": str(recovery_error),
                "should_retry": False
            }

    def _classify_error(self, error: Exception) -> str:
        """Classify an error into unified type."""
        error_class = error.__class__.__name__
        module_name = error.__class__.__module__

        # Try full module.class name first
        full_name = f"{module_name}.{error_class}"
        if full_name in self.error_mappings:
            return self.error_mappings[full_name]

        # Try just class name
        if error_class in self.error_mappings:
            return self.error_mappings[error_class]

        # Default to unknown
        return "UNKNOWN_ERROR"

    def _retry_with_backoff(
        self,
        error: Exception,
        backend_type: BackendType,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Retry with exponential backoff."""
        return {
            "strategy": "RETRY_BACKOFF",
            "should_retry": True,
            "backoff_seconds": min(60, 2 ** context.get("retry_count", 0)),
            "max_retries": 3
        }

    def _retry_with_timeout(
        self,
        error: Exception,
        backend_type: BackendType,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Retry with increased timeout."""
        return {
            "strategy": "RETRY_TIMEOUT",
            "should_retry": True,
            "new_timeout": min(300, context.get("current_timeout", 60) * 2),
            "max_retries": 2
        }

    def _switch_backend(
        self,
        error: Exception,
        backend_type: BackendType,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Switch to a different backend."""
        return {
            "strategy": "SWITCH_BACKEND",
            "should_retry": True,
            "new_backend": self._select_alternative_backend(backend_type),
            "preserve_params": True
        }

    def _default_recovery(
        self,
        error: Exception,
        backend_type: BackendType,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Default recovery strategy."""
        return {
            "strategy": "FAIL_FAST",
            "should_retry": False,
            "error_message": f"Unhandled error: {str(error)}"
        }

    def _select_alternative_backend(self, failed_backend: BackendType) -> BackendType:
        """Select an alternative backend when one fails."""
        alternatives = {
            BackendType.GEMINI: BackendType.VERTEX,
            BackendType.VERTEX: BackendType.GEMINI,
            BackendType.GROK: BackendType.GEMINI
        }
        return alternatives.get(failed_backend, BackendType.GEMINI)


class MetricsCollector:
    """
    Collect and report metrics for the unified API.

    Tracks performance, errors, and backend usage.
    """

    def __init__(self):
        self.metrics = {
            "requests_total": 0,
            "requests_by_backend": {},
            "errors_total": 0,
            "errors_by_type": {},
            "response_times": [],
            "backend_switches": 0
        }

    def record_request(self, backend_type: BackendType) -> None:
        """Record a request."""
        self.metrics["requests_total"] += 1

        backend_key = backend_type.value
        if backend_key not in self.metrics["requests_by_backend"]:
            self.metrics["requests_by_backend"][backend_key] = 0
        self.metrics["requests_by_backend"][backend_key] += 1

    def record_error(self, error_type: str) -> None:
        """Record an error."""
        self.metrics["errors_total"] += 1

        if error_type not in self.metrics["errors_by_type"]:
            self.metrics["errors_by_type"][error_type] = 0
        self.metrics["errors_by_type"][error_type] += 1

    def record_response_time(self, duration: float) -> None:
        """Record response time."""
        self.metrics["response_times"].append(duration)

        # Keep only last 1000 measurements
        if len(self.metrics["response_times"]) > 1000:
            self.metrics["response_times"] = self.metrics["response_times"][-1000:]

    def record_backend_switch(self) -> None:
        """Record a backend switch."""
        self.metrics["backend_switches"] += 1

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        if self.metrics["response_times"]:
            avg_response_time = sum(self.metrics["response_times"]) / len(self.metrics["response_times"])
            max_response_time = max(self.metrics["response_times"])
            min_response_time = min(self.metrics["response_times"])
        else:
            avg_response_time = max_response_time = min_response_time = 0

        return {
            "total_requests": self.metrics["requests_total"],
            "requests_by_backend": self.metrics["requests_by_backend"],
            "total_errors": self.metrics["errors_total"],
            "errors_by_type": self.metrics["errors_by_type"],
            "avg_response_time": avg_response_time,
            "max_response_time": max_response_time,
            "min_response_time": min_response_time,
            "backend_switches": self.metrics["backend_switches"]
        }


class UnifiedTranscriberAPI:
    """
    Unified API for all transcription backends.

    This is the main entry point that solves the critical API mismatch issue.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the unified API.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.registry = BackendRegistry()
        self.parameter_mapper = ParameterMapper()
        self.method_resolver = MethodResolver()
        self.error_handler = UnifiedErrorHandler()
        self.metrics = MetricsCollector()

        # Register default backends
        self._register_default_backends()

        logger.info("Unified Transcriber API initialized")

    def _register_default_backends(self) -> None:
        """Register default transcription backends."""
        # Gemini removed - using Voxtral-Grok pipeline
        # API backends deprecated - use main CLI with VideoIntelligenceRetrieverV2
        logger.warning("Unified Transcriber API deprecated - use main CLI pipeline")

        # Register Vertex backend
        vertex_config = BackendConfig(
            backend_type=BackendType.VERTEX,
            name="Vertex AI",
            class_path="clipscribe.retrievers.vertex_ai_transcriber.VertexAITranscriber",
            parameters={}
        )
        self.registry.register_backend(
            BackendType.VERTEX,
            VertexAITranscriber,
            vertex_config
        )

        # Register Grok backend
        grok_config = BackendConfig(
            backend_type=BackendType.GROK,
            name="Grok 4",
            class_path="clipscribe.retrievers.grok_transcriber.GrokTranscriber",
            parameters={}
        )
        self.registry.register_backend(
            BackendType.GROK,
            GrokTranscriber,
            grok_config
        )

    async def transcribe(
        self,
        **kwargs
    ) -> TranscriptionResult:
        """
        Unified transcription method with hybrid fallback logic.

        This method automatically:
        - Selects appropriate backend (prefers Grok for sensitive content)
        - Maps parameters correctly
        - Resolves method signatures
        - Handles safety filter blocks by falling back to Grok
        - Handles errors gracefully
        - Collects metrics

        Args:
            **kwargs: Transcription parameters (backend agnostic)

        Returns:
            TranscriptionResult with unified format
        """
        start_time = time.time()
        attempted_backends = []

        try:
            # Step 1: Check for explicit backend preference
            if "force_backend" in kwargs:
                preferred_backend = kwargs["force_backend"]
                if isinstance(preferred_backend, str):
                    preferred_backend = BackendType(preferred_backend)
            elif "backend_preference" in kwargs and kwargs["backend_preference"]:
                # Handle list of preferences
                backend_pref = kwargs["backend_preference"]
                if isinstance(backend_pref, list) and len(backend_pref) > 0:
                    preferred_backend = backend_pref[0]
                    if isinstance(preferred_backend, str):
                        preferred_backend = BackendType(preferred_backend)
                else:
                    # Default: Determine if content is sensitive and prefer Grok
                    is_sensitive = self._is_sensitive_content(kwargs)
                    preferred_backend = BackendType.GROK if is_sensitive else BackendType.GEMINI
            else:
                # Default: Determine if content is sensitive and prefer Grok
                is_sensitive = self._is_sensitive_content(kwargs)
                preferred_backend = BackendType.GROK if is_sensitive else BackendType.GEMINI

            # Step 2: Try backends in order of preference
            backends_to_try = [preferred_backend]
            if preferred_backend != BackendType.GEMINI:
                backends_to_try.append(BackendType.GEMINI)
            if preferred_backend != BackendType.VERTEX:
                backends_to_try.append(BackendType.VERTEX)

            result = None
            final_backend = None

            for backend_type in backends_to_try:
                attempted_backends.append(backend_type)

                try:
                    backend = self.registry.get_backend(backend_type)
                    if not backend:
                        logger.warning(f"Backend {backend_type.value} not available, skipping")
                        continue

                    # Step 3: Map parameters for this backend
                    mapped_params = self.parameter_mapper.map_parameters(backend_type, kwargs)

                    # Step 4: Resolve method
                    method = self.method_resolver.resolve_method(backend, "transcribe")
                    if not method:
                        logger.warning(f"No compatible transcribe method found for {backend_type.value}")
                        continue

                    # Step 5: Execute with backend-specific error handling
                    result = await self._execute_with_backend_error_handling(
                        method, mapped_params, backend_type, kwargs
                    )

                    final_backend = backend_type
                    break  # Success, stop trying backends

                except Exception as e:
                    logger.warning(f"Backend {backend_type.value} failed: {e}")

                    # Check if this is a safety filter block that should trigger Grok fallback
                    if self._is_safety_filter_error(e) and backend_type != BackendType.GROK:
                        logger.info("Safety filter detected, will try Grok fallback")
                        continue  # Try next backend
                    else:
                        # Non-safety error, don't retry with other backends
                        raise e

            if not result:
                available_backends = [b.value for b in self.registry.list_available_backends()]
                raise RuntimeError(f"All backends failed. Attempted: {[b.value for b in attempted_backends]}. Available: {available_backends}")

            # Step 6: Normalize result
            normalized_result = self._normalize_result(result, final_backend)

            # Step 7: Record metrics
            self.metrics.record_request(final_backend)
            self.metrics.record_response_time(time.time() - start_time)

            if len(attempted_backends) > 1:
                logger.info(f"Successfully used {final_backend.value} after trying {attempted_backends}")
                self.metrics.record_backend_switch()

            return normalized_result

        except Exception as e:
            # Record error
            self.metrics.record_error(type(e).__name__)
            self.metrics.record_response_time(time.time() - start_time)

            logger.error(f"All transcription backends failed. Attempted: {[b.value for b in attempted_backends]}")
            raise RuntimeError(f"Unified transcription failed after trying {len(attempted_backends)} backends: {e}")

    async def _execute_with_backend_error_handling(
        self,
        method: Callable,
        params: Dict[str, Any],
        backend_type: BackendType,
        original_params: Dict[str, Any]
    ) -> Any:
        """
        Execute method with backend-specific error handling.

        Args:
            method: Method to execute
            params: Mapped parameters
            backend_type: Backend type
            original_params: Original parameters

        Returns:
            Method result

        Raises:
            Exception: If execution fails
        """
        try:
            # Execute the method
            if asyncio.iscoroutinefunction(method):
                result = await method(**params)
            else:
                result = method(**params)

            return result

        except Exception as e:
            # Log the error with backend context
            logger.warning(f"Error in {backend_type.value} backend: {e}")

            # Check for safety filter errors
            if self._is_safety_filter_error(e):
                logger.info(f"Safety filter error detected in {backend_type.value}")
                self.metrics.record_error("SAFETY_FILTER_BLOCK")

            raise e

    def _is_safety_filter_error(self, error: Exception) -> bool:
        """
        Check if an error is due to safety filter blocking.

        Args:
            error: The error to check

        Returns:
            True if it's a safety filter error
        """
        error_str = str(error).lower()
        error_message = getattr(error, 'message', '').lower()

        safety_indicators = [
            'safety',
            'blocked',
            'finish_reason',
            'content filter',
            'harmful',
            'inappropriate',
            'finish_reason: 2',  # Legacy Gemini safety block
            'content_policy',
            'safety_settings'
        ]

        return any(indicator in error_str or indicator in error_message for indicator in safety_indicators)

    def _select_backend(self, params: Dict[str, Any]) -> BackendType:
        """
        Select the appropriate backend based on parameters and availability.

        Args:
            params: Request parameters

        Returns:
            Selected backend type
        """
        # Check for explicit backend selection
        if "backend" in params:
            backend_name = params["backend"]
            try:
                return BackendType(backend_name)
            except ValueError:
                logger.warning(f"Unknown backend: {backend_name}, using default")

        # Check for content-based selection
        if self._is_sensitive_content(params):
            # Prefer Grok for sensitive content (when available)
            if BackendType.GROK in self.registry.list_available_backends():
                return BackendType.GROK

        # Default to Voxtral (Gemini removed)
        return BackendType.VERTEX  # Fallback to Vertex since Gemini is removed

    def _is_sensitive_content(self, params: Dict[str, Any]) -> bool:
        """
        Check if content appears to be sensitive.

        Args:
            params: Request parameters

        Returns:
            True if content appears sensitive
        """
        # This is a simple heuristic - will be enhanced with ML later
        sensitive_keywords = [
            "pegasus", "spyware", "surveillance", "intelligence",
            "military", "defense", "classified", "terrorism"
        ]

        text_content = ""
        if "metadata" in params and params["metadata"]:
            title = params["metadata"].get("title", "")
            description = params["metadata"].get("description", "")
            text_content = f"{title} {description}".lower()

        for keyword in sensitive_keywords:
            if keyword in text_content:
                return True

        return False

    async def _execute_with_error_handling(
        self,
        method: Callable,
        params: Dict[str, Any],
        backend_type: BackendType,
        original_params: Dict[str, Any]
    ) -> Any:
        """
        Execute method with comprehensive error handling.

        Args:
            method: Method to execute
            params: Mapped parameters
            backend_type: Backend type
            original_params: Original parameters

        Returns:
            Method result
        """
        retry_count = 0
        max_retries = 3
        context = {"retry_count": retry_count}

        while retry_count <= max_retries:
            try:
                # Execute the method
                if asyncio.iscoroutinefunction(method):
                    result = await method(**params)
                else:
                    result = method(**params)

                return result

            except Exception as e:
                retry_count += 1
                context["retry_count"] = retry_count

                if retry_count > max_retries:
                    raise e

                # Handle the error
                error_result = self.error_handler.handle_error(
                    e, backend_type, original_params, context
                )

                if not error_result.get("should_retry", False):
                    raise e

                # Apply recovery strategy
                await self._apply_recovery_strategy(error_result, backend_type)

    async def _apply_recovery_strategy(
        self,
        error_result: Dict[str, Any],
        backend_type: BackendType
    ) -> None:
        """
        Apply a recovery strategy.

        Args:
            error_result: Error handling result
            backend_type: Current backend type
        """
        strategy = error_result.get("strategy")

        if strategy == "RETRY_BACKOFF":
            backoff_seconds = error_result.get("backoff_seconds", 1)
            logger.info(f"Retrying after {backoff_seconds} seconds")
            await asyncio.sleep(backoff_seconds)

        elif strategy == "SWITCH_BACKEND":
            new_backend = error_result.get("new_backend")
            if new_backend:
                logger.info(f"Switching from {backend_type.value} to {new_backend.value}")
                self.metrics.record_backend_switch()

    def _normalize_result(
        self,
        result: Any,
        backend_type: BackendType
    ) -> TranscriptionResult:
        """
        Normalize result to unified format.

        Args:
            result: Backend-specific result
            backend_type: Backend that produced the result

        Returns:
            Normalized TranscriptionResult
        """
        # Define valid fields for TranscriptionResult
        valid_fields = {
            "transcript", "entities", "relationships", "key_points",
            "summary", "backend", "processing_cost", "processing_time"
        }
        
        # This is a simplified normalization - will be expanded
        if isinstance(result, dict):
            # Filter out any fields not in TranscriptionResult
            filtered_result = {
                k: v for k, v in result.items()
                if k in valid_fields
            }
            # Ensure backend is set
            filtered_result["backend"] = backend_type.value
            return TranscriptionResult(**filtered_result)
        elif hasattr(result, 'to_dict'):
            result_dict = result.to_dict()
            filtered_result = {
                k: v for k, v in result_dict.items()
                if k in valid_fields
            }
            filtered_result["backend"] = backend_type.value
            return TranscriptionResult(**filtered_result)
        else:
            # Fallback
            return TranscriptionResult(
                transcript=result.get("transcript", "") if isinstance(result, dict) else str(result),
                entities=result.get("entities", []) if isinstance(result, dict) else [],
                relationships=result.get("relationships", []) if isinstance(result, dict) else [],
                backend=backend_type.value
            )

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get API usage metrics.

        Returns:
            Metrics summary
        """
        return self.metrics.get_summary()

    def get_backend_health(self) -> Dict[str, Any]:
        """
        Get health status of all backends.

        Returns:
            Health status summary
        """
        health = {}
        for backend_type in BackendType:
            backend_health = self.registry.get_health_status(backend_type)
            if backend_health:
                health[backend_type.value] = {
                    "healthy": backend_health.is_healthy,
                    "last_check": backend_health.last_check,
                    "error_count": backend_health.error_count,
                    "last_error": backend_health.last_error
                }
        return health
