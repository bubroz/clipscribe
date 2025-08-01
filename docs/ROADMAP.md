# ClipScribe Development Roadmap

*Last Updated: July 31, 2025 - Test Suite Stabilized*

## Architecture: Quality-First by Default

### Previous State
- **Hybrid Extraction (Old Default)**: Gemini 2.5 Flash (~$0.003/video). User feedback indicated this was "seriously lacking in accuracy."
- **Pro Extraction (Old Flag)**: Gemini 2.5 Pro (~$0.017/video) available via `--use-pro`.

### Architectural Decision (v2.21.0)
Based on a comprehensive benchmark analysis (`BENCHMARK_REPORT.md`), we have shifted to a **Quality-First architecture**:

1.  **Default to Gemini 2.5 Pro**: Ensures the highest quality, professional-grade intelligence for all users out of the box.
2.  **Optional `--use-flash` flag**: Provides a cost-conscious option for users who prioritize speed and volume over maximum quality.

This change aligns with our core identity of providing reliable video intelligence and directly addresses user feedback on quality.

---

## Logging Architecture: `structlog` Adoption

### Decision (v2.22.0)
After a comprehensive review of Python's logging landscape, we have decided to adopt the **`structlog`** library to professionalize our application's logging.

**Justification:**
- **Best of Both Worlds**: It enhances the fast, stable standard `logging` module without replacing it.
- **Unmatched Flexibility**: The processor-based architecture allows for separate, optimal configurations for both human-readable console output (via `rich`) and machine-readable, structured JSON file output.
- **Production Ready**: This move enables powerful log querying, monitoring, and debugging, which are essential for a professional-grade tool.

---

## Immediate Priorities (Current State: v2.22.2)

### Priority 1: Systematic Test Coverage Improvement (Next 4-6 hours)
**Current Status**: 44% overall coverage (target: 80%+)

**Critical Gaps**:
- Retrievers: 17-68% coverage
- Extractors: 0-91% coverage  
- Core processing paths require more comprehensive testing.

**Tasks**:
1. Add integration tests for the full video processing pipeline.
2. Add unit tests for critical extractor components.
3. Add tests for error handling and edge cases.
4. Validate production readiness through comprehensive testing.

**Why First**: A robust test suite is the foundation for reliable production deployment and future feature development.

### Priority 2: Structured Logging Implementation (Next 2-3 hours)
**Tasks**:
1. **Add Dependencies**: `poetry add structlog rich`
2. **Create New Config**: A new `logging_config.py` module will be created to house the `structlog` configuration.
3. **Integrate and Refactor**: The application will be updated to use the new structured logger, and key logging statements will be enriched with contextual key-value pairs.

**Why Second**: A quality-of-life improvement for debugging and monitoring, but not user-blocking.

---

## Future Roadmap Items

### Q4 2025: Advanced Features & Polish
- **Output Verification**: Implement a `--verify-output` flag for post-processing validation of all generated files.
- **Enhanced Cost Management**: Add a `--max-cost` flag, session-based cost tracking, and pre-processing cost estimates.
- **Performance Optimization**: Profile and optimize bottlenecks discovered during testing.

### Q1 2026: Advanced Intelligence
- **Multi-Modal Intelligence**: Integrate visual scene analysis and audio sentiment identification.
- **Smart Auto-Selection**: Research content complexity analysis to potentially auto-select the best model for a given video.

### Q2 2026: Enterprise Features
- **Advanced Security**: Implement advanced security and compliance features.
- **Custom Models**: Allow for custom model training and fine-tuning.
- **Enterprise Integrations**: Develop enterprise-grade API and integrations.

---

## Contributing to Roadmap
- See GitHub issues for tasks
- Run benchmarks locally: `poetry run pytest --durations=0`
- Submit PRs with data to inform decisions
