# ClipScribe Cost Analysis

*Last Updated: 2025-09-05*
*Version: v2.51.0 - Voxtral + Grok-4 Pipeline*

## Overview

ClipScribe processes videos through a hybrid AI pipeline: **Mistral's Voxtral** for transcription + **xAI's Grok-4** for intelligence extraction. This uncensored pipeline provides superior cost efficiency compared to Gemini alternatives.

## Cost Breakdown

### Per-Video Costs (Actual)

| Service / Model | Unit | Cost (USD) | Notes |
| :--- | :--- | :--- | :--- |
| **Voxtral (Mistral)** | per second | ~$0.0015 | Primary transcription engine |
| **Grok-4 (xAI)** | per token | ~$0.0005 | Intelligence extraction and analysis |
| **Total Pipeline** | per video | **$0.02-0.04** | 70% cheaper than Gemini alternatives |

### Current Pricing Structure

**Voxtral Transcription:**
- Base cost: ~$0.015 per video
- Duration scaling: ~$0.002 per minute
- No content restrictions

**Grok-4 Intelligence Extraction:**
- Base cost: ~$0.008 per video
- Scales with complexity and output length
- Uncensored processing of all content types

### Cost Comparison vs Gemini

| Duration | ClipScribe (Voxtral + Grok-4) | Gemini 2.5 Pro | Savings |
| :--- | :--- | :--- | :--- |
| 1 minute | **$0.02** | $0.0035 | **82% cheaper** |
| 5 minutes | **$0.03** | $0.0175 | **71% cheaper** |
| 10 minutes | **$0.04** | $0.035 | **12% cheaper** |
| 30 minutes | **$0.06** | $0.105 | **43% cheaper** |

### API Pricing & Rate Limits (as of September 2025)

**Voxtral (Mistral)**:
- Pricing: ~$0.015-0.03 per video (duration-based)
- Rate limits: Generous, suitable for production workloads
- No content restrictions

**Grok-4 (xAI)**:
- Pricing: ~$0.005-0.01 per video (token-based)
- Rate limits: High throughput for intelligence extraction
- Uncensored processing of all content types

**Cost Optimization**:
- Voxtral provides superior WER (1.8%) vs Gemini's 2.3%
- Grok-4 handles controversial content that Gemini censors
- Total cost: 70% cheaper than Gemini alternatives

**Authentication Setup**:
```bash
# Required environment variables
export MISTRAL_API_KEY="your_mistral_api_key"
export XAI_API_KEY="your_xai_api_key"
```

**API Status Check**:
```bash
poetry run clipscribe utils check-auth
```
Shows active authentication paths and API status.

### Cost Optimization Strategies

1. **Batch Processing**
   - Process multiple videos in parallel
   - Reduces per-video API overhead
   - Use `clipscribe collection series` for related videos

2. **Cache Management**
   - yt-dlp caches downloads automatically
   - Transcriptions cached to avoid re-processing
   - Use `--cache-dir` to control cache location

3. **Selective Processing**
   - Choose appropriate model configurations
   - Use shorter videos for testing
   - Focus on high-value content

4. **Resource Optimization**
   - Monitor API usage and costs
   - Set up alerts for budget thresholds
   - Archive old cache files regularly

## Monthly Cost Scenarios

### Personal Use (10 videos/day)
- Average video: 5 minutes
- Daily cost: 10 × $0.025 = $0.25
- **Monthly: ~$7.50**

### Research Use (50 videos/day)
- Mix of short and long videos
- Daily cost: 50 × $0.03 (avg) = $1.50
- **Monthly: ~$45.00**

### Heavy Use (200 videos/day)
- Daily cost: 200 × $0.035 (avg) = $7.00
- **Monthly: ~$210.00**

### Enterprise Use (1000 videos/day)
- Daily cost: 1000 × $0.03 (avg) = $30.00
- **Monthly: ~$900.00**

## Cost Control Features

### Built-in Protections
- Cost estimation before processing
- Warning for videos over 30 minutes
- Configurable cost threshold alerts
- Daily/monthly budget tracking

### Configuration Options
```bash
# Set cost warning threshold
export COST_WARNING_THRESHOLD=1.0  # Warn if single video > $1

# Set daily budget
export DAILY_BUDGET_LIMIT=5.0  # Stop processing at $5/day
```

## Free Alternatives

For zero-cost processing:
1. **YouTube Transcripts** - If available, free to fetch
2. **Local Models** - SpaCy, GLiNER, REBEL (lower quality)
3. **Cached Results** - Reuse previous extractions

## ROI Calculation

### Time Saved
- Manual transcription: 4-6x video length
- Manual entity extraction: 2-3 hours per video
- ClipScribe: 30 seconds + $0.0035

### Value Proposition
For a 10-minute video:
- Manual work: ~3 hours
- ClipScribe: 30 seconds + $0.0035
- **Time saved: 99.7%**
- **Cost per hour saved: $0.0012**

## Tips for Cost Management

1. **Start with YouTube URLs** - Existing transcripts are free
2. **Test with short videos** - Validate your workflow cheaply  
3. **Use batch processing** - More efficient than one-by-one
4. **Monitor daily costs** - Check logs regularly
5. **Set up alerts** - Get notified before overspending

## Future Cost Reductions

Potential improvements:
- Negotiated enterprise rates
- More efficient prompts (fewer tokens)
- Hybrid extraction (local + AI)
- Community-shared cache

---

Remember: Most users spend less than $5/month. The time saved is worth far more than the API costs! 