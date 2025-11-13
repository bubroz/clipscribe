"""Grok intelligence extraction provider (wraps existing GrokAPIClient)."""

import json
import os
from typing import Optional, Dict
from ..base import (
    IntelligenceProvider,
    TranscriptResult,
    IntelligenceResult,
    ConfigurationError,
    ProcessingError,
)
from clipscribe.retrievers.grok_client import GrokAPIClient


class GrokProvider(IntelligenceProvider):
    """xAI Grok intelligence extraction (wraps existing GrokAPIClient).
    
    Features (all preserved from existing client):
    - Prompt caching (75% savings on cached tokens)
    - Two-tier pricing (<128K vs >128K context)
    - Server-side tools (web_search, x_search)
    - json_schema structured outputs
    - Detailed cost breakdown
    - Cache statistics tracking
    
    Pricing (<128K context, 99% of videos):
    - Input: $0.20/M tokens
    - Output: $0.50/M tokens
    - Cached: $0.05/M tokens (75% savings!)
    
    Typical cost: $0.002-0.005 for 30min video
    
    100% capability preservation by wrapping existing GrokAPIClient.
    
    Existing code: src/clipscribe/retrievers/grok_client.py
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "grok-4-fast-reasoning",
    ):
        """Initialize Grok provider.
        
        Args:
            api_key: xAI API key (or from XAI_API_KEY env var)
            model: Grok model to use
            
        Raises:
            ConfigurationError: If API key not provided
        """
        api_key = api_key or os.getenv("XAI_API_KEY")
        if not api_key:
            raise ConfigurationError(
                "XAI_API_KEY required.\n"
                "Get key from: https://x.ai/api\n"
                "Set via: export XAI_API_KEY=your_key"
            )
        
        # Reuse existing GrokAPIClient (preserves ALL features!)
        self.client = GrokAPIClient(api_key=api_key)
        self.model = model
    
    @property
    def name(self) -> str:
        """Provider identifier."""
        return "grok"
    
    async def extract(
        self,
        transcript: TranscriptResult,
        metadata: Optional[Dict] = None,
    ) -> IntelligenceResult:
        """Extract intelligence from transcript using Grok.
        
        Args:
            transcript: Transcription result
            metadata: Optional video/context metadata
            
        Returns:
            IntelligenceResult with entities, relationships, topics, etc.
            All Grok features preserved (caching, cost breakdown, etc.)
            
        Raises:
            ProcessingError: If extraction fails
        """
        try:
            # Build extraction prompt (reuse existing)
            from clipscribe.prompts.intelligence_extraction import create_intelligence_extraction_prompt
            from clipscribe.schemas_grok import get_video_intelligence_schema
            
            # Combine transcript segments into full text
            transcript_text = " ".join(seg.text for seg in transcript.segments)
            
            # Build prompt with metadata
            prompt = create_intelligence_extraction_prompt(transcript_text, metadata or {})
            
            # Call existing Grok client (ALL features preserved!)
            # Note: get_video_intelligence_schema() returns full response_format dict
            schema_format = get_video_intelligence_schema()
            
            response = await self.client.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a precise intelligence extraction system following strict quality standards."
                    },
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.1,
                max_tokens=4096,
                response_format=schema_format,  # Already includes "type": "json_schema" wrapper
            )
            
            # Parse JSON result
            content = response["choices"][0]["message"]["content"]
            result = json.loads(content)
            
            # Calculate cost using EXISTING client method (preserves all features!)
            usage = response.get("usage", {})
            cost_breakdown = self.client.calculate_cost(
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                cached_tokens=usage.get("cached_tokens", 0),
                model=self.model,
                return_breakdown=True,
            )
            
            # Build cache stats
            prompt_tokens = usage.get("prompt_tokens", 0)
            cached_tokens = usage.get("cached_tokens", 0)
            
            # Calculate CORRECT hit rate percentage
            # hit_rate = cached_tokens / (prompt_tokens + cached_tokens) * 100
            # Example: 50K prompt + 50K cached = 50% hit rate (not 100%!)
            total_input_tokens = prompt_tokens + cached_tokens
            hit_rate_percent = (cached_tokens / total_input_tokens * 100) if total_input_tokens > 0 else 0.0
            
            cache_stats = {
                "cache_hits": 1 if cached_tokens > 0 else 0,
                "cache_misses": 0 if cached_tokens > 0 else 1,
                "cached_tokens": cached_tokens,
                "prompt_tokens": prompt_tokens,
                "total_input_tokens": total_input_tokens,
                "cache_savings": cost_breakdown.get("cache_savings", 0),
                "hit_rate_percent": round(hit_rate_percent, 2),
            }
            
            return IntelligenceResult(
                entities=result.get("entities", []),
                relationships=result.get("relationships", []),
                topics=result.get("topics", []),
                key_moments=result.get("key_moments", []),
                sentiment=result.get("sentiment", {}),
                provider="grok",
                model=self.model,
                cost=cost_breakdown["total"],
                cost_breakdown=cost_breakdown,  # Full Grok breakdown preserved!
                cache_stats=cache_stats,        # Cache stats preserved!
                metadata={
                    "usage": usage,
                    "pricing_tier": cost_breakdown.get("pricing_tier"),
                    "context_tokens": cost_breakdown.get("context_tokens"),
                }
            )
            
        except json.JSONDecodeError as e:
            raise ProcessingError(f"Failed to parse Grok response: {e}")
        except Exception as e:
            raise ProcessingError(f"Grok extraction failed: {e}")
    
    def estimate_cost(self, transcript_length: int) -> float:
        """Estimate Grok processing cost.
        
        Args:
            transcript_length: Transcript text length in characters
            
        Returns:
            Estimated cost in USD
        """
        # Estimate tokens (1 char ≈ 0.25 tokens)
        estimated_tokens = transcript_length // 4
        output_tokens = 4000  # Typical output size
        
        # Calculate cost using existing client (without caching for conservative estimate)
        cost_breakdown = self.client.calculate_cost(
            input_tokens=estimated_tokens,
            output_tokens=output_tokens,
            model=self.model,
            return_breakdown=False,
        )
        
        return cost_breakdown
    
    def validate_config(self) -> bool:
        """Validate Grok configuration.
        
        Returns:
            True if API key is set
        """
        return bool(self.client.api_key)

