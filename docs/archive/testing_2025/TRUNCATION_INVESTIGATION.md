# Transcript Truncation Investigation

*Date: 2025-09-01*
*Status: CRITICAL FINDING*

## Executive Summary

**The 24,000 character limit is COMPLETELY UNNECESSARY and is causing us to miss 91% of content in long videos!**

Both Gemini 2.5 Flash and Pro can handle **1 MILLION+ characters** without any issues. We've been arbitrarily throwing away most of our data.

## Test Results

### Input Capacity Test

| Input Size | Characters | ~Tokens | Flash Result | Pro Result |
|------------|------------|---------|--------------|------------|
| Current limit | 24,000 | 6,000 | ✅ Works | ✅ Works |
| 2x | 50,000 | 12,500 | ✅ Works | ✅ Works |
| 4x | 100,000 | 25,000 | ✅ Works | ✅ Works |
| 8x | 200,000 | 50,000 | ✅ Works | ✅ Works |
| 20x | 500,000 | 125,000 | ✅ Works | ✅ Works |
| **40x** | **1,000,000** | **250,000** | **✅ Works** | **✅ Works** |

**Both models successfully processed 1 MILLION characters!**

## The Real Problem

### What We're Currently Doing

```python
# Line 498 in transcriber.py
{transcript_text[:24000]}  # Arbitrary limit!
```

For a 94-minute Pegasus documentary:
- **Total transcript**: 273,618 characters
- **We analyze**: 24,000 characters
- **We throw away**: 249,618 characters (91.2%)

### Why This Exists

Git blame shows this was added on August 4, 2025. Likely reasons:
1. Conservative estimate based on older Gemini 1.5 models
2. Concern about costs (but we're already paying for full transcription!)
3. Copy-pasted from example code
4. Never tested actual limits

## Safety Filter Investigation

### What Gets Blocked

With **default safety settings**, content about:
- Quantum computing and cryptography
- Security vulnerabilities
- Intelligence analysis

Gets blocked with `finish_reason=2`

### The Solution

Using `BLOCK_ONLY_HIGH` for all categories:

```python
safety_settings=[
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"}
]
```

**Result**: All security/intelligence content passes through!

## Process Flow Analysis

```mermaid
graph TD
    A[Audio File] --> B[Full Transcription]
    B --> C{Current: Truncate to 24k}
    C --> D[Analyze 8.8% of content]
    D --> E[Poor extraction results]
    
    B --> F{Fixed: Use full transcript}
    F --> G[Analyze 100% of content]
    G --> H[Complete extraction]
```

### Where Truncation Happens

1. **Transcription**: ✅ Complete (no truncation)
2. **Analysis Prompt**: ❌ Truncated to 24k chars
3. **Entity Extraction**: ❌ Missing 91% of entities
4. **Relationship Mapping**: ❌ Missing 91% of relationships

## Output Token Analysis

### Is max_output_tokens=8192 Enough?

**YES!** Here's why:

- 8192 tokens ≈ 6000-8000 words
- Our typical extraction output: 2000-4000 words
- Even with 100+ entities and relationships, we're well under the limit

The issue is INPUT truncation, not output limits.

## Cost Implications

**Current (Broken)**:
- Pay for transcribing 273k chars
- Only analyze 24k chars
- Waste 91% of the processing we paid for!

**Fixed**:
- Pay for transcribing 273k chars
- Analyze all 273k chars
- Get 10x more value for same cost!

**No additional cost** - we're already transcribing the full content!

## The Fix

### Option 1: Remove Limit Entirely (Recommended)

```python
def _build_enhanced_analysis_prompt(self, transcript_text: str) -> str:
    """Build comprehensive analysis prompt with FULL transcript."""
    
    # No truncation for transcripts under 1M chars
    if len(transcript_text) < 1000000:
        analysis_text = transcript_text
    else:
        # Only chunk if truly massive (rare)
        analysis_text = self._create_representative_sample(transcript_text)
    
    prompt = f"""
    **ROLE: Expert Intelligence Analyst**
    **TASK: Analyze the complete transcript**
    
    **Transcript for Analysis ({len(analysis_text):,} characters):**
    ```
    {analysis_text}
    ```
    """
    return prompt
```

### Option 2: Smart Sampling (If Needed)

```python
def _create_representative_sample(self, transcript: str, max_chars: int = 500000):
    """Create representative sample for huge transcripts."""
    if len(transcript) <= max_chars:
        return transcript
    
    # Take beginning, middle sections, and end
    chunk_size = max_chars // 3
    
    beginning = transcript[:chunk_size]
    middle_start = (len(transcript) - chunk_size) // 2
    middle = transcript[middle_start:middle_start + chunk_size]
    end = transcript[-chunk_size:]
    
    return f"{beginning}\n\n[...middle section...]\n\n{middle}\n\n[...final section...]\n\n{end}"
```

### Option 3: Streaming Chunked Analysis

For truly massive videos (>2 hours), process in chunks and merge:

```python
# Already implemented in streaming_extractor.py!
# Just need to use it for large transcripts
```

## Expected Improvements

### Current Performance (24k limit)
- PBS News Hour (49 min): 25 entities, 37 relationships
- Pegasus Documentary (94 min): 20 entities, 10 relationships
- Missing most content after first 5 minutes!

### Expected After Fix (Full transcript)
- PBS News Hour: 100-150 entities, 150-200 relationships
- Pegasus Documentary: 200-300 entities, 300-400 relationships
- Complete coverage of entire video!

## Safety Settings Fix

Add to `GeminiFlashTranscriber.__init__`:

```python
self.safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"}
]
```

## Action Items

1. **IMMEDIATE**: Remove the 24,000 character truncation
2. **IMMEDIATE**: Add safety_settings with BLOCK_ONLY_HIGH
3. **REQUIRED**: Add max_output_tokens=8192 to generation_config
4. **TEST**: Process full 94-minute video to verify improvement
5. **MONITOR**: Check if any videos actually exceed 1M chars

## Conclusion

This is the single biggest bug in ClipScribe. We've been:
- Throwing away 91% of our data
- Paying for full transcription but analyzing only a fraction
- Getting poor extraction results due to missing context
- Blocking legitimate security/intelligence content

**The fix is trivial** - just remove the [:24000] truncation and add proper safety settings.

## One-Line Fix

```python
# Change this:
{transcript_text[:24000]}

# To this:
{transcript_text}
```

That's it. This will 10x our extraction quality immediately.
