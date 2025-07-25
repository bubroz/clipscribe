# ClipScribe Development Roadmap

*Last Updated: 2025-07-25*

## Architecture Decision: Hybrid vs Pro-Only Extraction

### Current State
- **Hybrid Extraction (Default)**: Gemini 2.5 Flash (~$0.003/video) with local model fallbacks
- **Pro Extraction (--use-pro)**: Gemini 2.5 Pro (~$0.017/video) for highest quality
- **Quality Gap**: User feedback indicates hybrid output can be "seriously lacking in accuracy"

### Decision Framework

#### Option 1: Keep Hybrid as Default (Cost-First)
**Pros:**
- Lower barrier to entry (~$0.003 vs $0.017 per video)
- Good enough for basic transcription and entity extraction
- Supports cost-conscious users and high-volume processing
- **Speed**: Gemini 2.5 Flash typically faster than Pro (analysis needed)

**Cons:**
- Quality complaints from users expecting professional-grade output
- May hurt product reputation if default experience is subpar
- Requires users to know about --use-pro flag for quality work

#### Option 2: Switch to Pro-Only Default (Quality-First)
**Pros:**
- Consistent high-quality output experience
- Eliminates quality gap confusion
- Aligns with "video intelligence" positioning vs basic transcription

**Cons:**
- Higher cost barrier (~6x more expensive)
- May limit adoption for high-volume use cases
- Still need hybrid option for cost-sensitive scenarios
- **Speed**: Gemini 2.5 Pro may be slower than Flash (needs benchmarking)

#### Option 3: Smart Auto-Selection (Adaptive)
**Pros:**
- Automatically choose model based on content complexity
- Best of both worlds: cost efficiency + quality when needed
- User doesn't need to understand model differences
- **Speed**: Optimizes for both speed and quality based on content

**Cons:**
- Added complexity in decision logic
- Unpredictable costs for users
- Risk of wrong model selection
- **Speed**: Analysis overhead for auto-selection

### Speed Analysis Required

**CRITICAL RESEARCH NEEDED**: Before implementing architecture decision, we need:

1. **Processing Speed Benchmarks**:
   - [ ] Gemini 2.5 Flash vs Pro speed comparison (same video)
   - [ ] Download speed impact: audio-only vs full video
   - [ ] End-to-end processing time analysis
   - [ ] Concurrent processing performance

2. **Speed Optimization Opportunities**:
   - [ ] Audio-only processing as default with video fallback
   - [ ] Parallel download + processing pipeline
   - [ ] Smarter mode detection to avoid unnecessary video downloads
   - [ ] Streaming processing for long videos

3. **Cost vs Speed vs Quality Matrix**:
   ```
   Model    | Speed | Cost  | Quality | Use Case
   ---------|-------|-------|---------|----------
   Flash    | Fast  | Low   | Good    | High volume
   Pro      | ?     | High  | High    | Quality critical
   Auto     | ?     | ?     | ?       | General use
   ```

### Recommendation: Quality-First with Cost Options

**Proposed Changes:**
1. **Default to Gemini 2.5 Pro** for highest quality user experience
2. **Add --use-flash flag** for cost-conscious processing
3. **Clear cost messaging** in CLI output ($0.017 vs $0.003)
4. **Batch processing discounts** for high-volume Pro usage

**Implementation Plan:**

#### Phase 1: Quality-First Default (v2.21.0)
- [ ] Switch default model from Flash to Pro
- [ ] Add --use-flash flag for cost-conscious users  
- [ ] Update CLI help text with cost implications
- [ ] Add cost warnings for large batch jobs

#### Phase 2: Enhanced Cost Management (v2.22.0)
- [ ] Add --max-cost flag to prevent runaway expenses
- [ ] Implement cost tracking across sessions
- [ ] Add cost estimation before processing
- [ ] Create cost-per-minute calculator

#### Phase 3: Smart Auto-Selection (v2.23.0)
- [ ] Content complexity analysis
- [ ] Auto-model selection based on content type
- [ ] User preferences and cost limits
- [ ] Fallback strategies for rate limits

### Quality Metrics to Track

**Before Change (Hybrid Default):**
- Entity extraction accuracy
- Relationship specificity scores
- User satisfaction ratings
- Cost per quality unit

**After Change (Pro Default):**
- Improved entity/relationship quality
- Reduced "seriously lacking accuracy" feedback
- Adoption rate vs cost increase
- Cost optimization usage (--use-flash)

### Timeline
- **Decision Point**: End of July 2025
- **Implementation**: August 2025
- **Quality Assessment**: September 2025
- **Iteration**: October 2025

### Success Criteria
1. **Quality**: >90% reduction in quality complaints
2. **Adoption**: <20% decrease in new user adoption
3. **Revenue**: Cost increase offset by improved user retention
4. **Satisfaction**: >4.5/5 average quality rating

---

## Future Roadmap Items

### Timeline Intelligence (Q4 2025)
- Replace Gemini with specialized timeline models
- Accurate timestamp extraction and temporal chains
- Evidence synchronization with video timestamps
- Timeline visualization and export

### Multi-Modal Intelligence (Q1 2026)
- Visual scene analysis integration
- Audio sentiment and speaker identification
- Synchronized text + visual + audio extraction
- Cross-modal relationship detection

### Enterprise Features (Q2 2026)
- Advanced security and compliance features
- Custom model training and fine-tuning
- Enterprise-grade API and integrations
- Advanced analytics and reporting

### Performance Optimization (Ongoing)
- Streaming extraction for long videos
- Parallel processing improvements
- Memory optimization for large collections
- Cost optimization algorithms 

## Short-Term Priorities (Next 1-2 Weeks) 🚀

1. **Benchmark Speed Differentials** (Critical for Architecture Decision)
   - Compare hybrid vs pro-only: Time per minute, entities/relationships per second
   - Tools: Use tests/integration/test_full_workflow.py with timing
   - Goal: <20% speed loss for >50% quality gain to justify Pro default

## Contributing to Roadmap
- See GitHub issues for tasks
- Run benchmarks locally: poetry run pytest --durations=0
- Submit PRs with data to inform decisions 