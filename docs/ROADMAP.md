# ClipScribe Development Roadmap

*Last Updated: 2025-07-30*

## Architecture: Quality-First by Default

### Previous State
- **Hybrid Extraction (Old Default)**: Gemini 2.5 Flash (~$0.003/video). User feedback indicated this was "seriously lacking in accuracy."
- **Pro Extraction (Old Flag)**: Gemini 2.5 Pro (~$0.017/video) available via `--use-pro`.

### Architectural Decision (v2.21.0)
Based on a comprehensive benchmark analysis (`BENCHMARK_REPORT.md`), we have shifted to a **Quality-First architecture**:

1.  **Default to Gemini 2.5 Pro**: Ensures the highest quality, professional-grade intelligence for all users out of the box.
2.  **Optional `--use-flash` flag**: Provides a cost-conscious option for users who prioritize speed and volume over maximum quality.

This change aligns with our core identity of providing reliable video intelligence and directly addresses user feedback on quality.

### Implementation Plan

#### Phase 1: Quality-First Default (v2.21.0) - ✅ COMPLETE
- [x] Switched default model from Flash to Pro.
- [x] Renamed `--use-pro` to `--use-flash` for the cost-conscious option.
- [x] Updated all CLI help text and documentation.
- [x] Completed and documented a comprehensive benchmark analysis.

#### Phase 2: Enhanced Cost Management (v2.22.0)
- [ ] Add `--max-cost` flag to prevent runaway expenses.
- [ ] Implement cost tracking across sessions.
- [ ] Add cost estimation before processing.
- [ ] Create cost-per-minute calculator.

#### Phase 3: Smart Auto-Selection (v2.23.0)
- [ ] Research content complexity analysis to potentially auto-select the best model.
- [ ] Explore user preferences and cost limits for smarter defaults.

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