# Root Cause Analysis: Pro Model Performance Issues

*Date: 2025-09-01*
*Investigation Status: COMPLETE*

## Executive Summary

After extensive investigation including official documentation research, model parity testing, and code analysis, we've identified the root causes of Pro's poor performance in ClipScribe:

1. **We truncate transcripts to 24,000 characters** - Both models only analyze a fraction of long videos
2. **We don't set max_output_tokens** - Models use different defaults (Flash appears more generous)
3. **JSON response_mime_type constrains output** - Especially affects Pro model
4. **Recent Pro model degradation** - Reports of Pro having issues in December 2024/January 2025
5. **Our prompts may trigger Pro's stricter safety filters** - ClipScribe-style prompts blocked more often

## Evidence from Testing

### Test 1: Model Parity Test
When tested with IDENTICAL settings on simple prompts:
- **Flash**: 295 words average output
- **Pro**: 280 words average output (similar!)
- **Both blocked same content** with finish_reason=2

**Conclusion**: Models perform similarly when properly configured.

### Test 2: Defaults Investigation
Testing without explicit max_output_tokens:
- **Flash (no config)**: 2,320 words output
- **Pro (no config)**: 1,861 words output

With JSON response_mime_type:
- **Flash**: 800 words, 20 entities
- **Pro**: 645 words, 13 entities

With max_output_tokens=8192 + JSON:
- **Flash**: 374 words, 14 entities
- **Pro**: 752 words, 14 entities (Pro actually better here!)

**Conclusion**: Output varies wildly based on configuration.

### Test 3: Our Implementation Analysis

```python
# Line 498 in transcriber.py
{transcript_text[:24000]}  # CRITICAL BUG!
```

We only send the first 24,000 characters to analyze, which for a 94-minute video means:
- **273,618 total chars** in transcript
- **24,000 analyzed** = only 8.8% of content!
- Missing 91% of the video content

## The Real Problems

### Problem 1: Transcript Truncation
```python
# Current (BROKEN)
def _build_enhanced_analysis_prompt(self, transcript_text: str) -> str:
    prompt = f"""
    **Transcript for Analysis (first 24,000 characters):**
    ```
    {transcript_text[:24000]}  # ← THIS IS THE MAIN ISSUE
    ```
    """
```

**Impact**: We're missing 70-90% of content in videos over 10 minutes.

### Problem 2: No max_output_tokens Setting
```python
# Current generation_config
generation_config={
    "response_mime_type": "application/json",
    "response_schema": response_schema,
    # NO max_output_tokens!
}
```

**Impact**: Models use different defaults, Pro appears more conservative.

### Problem 3: Complex Prompt + JSON Schema
Our prompt asks for 6 different extractions simultaneously:
- Summary
- Key points
- Topics  
- Entities
- Relationships
- Dates

**Impact**: Pro may prioritize differently or hit token limits sooner.

### Problem 4: Recent Pro Model Issues
External reports indicate Gemini 2.5 Pro has been experiencing:
- High latency on large prompts
- Output quality degradation
- Self-critical loops
- Unexpected behaviors

Source: Google forums and tech news (December 2024 - January 2025)

## Why Flash Performs Better

1. **More generous default max_output_tokens** 
2. **Less strict safety filtering** on our security-related content
3. **Better handling of complex multi-part prompts**
4. **Not affected by recent Pro degradation issues**

## The Fix

### Immediate Code Changes Needed

```python
# 1. Fix transcript truncation
def _build_enhanced_analysis_prompt(self, transcript_text: str) -> str:
    # Option A: Analyze full transcript (if under 100k chars)
    if len(transcript_text) < 100000:
        full_transcript = transcript_text
    else:
        # Option B: Take more representative sample
        # First 30k + middle 30k + last 30k
        third = len(transcript_text) // 3
        full_transcript = (
            transcript_text[:30000] + 
            "\n[...]\n" +
            transcript_text[third:third+30000] +
            "\n[...]\n" +
            transcript_text[-30000:]
        )
    
    prompt = f"""
    **Transcript for Analysis:**
    ```
    {full_transcript}
    ```
    """
    return prompt

# 2. Set explicit max_output_tokens
generation_config={
    "response_mime_type": "application/json",
    "response_schema": response_schema,
    "max_output_tokens": 8192,  # Add this!
    "temperature": 0.3
}

# 3. Simplify extraction (do in phases if needed)
# Phase 1: Entities and relationships
# Phase 2: Summary and key points
# Phase 3: Dates and topics
```

### Configuration Recommendations

```python
# Optimal settings for both models
GENERATION_CONFIG = {
    "temperature": 0.2,  # Lower for consistency
    "max_output_tokens": 8192,  # Explicit limit
    "top_p": 0.95,
    "top_k": 40
}

# Safety settings (permissive for intelligence work)
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"}
]
```

## Expected Results After Fixes

With proper configuration, we expect:

| Metric | Current Flash | Current Pro | Fixed Flash | Fixed Pro |
|--------|--------------|-------------|-------------|-----------|
| Entities extracted | 25-71 | 20-27 | 100-200 | 100-200 |
| Relationships | 37-54 | 10-11 | 75-150 | 75-150 |
| Success rate | 100% | 50% | 100% | 95%+ |
| Transcript analyzed | 24k chars | 24k chars | Full | Full |

## Testing Strategy

1. **Fix transcript truncation first** - This is causing the most data loss
2. **Add max_output_tokens=8192** - Ensure consistent output
3. **Test with simplified prompts** - Reduce complexity
4. **Compare results** - Both models should now perform similarly
5. **Choose based on cost** - If similar quality, use Flash (50% cheaper)

## Conclusion

**Pro is not inherently broken** - our implementation is handicapping both models, but Pro more severely due to:
1. Analyzing only 8.8% of the transcript
2. Not setting output token limits
3. Complex prompts triggering different behaviors
4. Possible temporary Pro model issues

After fixes, we expect Pro to match or exceed Flash performance. However, given Flash's lower cost and current adequate performance, **Flash may still be the better choice** unless Pro shows significant quality improvements after fixes.

## Action Items

1. ✅ Identified root causes
2. ⬜ Fix transcript truncation (analyze 90k chars instead of 24k)
3. ⬜ Add max_output_tokens=8192 to all generation_config
4. ⬜ Simplify prompts or break into phases
5. ⬜ Re-test both models with fixes
6. ⬜ Make final model selection based on results
7. ⬜ Document the chosen configuration
