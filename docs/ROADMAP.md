# ClipScribe Development Roadmap

*Last Updated: July 31, 2025*

## Strategic Overview

Following a comprehensive test suite overhaul, ClipScribe is in a stable, production-ready state. The next phase of development focuses on reinforcing this foundation and then delivering high-value, user-centric features. Our priorities are organized into a tiered system to ensure we build a robust, professional-grade tool.

---

## Tier 1: Foundational Stability & Trust (Immediate Priorities)

This tier includes essential technical tasks that ensure the long-term health, maintainability, and trustworthiness of the application.

### Priority 1: Structured Logging Implementation (`structlog`)
- **Status**: Not Started
- **Effort**: ~2-3 hours
- **Justification**: Structured (JSON) logs are critical for efficient debugging and monitoring in a production environment. Adopting `structlog` will professionalize our logging, making the application easier to maintain and troubleshoot.
- **Tasks**:
  1. Add `structlog` and `rich` dependencies.
  2. Create a `logging_config.py` module for configuration.
  3. Integrate the new logger throughout the application.

### Priority 2: Systematic Test Coverage Improvement
- **Status**: Not Started
- **Effort**: ~4-6+ hours
- **Justification**: While all 39 of our existing tests are passing, our overall test *coverage* is still below the 80% industry standard. Uncovered code is a liability. Increasing coverage is the single most important task for ensuring long-term stability and preventing regressions.
- **Tasks**:
  1. Add unit tests for critical extractor and retriever components.
  2. Increase integration test coverage for all CLI commands.
  3. Add tests for error handling and edge cases.

---

## Tier 2: Core Product Value & User Experience (Next Priorities)

This tier focuses on features that directly enhance the user's experience and trust in the core functionality of ClipScribe.

### Priority 3: Enhanced Cost Management
- **Status**: Not Started
- **Justification**: While our cost model is a key feature, the user interface for it is minimal. Enhancing cost management features will build user trust and improve the core value proposition.
- **Tasks**:
  1. Implement a `--max-cost` flag to prevent budget overruns.
  2. Add pre-run cost estimates for all processing commands.
  3. Improve the visibility of cost tracking in the final output.

### Priority 4: Refined CLI User Experience
- **Status**: Not Started
- **Justification**: A polished CLI is a hallmark of a professional tool. Now that the CLI is fast and stable, we can focus on making it more intuitive and informative.
- **Tasks**:
  1. Improve the real-time progress bars to be more descriptive.
  2. Ensure all output tables are consistent and easy to read.
  3. Refine success and error messages to be clearer and more actionable.

---

## Tier 3: High-Value Feature Enhancements (Future Work)

This tier includes new, high-impact features that build on our stable foundation to expand ClipScribe's capabilities.

### Priority 5: Visual Entity Recognition (VER)
- **Status**: Not Started
- **Justification**: We already pay for multimodal (video) processing. Extracting entities from on-screen text (chyrons, slides, logos) is a high-value feature that leverages our existing pipeline for a relatively low implementation cost.
- **Tasks**:
  1. Integrate an OCR library to extract text from video frames.
  2. Develop logic to correlate extracted text with timestamps.
  3. Add visually-extracted entities to the final output.

### Priority 6: Output Verification
- **Status**: Not Started
- **Justification**: For users in research and intelligence, data integrity is paramount. An output verification feature would provide a strong guarantee of quality and completeness.
- **Tasks**:
  1. Implement a `--verify-output` flag.
  2. Add checks for valid JSON, non-empty files, and cross-file consistency.
  3. Provide a clear verification report to the user.

---

## Contributing to Roadmap
- See GitHub issues for detailed tasks.
- Run tests and benchmarks to inform decisions: `poetry run pytest -v`
- Submit PRs with clear justifications and links to roadmap items.
