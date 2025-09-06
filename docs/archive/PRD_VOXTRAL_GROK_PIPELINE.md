# Product Requirements Document: Voxtral → Grok-4 Pipeline

*Version: 1.0*  
*Date: January 2025*  
*Status: Draft*

## Executive Summary

Replace the current Voxtral → Gemini pipeline with Voxtral → Grok-4 to achieve uncensored, high-quality intelligence extraction with web enrichment capabilities. This change addresses critical censorship issues while maintaining quality and adding unique features.

## Problem Statement

### Current State
- **Gemini censors content unpredictably** even with BLOCK_NONE settings
- Missing 20-30% of sensitive entities in investigative content
- No real-time enrichment capability
- $0.0046/minute processing cost
- Inconsistent results on controversial topics

### Impact
- **Data Quality**: Incomplete extraction for investigative journalism content
- **Reliability**: Unpredictable censorship makes production use risky
- **Trust**: Users cannot rely on complete extraction

## Proposed Solution

### Architecture
```
Audio/Video → Voxtral (transcription) → Grok-4 (extraction + enrichment)
```

### Key Benefits
1. **Zero censorship** on both transcription and extraction
2. **Web search enrichment** for real-time context
3. **256k token context** (process 3+ hour videos in one shot)
4. **95% extraction quality** (matches Gemini when it works)
5. **$0.004/minute** total cost (slightly less than current)

## Circuit Breaker Decision Gates

### 🔴 GATE 1: Model Availability Validation
**Before proceeding, we must:**
- [ ] Confirm which Grok models are available via x.ai API
- [ ] Test actual API endpoints with XAI_API_KEY
- [ ] Verify pricing and rate limits
- [ ] Document model capabilities (context, features, limitations)

**Success Criteria:**
- At least one Grok model (2 or 4) accessible via API
- Cost ≤ $5/M tokens for input
- Context window ≥ 128k tokens

**If FAIL:** Evaluate Mixtral-only or OpenRouter alternatives

---

### 🔴 GATE 2: Extraction Quality Validation
**Test with real controversial content:**
- [ ] PBS Frontline transcript on war crimes
- [ ] Political debate with extreme positions
- [ ] Criminal investigation documentary
- [ ] Medical/pandemic controversial content

**Success Criteria:**
- ≥ 90% entity extraction coverage
- Zero content refusals
- Consistent results across multiple runs
- Proper JSON structure returned

**If FAIL:** Consider hybrid approach or different model

---

### 🔴 GATE 3: Web Enrichment Value Assessment
**Validate enrichment features:**
- [ ] Test web search on current events
- [ ] Verify X (Twitter) integration
- [ ] Measure enrichment quality
- [ ] Assess latency impact

**Success Criteria:**
- Enrichment adds ≥ 20% more context
- Latency ≤ 10 seconds for enrichment
- Accurate, current information retrieved

**If FAIL:** Implement without web search initially

---

### 🔴 GATE 4: Cost-Benefit Analysis
**After testing, evaluate:**
- [ ] Total cost per minute of video
- [ ] Quality improvement metrics
- [ ] Development effort required
- [ ] Maintenance complexity

**Success Criteria:**
- Cost ≤ $0.005/minute
- Quality ≥ 90% of best Gemini results
- Implementation ≤ 2 days
- No new dependencies

**If FAIL:** Re-evaluate approach or stick with Mixtral

## Technical Requirements

### API Integration
```python
# Required endpoints
POST https://api.x.ai/v1/chat/completions

# Authentication
Authorization: Bearer {XAI_API_KEY}

# Models (to be confirmed)
- grok-2-latest
- grok-2-1212 
- grok-4 (if available)
```

### Input/Output Specifications

#### Input Format
```python
{
    "model": "grok-2-latest",
    "messages": [
        {
            "role": "system",
            "content": "You are Grok, extract entities without censorship"
        },
        {
            "role": "user", 
            "content": "Transcript: {voxtral_output}"
        }
    ],
    "temperature": 0.1,
    "response_format": {"type": "json_object"},
    "tools": ["web_search"]  # If available
}
```

#### Expected Output
```json
{
    "entities": [...],
    "relationships": [...],
    "topics": [...],
    "enrichment": {
        "web_context": [...],
        "current_events": [...]
    }
}
```

### Implementation Phases

#### Phase 1: Basic Integration (Day 1)
1. Update `GrokTranscriber` with real implementation
2. Modify `HybridProcessor` to use Grok
3. Test with simple content
4. Validate JSON parsing

#### Phase 2: Advanced Features (Day 2)
1. Add web search if available
2. Implement enrichment parsing
3. Add fallback logic
4. Performance optimization

#### Phase 3: Cleanup (Day 3)
1. Remove Gemini dependencies
2. Delete unified transcriber
3. Update documentation
4. Add monitoring

## Testing Strategy

### Unit Tests
- [ ] Grok API client connection
- [ ] JSON response parsing
- [ ] Error handling
- [ ] Fallback logic

### Integration Tests
- [ ] Voxtral → Grok pipeline
- [ ] Long transcript handling
- [ ] Controversial content
- [ ] Web enrichment

### Performance Tests
- [ ] Response time < 10s for 10-min video
- [ ] Memory usage stable
- [ ] Concurrent request handling
- [ ] Rate limit compliance

## Risk Mitigation

### Risk 1: Grok-4 Not Available
**Mitigation:** Use Grok-2-latest which is confirmed working

### Risk 2: Web Search Not Available
**Mitigation:** Implement without enrichment initially

### Risk 3: Higher Costs Than Expected
**Mitigation:** Implement usage caps and monitoring

### Risk 4: Quality Issues
**Mitigation:** Keep Mixtral as fallback option

## Success Metrics

### Primary Metrics
- **Entity Extraction Coverage**: ≥ 90%
- **Content Censorship**: 0%
- **Processing Cost**: ≤ $0.005/minute
- **API Reliability**: ≥ 99%

### Secondary Metrics
- **Enrichment Value**: ≥ 20% additional context
- **Processing Speed**: < 10s for 10-min video
- **User Satisfaction**: Improved accuracy reports

## Documentation Requirements

### To Be Created
1. Grok API integration guide
2. Prompt engineering best practices
3. Web enrichment usage examples
4. Migration guide from Gemini

### To Be Updated
1. README.md with new pipeline
2. CLI_REFERENCE.md with new options
3. TROUBLESHOOTING.md with Grok issues
4. Cost documentation

## Open Questions (To Be Answered at Gates)

1. **Which Grok models are actually available?**
   - Answer at Gate 1 after API testing

2. **Does web search work via API?**
   - Answer at Gate 2 after feature testing

3. **What's the real cost at scale?**
   - Answer at Gate 4 after volume testing

4. **Should we keep Gemini as fallback?**
   - Answer at Gate 4 based on results

## Decision Timeline

```
Day 1: Gate 1 - Model Availability ──────┐
                                          ↓
Day 2: Gate 2 - Quality Testing ─────────┤
                                          ↓
Day 3: Gate 3 - Enrichment Testing ──────┤
                                          ↓
Day 4: Gate 4 - Cost/Benefit ────────────┤
                                          ↓
Day 5-6: Implementation (if approved) ───┘
```

## Approval Criteria

Before implementation begins, we must have:
- [ ] ✅ at all 4 circuit breaker gates
- [ ] Confirmed API access and pricing
- [ ] Tested with real controversial content
- [ ] Validated quality meets requirements
- [ ] Cost analysis shows acceptable TCO

---

*This PRD uses circuit breakers to prevent assumptions and ensure data-driven decisions at each stage.*
