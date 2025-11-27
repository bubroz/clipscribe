"""
Retry Manager for ClipScribe - Implements exponential backoff, circuit breaker,
and dead letter queue patterns for robust job processing.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable, Dict, Optional

# Import redis conditionally
try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_attempts: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    backoff_factor: float = 2.0
    jitter: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 300  # 5 minutes
    dead_letter_ttl: int = 604800  # 7 days


@dataclass
class RetryState:
    """State tracking for retry operations."""

    attempt: int = 0
    last_attempt: Optional[datetime] = None
    next_retry: Optional[datetime] = None
    failures: int = 0
    circuit_breaker_tripped: bool = False
    circuit_breaker_until: Optional[datetime] = None


class RetryManager:
    """Manages retry logic with exponential backoff and circuit breaker patterns."""

    def __init__(self, redis_conn=None, config: Optional[RetryConfig] = None):
        self.redis = redis_conn if REDIS_AVAILABLE else None
        self.config = config or RetryConfig()
        self._circuit_breaker_state: Dict[str, RetryState] = {}

    def _get_retry_key(self, operation_id: str) -> str:
        """Get Redis key for retry state."""
        return f"cs:retry:{operation_id}"

    def _load_retry_state(self, operation_id: str) -> RetryState:
        """Load retry state from Redis or create new."""
        if not REDIS_AVAILABLE or not self.redis:
            return RetryState()

        try:
            key = self._get_retry_key(operation_id)
            data = self.redis.get(key)
            if data:
                state_dict = json.loads(data.decode())
                return RetryState(
                    attempt=state_dict.get("attempt", 0),
                    last_attempt=(
                        datetime.fromisoformat(state_dict["last_attempt"])
                        if state_dict.get("last_attempt")
                        else None
                    ),
                    next_retry=(
                        datetime.fromisoformat(state_dict["next_retry"])
                        if state_dict.get("next_retry")
                        else None
                    ),
                    failures=state_dict.get("failures", 0),
                    circuit_breaker_tripped=state_dict.get("circuit_breaker_tripped", False),
                    circuit_breaker_until=(
                        datetime.fromisoformat(state_dict["circuit_breaker_until"])
                        if state_dict.get("circuit_breaker_until")
                        else None
                    ),
                )
        except Exception as e:
            logger.warning(f"Failed to load retry state for {operation_id}: {e}")

        return RetryState()

    def _save_retry_state(self, operation_id: str, state: RetryState):
        """Save retry state to Redis."""
        if not REDIS_AVAILABLE or not self.redis:
            return

        try:
            key = self._get_retry_key(operation_id)
            state_dict = {
                "attempt": state.attempt,
                "last_attempt": state.last_attempt.isoformat() if state.last_attempt else None,
                "next_retry": state.next_retry.isoformat() if state.next_retry else None,
                "failures": state.failures,
                "circuit_breaker_tripped": state.circuit_breaker_tripped,
                "circuit_breaker_until": (
                    state.circuit_breaker_until.isoformat() if state.circuit_breaker_until else None
                ),
            }
            self.redis.set(key, json.dumps(state_dict), ex=self.config.dead_letter_ttl)
        except Exception as e:
            logger.warning(f"Failed to save retry state for {operation_id}: {e}")

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for exponential backoff."""
        delay = min(
            self.config.base_delay * (self.config.backoff_factor**attempt), self.config.max_delay
        )

        if self.config.jitter:
            # Add random jitter (±25%)
            import random

            jitter_factor = random.uniform(0.75, 1.25)
            delay *= jitter_factor

        return delay

    def _check_circuit_breaker(self, operation_id: str, state: RetryState) -> bool:
        """Check if circuit breaker should trip."""
        if state.circuit_breaker_tripped:
            if state.circuit_breaker_until and datetime.now() < state.circuit_breaker_until:
                return False  # Still tripped
            else:
                # Reset circuit breaker
                state.circuit_breaker_tripped = False
                state.circuit_breaker_until = None
                state.failures = 0
                return True

        if state.failures >= self.config.circuit_breaker_threshold:
            # Trip circuit breaker
            state.circuit_breaker_tripped = True
            state.circuit_breaker_until = datetime.now() + timedelta(
                seconds=self.config.circuit_breaker_timeout
            )
            logger.warning(
                f"Circuit breaker tripped for {operation_id}, resetting at {state.circuit_breaker_until}"
            )
            return False

        return True

    async def execute_with_retry(
        self,
        operation_id: str,
        operation: Callable[[], Awaitable[Any]],
        should_retry: Optional[Callable[[Exception], bool]] = None,
    ) -> Any:
        """
        Execute operation with retry logic.

        Args:
            operation_id: Unique identifier for this operation
            operation: Async callable to execute
            should_retry: Optional function to determine if exception should be retried

        Returns:
            Result of the operation

        Raises:
            Exception: Last exception if all retries exhausted
        """
        state = self._load_retry_state(operation_id)

        while state.attempt < self.config.max_attempts:
            try:
                # Check circuit breaker
                if not self._check_circuit_breaker(operation_id, state):
                    raise CircuitBreakerException(
                        f"Circuit breaker active for {operation_id} until {state.circuit_breaker_until}"
                    )

                # Execute operation
                result = await operation()

                # Success - reset failure count
                if state.failures > 0:
                    state.failures = 0
                    logger.info(
                        f"Operation {operation_id} recovered after {state.attempt} attempts"
                    )

                # Clean up successful state
                if self.redis:
                    self.redis.delete(self._get_retry_key(operation_id))

                return result

            except Exception as e:
                state.attempt += 1
                state.failures += 1
                state.last_attempt = datetime.now()

                # Check if we should retry this exception
                if should_retry and not should_retry(e):
                    logger.info(f"Operation {operation_id} failed with non-retryable error: {e}")
                    raise

                # Check if we've exhausted retries
                if state.attempt >= self.config.max_attempts:
                    logger.error(
                        f"Operation {operation_id} failed after {state.attempt} attempts: {e}"
                    )

                    # Move to dead letter queue
                    self._move_to_dead_letter(operation_id, e, state)
                    raise MaxRetriesExceededException(
                        f"Operation {operation_id} failed after {state.attempt} attempts: {e}"
                    )

                # Calculate next retry time
                delay = self._calculate_delay(state.attempt - 1)
                state.next_retry = datetime.now() + timedelta(seconds=delay)

                logger.warning(
                    f"Operation {operation_id} attempt {state.attempt} failed: {e}. Retrying in {delay:.1f}s"
                )

                # Save state and wait
                self._save_retry_state(operation_id, state)
                await asyncio.sleep(delay)

        # This should never be reached, but just in case
        raise MaxRetriesExceededException(f"Unexpected retry loop exit for {operation_id}")

    def _move_to_dead_letter(self, operation_id: str, error: Exception, state: RetryState):
        """Move failed operation to dead letter queue."""
        if not REDIS_AVAILABLE or not self.redis:
            return

        try:
            dead_letter_key = f"cs:dead_letter:{operation_id}"
            dead_letter_data = {
                "operation_id": operation_id,
                "error": str(error),
                "error_type": type(error).__name__,
                "attempts": state.attempt,
                "last_attempt": state.last_attempt.isoformat() if state.last_attempt else None,
                "created_at": datetime.now().isoformat(),
            }

            self.redis.set(
                dead_letter_key, json.dumps(dead_letter_data), ex=self.config.dead_letter_ttl
            )
            logger.info(f"Moved operation {operation_id} to dead letter queue")
        except Exception as e:
            logger.error(f"Failed to move {operation_id} to dead letter queue: {e}")

    def get_retry_status(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get current retry status for an operation."""
        state = self._load_retry_state(operation_id)
        if state.attempt == 0:
            return None

        return {
            "attempt": state.attempt,
            "max_attempts": self.config.max_attempts,
            "failures": state.failures,
            "last_attempt": state.last_attempt.isoformat() if state.last_attempt else None,
            "next_retry": state.next_retry.isoformat() if state.next_retry else None,
            "circuit_breaker_tripped": state.circuit_breaker_tripped,
            "circuit_breaker_until": (
                state.circuit_breaker_until.isoformat() if state.circuit_breaker_until else None
            ),
        }

    def reset_retry_state(self, operation_id: str):
        """Reset retry state for an operation."""
        if self.redis:
            self.redis.delete(self._get_retry_key(operation_id))
        if operation_id in self._circuit_breaker_state:
            del self._circuit_breaker_state[operation_id]

    def get_dead_letter_queue(self, limit: int = 100) -> list:
        """Get contents of dead letter queue."""
        if not REDIS_AVAILABLE or not self.redis:
            return []

        try:
            pattern = "cs:dead_letter:*"
            keys = self.redis.keys(pattern)
            if not keys:
                return []

            dead_letters = []
            for key in keys[:limit]:
                try:
                    data = self.redis.get(key)
                    if data:
                        dead_letters.append(json.loads(data.decode()))
                except Exception as e:
                    logger.warning(f"Failed to parse dead letter entry {key}: {e}")

            return dead_letters
        except Exception as e:
            logger.error(f"Failed to get dead letter queue: {e}")
            return []


class CircuitBreakerException(Exception):
    """Exception raised when circuit breaker is active."""

    pass


class MaxRetriesExceededException(Exception):
    """Exception raised when maximum retry attempts exceeded."""

    pass


# Default retry manager instance
default_retry_manager: Optional[RetryManager] = None


def get_retry_manager(redis_conn=None) -> RetryManager:
    """Get or create default retry manager instance."""
    global default_retry_manager
    if default_retry_manager is None:
        default_retry_manager = RetryManager(redis_conn)
    return default_retry_manager


def should_retry_network_error(error: Exception) -> bool:
    """Determine if a network-related error should be retried."""
    retryable_errors = (
        ConnectionError,
        TimeoutError,
        OSError,  # Includes network-related OS errors
    )

    # Check for specific error messages
    error_msg = str(error).lower()
    retryable_messages = [
        "connection",
        "timeout",
        "network",
        "dns",
        "unreachable",
        "reset",
        "broken pipe",
    ]

    return isinstance(error, retryable_errors) or any(
        msg in error_msg for msg in retryable_messages
    )


def should_retry_api_error(error: Exception) -> bool:
    """Determine if an API-related error should be retried."""
    # Retry on 5xx errors, timeout, and some 4xx errors
    if hasattr(error, "response"):
        status_code = getattr(error.response, "status_code", None)
        if status_code:
            return status_code >= 500 or status_code in [408, 429]

    return should_retry_network_error(error)
