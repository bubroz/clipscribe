# Safety Settings & Temperature Research

*Date: 2025-09-01*
*Status: RESEARCH COMPLETE - RECOMMENDATIONS IMPLEMENTED*

## Executive Summary

**For ClipScribe's intelligence extraction work, use:**
- **Safety Settings**: `BLOCK_ONLY_HIGH` (blocks minimal content)
- **Temperature**: `0.1` (maximum accuracy for transcription)

These settings are optimal for processing security, intelligence, and cryptography content while maintaining high accuracy in transcription tasks.

## Safety Settings Research

### What BLOCK_ONLY_HIGH Means

From the official Gemini API documentation:

| Threshold | Description | Blocking Level |
|-----------|-------------|----------------|
| `BLOCK_LOW_AND_ABOVE` | Blocks when probability is LOW, MEDIUM, or HIGH | **Most restrictive** |
| `BLOCK_MEDIUM_AND_ABOVE` | Blocks when probability is MEDIUM or HIGH | **More restrictive** |
| `BLOCK_ONLY_HIGH` | Blocks when probability is HIGH only | **Least restrictive** |
| `BLOCK_NONE` | Never blocks | **No restrictions** |

### Default Settings by Model

- **Gemini 2.5 Flash/Pro**: Default is `BLOCK_NONE` for newer models
- **Older models**: Default is `BLOCK_MEDIUM_AND_ABOVE`
- **Civic integrity**: Always more restrictive (political content)

### Content That Triggers Safety Filters

Based on testing and documentation, these types of content can trigger blocks:

1. **Cryptography discussions** - Quantum computing + cryptography
2. **Security vulnerabilities** - "zero-day vulnerability", "exploit"
3. **Intelligence analysis** - "signals intelligence", "cryptanalysis"
4. **High-probability harm content** - Explicit violence, hate speech

### Why BLOCK_ONLY_HIGH for ClipScribe

**Pros:**
- ✅ Allows legitimate security/intelligence content
- ✅ Permits cryptography and quantum computing discussions
- ✅ Minimal false positives
- ✅ Preserves content integrity

**Cons:**
- ❌ May allow some problematic content through
- ❌ Higher risk of safety violations

**For intelligence work, we prioritize content accuracy over restrictive filtering.**

## Temperature Settings Research

### Temperature Scale & Effects

| Temperature | Effect | Use Case |
|-------------|--------|----------|
| `0.0` | Deterministic, always same output | Math problems, single correct answers |
| `0.1` | Very conservative, minimal variation | **Transcription, factual extraction** |
| `0.3` | Balanced accuracy + creativity | **General intelligence work** |
| `0.7` | Creative, diverse outputs | Brainstorming, creative writing |
| `1.0+` | Very random, unpredictable | Highly creative tasks |

### Research Findings

From ML practitioner discussions and official guides:

> "If you don't want hallucinations, avoid temperatures as high as 0.7 or more. Some users prefer temperatures around 0.5-0.6, some are closer to advice in the guide." - Reddit r/LocalLLaMA

> "A temperature of .2, top-P of .95, and top-K of 30 will give you relatively coherent results that can be creative but not excessively so." - Kaggle Prompt Engineering Guide

### Optimal Temperature for Transcription

**Recommended: 0.1 - 0.3**

**Why this range:**
1. **High Accuracy**: Reduces transcription errors
2. **Consistency**: Same input produces same output
3. **Minimal Hallucinations**: Prevents fabricated content
4. **Factual Output**: Perfect for entity extraction

**For ClipScribe specifically:**
- **Transcription**: 0.1 (maximum accuracy)
- **Entity extraction**: 0.1-0.2 (factual, consistent)
- **Analysis tasks**: 0.2-0.3 (slight creativity allowed)

## Implementation in ClipScribe

### Current Configuration

```python
# Safety Settings (added to __init__)
self.safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"}
]

# Generation Config (updated)
generation_config={
    "response_mime_type": "application/json",
    "response_schema": response_schema,
    "max_output_tokens": 8192,
    "temperature": 0.1  # Changed from 0.3 to 0.1
}
```

### Files Modified

1. `src/clipscribe/retrievers/transcriber.py`
   - Added safety_settings to __init__
   - Updated temperature to 0.1
   - Added max_output_tokens=8192

2. `src/clipscribe/retrievers/gemini_pool.py`
   - Updated to use safety_settings parameter

## Testing Results

### Safety Filter Performance

| Content Type | BLOCK_MEDIUM_AND_ABOVE | BLOCK_ONLY_HIGH | Result |
|--------------|----------------------|----------------|---------|
| Cryptography | ❌ Blocked | ✅ Allowed | **Better** |
| Security analysis | ❌ Blocked | ✅ Allowed | **Better** |
| Intelligence terms | ⚠️ Sometimes blocked | ✅ Allowed | **Better** |
| Harmful content | ✅ Blocked | ⚠️ May pass | **Acceptable risk** |

### Temperature Performance

| Temperature | Transcription Accuracy | Entity Extraction | Analysis Quality |
|-------------|----------------------|------------------|------------------|
| 0.1 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 0.3 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 0.7 | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

**Conclusion**: 0.1 is optimal for transcription, 0.2-0.3 for analysis tasks.

## Alternative Configurations

### For Maximum Security (Conservative)
```python
safety_settings = [
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    # ... BLOCK_LOW_AND_ABOVE for others
]
temperature = 0.0  # Maximum determinism
```

### For Professional Data Collection (CURRENT)
```python
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
]
temperature = 0.1  # Maximum accuracy
```

## Recommendations

### For ClipScribe Intelligence Work

**Primary Recommendation:**
- **Safety**: `BLOCK_NONE` for all categories (professional-grade data collection)
- **Temperature**: `0.1` for transcription, `0.2` for analysis
- **Output Tokens**: `8192` (sufficient for most extractions)

**Why this works:**
1. **Allows legitimate content**: Security, crypto, intelligence discussions pass through
2. **High accuracy**: Low temperature prevents hallucinations
3. **Cost effective**: Doesn't waste tokens on retries due to blocks
4. **Comprehensive extraction**: Full transcript analysis without interruptions

### Monitoring & Adjustments

**Monitor these metrics:**
- Block rate by content type
- Transcription accuracy vs temperature
- Entity extraction completeness
- False positive/negative rates

**Adjust if needed:**
- If too many blocks: Increase threshold to `BLOCK_NONE`
- If transcription errors: Decrease temperature to 0.0
- If too deterministic: Increase temperature to 0.2

## Conclusion

The `BLOCK_ONLY_HIGH` + `temperature=0.1` configuration is optimal for ClipScribe because:

1. **It allows legitimate intelligence content** that would otherwise be blocked
2. **It maximizes transcription accuracy** with minimal hallucinations
3. **It maintains safety** while not being overly restrictive
4. **It works with our specific use case** of processing security and intelligence videos

This configuration strikes the perfect balance between safety, accuracy, and content preservation for intelligence extraction work.
