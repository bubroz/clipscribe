# ClipScribe Model Comparison PRD

*Version: 1.0*  
*Date: September 1, 2025*  
*Status: Draft*

## Executive Summary

This PRD defines the systematic comparison framework for evaluating Gemini 2.5 Flash versus Gemini 2.5 Pro models in ClipScribe's video intelligence extraction pipeline. The goal is to determine the optimal model selection strategy balancing quality, cost, and performance.

## 1. Comparison Objectives

### Key Questions to Answer
1. **Quality Delta**: How much better is Pro vs Flash for entity/relationship extraction?
2. **Cost Justification**: Is the 5-6x cost increase justified by quality improvements?
3. **Use Case Optimization**: Which model for which content types?
4. **Hybrid Potential**: Can we use Flash for some tasks, Pro for others?
5. **Customer Segmentation**: Different models for different pricing tiers?

## 2. Model Specifications

### 2.1 Gemini 2.5 Flash
```yaml
model: gemini-2.5-flash
pricing:
  audio: $0.002/minute
  video: $0.0035/minute (with visual analysis)
  
characteristics:
  - Speed: Very fast inference
  - Context: 1M tokens
  - Strengths: Basic extraction, transcription, simple relationships
  - Weaknesses: Complex reasoning, nuanced relationships
  
use_cases:
  - High-volume processing
  - Cost-sensitive applications
  - Basic intelligence extraction
  - Real-time requirements
```

### 2.2 Gemini 2.5 Pro
```yaml
model: gemini-2.5-pro
pricing:
  audio: $0.01/minute (5x Flash)
  video: $0.02/minute (5.7x Flash)
  
characteristics:
  - Speed: Slower but more thorough
  - Context: 2M tokens
  - Strengths: Deep analysis, complex relationships, reasoning
  - Weaknesses: Cost, processing time
  
use_cases:
  - High-value content
  - Complex analysis requirements
  - Premium tier customers
  - Critical intelligence extraction
```

## 3. Comparison Methodology

### 3.1 Test Matrix

| Content Category | Videos | Flash Runs | Pro Runs | Metrics Focus |
|-----------------|---------|------------|----------|---------------|
| News/Current Events | 10 | 10 | 10 | Entity completeness |
| Technical Content | 10 | 10 | 10 | Technical accuracy |
| Interviews | 10 | 10 | 10 | Speaker attribution |
| Government/Policy | 10 | 10 | 10 | Relationship depth |
| Educational | 10 | 10 | 10 | Concept extraction |

### 3.2 Side-by-Side Processing
```python
def compare_models(video_url: str) -> dict:
    # Cache video to ensure identical input
    video_path = cache_manager.get_or_download(video_url)
    
    # Process with Flash
    flash_start = time.time()
    flash_result = process_with_flash(video_path)
    flash_time = time.time() - flash_start
    
    # Process with Pro
    pro_start = time.time()
    pro_result = process_with_pro(video_path)
    pro_time = time.time() - pro_start
    
    return {
        'video_url': video_url,
        'flash': {
            'entities': len(flash_result.entities),
            'relationships': len(flash_result.relationships),
            'time': flash_time,
            'cost': flash_result.cost,
            'confidence_avg': mean([e.confidence for e in flash_result.entities])
        },
        'pro': {
            'entities': len(pro_result.entities),
            'relationships': len(pro_result.relationships),
            'time': pro_time,
            'cost': pro_result.cost,
            'confidence_avg': mean([e.confidence for e in pro_result.entities])
        },
        'delta': {
            'entity_increase': (len(pro_result.entities) - len(flash_result.entities)) / len(flash_result.entities),
            'relationship_increase': (len(pro_result.relationships) - len(flash_result.relationships)) / len(flash_result.relationships),
            'time_increase': pro_time / flash_time,
            'cost_increase': pro_result.cost / flash_result.cost,
            'value_ratio': calculate_value_ratio(flash_result, pro_result)
        }
    }
```

## 4. Quality Comparison Metrics

### 4.1 Quantitative Metrics

#### Entity Extraction Comparison
```python
metrics = {
    'entity_count_delta': pro.entity_count - flash.entity_count,
    'entity_type_diversity': len(set(pro.entity_types)) - len(set(flash.entity_types)),
    'entity_overlap': len(set(pro.entities) & set(flash.entities)) / len(set(pro.entities) | set(flash.entities)),
    'unique_to_pro': set(pro.entities) - set(flash.entities),
    'unique_to_flash': set(flash.entities) - set(pro.entities)
}
```

#### Relationship Extraction Comparison
```python
metrics = {
    'relationship_count_delta': pro.rel_count - flash.rel_count,
    'relationship_depth': pro.avg_chain_length - flash.avg_chain_length,
    'causal_relationships': pro.causal_count - flash.causal_count,
    'temporal_relationships': pro.temporal_count - flash.temporal_count,
    'relationship_accuracy': validate_relationships(pro) - validate_relationships(flash)
}
```

### 4.2 Qualitative Metrics

#### Intelligence Value Assessment
| Criterion | Weight | Flash Score | Pro Score | Notes |
|-----------|--------|-------------|-----------|-------|
| Entity Relevance | 25% | TBD | TBD | Are entities meaningful? |
| Relationship Accuracy | 25% | TBD | TBD | Are relationships correct? |
| Context Preservation | 20% | TBD | TBD | Is context maintained? |
| Insight Generation | 20% | TBD | TBD | New insights discovered? |
| Completeness | 10% | TBD | TBD | Coverage of content |

## 5. Cost-Benefit Analysis

### 5.1 Value Calculation Framework
```python
def calculate_value_score(flash_result, pro_result):
    # Quality improvement
    quality_multiplier = pro_result.f1_score / flash_result.f1_score
    
    # Cost increase
    cost_multiplier = pro_result.cost / flash_result.cost
    
    # Value ratio (>1 means Pro provides better value)
    value_ratio = quality_multiplier / cost_multiplier
    
    # Adjusted for use case importance
    if content_type == 'critical_intelligence':
        value_ratio *= 1.5  # Quality matters more
    elif content_type == 'bulk_processing':
        value_ratio *= 0.7  # Cost matters more
    
    return value_ratio
```

### 5.2 Break-Even Analysis
```yaml
scenarios:
  scenario_1:
    name: "Pro Always"
    monthly_cost: $500
    quality_score: 95%
    customer_satisfaction: High
    
  scenario_2:
    name: "Flash Always"
    monthly_cost: $100
    quality_score: 75%
    customer_satisfaction: Medium
    
  scenario_3:
    name: "Hybrid (Flash default, Pro on demand)"
    monthly_cost: $200
    quality_score: 85%
    customer_satisfaction: High
    
  scenario_4:
    name: "Tiered (Flash for basic, Pro for premium)"
    monthly_cost: Variable
    quality_score: Variable
    customer_satisfaction: High
```

## 6. Hybrid Model Strategy

### 6.1 Task-Based Selection
```python
def select_model(video_metadata, user_tier, task_type):
    # Always use Pro for:
    if task_type in ['legal_analysis', 'intelligence_briefing', 'medical_content']:
        return 'pro'
    
    # Always use Flash for:
    if task_type in ['basic_transcription', 'content_summary', 'quick_preview']:
        return 'flash'
    
    # Hybrid approach for extraction:
    if task_type == 'entity_extraction':
        # Use Flash for initial extraction
        flash_result = extract_with_flash(video)
        
        # Use Pro only if Flash finds interesting content
        if flash_result.entity_count > 50 or flash_result.complexity_score > 0.7:
            return 'pro'  # Reprocess with Pro
        else:
            return 'flash'  # Keep Flash results
```

### 6.2 Progressive Enhancement
```yaml
pipeline:
  step_1:
    model: flash
    task: transcription
    output: transcript.json
    
  step_2:
    model: flash
    task: basic_entity_extraction
    output: entities_basic.json
    
  step_3:
    condition: if entities_basic.count > threshold
    model: pro
    task: deep_relationship_extraction
    input: transcript.json + entities_basic.json
    output: relationships_deep.json
    
  step_4:
    condition: if user_tier == 'premium'
    model: pro
    task: insight_generation
    output: insights.json
```

## 7. Test Scenarios

### 7.1 Stoic Viking Channel Test
**Objective**: Process 10 videos from The Stoic Viking channel with both models

```python
test_suite = {
    'channel': '@TheStoicViking',
    'videos': [/* 10 video URLs */],
    'metrics': {
        'total_entities_flash': 0,
        'total_entities_pro': 0,
        'total_cost_flash': 0,
        'total_cost_pro': 0,
        'series_detection_flash': 0,
        'series_detection_pro': 0,
        'cross_video_resolution_flash': 0,
        'cross_video_resolution_pro': 0
    }
}
```

### 7.2 News Coverage Comparison
**Objective**: Same event from multiple sources, both models

```python
event = "Major Policy Announcement"
sources = ['PBS', 'CNN', 'Fox', 'WhiteHouse']

for source in sources:
    flash_result = process_with_flash(source)
    pro_result = process_with_pro(source)
    
    compare_results[source] = {
        'entity_overlap': calculate_overlap(flash_result, pro_result),
        'contradiction_detection': {
            'flash': flash_result.contradictions,
            'pro': pro_result.contradictions
        },
        'bias_indicators': {
            'flash': flash_result.bias_score,
            'pro': pro_result.bias_score
        }
    }
```

## 8. Decision Framework

### 8.1 Model Selection Decision Tree
```
START
  │
  ├─ Is content >30 minutes?
  │   ├─ YES → Consider Flash (cost control)
  │   └─ NO → Continue
  │
  ├─ Is user Premium tier?
  │   ├─ YES → Use Pro
  │   └─ NO → Continue
  │
  ├─ Is content technical/complex?
  │   ├─ YES → Use Pro
  │   └─ NO → Continue
  │
  ├─ Is cost critical?
  │   ├─ YES → Use Flash
  │   └─ NO → Use Pro
```

### 8.2 Pricing Model Impact

#### Option A: Single Model Pricing
- **Flash Only**: $0.002-0.004/minute - High volume, lower quality
- **Pro Only**: $0.01-0.02/minute - Premium quality, lower volume

#### Option B: Tiered Pricing
```yaml
tiers:
  basic:
    model: flash
    price: $0.003/minute
    features: Basic extraction
    
  professional:
    model: flash + selective pro
    price: $0.008/minute
    features: Enhanced extraction
    
  enterprise:
    model: pro
    price: $0.015/minute
    features: Maximum intelligence
```

#### Option C: Usage-Based
- Let users choose per job
- Flash: $0.003/minute
- Pro: $0.015/minute
- Default to Flash unless specified

## 9. Implementation Plan

### Phase 1: Infrastructure (Day 1-2)
- Implement model selection parameter
- Add caching to avoid re-downloading
- Create comparison pipeline

### Phase 2: Testing (Day 3-5)
- Run 50 videos through both models
- Collect all metrics
- Generate comparison reports

### Phase 3: Analysis (Day 6-7)
- Analyze quality differences
- Calculate value ratios
- Identify optimal use cases

### Phase 4: Decision (Day 8)
- Choose model strategy
- Update pricing model
- Document recommendations

## 10. Success Criteria

### Minimum Requirements
- Pro must show >25% quality improvement to justify 5x cost
- Flash must achieve >70% of Pro's quality for basic use cases
- Hybrid approach must reduce costs by >40% vs Pro-only

### Optimal Outcomes
- Clear use-case segmentation
- 50% cost reduction with <10% quality loss
- Customer choice flexibility
- Predictable cost model

## 11. Risks and Mitigations

### Risk 1: Pro Not Worth Cost
- **Mitigation**: Implement hybrid approach
- **Fallback**: Use Flash with enhanced prompting

### Risk 2: Flash Quality Too Low
- **Mitigation**: Selective Pro enhancement
- **Fallback**: Pro-only for paid tiers

### Risk 3: Unpredictable Costs
- **Mitigation**: Clear model selection rules
- **Fallback**: Hard cost limits per job

---

## Appendix: Expected Results

### Hypothesis
Based on initial observations:
- Pro will extract 30-50% more entities
- Pro will find 2x more relationships
- Pro will have 20% better accuracy
- Flash will be 3x faster
- Hybrid approach will be optimal

### Validation Required
These hypotheses must be validated through systematic testing before making final decisions.

---

*This document will be updated with actual test results and final recommendations.*
