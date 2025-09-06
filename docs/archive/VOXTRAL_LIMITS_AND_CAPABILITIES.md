# Voxtral API Limits and Capabilities

## Official Mistral Documentation Summary

Based on official Mistral documentation (January 2025), here are the complete limits and capabilities for Voxtral.

## 📊 Models and Pricing

| Model | Parameters | Use Case | Price |
|-------|-----------|----------|-------|
| **Voxtral Small** | 24B | Production, highest accuracy | $0.001/min |
| **Voxtral Mini** | 3B | Edge deployment, balanced | $0.001/min |
| **Voxtral Mini Transcribe** | 3B | Optimized for transcription | $0.001/min |

**Note**: All models have the same API pricing!

## 🎯 Technical Limits

### Audio Duration Limits
- **Chat with Audio**: ≈20 minutes maximum
- **Transcription Endpoint**: ≈15 minutes currently (longer coming soon)
- **Context Window**: 32,000 tokens
  - Transcription: Up to 30 minutes
  - Understanding/Q&A: Up to 40 minutes

### File Size and Format
- **Maximum file size**: Not explicitly stated (estimated 200MB based on duration)
- **Supported formats**: MP3, MP4, M4A, WAV, FLAC, OGG, WEBM
- **Upload methods**:
  1. Direct file upload
  2. URL (public audio files)
  3. Base64 encoded
  4. Pre-uploaded to Mistral cloud

### Rate Limits
- **Requests**: Based on workspace tier
- **Free tier**: Restrictive (exact limits vary)
- **Paid tiers**: Higher limits, contact support for increases
- **Tokens per minute/month**: Tier-dependent

## ✅ Capabilities

### Core Features
- **Automatic language detection**
- **Multilingual support**: English, Spanish, French, Portuguese, Hindi, German, Dutch, Italian
- **Timestamp granularities**: Segment-level timestamps
- **Response formats**: JSON, verbose JSON
- **No content filters**: Processes all content types

### Advanced Features
- **Q&A on audio content**: Direct questions about audio
- **Summarization**: Generate summaries without separate LLM
- **Function calling**: Trigger backend functions from voice
- **Speaker diarization**: Coming soon
- **Emotion detection**: Coming soon

## 📈 Performance Benchmarks

### Accuracy (Word Error Rate)
| Dataset | Voxtral Small | Gemini 2.5 Flash | Whisper v3 |
|---------|---------------|------------------|------------|
| LibriSpeech Clean | 1.8% | 2.3% | 2.1% |
| Mozilla CV | 4.2% | 5.1% | 4.8% |
| FLEURS | 6.3% | 7.8% | 7.2% |

### Processing Speed
- **Real-time factor**: < 0.5x (faster than real-time)
- **API latency**: < 2 seconds for initialization
- **Concurrent requests**: Limited by tier

## 🔧 API Endpoints

### 1. Transcription Endpoint
```
POST /v1/audio/transcriptions
```
- Optimized for pure transcription
- Uses Voxtral Mini Transcribe
- Supports timestamps

### 2. Chat Completions (Audio)
```
POST /v1/chat/completions
```
- Full audio understanding
- Q&A capabilities
- Function calling

### 3. File Management
```
POST /v1/files (upload)
GET /v1/files/{id}/url (get signed URL)
DELETE /v1/files/{id} (cleanup)
```

## 💰 Cost Comparison

| Service | Cost/min | 94-min Video | Notes |
|---------|----------|--------------|-------|
| Voxtral | $0.001 | $0.094 | No filters, high accuracy |
| Gemini Flash | $0.0035 | $0.33 | Content filters |
| Whisper API | $0.006 | $0.56 | Hallucination issues |
| AssemblyAI | $0.012 | $1.13 | No filters |

## ⚠️ Current Limitations

### What Voxtral CANNOT do (yet):
1. **Process > 20 min audio in single request** (must chunk)
2. **Real-time streaming transcription** (batch only)
3. **Speaker identification** (coming soon)
4. **Emotion detection** (coming soon)
5. **Custom vocabulary training** (enterprise only)

### Workarounds for Long Audio:
1. **Chunk into segments**: Split at natural pauses
2. **Increase playback speed**: 1.5x-2x speed
3. **Use multiple requests**: Process in parallel

## 🚀 Advantages Over Gemini

| Feature | Voxtral | Gemini |
|---------|---------|--------|
| Content Filters | None ✅ | Aggressive ❌ |
| Cost | $0.001/min ✅ | $0.0035/min |
| Accuracy (WER) | 1.8% ✅ | 2.3% |
| Max Duration | 30-40 min ✅ | Variable |
| Open Source | Yes ✅ | No |
| Local Deployment | Yes ✅ | No |

## 🔐 Authentication

```python
# Required header
headers = {
    "Authorization": f"Bearer {MISTRAL_API_KEY}",
    # OR
    "x-api-key": MISTRAL_API_KEY
}
```

## 📝 Best Practices

1. **For long videos (> 15 min)**:
   - Use chunking strategy
   - Process chunks in parallel
   - Maintain overlap for context

2. **For production**:
   - Use Voxtral Small for best accuracy
   - Implement retry logic
   - Monitor rate limits

3. **For cost optimization**:
   - Batch process when possible
   - Cache results
   - Use appropriate model for task

## 🎯 ClipScribe Integration Status

### Implemented ✅
- Full async API client
- All 3 model variants
- Smart fallback from Gemini
- Cost tracking
- Error handling and retries

### Matches/Exceeds Gemini ✅
- **Async/await**: Full support
- **Retry logic**: Exponential backoff
- **Cost tracking**: Per-request tracking
- **Error handling**: Comprehensive
- **Timeout support**: Configurable
- **Multiple models**: 3 variants
- **Fallback integration**: Seamless
- **Progress logging**: Detailed
- **JSON output**: Structured

### Superior to Gemini ✅
- **No content filters** (processes everything)
- **70% cheaper** ($0.001 vs $0.0035)
- **Better accuracy** (1.8% vs 2.3% WER)
- **Longer chunks** (30-40 min vs variable)
- **Open source** (full control)

## 📚 References

- [Mistral Audio Documentation](https://docs.mistral.ai/capabilities/audio/)
- [API Rate Limits](https://admin.mistral.ai/plateforme/limits)
- [Voxtral Models](https://mistral.ai/news/voxtral)
- [Pricing](https://mistral.ai/pricing)
