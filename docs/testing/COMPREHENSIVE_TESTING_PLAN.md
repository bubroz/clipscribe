# ARGOS/ClipScribe Comprehensive Testing Plan

*Created: 2025-06-28*  
*Status: CRITICAL - Multiple production-blocking bugs identified*

## Executive Summary

ARGOS/ClipScribe has reached a critical juncture where multiple "complete" features have fundamental bugs preventing basic functionality. This document outlines a systematic approach to testing, fixing, and validating all features before any new development.

## Critical Issues Requiring Immediate Fix

### 1. Timeline Intelligence - Date Extraction Logic
**Severity**: CRITICAL  
**Impact**: Feature completely broken for intended purpose

**Current Bug**:
```python
# WRONG - adds video seconds as days
event_timestamp = video.metadata.published_at + timedelta(seconds=key_point.timestamp)
```

**Required Fix**:
```python
# Option 1: Use video timestamp properly
event_timestamp = video.metadata.published_at  # Don't add seconds as days

# Option 2: Only show events with extracted dates
if extracted_date_obj:
    event_timestamp = extracted_date_obj.parsed_date
else:
    continue  # Skip events without real dates
```

### 2. Information Flow Maps - Model Attribute Errors
**Severity**: CRITICAL  
**Impact**: Page crashes immediately on load

**Required Fixes**:
- Line 51: Replace `flow_map.flow_pattern_analysis` with direct attributes
- Use `flow_map.learning_progression` instead of `flow_map.flow_pattern_analysis.learning_progression`
- Use `flow_map.strategic_insights` instead of `flow_map.flow_pattern_analysis.strategic_insights`
- Audit entire file for model mismatches

### 3. Model-UI Synchronization
**Severity**: HIGH  
**Impact**: Multiple UI features broken

**Required Actions**:
- Generate model documentation from Pydantic models
- Update all UI code to match actual model attributes
- Add runtime validation of model structures

## Testing Phases

### Phase 1: Core Functionality Testing (Backend)

#### 1.1 Single Video Processing
- [ ] Process PBS NewsHour video successfully
- [ ] Verify transcript extraction accuracy
- [ ] Check entity extraction (SpaCy + GLiNER)
- [ ] Validate relationship extraction (REBEL)
- [ ] Confirm knowledge graph generation
- [ ] Test all output formats (JSON, TXT, CSV, etc.)

#### 1.2 Multi-Video Collection Processing
- [ ] Process 2-part PBS series
- [ ] Verify cross-video entity resolution
- [ ] Check unified knowledge graph generation
- [ ] Validate collection summary generation
- [ ] Test series detection functionality

#### 1.3 Enhanced Features
- [ ] Video retention system (delete/keep_processed/keep_all)
- [ ] Cost tracking accuracy
- [ ] Performance metrics collection
- [ ] Error handling and recovery

### Phase 2: UI Testing (Mission Control)

#### 2.1 Page Load Testing
- [ ] Main Dashboard - loads without errors
- [ ] Collections - displays data correctly
- [ ] Information Flow Maps - CURRENTLY BROKEN
- [ ] Timeline Intelligence - shows proper dates (CURRENTLY BROKEN)
- [ ] Analytics - all metrics display

#### 2.2 Interactive Feature Testing
- [ ] Search and filtering on all pages
- [ ] Data export functionality
- [ ] Visualization rendering
- [ ] Real-time processing monitor
- [ ] Settings persistence

#### 2.3 Data Flow Testing
- [ ] Process video through CLI
- [ ] Verify data appears in UI
- [ ] Test all data transformations
- [ ] Validate export formats

### Phase 3: Timeline Feature Evaluation

#### 3.1 Applicability Assessment
- [ ] Determine which video types benefit from timeline extraction
- [ ] Document when timeline feature should be used
- [ ] Consider making timeline optional based on content type

#### 3.2 Date Extraction Testing
- [ ] Test with historical documentaries (dates in content)
- [ ] Test with news videos (current events)
- [ ] Test with tutorials (no historical dates)
- [ ] Validate LLM date extraction accuracy

#### 3.3 Timeline Export Testing
- [ ] JSON export with proper dates
- [ ] Timeline.js format validation
- [ ] CSV export functionality
- [ ] ICS calendar format

### Phase 4: Information Flow Testing

#### 4.1 Concept Extraction
- [ ] Verify concept identification accuracy
- [ ] Test maturity level assignment
- [ ] Validate concept clustering
- [ ] Check dependency detection

#### 4.2 Evolution Tracking
- [ ] Test concept evolution across videos
- [ ] Verify progression tracking
- [ ] Validate flow visualizations
- [ ] Check strategic insights generation

### Phase 5: Integration Testing

#### 5.1 End-to-End Workflows
- [ ] Single video: URL → Process → View in UI → Export
- [ ] Collection: Multiple URLs → Process → Unified Analysis → Export
- [ ] Series: Auto-detection → Confirmation → Analysis → Timeline

#### 5.2 Error Scenarios
- [ ] Invalid video URLs
- [ ] Private/deleted videos
- [ ] API quota exceeded
- [ ] Network failures
- [ ] Corrupt data handling

## Test Data Sets

### Required Test Videos
1. **PBS NewsHour Pegasus Series** (2 parts) - Historical dates, entities, relationships
2. **Technical Tutorial** - Concepts, no historical dates
3. **News Compilation** - Multiple dates and events
4. **Short Clip** (<5 min) - Performance baseline
5. **Long Documentary** (>1 hour) - Stress testing

### Expected Outcomes
- Document expected results for each test video
- Create golden data sets for regression testing
- Establish performance benchmarks

## Testing Tools & Procedures

### Manual Testing Checklist
```bash
# 1. Clean environment
rm -rf output/
poetry run pytest tests/  # Ensure base tests pass

# 2. Process test video
poetry run clipscribe transcribe "https://www.youtube.com/watch?v=6ZVj1_SE4Mo" \
  --use-advanced-extraction \
  --llm-validate

# 3. Launch UI
poetry run streamlit run streamlit_app/ClipScribe_Mission_Control.py

# 4. Verify each page loads and displays data correctly
```

### Automated Testing (Future)
- UI testing with Playwright/Selenium
- API testing with pytest
- Performance benchmarking
- Regression test suite

## Success Criteria

### Minimum Viable Product (MVP)
1. All UI pages load without errors
2. Core video processing works reliably
3. Timeline shows meaningful dates (or feature is disabled)
4. Information flows display correctly
5. No data loss or corruption

### Production Ready
1. All features work as documented
2. Comprehensive error handling
3. Performance meets benchmarks
4. User documentation complete
5. 90%+ test coverage

## Timeline & Priorities

### Week 1: Critical Bug Fixes
- Day 1-2: Fix timeline date logic
- Day 3-4: Fix Information Flow Maps UI
- Day 5-7: Basic integration testing

### Week 2: Comprehensive Testing
- Complete all testing phases
- Document findings
- Create user guides

### Week 3: Stabilization
- Fix remaining bugs
- Performance optimization
- Prepare for release

## Recommendations

1. **Immediate Actions**:
   - Fix the two critical bugs blocking basic functionality
   - Run through Phase 1 & 2 testing manually
   - Document all issues found

2. **Process Improvements**:
   - Require manual testing before marking features "complete"
   - Add integration tests for UI-model interactions
   - Create staging environment for pre-release testing

3. **Feature Considerations**:
   - Make timeline feature optional/configurable
   - Add content type detection to enable relevant features
   - Improve error messages and user guidance

## Conclusion

ARGOS/ClipScribe has significant potential but requires immediate stabilization. The timeline and information flow features need fundamental fixes before they can provide value. A systematic testing approach will ensure all features work reliably before adding new functionality.

**Current Status**: NOT PRODUCTION READY - Critical bugs in core features
**Target Status**: Stable, tested, and documented for v2.19.0 release 