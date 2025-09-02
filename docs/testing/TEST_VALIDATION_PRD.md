# ClipScribe Test Validation PRD (Product Requirements Document)

*Version: 1.0*  
*Date: September 1, 2025*  
*Status: Draft*

## Executive Summary

This PRD defines the comprehensive testing and validation framework for ClipScribe's video intelligence extraction capabilities. It establishes metrics, methodologies, and success criteria for evaluating output quality, performance, and cost-effectiveness.

## 1. Testing Objectives

### Primary Goals
1. **Quality Validation**: Ensure extraction accuracy meets intelligence analyst standards
2. **Performance Benchmarking**: Establish baseline metrics for speed, cost, and scalability
3. **Model Comparison**: Quantify differences between Gemini 2.5 Flash vs Pro
4. **Cost Optimization**: Validate actual costs align with business model
5. **Edge Case Handling**: Identify and document system limitations

### Success Criteria
- Entity extraction precision >85%
- Relationship accuracy >75%
- Processing cost <$0.02/minute (Pro) or <$0.004/minute (Flash)
- Zero false security/privacy violations
- 95% successful job completion rate

## 2. Quality Metrics Framework

### 2.1 Entity Extraction Metrics

#### Quantitative Metrics
```python
# Core Metrics
precision = true_positives / (true_positives + false_positives)
recall = true_positives / (true_positives + false_negatives)
f1_score = 2 * (precision * recall) / (precision + recall)

# Additional Metrics
entity_density = entities_extracted / video_duration_minutes
type_accuracy = correctly_typed_entities / total_entities
confidence_calibration = actual_accuracy_at_confidence / predicted_confidence
```

#### Qualitative Assessment
- **Relevance Score**: Are extracted entities meaningful to the content?
- **Granularity Level**: Are entities too generic or too specific?
- **Temporal Accuracy**: Are entities correctly associated with timestamps?
- **Context Preservation**: Do entities maintain their contextual meaning?

### 2.2 Relationship Extraction Metrics

#### Graph Quality Metrics
- **Edge Density**: relationships / (entities * (entities - 1) / 2)
- **Connected Components**: Number of isolated subgraphs
- **Clustering Coefficient**: Measure of graph interconnectedness
- **Path Length**: Average shortest path between entities

#### Relationship Accuracy
- **Directionality Correctness**: Proper subject-object relationships
- **Relationship Type Accuracy**: Correct classification of relationship types
- **Temporal Relationships**: Before/after/during accuracy
- **Causal Chain Validity**: Logical consistency of cause-effect chains

### 2.3 Transcript Quality Metrics

#### Accuracy Metrics
- **Word Error Rate (WER)**: Standard ASR metric
- **Speaker Diarization Accuracy**: Multi-speaker identification
- **Punctuation Accuracy**: Sentence boundary detection
- **Technical Term Recognition**: Domain-specific vocabulary

#### Intelligence Value Metrics
- **Quote Precision**: Exact quotes with timestamps
- **Context Windows**: Sufficient context for understanding
- **Contradiction Detection**: Identifying conflicting statements
- **Narrative Flow**: Logical progression tracking

## 3. Performance Metrics

### 3.1 Processing Performance
```yaml
metrics:
  latency:
    - download_time_seconds
    - transcription_time_seconds
    - extraction_time_seconds
    - total_processing_time
  
  throughput:
    - videos_per_hour
    - concurrent_job_capacity
    - queue_processing_rate
  
  reliability:
    - success_rate_percentage
    - retry_count_average
    - timeout_rate
    - error_recovery_time
```

### 3.2 Cost Metrics
```yaml
cost_breakdown:
  per_video:
    - api_costs (Gemini API calls)
    - storage_costs (GCS)
    - compute_costs (Cloud Run/GCE)
    - network_costs (egress)
  
  per_minute:
    - flash_model_cost
    - pro_model_cost
    - infrastructure_overhead
  
  efficiency:
    - cost_per_entity_extracted
    - cost_per_relationship_mapped
    - cost_per_insight_generated
```

### 3.3 Scalability Metrics
- **Concurrent Processing**: Max parallel jobs without degradation
- **Memory Efficiency**: RAM usage per video minute
- **Storage Efficiency**: Output size vs input size ratio
- **API Rate Limit Utilization**: Percentage of available quota used

## 4. Test Scenarios

### 4.1 Content Type Matrix

| Content Type | Test Videos | Key Metrics | Success Criteria |
|-------------|------------|-------------|------------------|
| News/Current Events | PBS NewsHour, CNN, Fox | Entity diversity, bias detection | >100 entities/episode |
| Technical/Educational | Tutorials, lectures | Concept extraction, accuracy | >90% term accuracy |
| Interviews/Podcasts | Long-form conversations | Speaker tracking, quote accuracy | >95% speaker ID |
| Government/Official | Press briefings, hearings | Policy entities, relationships | Complete speaker roster |
| Series/Multi-part | Stoic Viking, documentaries | Cross-video resolution | >80% entity matching |

### 4.2 Duration Categories

| Duration | Video Count | Model | Expected Cost | Key Focus |
|----------|------------|-------|---------------|-----------|
| <5 min | 20 | Both | Flash: $0.02, Pro: $0.10 | Speed, basic extraction |
| 5-15 min | 15 | Both | Flash: $0.05, Pro: $0.25 | Balance, full pipeline |
| 15-30 min | 10 | Both | Flash: $0.10, Pro: $0.50 | Memory, completeness |
| 30-60 min | 5 | Both | Flash: $0.20, Pro: $1.00 | Scalability, cost |
| >60 min | 3 | Pro only | Pro: $2.00+ | Infrastructure limits |

### 4.3 Edge Cases

1. **Minimal Content**
   - Silent videos
   - Music-only content
   - Static images
   - Expected: Minimal extraction, low cost

2. **Complex Content**
   - Multiple languages
   - Technical jargon
   - Rapid speaker changes
   - Visual-only information

3. **Problem Content**
   - Corrupted audio
   - Low quality video
   - Background noise
   - Non-standard formats

## 5. Validation Methodology

### 5.1 Ground Truth Creation

#### Manual Annotation Process
1. Select 10 representative videos
2. Human analysts create gold standard:
   - Complete entity list
   - Verified relationships
   - Key quotes with timestamps
3. Inter-annotator agreement >80%
4. Use as benchmark for automated testing

#### Automated Validation
```python
def validate_extraction(extracted, ground_truth):
    return {
        'precision': calculate_precision(extracted, ground_truth),
        'recall': calculate_recall(extracted, ground_truth),
        'f1': calculate_f1(extracted, ground_truth),
        'missing_critical': find_missing_critical_entities(extracted, ground_truth),
        'false_positives': identify_false_positives(extracted, ground_truth)
    }
```

### 5.2 A/B Testing Framework

#### Flash vs Pro Comparison
```python
test_suite = {
    'video_id': 'stoic_viking_001',
    'flash_result': process_with_flash(video),
    'pro_result': process_with_pro(video),
    'metrics': {
        'entity_delta': len(pro.entities) - len(flash.entities),
        'relationship_delta': len(pro.relationships) - len(flash.relationships),
        'cost_ratio': pro.cost / flash.cost,
        'quality_ratio': pro.f1_score / flash.f1_score,
        'value_score': (pro.quality / flash.quality) / (pro.cost / flash.cost)
    }
}
```

### 5.3 Cross-Source Validation

#### Multi-Source Entity Resolution
1. Process same event from 3+ sources
2. Measure:
   - Entity overlap percentage
   - Contradiction detection rate
   - Narrative consistency
   - Bias indicators

## 6. Testing Pipeline

### 6.1 Automated Test Suite
```yaml
daily_tests:
  - smoke_test: 1 short video, basic validation
  - regression_test: 5 videos, compare to baseline
  - performance_test: Measure latency and throughput

weekly_tests:
  - comprehensive_suite: All test categories
  - edge_case_validation: Problem content
  - cost_analysis: Detailed cost breakdown

release_tests:
  - full_validation: Complete test matrix
  - load_testing: Concurrent processing limits
  - security_scan: Data privacy validation
```

### 6.2 Continuous Monitoring
```python
class QualityMonitor:
    def track_metrics(self, job_result):
        metrics = {
            'entity_count': len(job_result.entities),
            'relationship_count': len(job_result.relationships),
            'processing_time': job_result.duration,
            'cost': job_result.cost,
            'confidence_avg': mean([e.confidence for e in job_result.entities])
        }
        
        # Alert on anomalies
        if metrics['entity_count'] < 10 and job_result.duration > 300:
            alert("Low extraction for long video")
        
        return metrics
```

## 7. Success Criteria

### 7.1 Minimum Viable Quality (MVQ)
- **Entity Extraction**: >50 entities for 10-min video (information-dense)
- **Relationship Mapping**: >30 relationships for 10-min video
- **Transcript Accuracy**: >95% for clear speech
- **Processing Success**: >95% completion rate
- **Cost Efficiency**: <$0.02/minute for Pro model

### 7.2 Production Ready Criteria
- **Quality**: F1 score >0.80 on test set
- **Performance**: <5 minutes processing for 30-min video
- **Reliability**: 99% uptime, <1% error rate
- **Cost**: Predictable and within budget
- **Scale**: Handle 100 concurrent videos

### 7.3 Competitive Benchmarks
| Metric | ClipScribe Target | Human Analyst | Competitor |
|--------|------------------|---------------|------------|
| Cost/hour | <$1.20 | $50-100 | $5-10 |
| Processing Time | <10% of duration | 3-5x duration | 50% of duration |
| Entity Recall | >80% | 95% | 60-70% |
| Scalability | Unlimited | Limited | Moderate |

## 8. Testing Artifacts

### 8.1 Required Outputs
1. **Test Results Database**: All test runs with metrics
2. **Quality Dashboard**: Real-time quality metrics
3. **Cost Analysis Report**: Detailed cost breakdown
4. **Model Comparison Matrix**: Flash vs Pro analysis
5. **Edge Case Documentation**: Known limitations

### 8.2 Test Data Management
```yaml
test_data:
  storage:
    location: gs://clipscribe-test-data/
    structure:
      - /videos/          # Cached test videos
      - /ground_truth/    # Manual annotations
      - /results/         # Test outputs
      - /metrics/         # Calculated metrics
  
  retention:
    videos: 30 days
    results: 90 days
    metrics: indefinite
```

## 9. Risk Mitigation

### 9.1 Quality Risks
- **Risk**: Poor extraction on new content types
- **Mitigation**: Continuous test suite expansion
- **Monitoring**: Track extraction rates by category

### 9.2 Cost Risks
- **Risk**: Costs exceed projections
- **Mitigation**: Implement hard cost limits
- **Monitoring**: Real-time cost tracking

### 9.3 Performance Risks
- **Risk**: Timeout on long videos
- **Mitigation**: Cloud Run Jobs architecture
- **Monitoring**: Track timeout rates

## 10. Implementation Timeline

### Phase 1: Infrastructure (Week 1)
- Day 1-2: Cloud Run Jobs implementation
- Day 3: Caching layer
- Day 4: Model selection parameter
- Day 5: Basic metrics collection

### Phase 2: Baseline Testing (Week 2)
- Day 6-7: Process test suite with Flash
- Day 8-9: Process test suite with Pro
- Day 10: Initial comparison analysis

### Phase 3: Optimization (Week 3)
- Based on Week 2 findings
- Implement improvements
- Re-test and validate

### Phase 4: Production Validation (Week 4)
- Full test suite execution
- Documentation
- Go/No-Go decision

---

## Appendix A: Test Video Selection Criteria

Videos should be selected to represent:
1. **Diverse content types**: News, education, interviews
2. **Various durations**: 1 min to 2+ hours
3. **Different quality levels**: HD, SD, low quality
4. **Multiple speakers**: Single, dialogue, panel
5. **Technical complexity**: Simple to highly technical
6. **Information density**: Sparse to extremely dense

## Appendix B: Metric Calculation Formulas

```python
# Entity Metrics
def calculate_entity_precision(extracted, ground_truth):
    true_positives = len(set(extracted) & set(ground_truth))
    false_positives = len(set(extracted) - set(ground_truth))
    return true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0

# Relationship Metrics
def calculate_relationship_accuracy(extracted_rels, ground_truth_rels):
    correct = sum(1 for r in extracted_rels if r in ground_truth_rels)
    return correct / len(extracted_rels) if extracted_rels else 0

# Cost Metrics
def calculate_value_score(quality_score, cost):
    # Higher is better: quality per dollar
    return quality_score / cost if cost > 0 else 0
```

---

*This document should be updated as testing reveals new insights and requirements.*
