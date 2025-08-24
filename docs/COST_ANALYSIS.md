# ClipScribe Cost Analysis

*Last Updated: August 23, 2025*

## Overview

ClipScribe processes videos through Google's Gemini AI models. Understanding the cost structure helps you make informed decisions about usage.

## Cost Breakdown

### Per-Video Costs (Estimated)

| Service / Model | Unit | Cost (USD) | Notes |
| :--- | :--- | :--- | :--- |
| **Gemini 2.5 Flash** | 1k characters (input) | $0.000125 | Primary model for transcription and standard analysis. |
| **Gemini 2.5 Flash** | 1k characters (output) | $0.000250 | |
| **Gemini 2.5 Pro** | 1k characters (input) | $0.00125 | Used for complex reasoning and multi-video synthesis. |
| **Gemini 2.5 Pro** | 1k characters (output) | $0.00250 | |
| YouTube Transcript API | per video | $0.00 | Free, used when available. |

The following table outlines the estimated cost per minute of video processing, which includes transcription, entity and relationship extraction, and knowledge graph generation using our **Gemini 2.5 Pro**-based system. Use the `--use-flash` flag for a lower-cost option.

| Video Duration | High Quality (Pro - Default) | Standard Quality (Flash) |
| :--- | :--- | :--- |
| 1 minute | **$0.002** (actual) | ~$0.0035 (estimated) |
| 10 minutes | **$0.031** (actual) | ~$0.035 (estimated) |
| 30 minutes | ~$0.60 | ~$0.105 |
| 60 minutes | ~$1.20 | ~$0.210 |

### API Pricing & Rate Limits (as of August 2025)

**Gemini 2.5 Flash** (pricing reference):
- Input: $0.075 per 1M tokens
- Output: $0.30 per 1M tokens

Rate limits (requests per minute, RPM) depend on authentication tier:
- Free (unlinked API key): ~10 RPM
- Tier 1 (billed project, <$250): ~2,000 RPM
- Tier 2 (billed project, >$250): ~5,000 RPM
- Tier 3 (billed project, >$1,000): ~10,000 RPM
- Vertex AI (enterprise): project-based, customizable quotas

Recommendation: Link your Google AI Studio API key to a billed GCP project to unlock higher quotas, or use Vertex AI for enterprise workloads. Use the auth utility to verify path and quotas:
```bash
poetry run clipscribe utils check-auth
```

Two access paths to Gemini:
- Google AI Studio (API key): set `GOOGLE_API_KEY`; best for individuals/rapid prototyping.
- Vertex AI (enterprise): set `USE_VERTEX_AI=true`, `VERTEX_AI_PROJECT`, and `GOOGLE_APPLICATION_CREDENTIALS`.

Auth check utility:
```bash
poetry run clipscribe utils check-auth
```
Shows which path is active and links to the correct console for quota/billing.

**Token Estimation Formula** (rule-of-thumb):
- Video: ~6K tokens per minute of content
- Transcript + Analysis: ~1K output tokens per minute

### Cost Optimization Strategies

1. **Use Free Tier First**
   - 1500 requests per day free
   - Perfect for personal use

2. **Batch Processing**
   - Process multiple videos in one session
   - Reduces per-video overhead

3. **Cache Results**
   - Never process the same video twice
   - Results are saved locally

4. **Smart Extraction**
   - Only extract what you need
   - Skip expensive features if not required

## Monthly Cost Scenarios

### Personal Use (10 videos/day)
- Average video: 10 minutes
- Daily cost: 10 × $0.20 = $2.00
- **Monthly: ~$60.00**

### Research Use (50 videos/day)
- Mix of short and long videos
- Daily cost: 50 × $0.15 (avg) = $7.50
- **Monthly: ~$225.00**

### Heavy Use (200 videos/day)
- Exceeds free tier
- Daily cost: 200 × $0.15 (avg) = $30.00
- **Monthly: ~$900.00**

### Enterprise Use (1000 videos/day)
Monthly: ~$105

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