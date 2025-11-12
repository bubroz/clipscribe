"""
Grok Prompt Caching Utility

Manages prompt caching for cost optimization with xAI Grok API.
Automatic caching introduced in May 2025 reduces input token costs by 50%
for repeated prompt prefixes >1024 tokens.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


@dataclass
class CacheStats:
    """Statistics for prompt caching performance."""

    hits: int = 0
    misses: int = 0
    total_savings: float = 0.0
    cached_tokens: int = 0
    total_tokens: int = 0
    last_updated: datetime = field(default_factory=datetime.now)

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate percentage."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0

    @property
    def avg_savings_per_request(self) -> float:
        """Calculate average savings per request."""
        total = self.hits + self.misses
        return (self.total_savings / total) if total > 0 else 0.0


class GrokPromptCache:
    """
    Manages cached prompts for cost optimization with Grok API.

    xAI's automatic caching (May 2025):
    - Caches prompt prefixes >1024 tokens automatically
    - 50% discount on cached input tokens
    - Same prefix within cache TTL = cache hit
    - No API changes needed - automatic detection

    This class tracks cache performance and estimates savings.
    """

    def __init__(self):
        """Initialize prompt cache manager."""
        self.stats = CacheStats()
        self._cache_threshold = 1024  # Minimum tokens for caching

        logger.info("GrokPromptCache initialized (automatic caching via xAI)")

    def build_cached_message(
        self, system_prompt: str, user_content: str, use_caching: bool = True
    ) -> List[Dict[str, str]]:
        """
        Build message structure optimized for prompt caching.

        Best practices for caching:
        1. Put stable content (system prompt) first
        2. Put variable content (user input) last
        3. Ensure system prompt >1024 tokens for caching
        4. Use consistent system prompts across requests

        Args:
            system_prompt: Stable system prompt (will be cached if >1024 tokens)
            user_content: Variable user input (not cached)
            use_caching: Whether to optimize for caching (default True)

        Returns:
            List of message dictionaries
        """
        if use_caching:
            # Optimal structure for caching: system message first
            return [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ]
        else:
            # Non-cached structure (combined message)
            combined = f"{system_prompt}\n\n{user_content}"
            return [{"role": "user", "content": combined}]

    def record_api_response(
        self, usage_stats: Dict[str, int], cost_breakdown: Dict[str, float]
    ) -> None:
        """
        Record cache performance from API response.

        Args:
            usage_stats: Token usage from response (includes cached_tokens)
            cost_breakdown: Cost breakdown (includes cache_savings)
        """
        cached_tokens = usage_stats.get("cached_tokens", 0)
        total_tokens = usage_stats.get("total_tokens", 0)
        cache_savings = cost_breakdown.get("cache_savings", 0.0)

        # Record cache hit or miss
        if cached_tokens > 0:
            self.stats.hits += 1
            self.stats.cached_tokens += cached_tokens
            self.stats.total_savings += cache_savings
            logger.debug(f"Cache HIT: {cached_tokens} tokens cached, ${cache_savings:.4f} saved")
        else:
            self.stats.misses += 1
            logger.debug("Cache MISS: No cached tokens")

        self.stats.total_tokens += total_tokens
        self.stats.last_updated = datetime.now()

    def estimate_cache_savings(
        self, input_tokens: int, cache_hit: bool, model: str = "grok-4-fast-reasoning"
    ) -> float:
        """
        Estimate cost savings from caching with correct xAI pricing.
        
        xAI Pricing (November 2025):
        - Input: $0.20 per 1M tokens
        - Cached: $0.05 per 1M tokens (75% savings!)
        
        Source: https://docs.x.ai/docs/pricing

        Args:
            input_tokens: Number of input tokens that could be cached
            cache_hit: Whether this would be a cache hit
            model: Model being used (grok-4-fast-reasoning or grok-4-fast-non-reasoning)

        Returns:
            Estimated savings in USD
        """
        if not cache_hit or input_tokens < self._cache_threshold:
            return 0.0

        # Pricing per 1M tokens (November 2025)
        pricing = {
            "grok-4-fast-reasoning": 0.20,
            "grok-4-fast-non-reasoning": 0.20,
            "grok-4-fast": 0.20,  # Alias
            "grok-4-fast-reasoning-latest": 0.20,  # Alias
        }

        rate = pricing.get(model, pricing["grok-4-fast-reasoning"])

        # 75% savings on cached tokens (cached=$0.05 vs input=$0.20)
        full_cost = (input_tokens / 1_000_000) * rate
        cached_cost = full_cost * 0.25  # Pay 25% of input price for cached
        savings = full_cost - cached_cost  # 75% savings

        return round(savings, 6)

    def should_use_caching(self, system_prompt: str) -> bool:
        """
        Determine if prompt caching would be beneficial.

        Args:
            system_prompt: System prompt to evaluate

        Returns:
            True if caching is recommended
        """
        # Rough estimate: 4 characters per token
        estimated_tokens = len(system_prompt) // 4

        return estimated_tokens >= self._cache_threshold

    def get_stats_summary(self) -> Dict[str, Any]:
        """
        Get summary of caching statistics.

        Returns:
            Dict with cache performance metrics
        """
        return {
            "total_requests": self.stats.hits + self.stats.misses,
            "cache_hits": self.stats.hits,
            "cache_misses": self.stats.misses,
            "hit_rate_percent": round(self.stats.hit_rate, 2),
            "total_savings_usd": round(self.stats.total_savings, 4),
            "avg_savings_per_request_usd": round(self.stats.avg_savings_per_request, 4),
            "cached_tokens_total": self.stats.cached_tokens,
            "total_tokens_processed": self.stats.total_tokens,
            "last_updated": self.stats.last_updated.isoformat(),
        }

    def reset_stats(self) -> None:
        """Reset cache statistics."""
        self.stats = CacheStats()
        logger.info("Cache statistics reset")

    def log_stats(self) -> None:
        """Log current cache statistics."""
        summary = self.get_stats_summary()
        logger.info(
            f"Cache Stats: {summary['cache_hits']}/{summary['total_requests']} hits "
            f"({summary['hit_rate_percent']}%), "
            f"${summary['total_savings_usd']:.4f} saved"
        )


# Global cache instance
_global_cache = None


def get_prompt_cache() -> GrokPromptCache:
    """
    Get or create global prompt cache instance.

    Returns:
        Global GrokPromptCache instance
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = GrokPromptCache()
    return _global_cache
