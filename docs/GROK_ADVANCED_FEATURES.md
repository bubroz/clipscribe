# Grok Advanced Features Guide

*Last Updated: November 11, 2025*

ClipScribe now integrates all cutting-edge xAI Grok features released between May-November 2025, delivering enhanced intelligence extraction with significant cost savings.

## Table of Contents

- [Overview](#overview)
- [Prompt Caching](#prompt-caching)
- [Server-Side Tools](#server-side-tools)
- [Collections API & Knowledge Base](#collections-api--knowledge-base)
- [Structured Outputs](#structured-outputs)
- [Cost Optimization](#cost-optimization)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)

## Overview

### What's New (November 2025)

**Prompt Caching (May 2025)**
- Automatic 50% cost savings on repeated system prompts
- Zero code changes required
- Transparent cache hit/miss tracking

**Server-Side Tools (October 2025)**
- `web_search`: Fact-check entities with web search
- `x_search`: Real-time context from X/Twitter  
- `code_execution`: Verify calculations and data
- `collections_search`: Search your knowledge base

**Collections API (August 2025)**
- Build searchable knowledge base of all videos
- Cross-video entity linking
- Temporal intelligence across collection

**Structured Outputs (November 2025)**
- Type-safe `json_schema` mode (vs basic `json_object`)
- Guaranteed response structure
- Reduced parsing errors

### Key Benefits

| Feature | Benefit | Impact |
|---------|---------|--------|
| Prompt Caching | 50% cost reduction on repeated prompts | $0.0015 savings per extraction |
| Fact-Checking | Higher entity confidence | +10-15% confidence improvement |
| Knowledge Base | Cross-video intelligence | Discover entity relationships across videos |
| Structured Outputs | Type safety | Zero parsing errors |

## Prompt Caching

### How It Works

xAI automatically caches prompt prefixes >1024 tokens. When you send similar prompts, cached portions cost 50% less.

**Example:**
```
First request:  1000 input tokens @ $0.003/1K = $0.003
Second request: 500 cached + 500 new @ $0.003/1K = $0.00225
Savings: $0.00075 (25%)
```

### Implementation

ClipScribe automatically optimizes for caching:

```python
from clipscribe.utils.prompt_cache import get_prompt_cache

# Get global cache instance
cache = get_prompt_cache()

# Build cached message (system prompt cached, user content varies)
messages = cache.build_cached_message(
    system_prompt="You are an AI that extracts entities...",  # Cached
    user_content=f"Transcript: {video_transcript}"  # Not cached
)

# Cache statistics
stats = cache.get_stats_summary()
print(f"Cache hit rate: {stats['hit_rate_percent']}%")
print(f"Total savings: ${stats['total_savings_usd']:.4f}")
```

### Cache Performance Tracking

```python
# Automatic tracking in hybrid processor
{
    "total_requests": 100,
    "cache_hits": 65,
    "hit_rate_percent": 65.0,
    "total_savings_usd": 0.0975,
    "avg_savings_per_request_usd": 0.00097
}
```

## Server-Side Tools

### Available Tools

**1. web_search**
- Search the web for factual verification
- Returns sources and snippets
- Use cases: Verify entity existence, get current information

**2. x_search**
- Search X/Twitter for real-time information
- Use cases: Breaking news, trending topics, public sentiment

**3. code_execution**
- Execute Python code to verify calculations
- Use cases: Statistics verification, data analysis

**4. collections_search**
- Search your video knowledge base
- Use cases: Cross-reference entities, find related videos

### Fact-Checking Workflow

```python
from clipscribe.intelligence.fact_checker import GrokFactChecker

# Initialize fact checker with tools
fact_checker = GrokFactChecker(
    api_key=settings.xai_api_key,
    enable_web_search=True,
    enable_x_search=True,
    enable_code_execution=False  # Optional
)

# Fact-check entities
fact_check_results = await fact_checker.fact_check_entities(
    entities=video_intelligence.entities,
    confidence_threshold=0.7  # Only check entities below 70%
)

# Review results
for result in fact_check_results:
    if result.verified:
        print(f"{result.entity_name}: Verified!")
        print(f"  Sources: {result.sources}")
        print(f"  New confidence: {result.verification_confidence:.2f}")
```

### Enrichment Example

```python
# Enrich entity with current information
enrichment = await fact_checker.enrich_with_current_info(
    entity=entity,
    search_query="Elon Musk SpaceX latest news"
)

print(f"Summary: {enrichment['summary']}")
print(f"Sources: {enrichment['sources']}")
```

## Collections API & Knowledge Base

### Building Your Knowledge Base

```python
from clipscribe.knowledge.collection_manager import VideoKnowledgeBase

# Initialize knowledge base
kb = VideoKnowledgeBase(
    api_key=settings.xai_api_key,
    collection_name="my-videos"
)

# Initialize collection (or connect to existing)
collection_id = await kb.initialize_collection()

# Add processed video
file_id = await kb.add_video_to_knowledge_base(
    video_id="youtube_abc123",
    transcript=full_transcript,
    intelligence=video_intelligence
)
```

### Searching Your Knowledge Base

```python
# Semantic search across all videos
results = await kb.search_knowledge_base(
    query="SpaceX Starship timeline",
    top_k=5
)

for result in results:
    print(f"Video: {result.title}")
    print(f"Relevance: {result.relevance_score:.2f}")
    print(f"Match: {result.matched_content[:200]}...")
```

### Cross-Video Entity Linking

```python
# Find all videos mentioning an entity
references = await kb.cross_reference_entity(
    entity_name="Elon Musk",
    entity_type="PERSON"
)

for ref in references:
    print(f"{ref.title}: {ref.entity_mentions} mentions")
    print(f"Contexts: {ref.contexts[:2]}")
```

### Entity Co-Occurrence Analysis

```python
# Find videos where two entities appear together
cooccurrences = await kb.find_entity_cooccurrences(
    entity1="SpaceX",
    entity2="Mars"
)

print(f"Found {len(cooccurrences)} videos mentioning both")
```

## Structured Outputs

### Why json_schema vs json_object?

| Feature | json_object | json_schema |
|---------|-------------|-------------|
| Type safety | ❌ No | ✅ Yes |
| Schema enforcement | ❌ No | ✅ Yes |
| Parsing errors | ⚠️ Possible | ✅ Eliminated |
| Response guarantees | ❌ Best effort | ✅ Guaranteed |

### Implementation

```python
from clipscribe.models.grok_schemas import get_video_intelligence_schema

# Get structured output schema
response_format = get_video_intelligence_schema()

# Use in API call
response = await grok_client.chat_completion(
    messages=messages,
    model="grok-4-fast-reasoning",
    response_format=response_format  # Type-safe schema
)

# Response guaranteed to match VideoIntelligence schema
result = json.loads(response["choices"][0]["message"]["content"])
# No validation needed - schema enforced by API
```

### Available Schemas

```python
from clipscribe.models.grok_schemas import (
    get_video_intelligence_schema,  # Full intelligence extraction
    get_entity_schema,              # Entities only
    get_relationship_schema,        # Relationships only
    get_topic_schema               # Topics only
)
```

## Cost Optimization

### Cost Breakdown

**Traditional Approach (json_object, no caching):**
```
Input tokens: 10,000 @ $0.003/1K = $0.030
Output tokens: 2,000 @ $0.010/1K = $0.020
Total: $0.050
```

**Optimized Approach (json_schema + caching):**
```
Input tokens: 5,000 @ $0.003/1K = $0.015
Cached tokens: 5,000 @ $0.0015/1K = $0.0075
Output tokens: 2,000 @ $0.010/1K = $0.020
Total: $0.0425
Savings: $0.0075 (15%)
```

### Monthly Cost Impact

For 1,000 videos/month:

| Configuration | Cost/Video | Monthly Cost | Annual Cost |
|---------------|------------|--------------|-------------|
| Basic | $0.050 | $50 | $600 |
| With Caching (60% hit rate) | $0.035 | $35 | $420 |
| **Savings** | **$0.015** | **$15** | **$180** |

### Cost Tracking

```python
# Detailed cost breakdown
cost_breakdown = grok_client.calculate_cost(
    input_tokens=1000,
    output_tokens=200,
    cached_tokens=500,
    tool_calls=2
)

print(f"Input cost: ${cost_breakdown['input_cost']:.4f}")
print(f"Cached cost: ${cost_breakdown['cached_cost']:.4f}")
print(f"Output cost: ${cost_breakdown['output_cost']:.4f}")
print(f"Cache savings: ${cost_breakdown['cache_savings']:.4f}")
print(f"Tool cost: ${cost_breakdown['tool_cost']:.4f}")
print(f"Total: ${cost_breakdown['total']:.4f}")
```

## Configuration

### Environment Variables

Add to `env.production`:

```bash
# xAI API Key (Required)
XAI_API_KEY=your_xai_api_key_here

# Prompt Caching (Recommended)
ENABLE_GROK_PROMPT_CACHING=true

# Fact Checking with Tools
ENABLE_GROK_FACT_CHECKING=true
ENABLE_GROK_WEB_SEARCH=true
ENABLE_GROK_X_SEARCH=true
ENABLE_GROK_CODE_EXECUTION=false  # Use with caution
FACT_CHECK_CONFIDENCE_THRESHOLD=0.7

# Knowledge Base / Collections
ENABLE_KNOWLEDGE_BASE=true
GROK_COLLECTION_ID=  # Leave empty to auto-create
GROK_COLLECTION_NAME=clipscribe-videos
AUTO_ADD_TO_KNOWLEDGE_BASE=true

# Structured Outputs
ENABLE_GROK_STRUCTURED_OUTPUTS=true
```

### Python Settings

```python
from clipscribe.config.settings import Settings

settings = Settings()

# Override defaults
settings.enable_grok_fact_checking = True
settings.fact_check_confidence_threshold = 0.8
settings.enable_knowledge_base = True
```

## Usage Examples

### Basic Video Processing with Advanced Features

```python
from clipscribe.processors.hybrid_processor import HybridProcessor

# Initialize with advanced features enabled
processor = HybridProcessor(
    voxtral_model="voxtral-mini-2507",
    grok_model="grok-4-fast-reasoning"
)

# Process video (automatic caching, fact-checking, KB integration)
result = await processor.process_video(
    audio_path="video.mp3",
    metadata={
        "video_id": "youtube_abc123",
        "title": "SpaceX Starship Update",
        "channel": "SpaceX",
        "duration": 1800
    }
)

# Results include:
# - Entities (fact-checked if confidence < 0.7)
# - Relationships (with evidence)
# - Topics and key moments
# - Cost breakdown (with cache savings)
# - Automatic addition to knowledge base
```

### Manual Fact-Checking

```python
from clipscribe.intelligence.fact_checker import GrokFactChecker

fact_checker = GrokFactChecker(api_key=settings.xai_api_key)

# Fact-check specific entities
for entity in low_confidence_entities:
    result = await fact_checker.fact_check_entity(
        entity=entity,
        context=surrounding_transcript
    )
    
    if result.verified:
        entity.confidence = result.verification_confidence
        print(f"✅ {entity.name}: Verified via {result.tool_used}")
    else:
        print(f"⚠️  {entity.name}: Could not verify")
```

### Knowledge Base Queries

```python
from clipscribe.knowledge.collection_manager import VideoKnowledgeBase

kb = VideoKnowledgeBase(api_key=settings.xai_api_key)
await kb.initialize_collection()

# Query knowledge base
results = await kb.search_knowledge_base(
    query="What videos discuss Mars colonization?",
    top_k=10
)

# Cross-reference entities
elon_videos = await kb.cross_reference_entity("Elon Musk")
print(f"Found {len(elon_videos)} videos mentioning Elon Musk")

# Entity co-occurrence
spacex_mars = await kb.find_entity_cooccurrences("SpaceX", "Mars")
```

### Cache Performance Monitoring

```python
from clipscribe.utils.prompt_cache import get_prompt_cache

cache = get_prompt_cache()

# After processing videos
stats = cache.get_stats_summary()

print(f"Cache Performance:")
print(f"  Hit rate: {stats['hit_rate_percent']:.1f}%")
print(f"  Total requests: {stats['total_requests']}")
print(f"  Cache hits: {stats['cache_hits']}")
print(f"  Total savings: ${stats['total_savings_usd']:.2f}")

# Log stats periodically
cache.log_stats()
```

## Best Practices

### 1. Maximize Cache Hits

✅ **Do:**
- Use consistent system prompts
- Keep variable content in user messages
- Process similar videos in batches

❌ **Don't:**
- Randomize system prompts
- Mix static and dynamic content
- Process unrelated content sequentially

### 2. Fact-Checking Strategy

✅ **Do:**
- Set reasonable confidence thresholds (0.7-0.8)
- Fact-check important entities (people, organizations)
- Use web_search for general verification
- Use x_search for current events

❌ **Don't:**
- Fact-check every entity (expensive)
- Set threshold too high (misses opportunities)
- Use code_execution without validation

### 3. Knowledge Base Management

✅ **Do:**
- Initialize collection once per session
- Use descriptive collection names
- Add videos automatically
- Search before processing (avoid duplicates)

❌ **Don't:**
- Create new collection per video
- Upload same video multiple times
- Skip initialization check

### 4. Cost Management

✅ **Do:**
- Enable prompt caching
- Monitor cache hit rate
- Track cost per video
- Set daily/monthly limits

❌ **Don't:**
- Disable caching for savings
- Ignore cost breakdown
- Process without budgets

## Troubleshooting

### Cache Not Working

**Symptom:** 0% cache hit rate

**Solutions:**
1. Ensure system prompts >1024 tokens
2. Check `ENABLE_GROK_PROMPT_CACHING=true`
3. Verify consistent prompt structure
4. Wait for cache TTL (varies)

### Fact-Checking Errors

**Symptom:** Fact-checking always fails

**Solutions:**
1. Verify tool permissions
2. Check network connectivity
3. Review API rate limits
4. Reduce concurrent checks

### Knowledge Base Issues

**Symptom:** Collection not found

**Solutions:**
1. Call `initialize_collection()` first
2. Check `GROK_COLLECTION_ID` setting
3. Verify API key permissions
4. Check collection wasn't deleted

### Cost Higher Than Expected

**Symptom:** Costs not decreasing

**Solutions:**
1. Check cache hit rate
2. Verify caching enabled
3. Review tool usage (tools may cost extra)
4. Monitor token usage

## Performance Metrics

### Expected Performance

| Metric | Target | Excellent |
|--------|--------|-----------|
| Cache hit rate | >40% | >60% |
| Cost reduction | >20% | >40% |
| Fact-check improvement | >5% | >15% |
| KB search latency | <3s | <2s |

### Monitoring

```python
# Track performance over time
performance = {
    "cache_hit_rate": cache.get_stats_summary()["hit_rate_percent"],
    "avg_cost_per_video": total_cost / video_count,
    "avg_entities_per_video": total_entities / video_count,
    "fact_check_success_rate": verified / total_checked
}

# Log to monitoring system
logger.info(f"Performance metrics: {performance}")
```

## Additional Resources

- [xAI API Documentation](https://docs.x.ai)
- [Files API Guide](https://docs.x.ai/files)
- [Collections API Guide](https://docs.x.ai/collections)
- [Tools Documentation](https://docs.x.ai/tools)
- [ClipScribe Core Documentation](../README.md)

---

**Questions or Issues?**
- GitHub: https://github.com/bubroz/clipscribe/issues
- Documentation: https://github.com/bubroz/clipscribe#readme

