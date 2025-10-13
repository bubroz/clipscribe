# ClipScribe Infrastructure Cost Analysis PRD

*Last Updated: 2025-08-31*
*Version: 1.2*
*Status: In Development*

## Executive Summary

This PRD provides a comprehensive cost analysis for ClipScribe's infrastructure across three deployment phases. It compares Cloud Run, Compute Engine, and GKE options with detailed breakdowns, optimization strategies, and scaling projections for a solo developer bootstrapping the service.

**Critical Update**: Revised pricing strategy to focus on education-friendly tiers with clear progression paths. Implementing token-based beta system before full payment integration.

## Cost Overview by Phase

### Quick Comparison Table

| Phase | Platform | Base Cost | Per-Video Cost | Break-even Point |
|-------|----------|-----------|----------------|------------------|
| Phase 1 | Hybrid (CR+CE) | $30-45/mo | $0.01-0.10 | ~200 videos/mo |
| Phase 2 | Optimized Hybrid | $45-70/mo | $0.008-0.08 | ~500 videos/mo |
| Phase 3 | GKE | $223/mo | $0.005-0.05 | ~2000 videos/mo |

## Detailed Cost Breakdown

### Phase 1: Hybrid Architecture (Cloud Run + Compute Engine)

#### 1.1 Infrastructure Costs

**Compute Costs:**
```
CPU: $0.0000024/vCPU-second
Memory: $0.0000025/GiB-second

Per Job (20-minute average):
- CPU: 2 vCPU × 1200s × $0.0000024 = $0.00576
- Memory: 4 GiB × 1200s × $0.0000025 = $0.012
- Total compute per job: $0.01776
```

**Storage Costs (GCS):**
```
Storage: $0.020/GB/month
Operations: $0.005/10k operations
Egress: $0.12/GB (to internet)

Per Job:
- Transcript + artifacts: ~1MB = $0.00002
- Operations (read/write): ~10 = $0.000005
- Egress (user downloads): 1MB = $0.00012
- Total storage per job: $0.000145
```

**Redis (Memorystore):**
```
Basic tier: 1GB instance
Cost: $0.016/GB/hour = $11.52/month
Alternative: Redis Labs free tier (30MB)
```

**Total Phase 1 Costs:**
```
Fixed:
- Redis: $11.52/month
- Compute Engine (preemptible): $29.13/month
- Disk: $4.00/month
Total fixed: $44.65/month

Variable:
- Short videos (<45 min): $0.018/job (Cloud Run)
- Long videos (45+ min): $0.001/job (VM overhead only)
Monthly estimate (100 jobs): $46.45
Monthly estimate (500 jobs): $53.65
```

#### 1.2 API Costs

**Gemini API:**
```
Flash (default):
- Input: $0.00001875/1k tokens
- Output: $0.0000375/1k tokens
- Audio: $0.0000125/second

Pro (high quality):
- Input: $0.0000625/1k tokens
- Output: $0.000125/1k tokens
- Audio: $0.000025/second

Per 10-minute video:
- Flash: 600s × $0.0000125 = $0.0075
- Pro: 600s × $0.000025 = $0.015
```

### Phase 2: Hybrid Architecture

#### 2.1 Additional Compute Engine Costs

**VM Specifications:**
```
e2-standard-4 (4 vCPU, 16GB RAM)
Regular: $97.09/month
Preemptible: $29.13/month (70% discount)
Sustained use: ~25% additional discount
```

**Persistent Disk:**
```
100GB Standard: $4/month
100GB SSD: $17/month
```

**Phase 2 Total:**
```
Fixed costs:
- Redis: $11.52
- VM (preemptible): $29.13
- Disk: $4.00
- Cloud Run minimum: $0
Total fixed: $44.65/month

Variable costs:
- Short videos (Cloud Run): $0.018/job
- Long videos (VM): $0.001/job (electricity only)
```

#### 2.2 Cloud Tasks

```
Operations: $0.40/million
Typical usage: ~1000 tasks/month = $0.0004
Negligible cost
```

### Phase 3: GKE Production

#### 3.1 Cluster Costs

**Control Plane:**
```
Zonal cluster: Free
Regional cluster: $0.10/hour = $73/month
Recommendation: Start zonal, upgrade later
```

**Node Pool:**
```
Minimum 2 nodes (HA requirement)
n2-standard-4: $97.09/node/month
With sustained use: ~$73/node/month
Total nodes: $146/month
```

**Additional Services:**
```
Load Balancer: $18/month
Persistent Disks: $8/month (2×100GB)
Container Registry: $5/month
Total additional: $31/month
```

**Phase 3 Total:**
```
Fixed costs:
- Nodes: $146
- Control plane: $0 (zonal)
- Load balancer: $18
- Storage: $8
- Redis: $35 (upgraded 3GB)
- Monitoring: $8
Total fixed: $215/month

Variable costs:
- Highly efficient: $0.001-0.005/job
```

## Cost Optimization Strategies

### 1. Architecture Optimizations

#### 1.1 Smart Routing
```python
def route_job(video_duration: int, current_load: int) -> str:
    """Route job to optimal processor."""
    if video_duration < 900:  # <15 min
        return "cloud-run"  # Always Cloud Run for short
    elif video_duration < 2700:  # 15-45 min
        if current_load < 5:
            return "cloud-run"  # Use Cloud Run if low load
        else:
            return "compute-engine"  # Overflow to VM
    else:  # >45 min
        return "compute-engine"  # Always VM for long
```

#### 1.2 Batch Processing
```python
def batch_optimize():
    """Batch multiple short videos into single invocation."""
    # Saves on cold starts and connection overhead
    # Reduces per-video cost by 30-40%
```

### 2. Resource Optimizations

#### 2.1 Adaptive Quality
```python
class AdaptivQualityProcessor:
    def select_model(self, video_length: int, user_tier: str) -> str:
        if user_tier == "premium":
            return "gemini-pro"
        elif video_length < 300:  # <5 min
            return "gemini-pro"  # Pro for short videos (cheap)
        else:
            return "gemini-flash"  # Flash for long videos
```

#### 2.2 Caching Strategy
```python
CACHE_STRATEGY = {
    "transcripts": "30_days",     # Cache processed transcripts
    "metadata": "7_days",         # Cache video metadata
    "previews": "1_day",          # Cache preview generations
    "duplicate_detection": "90_days"  # Prevent reprocessing
}
```

### 3. Scaling Optimizations

#### 3.1 Preemptible Instances
```yaml
# 70% cost reduction for Compute Engine
gcloud compute instances create worker-vm \
    --preemptible \
    --max-run-duration=24h \
    --maintenance-policy=MIGRATE
```

#### 3.2 Committed Use Discounts
```
1-year commitment: 37% discount
3-year commitment: 55% discount
Break-even: ~6 months of consistent usage
```

## Cost Projections

### Monthly Projections by Usage

| Videos/Month | Phase 1 | Phase 2 | Phase 3 | Optimal Choice |
|--------------|---------|---------|---------|----------------|
| 100 | $13 | $46 | $223 | Phase 1 |
| 500 | $21 | $49 | $225 | Phase 1 |
| 1,000 | $30 | $53 | $227 | Phase 1/2 |
| 5,000 | $102 | $89 | $240 | Phase 2 |
| 10,000 | $192 | $134 | $255 | Phase 2 |
| 50,000 | $912 | $494 | $365 | Phase 3 |

### Cost Per Video by Length

| Video Length | Phase 1 | Phase 2 | Phase 3 |
|--------------|---------|---------|---------|
| 5 min | $0.008 | $0.008 | $0.002 |
| 20 min | $0.025 | $0.025 | $0.005 |
| 60 min | N/A | $0.035 | $0.008 |
| 180 min | N/A | $0.075 | $0.015 |

## Budget Alert Configuration

### 1. Cloud Billing Alerts

```yaml
budgets:
  - name: clipscribe-monthly
    amount: 100  # $100/month budget
    thresholds:
      - 50   # Alert at $50
      - 75   # Warning at $75
      - 90   # Critical at $90
      - 100  # Pause at $100
      - 110  # Emergency stop at $110
    
  - name: clipscribe-daily
    amount: 3.5  # ~$100/month = $3.33/day
    thresholds:
      - 80   # Alert at $2.80
      - 100  # Warning at $3.50
      - 120  # STOP at $4.20
```

### 2. Programmatic Cost Controls

```python
class CostController:
    def __init__(self, daily_limit: float = 2.0):
        self.daily_limit = daily_limit
        self.current_spend = 0
    
    async def check_budget(self) -> bool:
        """Check if we're within budget."""
        today_spend = await self.get_today_spend()
        
        if today_spend >= self.daily_limit:
            # Pause processing
            await self.pause_workers()
            await self.notify_admin(
                f"Daily budget ${self.daily_limit} exceeded. "
                f"Current: ${today_spend:.2f}"
            )
            return False
        
        return True
    
    async def estimate_job_cost(self, video_duration: int) -> float:
        """Estimate cost before processing."""
        compute_cost = (video_duration / 60) * 0.018
        api_cost = video_duration * 0.0000125
        return compute_cost + api_cost
```

## ROI Analysis

### Cost vs. Value Metrics

```
Customer Acquisition Cost (CAC): $30-100
Lifetime Value (LTV): $500-5,000
Break-even: 1-2 months per user
```

### Recommended Pricing Strategy

**Education-Focused Tiered Model:**

```
Student/Educator Tier: $39/month
- 40 videos/month (<90 minutes each)
- Gemini Flash model (fast & efficient)
- 30-day retention
- Basic API access (100 calls/month)
- Export to citation formats
- Target: Students, educators, libraries

Researcher Tier: $79/month
- 100 videos/month (<2 hours each)
- Choice of Flash or Pro model
- 60-day retention
- Full API access (1,000 calls/month)
- All export formats
- Priority processing
- Target: Academics, journalists, independent researchers

Analyst Tier: $199/month  
- 200 videos/month (<3 hours each)
- Gemini Pro model priority
- 90-day retention
- Unlimited API access
- Batch processing
- Custom entity training
- Priority support
- Target: OSINT analysts, consultants, businesses

Enterprise Tier: $999/month
- 1,000 videos/month (unlimited length)
- All models available
- 1-year retention
- White-label options
- SSO integration
- SLA guarantees
- Dedicated support
- Target: Corporations, law firms, agencies

Government/Intelligence: Custom ($10K-50K/year)
- On-premise deployment option
- Air-gapped configurations
- ITAR/FedRAMP compliance
- Custom integrations
- Dedicated infrastructure
- Target: Government agencies, defense contractors
```

**Beta Testing Tiers:**

```
Alpha Tier: FREE (Limited Release)
- 20 videos/month
- Up to 2 hours per video
- Flash model only
- 7-day retention
- Direct feedback channel
- Target: 5-10 trusted testers

Beta Tier: FREE (Closed Beta)
- 50 videos/month
- Up to 3 hours per video
- Flash + Pro models
- 30-day retention
- Beta features access
- Target: 20-50 early adopters
```

**Pay-Per-Video (No Subscription):**
```
Single video processing:
- 0-30 min: $0.99
- 30-60 min: $1.99
- 60-120 min: $3.99
- 120-240 min: $7.99
- 240+ min: $14.99

Bundle packages (30-day expiration):
- 5-video pack: $8.99 (save 10%)
- 10-video pack: $16.99 (save 15%)
- 25-video pack: $39.99 (save 20%)
```

**Usage-Based Overages:**
```
Additional videos beyond plan:
- <10 min: $0.50/video
- 10-60 min: $1.00/video
- 60-180 min: $2.00/video
- 180+ min: $5.00/video

Premium add-ons:
- Rush processing (15 min): +$5/video
- Multi-language extraction: +$1/video
- Custom entity training: +$100/setup + $10/month
- Bulk export (>1000 videos): +$50/export
```

### Market Positioning Rationale

**Why This Pricing Works:**

1. **Value Anchoring**: 
   - vs. Transcription services: 10x the value at 3x the price
   - vs. Intelligence platforms: 90% of capabilities at 1% of cost

2. **Clear Segmentation**:
   - Researcher: Price-sensitive, lower usage
   - Analyst: Value-driven, professional use
   - Enterprise: Feature-driven, compliance needs

3. **Growth Path**: Natural progression encourages upgrades

4. **Competitive Moat**: Long videos (2+ hours) that competitors can't handle

### Infrastructure Efficiency

```
Phase 1 Efficiency: 
- 90% of cost is API (Gemini)
- 10% infrastructure
- Optimization focus: Reduce API calls

Phase 2 Efficiency:
- 60% API costs
- 40% infrastructure
- Optimization focus: Improve utilization

Phase 3 Efficiency:
- 30% API costs
- 70% infrastructure
- Optimization focus: Scale efficiency
```

## Decision Framework

### When to Upgrade Phases

**Phase 1 → Phase 2:**
- Monthly costs exceed $100
- Need videos >60 minutes
- >1000 videos/month consistently

**Phase 2 → Phase 3:**
- Monthly costs exceed $500
- Need <1 minute job latency
- >10,000 videos/month
- Multiple concurrent users

### Emergency Cost Reduction

**If costs spike:**
1. Immediately pause non-essential processing
2. Switch all processing to Gemini Flash
3. Reduce worker instances to minimum
4. Enable aggressive caching
5. Implement request throttling

```python
EMERGENCY_CONFIG = {
    "max_daily_jobs": 100,
    "max_video_duration": 900,  # 15 min
    "force_model": "gemini-flash",
    "cache_everything": True,
    "reject_duplicates": True
}
```

## Beta Phase Cost Projections

### Alpha Phase (Month 1-2)
```
Infrastructure:
- Redis: $11.52/month
- Compute Engine: $29.13/month (preemptible)
- Cloud Run: ~$5/month (minimal usage)
- Monitoring: $0 (free tier)
Total: ~$46/month

API Costs (10 alpha users, 200 videos):
- Gemini Flash: ~$15/month
- Total with infrastructure: ~$61/month
```

### Beta Phase (Month 3-4)
```
Infrastructure: $46/month (same as alpha)

API Costs (50 beta users, 1000 videos):
- Gemini Flash: ~$75/month
- Gemini Pro (10%): ~$15/month
- Total with infrastructure: ~$136/month

Well within $100/month budget with headroom
```

### Early Access Phase (Month 5-6)
```
Infrastructure:
- Upgrade Redis: $35/month (3GB)
- Add second VM: $58/month total
- Cloud Run: ~$20/month
- Monitoring: $8/month
Total: ~$121/month

API Costs (200 users, 4000 videos):
- Mixed model usage: ~$350/month
- Total: ~$471/month

Revenue (assuming 50% paid):
- 50 Student @ $39: $1,950
- 30 Researcher @ $79: $2,370
- 20 Analyst @ $199: $3,980
- Total revenue: $8,300/month
- Profit margin: 94%
```

## Summary Recommendations

### For Solo Developer Bootstrap:

1. **Start with Phase 1** ($0-20/month)
   - Perfect for validation
   - No fixed costs
   - Pay only for usage

2. **Monitor these triggers for Phase 2:**
   - Consistent 500+ videos/month
   - Users requesting >60 min videos
   - Monthly cost exceeding $50

3. **Cost optimization priorities:**
   - Implement caching (40% reduction)
   - Batch processing (30% reduction)
   - Smart model selection (50% reduction)

4. **Budget safety:**
   - Set hard limit at $50/month initially
   - Auto-pause at 80% budget
   - Daily monitoring and alerts

Remember: Perfect infrastructure is the enemy of shipping. Start simple, monitor costs, optimize based on real usage.
