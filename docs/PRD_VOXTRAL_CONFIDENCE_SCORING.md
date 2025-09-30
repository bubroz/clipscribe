# PRD: Confidence Scoring System for Transcription Quality

**Version:** 1.0  
**Date:** September 6, 2025  
**Status:** Planning

## Executive Summary

Implement a comprehensive confidence scoring system to measure and track transcription quality, enabling quality assurance, error detection, and selective review of low-confidence segments.

## Problem Statement

Currently, we have no visibility into transcription quality:
- Can't identify potentially incorrect transcriptions
- No way to flag segments for human review
- Unable to provide quality guarantees
- No metrics for comparing model performance

## Solution Overview

Extract and aggregate confidence scores from Voxtral API to provide quality metrics at word, segment, and document levels.

## Technical Specification

### Confidence Hierarchy
```python
class ConfidenceMetrics:
    # Word Level
    word_confidences: List[float]  # Individual word scores
    
    # Segment Level  
    segment_confidences: List[float]  # Average per segment
    
    # Document Level
    overall_confidence: float  # Weighted average
    low_confidence_ratio: float  # % below threshold
    confidence_distribution: Dict[str, int]  # Histogram
```

### Quality Thresholds
```python
CONFIDENCE_THRESHOLDS = {
    "high": 0.90,      # Professional quality
    "medium": 0.75,    # Acceptable quality
    "low": 0.60,       # Needs review
    "critical": 0.50   # Likely errors
}
```

### Scoring Algorithm
```python
def calculate_quality_score(words: List[Dict]) -> QualityMetrics:
    """Calculate comprehensive quality metrics."""
    
    # Extract confidence scores
    confidences = [w.get('confidence', 0.0) for w in words]
    
    # Calculate metrics
    metrics = QualityMetrics(
        mean_confidence=np.mean(confidences),
        median_confidence=np.median(confidences),
        min_confidence=np.min(confidences),
        std_deviation=np.std(confidences),
        
        # Quality indicators
        high_quality_ratio=sum(c >= 0.90 for c in confidences) / len(confidences),
        needs_review_ratio=sum(c < 0.75 for c in confidences) / len(confidences),
        
        # Problem areas
        low_confidence_segments=find_problem_segments(words),
        quality_grade=assign_grade(np.mean(confidences))
    )
    
    return metrics
```

### Quality Grades
```python
def assign_grade(confidence: float) -> str:
    """Assign letter grade based on confidence."""
    if confidence >= 0.95: return "A+"  # Exceptional
    if confidence >= 0.90: return "A"   # Professional
    if confidence >= 0.85: return "B"   # Good
    if confidence >= 0.75: return "C"   # Acceptable
    if confidence >= 0.65: return "D"   # Poor
    return "F"  # Unacceptable
```

## User Interface

### Quality Report
```markdown
## Transcription Quality Report

**Overall Grade: B+ (87.3%)**

### Quality Metrics
- High Confidence Words: 78.2%
- Medium Confidence: 15.3%
- Low Confidence: 6.5%

### Problem Areas (Review Recommended)
- [2:15-2:18] "technical jargon here" (45% confidence)
- [5:42-5:45] "unclear audio segment" (52% confidence)

### Quality Distribution
```
90-100%: ████████████████ 78.2%
75-89%:  ████ 15.3%
60-74%:  ██ 4.8%
<60%:    █ 1.7%
```
```

## Implementation Plan

### Phase 1: Data Collection
- Extract confidence from API response
- Store confidence with each word
- Calculate segment averages

### Phase 2: Metrics Calculation
- Implement scoring algorithms
- Generate quality reports
- Add to output files

### Phase 3: Quality Assurance
- Flag low-confidence segments
- Generate review queues
- Track quality over time

## Success Metrics

- **Coverage:** 100% of transcripts have quality scores
- **Accuracy:** Confidence correlates with actual errors
- **Actionable:** Clear identification of problem areas
- **Performance:** < 100ms to calculate metrics

## Use Cases

1. **Automatic QA:** Flag videos needing human review
2. **Model Comparison:** Compare Voxtral models objectively
3. **Customer Transparency:** Show quality grades in output
4. **Selective Review:** Focus human effort on problem areas
5. **Quality Guarantees:** Only deliver high-confidence transcripts

## Future Enhancements

1. **ML-Based Correction:** Use patterns to auto-correct low-confidence words
2. **Context Enhancement:** Use surrounding high-confidence words to improve accuracy
3. **Quality Prediction:** Estimate quality before processing based on audio analysis
4. **Differential Confidence:** Compare multiple models to find consensus

## Acceptance Criteria

- [ ] Confidence scores extracted for all words
- [ ] Quality metrics calculated for each transcript
- [ ] Quality report included in output
- [ ] Low-confidence segments flagged
- [ ] Performance impact < 1%
