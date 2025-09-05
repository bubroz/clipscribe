# Product Requirements Document: Voxtral Integration with Smart Fallback
**Version:** 1.0  
**Date:** January 2025  
**Author:** ClipScribe Engineering Team  
**Status:** APPROVED FOR IMPLEMENTATION

## 1. Executive Summary

### Problem Statement
Gemini's safety filters block legitimate journalistic content (PBS Frontline, defense topics) with a 35% failure rate on sensitive content. Even with `BLOCK_NONE` settings, server-side filters reject critical documentary content. Additionally, Gemini's transcription costs ($0.0035/minute) are higher than necessary.

### Solution
Implement **Mistral's Voxtral Small (24B)** as the primary transcription service, retaining Gemini for entity extraction from text. This hybrid approach ensures 100% content processing success while reducing costs by 70%.

### Impact
- **Success Rate**: 100% for all content types (no censorship)
- **Accuracy Improvement**: 1.8% WER vs Gemini's 2.3% WER
- **Cost Reduction**: 70% lower transcription costs ($0.001/min vs $0.0035/min)
- **Performance**: 30-40 minute chunks processed natively

## 2. Requirements

### 2.1 Functional Requirements

#### FR-1: Voxtral API Integration
- Support for Voxtral Small (24B) model via Mistral API
- Authentication with API key management
- Async/await support for concurrent processing
- 32K token context window (30-40 min audio)

#### FR-2: Smart Fallback Strategy
```python
# Phase 1: Conservative Fallback
async def transcribe_with_fallback(video_path):
    try:
        # Try Gemini first for non-sensitive content
        result = await gemini_transcribe(video_path)
        if result.finish_reason != 2:  # Not safety blocked
            return result
    except Exception as e:
        logger.warning(f"Gemini failed: {e}")
    
    # Fallback to Voxtral for blocked/failed content
    return await voxtral_transcribe(video_path)

# Phase 2: Voxtral Primary (after validation)
async def transcribe_with_voxtral(video_path):
    # Use Voxtral for ALL transcription
    transcript = await voxtral.transcribe(video_path)
    
    # Use Gemini for entity extraction (text-only, rarely blocks)
    entities = await gemini.extract_entities(transcript.text)
    
    return combine_results(transcript, entities)
```

#### FR-3: Model Selection
- Support multiple Voxtral models:
  - Voxtral Small (24B) - Maximum accuracy
  - Voxtral Mini (3B) - Edge deployment option
  - Voxtral Mini Transcribe - API-optimized variant
- Configurable via environment variables
- Default to Voxtral Small for best accuracy

### 2.2 Non-Functional Requirements

#### NFR-1: Performance
- Process 94-minute videos in < 5 minutes
- Support concurrent chunk processing
- Maintain < 2 second API response time

#### NFR-2: Reliability
- 99.9% uptime for transcription service
- Automatic retry with exponential backoff
- Graceful degradation to Gemini if Voxtral unavailable

#### NFR-3: Cost Management
- Track per-model usage and costs
- Alert on unusual spending patterns
- Monthly cost reports by model

## 3. Technical Design

### 3.1 Architecture

```
Video Input
    ↓
[Content Classification]
    ↓
[Voxtral Transcription] ← Primary path
    ↓
[Text Output]
    ↓
[Gemini Entity Extraction] ← Text-only, no video
    ↓
[Combined Output]
```

### 3.2 Implementation Components

#### VoxtralTranscriber Class
```python
class VoxtralTranscriber:
    def __init__(self, api_key: str, model: str = "voxtral-small"):
        self.client = MistralAsyncClient(api_key=api_key)
        self.model = model
        
    async def transcribe(self, audio_path: str) -> TranscriptionResult:
        # Upload audio to Mistral
        file = await self.client.files.upload(audio_path)
        
        # Transcribe with Voxtral
        response = await self.client.audio.transcriptions.create(
            model=self.model,
            file=file.id,
            response_format="json"
        )
        
        return TranscriptionResult(
            text=response.text,
            language=response.language,
            duration=response.duration,
            cost=response.duration * 0.001 / 60  # $0.001/min
        )
```

### 3.3 Migration Strategy

#### Phase 1: Fallback Mode (Week 1-2)
- Implement Voxtral as fallback for Gemini blocks
- Test with PBS Frontline and sensitive content
- Monitor accuracy and performance metrics

#### Phase 2: A/B Testing (Week 3-4)
- Route 10% of traffic to Voxtral primary
- Compare accuracy metrics (WER, entity extraction)
- Validate cost savings

#### Phase 3: Full Migration (Week 5-6)
- Switch to Voxtral for all transcription
- Retain Gemini for entity extraction only
- Document 70% cost reduction

## 4. Success Metrics

### 4.1 Primary KPIs
- **Content Success Rate**: 100% (up from 65%)
- **Transcription Accuracy**: < 2% WER
- **Cost per Minute**: $0.001 (down from $0.0035)
- **Processing Time**: < 0.1x real-time

### 4.2 Secondary Metrics
- Entity extraction quality maintained
- User satisfaction scores
- API reliability (99.9% uptime)
- Support ticket reduction

## 5. Testing Requirements

### 5.1 Unit Tests
- Voxtral API client methods
- Fallback logic conditions
- Cost calculation accuracy
- Error handling paths

### 5.2 Integration Tests
- End-to-end video processing
- Gemini + Voxtral hybrid flow
- Long-form content (30+ minutes)
- Concurrent processing

### 5.3 Validation Tests
- PBS Frontline documentary (94 min)
- Security/defense content
- Multi-language videos
- Noisy audio conditions

## 6. Rollout Plan

### Week 1-2: Implementation
- [ ] Implement VoxtralTranscriber class
- [ ] Add fallback logic to transcriber
- [ ] Update configuration management
- [ ] Write comprehensive tests

### Week 3-4: Testing & Validation
- [ ] Test with sensitive content library
- [ ] Validate accuracy improvements
- [ ] Confirm cost reductions
- [ ] Load testing for scale

### Week 5-6: Production Deployment
- [ ] Deploy to staging environment
- [ ] A/B test with real traffic
- [ ] Monitor metrics dashboard
- [ ] Full production rollout

## 7. Risk Analysis

### Risks
1. **Voxtral API Stability** (Medium)
   - Mitigation: Keep Gemini as fallback
   
2. **Integration Complexity** (Low)
   - Mitigation: Phased rollout approach
   
3. **Cost Overruns** (Low)
   - Mitigation: Usage monitoring and alerts

### Benefits
1. **100% Content Coverage** - No censorship
2. **70% Cost Savings** - $0.001 vs $0.0035/min
3. **Better Accuracy** - 1.8% vs 2.3% WER
4. **Future Proof** - Open source, no vendor lock-in

## 8. Appendix

### A. Voxtral Model Comparison

| Model | Parameters | WER | Cost | Use Case |
|-------|-----------|-----|------|----------|
| Voxtral Small | 24B | 1.8% | $0.001/min | Production |
| Voxtral Mini | 3B | 2.5% | $0.001/min | Edge/Local |
| Voxtral Mini Transcribe | 3B | 2.3% | $0.001/min | High-volume |

### B. Cost Analysis (94-min PBS Frontline)

| Approach | Cost | Success Rate |
|----------|------|--------------|
| Gemini Only | $0.33 | 0% (blocked) |
| Gemini + AssemblyAI | $1.13 | 100% |
| Voxtral + Gemini | $0.10 | 100% |
| Pure Voxtral | $0.094 | 100% |

### C. API Documentation
- [Mistral API Docs](https://docs.mistral.ai/api/)
- [Voxtral Models](https://mistral.ai/news/voxtral)
- [Pricing](https://mistral.ai/pricing)
