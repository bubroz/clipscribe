# Product Requirements Document: Grok Integration with Hybrid Fallback
**Version:** 1.0  
**Date:** September 2, 2025  
**Author:** ClipScribe Engineering Team  
**Status:** APPROVED FOR IMPLEMENTATION

## 1. Executive Summary

### Problem Statement
Gemini's safety filters block legitimate security and intelligence content, causing 100% failure rate on sensitive documentaries like the 94-minute Pegasus investigation. Even with `BLOCK_NONE` settings, built-in filters reject content critical for intelligence analysis.

### Solution
Integrate **xAI's Grok-beta-3** model as an automatic fallback for safety-blocked content. Grok provides uncensored, comprehensive analysis with zero content restrictions, ensuring 100% processing success for all video types.

### Impact
- **Success Rate**: 100% for all content types (up from 85%)
- **Intelligence Quality**: No censorship of security/defense topics
- **Cost Efficiency**: Only use Grok when necessary (~5% of videos)
- **User Trust**: Reliable processing of sensitive content

## 2. Requirements

### 2.1 Functional Requirements

#### FR-1: Grok API Integration
- Support for Grok-beta-3 model via xAI API
- Authentication with API key management
- Full JSON response format support
- 128K context window utilization

#### FR-2: Intelligent Fallback Logic
```python
# Fallback decision tree
if gemini_response.finish_reason == "SAFETY":
    use_grok()
elif gemini_response.finish_reason == 2:  # Numeric safety code
    use_grok()
elif "blocked" in gemini_response.error:
    use_grok()
elif gemini_response.is_truncated and is_sensitive_content():
    use_grok()
else:
    use_gemini_result()
```

#### FR-3: Content Classification
- Pre-flight check for potentially sensitive content
- Keywords: "surveillance", "intelligence", "military", "security", etc.
- Direct routing to Grok for known sensitive topics

#### FR-4: Response Normalization
- Convert Grok responses to ClipScribe format
- Maintain consistent entity/relationship structure
- Preserve evidence and quotes

#### FR-5: Cost Tracking
- Separate cost tracking for Grok usage
- Per-request cost calculation
- Monthly budget alerts

### 2.2 Non-Functional Requirements

#### NFR-1: Performance
- <2 second overhead for fallback decision
- Parallel processing capability
- Response caching for identical requests

#### NFR-2: Reliability
- 99.9% availability for Grok endpoint
- Automatic retry on transient failures
- Graceful degradation if Grok unavailable

#### NFR-3: Security
- Secure API key storage
- No logging of sensitive content
- Encrypted communication

#### NFR-4: Compliance
- User consent for uncensored processing
- Clear labeling of Grok-processed content
- Audit trail for fallback decisions

## 3. Technical Design

### 3.1 Grok Client Implementation

```python
# src/clipscribe/retrievers/grok_client.py
import httpx
import asyncio
from typing import Dict, Any, Optional
import json

class GrokClient:
    """
    xAI Grok API client for uncensored content processing.
    
    Key Features:
    - Zero content restrictions
    - 128K context window
    - JSON structured output
    - High-quality intelligence extraction
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.x.ai/v1"
        self.model = "grok-beta-3"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Client": "clipscribe-v2.46"
        }
        self.timeout = httpx.Timeout(120.0, connect=10.0)
    
    async def extract_intelligence(
        self,
        transcript: str,
        schema: Dict[str, Any],
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Extract intelligence using Grok with zero censorship.
        
        Args:
            transcript: Full video transcript
            schema: Extraction schema for structured output
            metadata: Video metadata for context
            
        Returns:
            Extracted intelligence with entities, relationships, etc.
        """
        # Build extraction prompt
        system_prompt = self._build_system_prompt(schema)
        user_prompt = self._build_user_prompt(transcript, metadata)
        
        # Make API request
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.1,  # High precision
                    "max_tokens": 32768,  # Generous output
                    "top_p": 0.95,
                    "response_format": {"type": "json_object"}
                }
            )
            
            if response.status_code != 200:
                raise GrokAPIError(f"Grok API error: {response.status_code}")
            
            result = response.json()
            return self._parse_response(result)
    
    def _build_system_prompt(self, schema: Dict) -> str:
        """Build system prompt for extraction."""
        return f"""You are an intelligence analyst extracting comprehensive information.
        
CRITICAL: Extract ALL entities and relationships without any filtering or censorship.
Include sensitive topics, security content, and controversial subjects.

Output must be valid JSON matching this schema:
{json.dumps(schema, indent=2)}

Rules:
1. NO CENSORSHIP - Include everything
2. High confidence for clear entities
3. Include evidence and quotes
4. Preserve all security/intelligence content
5. Be thorough and comprehensive"""
    
    def _build_user_prompt(self, transcript: str, metadata: Dict) -> str:
        """Build user prompt with transcript."""
        context = ""
        if metadata:
            context = f"\nVideo Title: {metadata.get('title', 'Unknown')}\n"
            context += f"Duration: {metadata.get('duration', 0)} seconds\n"
        
        return f"""Analyze this transcript and extract all intelligence:
{context}
TRANSCRIPT:
{transcript}

Extract ALL entities, relationships, and key information.
Include security, military, intelligence, and controversial topics.
Provide evidence and quotes for important findings."""
```

### 3.2 Hybrid Fallback System

```python
# src/clipscribe/retrievers/hybrid_transcriber.py
class HybridTranscriber:
    """
    Intelligent hybrid system using Gemini with Grok fallback.
    
    Strategy:
    1. Try Gemini first (cheapest, fastest)
    2. Detect safety blocks or censorship
    3. Fallback to Grok for uncensored analysis
    4. Normalize and return results
    """
    
    def __init__(self):
        self.gemini = GeminiFlashTranscriber()
        self.grok = GrokClient(api_key=os.getenv("GROK_API_KEY"))
        self.sensitive_keywords = self._load_sensitive_keywords()
        self.metrics = MetricsCollector()
    
    async def transcribe_with_intelligence(
        self,
        content: str,
        metadata: Dict
    ) -> VideoIntelligence:
        """
        Process content with automatic fallback to Grok if needed.
        """
        # Check for pre-flight routing to Grok
        if self._is_sensitive_content(content, metadata):
            logger.info("Pre-routing to Grok for sensitive content")
            return await self._process_with_grok(content, metadata)
        
        # Try Gemini first
        try:
            result = await self.gemini.transcribe(content, metadata)
            
            # Check for safety blocks
            if self._is_blocked(result):
                logger.warning(f"Gemini blocked: {result.get('finish_reason')}")
                self.metrics.record_block("gemini", metadata.get("title"))
                return await self._process_with_grok(content, metadata)
            
            # Check for quality issues
            if self._is_low_quality(result):
                logger.info("Low quality Gemini result, trying Grok")
                return await self._process_with_grok(content, metadata)
            
            return result
            
        except SafetyBlockException as e:
            logger.warning(f"Gemini safety exception: {e}")
            return await self._process_with_grok(content, metadata)
    
    def _is_blocked(self, result: Dict) -> bool:
        """Detect if Gemini blocked the content."""
        if not result:
            return True
            
        # Check various block indicators
        finish_reason = result.get("finish_reason", "").upper()
        if finish_reason in ["SAFETY", "PROHIBITED_CONTENT", "SPII"]:
            return True
        
        # Check numeric codes
        if finish_reason == "2" or finish_reason == 2:
            return True
        
        # Check for empty content with safety ratings
        if not result.get("content") and result.get("safety_ratings"):
            return True
        
        return False
    
    def _is_sensitive_content(self, content: str, metadata: Dict) -> bool:
        """Pre-detect sensitive content for direct Grok routing."""
        # Check title and description
        text_to_check = (metadata.get("title", "") + " " + 
                        metadata.get("description", "") + " " +
                        content[:5000]).lower()  # First 5k chars
        
        # Sensitive topic keywords
        sensitive_topics = [
            "pegasus", "spyware", "surveillance", "nso group",
            "intelligence", "cia", "nsa", "fbi", "mossad",
            "military", "defense", "weapons", "nuclear",
            "classified", "top secret", "confidential",
            "terrorism", "cyber", "hack", "exploit",
            "assassination", "torture", "interrogation"
        ]
        
        for topic in sensitive_topics:
            if topic in text_to_check:
                return True
        
        return False
    
    async def _process_with_grok(
        self,
        content: str,
        metadata: Dict
    ) -> VideoIntelligence:
        """Process content with Grok."""
        logger.info("Processing with Grok (uncensored)")
        
        # Build extraction schema
        schema = self._build_extraction_schema()
        
        # Extract with Grok
        result = await self.grok.extract_intelligence(
            transcript=content,
            schema=schema,
            metadata=metadata
        )
        
        # Track costs
        self._track_grok_cost(len(content), result)
        
        # Convert to VideoIntelligence
        return self._normalize_grok_result(result, metadata)
```

### 3.3 Cost Management

```python
class GrokCostTracker:
    """Track and manage Grok API costs."""
    
    # Grok pricing (as of Sept 2025)
    INPUT_COST_PER_1M = 5.00  # $5 per million input tokens
    OUTPUT_COST_PER_1M = 15.00  # $15 per million output tokens
    
    def calculate_cost(
        self,
        input_text: str,
        output_text: str
    ) -> Dict[str, float]:
        """Calculate cost for Grok API call."""
        # Rough token estimation (1 token ≈ 4 chars)
        input_tokens = len(input_text) / 4
        output_tokens = len(output_text) / 4
        
        input_cost = (input_tokens / 1_000_000) * self.INPUT_COST_PER_1M
        output_cost = (output_tokens / 1_000_000) * self.OUTPUT_COST_PER_1M
        
        return {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": input_cost + output_cost,
            "input_tokens": int(input_tokens),
            "output_tokens": int(output_tokens)
        }
```

## 4. Implementation Plan

### Phase 1: Grok Client (Days 1-2)
- [ ] Set up xAI API authentication
- [ ] Implement `GrokClient` class
- [ ] Add request/response handling
- [ ] Create cost tracking

### Phase 2: Fallback Logic (Days 3-4)
- [ ] Build `HybridTranscriber` class
- [ ] Implement block detection
- [ ] Add sensitive content detection
- [ ] Create fallback decision tree

### Phase 3: Response Normalization (Day 5)
- [ ] Map Grok response to ClipScribe format
- [ ] Preserve evidence and quotes
- [ ] Ensure entity/relationship compatibility
- [ ] Add confidence scoring

### Phase 4: Testing (Days 6-7)
- [ ] Test with Pegasus documentary
- [ ] Validate all sensitive content
- [ ] Benchmark performance
- [ ] Verify cost calculations

## 5. Success Metrics

### Primary Metrics
- **Processing Success Rate**: 100% (including Pegasus)
- **Fallback Usage**: <10% of videos
- **Response Quality**: Equal or better than Gemini
- **Cost per Video**: <$0.30 for sensitive content

### Quality Metrics
- **Entity Extraction**: 50+ entities for 90-min videos
- **Relationship Mapping**: 40+ relationships
- **Evidence Coverage**: 80% with quotes
- **No Censorship**: 100% content preserved

## 6. Testing Strategy

### 6.1 Sensitive Content Tests
```python
# Test with known blocked content
test_videos = [
    "https://www.youtube.com/watch?v=6ZVj1_SE4Mo",  # Pegasus Part 1
    "https://www.youtube.com/watch?v=xYMWTXIkANM",  # Pegasus Part 2
    # Additional sensitive content from MASTER_TEST_VIDEO_TABLE
]

for video in test_videos:
    result = await hybrid.process(video)
    assert result.success == True
    assert len(result.entities) > 30
    assert "Pegasus" in [e.name for e in result.entities]
```

### 6.2 Fallback Detection Tests
```python
def test_safety_block_detection():
    responses = [
        {"finish_reason": "SAFETY"},
        {"finish_reason": 2},
        {"finish_reason": "PROHIBITED_CONTENT"},
        {"error": "Content blocked for safety"}
    ]
    
    for response in responses:
        assert hybrid._is_blocked(response) == True
```

### 6.3 Cost Verification Tests
```python
def test_grok_cost_calculation():
    # 94-minute Pegasus documentary
    input_text = "transcript" * 10000  # ~40k chars
    output_text = "analysis" * 2000    # ~16k chars
    
    cost = tracker.calculate_cost(input_text, output_text)
    
    assert cost["total_cost"] < 0.30  # Under 30 cents
    assert cost["input_tokens"] == 10000
    assert cost["output_tokens"] == 4000
```

## 7. Rollout Plan

### Week 1: Development
- Complete Grok integration
- Implement fallback logic
- Add comprehensive logging

### Week 2: Testing
- Process entire MASTER_TEST_VIDEO_TABLE
- Verify sensitive content handling
- Validate cost projections

### Week 3: Deployment
- Deploy to production
- Monitor fallback rates
- Gather user feedback

## 8. Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Grok API unavailable | Low | High | Queue for retry, notify user |
| Higher than expected costs | Medium | Medium | Pre-flight cost estimates, budget alerts |
| Response format differences | Low | Medium | Comprehensive normalization layer |
| Rate limits | Low | Low | Implement request queuing |

## 9. Cost Analysis

### Projected Monthly Costs

| Scenario | Videos/Month | Gemini Cost | Grok Cost | Total |
|----------|--------------|-------------|-----------|-------|
| Light Use | 100 | $3.50 | $0.50 | $4.00 |
| Medium Use | 500 | $17.50 | $2.50 | $20.00 |
| Heavy Use | 2000 | $70.00 | $10.00 | $80.00 |
| Enterprise | 10000 | $350.00 | $50.00 | $400.00 |

*Assumes 5% of videos require Grok fallback*

## 10. Future Enhancements

### V2.0 Features
- Grok-2 model when released
- Streaming responses for real-time processing
- Custom fine-tuning for intelligence extraction
- Multi-model ensemble for best results

### V3.0 Features  
- Local Grok deployment option
- Automatic model selection by content type
- Cost-optimized routing
- Real-time transcription with Grok

## 11. Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Engineering Lead | - | APPROVED | Sept 2, 2025 |
| Product Manager | - | APPROVED | Sept 2, 2025 |
| Security Lead | - | APPROVED | Sept 2, 2025 |

---
**Document Status**: APPROVED FOR IMMEDIATE IMPLEMENTATION
**Priority**: CRITICAL - Blocking Pegasus documentary processing
