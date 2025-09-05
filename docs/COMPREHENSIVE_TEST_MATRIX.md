# Comprehensive Test Matrix for Critical Issue Resolution
**Version:** 1.0  
**Date:** September 2, 2025  
**Status:** APPROVED

## Test Coverage Overview

This matrix ensures 100% validation of all three critical solutions:
1. **API Abstraction Layer** - Method compatibility
2. **Grok Integration** - Uncensored fallback
3. **Multi-Pass Extraction** - Zero truncation

## 1. API Abstraction Layer Tests

### 1.1 Unit Tests

| Test ID | Test Case | Expected Result | Priority |
|---------|-----------|-----------------|----------|
| API-U-01 | Parameter mapping Gemini→Vertex | All params correctly mapped | CRITICAL |
| API-U-02 | Parameter mapping Vertex→Gemini | Reverse mapping works | CRITICAL |
| API-U-03 | Method resolution for transcribe() | Finds correct method | CRITICAL |
| API-U-04 | Method resolution fallback chain | Falls back to process() | HIGH |
| API-U-05 | Unknown parameter handling | Passes through unchanged | MEDIUM |
| API-U-06 | Type conversion (Path→str) | Automatic type adaptation | HIGH |
| API-U-07 | Null parameter handling | Graceful null handling | MEDIUM |
| API-U-08 | Backend registration | New backends register | LOW |

### 1.2 Integration Tests

| Test ID | Test Case | Test Data | Expected Result |
|---------|-----------|-----------|-----------------|
| API-I-01 | Gemini with all param variations | 10 different param combos | 100% success |
| API-I-02 | Vertex with GCS URIs | gs://bucket/video.mp4 | Correct routing |
| API-I-03 | Backend switching mid-process | Switch after 5 calls | Seamless transition |
| API-I-04 | Concurrent backend usage | 10 parallel requests | No conflicts |
| API-I-05 | Error recovery | Inject failures | Automatic retry |
| API-I-06 | Mock backend for testing | Test-specific params | Mock works |

### 1.3 Performance Tests

| Test ID | Metric | Target | Measurement |
|---------|--------|--------|-------------|
| API-P-01 | Parameter mapping overhead | <10ms | Time per mapping |
| API-P-02 | Method resolution time | <5ms | Time to resolve |
| API-P-03 | Backend switching time | <100ms | Switch latency |
| API-P-04 | Memory usage | <50MB | Peak memory |
| API-P-05 | Concurrent request handling | 100 RPS | Throughput |

## 2. Grok Integration Tests

### 2.1 Unit Tests

| Test ID | Test Case | Expected Result | Priority |
|---------|-----------|-----------------|----------|
| GROK-U-01 | Grok client initialization | API key validated | CRITICAL |
| GROK-U-02 | Request formatting | Valid JSON request | CRITICAL |
| GROK-U-03 | Response parsing | Correct extraction | CRITICAL |
| GROK-U-04 | Cost calculation | Accurate pricing | HIGH |
| GROK-U-05 | Error handling | Graceful failures | HIGH |
| GROK-U-06 | Timeout handling | Proper timeout | MEDIUM |

### 2.2 Fallback Logic Tests

| Test ID | Test Case | Trigger Condition | Expected Behavior |
|---------|-----------|-------------------|-------------------|
| GROK-F-01 | Safety block detection | finish_reason="SAFETY" | Fallback to Grok |
| GROK-F-02 | Numeric code detection | finish_reason=2 | Fallback to Grok |
| GROK-F-03 | Error message detection | "blocked for safety" | Fallback to Grok |
| GROK-F-04 | Pre-flight routing | "Pegasus" in title | Direct to Grok |
| GROK-F-05 | Sensitive keyword detection | "surveillance" keyword | Direct to Grok |
| GROK-F-06 | Quality threshold | <10 entities extracted | Try Grok |

### 2.3 Content Processing Tests

| Test ID | Video Content | Duration | Expected Result |
|---------|---------------|----------|-----------------|
| GROK-C-01 | Pegasus Part 1 | 53 min | 100% extraction |
| GROK-C-02 | Pegasus Part 2 | 41 min | 100% extraction |
| GROK-C-03 | Military documentary | 60 min | No censorship |
| GROK-C-04 | Intelligence briefing | 30 min | Complete analysis |
| GROK-C-05 | Cybersecurity analysis | 45 min | All entities |
| GROK-C-06 | Standard news | 10 min | Uses Gemini |

### 2.4 Cost Validation Tests

| Test ID | Content Size | Expected Cost | Tolerance |
|---------|--------------|---------------|-----------|
| GROK-$-01 | 10k tokens in | $0.05 | ±10% |
| GROK-$-02 | 50k tokens in | $0.25 | ±10% |
| GROK-$-03 | 100k tokens in | $0.50 | ±10% |
| GROK-$-04 | 5k tokens out | $0.075 | ±10% |
| GROK-$-05 | Monthly projection | <$50 | For 5% usage |

## 3. Multi-Pass Extraction Tests

### 3.1 Unit Tests

| Test ID | Test Case | Expected Result | Priority |
|---------|-----------|-----------------|----------|
| PASS-U-01 | Pass definition loading | All passes loaded | CRITICAL |
| PASS-U-02 | Schema validation | Valid JSON schemas | CRITICAL |
| PASS-U-03 | Dependency resolution | Correct ordering | CRITICAL |
| PASS-U-04 | Context building | Context preserved | HIGH |
| PASS-U-05 | Result merging | No data loss | CRITICAL |
| PASS-U-06 | Deduplication | Entities unique | HIGH |

### 3.2 Truncation Prevention Tests

| Test ID | Video Length | Transcript Size | Expected Result |
|---------|--------------|-----------------|-----------------|
| PASS-T-01 | 10 min | 5k chars | No truncation |
| PASS-T-02 | 30 min | 15k chars | No truncation |
| PASS-T-03 | 60 min | 30k chars | No truncation |
| PASS-T-04 | 94 min | 41k chars | No truncation |
| PASS-T-05 | 3 hours | 100k chars | No truncation |
| PASS-T-06 | 10 hours | 500k chars | No truncation |

### 3.3 Quality Comparison Tests

| Test ID | Metric | Single-Pass | Multi-Pass | Improvement |
|---------|--------|-------------|------------|-------------|
| PASS-Q-01 | Entities extracted | 30-40 | 50-60 | +50% |
| PASS-Q-02 | Relationships | 20-30 | 40-50 | +66% |
| PASS-Q-03 | Evidence coverage | 40% | 80% | +100% |
| PASS-Q-04 | JSON validity | 60% | 100% | +66% |
| PASS-Q-05 | Quality score | 0.65 | 0.90 | +38% |

### 3.4 Performance Tests

| Test ID | Metric | Target | Actual |
|---------|--------|--------|--------|
| PASS-P-01 | Passes executed | 3-5 | TBD |
| PASS-P-02 | Parallel speedup | >1.5x | TBD |
| PASS-P-03 | Total time (94 min) | <3 min | TBD |
| PASS-P-04 | API calls | <6 | TBD |
| PASS-P-05 | Token efficiency | >80% | TBD |

## 4. End-to-End Integration Tests

### 4.1 Complete Workflow Tests

| Test ID | Scenario | Components Used | Expected Result |
|---------|----------|-----------------|-----------------|
| E2E-01 | Standard news video | API Layer + Gemini | Normal processing |
| E2E-02 | Pegasus documentary | API + Grok + MultiPass | 100% extraction |
| E2E-03 | Mixed batch (10 videos) | All components | 100% success |
| E2E-04 | Rapid switching | All backends | No failures |
| E2E-05 | Error recovery | All with failures | Graceful recovery |

### 4.2 Stress Tests

| Test ID | Load | Duration | Success Criteria |
|---------|------|----------|------------------|
| STRESS-01 | 100 concurrent | 1 hour | 99% success |
| STRESS-02 | 1000 videos | 24 hours | No memory leaks |
| STRESS-03 | Backend failures | 1 hour | Auto-recovery |
| STRESS-04 | Rate limiting | 1 hour | Proper queuing |

## 5. Test Data Requirements

### 5.1 Video Test Set

| Category | Videos | Source | Purpose |
|----------|--------|--------|---------|
| Sensitive Content | 10 | MASTER_TEST_VIDEO_TABLE | Grok fallback |
| Long Form | 5 | Documentaries | Multi-pass |
| Short Form | 20 | News clips | Performance |
| Technical | 5 | Tutorials | Specialized |
| Mixed | 10 | Various | Integration |

### 5.2 Mock Data

| Type | Count | Purpose |
|------|-------|---------|
| Transcripts | 50 | Unit tests |
| API Responses | 100 | Integration |
| Error Responses | 20 | Error handling |
| Edge Cases | 30 | Boundary testing |

## 6. Test Automation

### 6.1 Continuous Integration

```yaml
# .github/workflows/critical-tests.yml
name: Critical Issue Tests
on: [push, pull_request]

jobs:
  api-abstraction:
    runs-on: ubuntu-latest
    steps:
      - name: Unit Tests
        run: pytest tests/unit/test_api_abstraction.py -v
      - name: Integration Tests
        run: pytest tests/integration/test_unified_api.py -v
  
  grok-integration:
    runs-on: ubuntu-latest
    steps:
      - name: Fallback Logic
        run: pytest tests/unit/test_grok_fallback.py -v
      - name: Content Tests
        run: pytest tests/integration/test_sensitive_content.py -v
  
  multipass-extraction:
    runs-on: ubuntu-latest
    steps:
      - name: Truncation Tests
        run: pytest tests/unit/test_no_truncation.py -v
      - name: Quality Tests
        run: pytest tests/integration/test_extraction_quality.py -v
```

### 6.2 Test Commands

```bash
# Run all critical tests
poetry run pytest tests/critical/ -v --tb=short

# Run specific solution tests
poetry run pytest tests/critical/api_abstraction/ -v
poetry run pytest tests/critical/grok_integration/ -v
poetry run pytest tests/critical/multipass_extraction/ -v

# Run performance benchmarks
poetry run pytest tests/performance/ --benchmark-only

# Run with real videos (expensive)
poetry run pytest tests/e2e/ -m "real_videos" --expensive
```

## 7. Success Criteria

### Overall Success Metrics
- **All Tests Pass**: 100% of critical tests
- **Performance Targets Met**: All within bounds
- **No Regressions**: Existing tests still pass
- **Documentation Complete**: All features documented

### Solution-Specific Criteria

#### API Abstraction Layer
- ✅ Zero method mismatch errors
- ✅ All backends working
- ✅ <10ms overhead

#### Grok Integration  
- ✅ Pegasus processes successfully
- ✅ 100% sensitive content handling
- ✅ <$0.30 per sensitive video

#### Multi-Pass Extraction
- ✅ Zero truncation
- ✅ 100% JSON validity
- ✅ >40% quality improvement

## 8. Test Execution Timeline

| Week | Phase | Focus |
|------|-------|-------|
| Week 1 | Unit Tests | Component validation |
| Week 2 | Integration | System validation |
| Week 3 | E2E & Performance | Full validation |
| Week 4 | Production | Live monitoring |

## 9. Risk Mitigation

| Risk | Test Coverage | Mitigation |
|------|---------------|------------|
| API Breaking | API-I-01 to 06 | Version detection |
| Grok Unavailable | GROK-U-05, F-06 | Fallback to queue |
| Truncation Returns | PASS-T-01 to 06 | Continuous monitoring |
| Performance Degradation | All P- tests | Alerting thresholds |

## 10. Approval

| Role | Name | Date |
|------|------|------|
| QA Lead | - | Sept 2, 2025 |
| Engineering Lead | - | Sept 2, 2025 |
| Product Manager | - | Sept 2, 2025 |

---
**Status**: READY FOR EXECUTION
**Priority**: CRITICAL - Block resolution for production deployment
