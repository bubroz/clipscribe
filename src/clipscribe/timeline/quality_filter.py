"""Timeline Quality Filter - Ensuring High-Quality Temporal Intelligence.

This module implements comprehensive quality filtering for Timeline Intelligence v2.0,
addressing quality issues that plagued the original timeline implementation:

QUALITY FILTERS:
- Wrong date detection: Reject dates that don't make sense contextually
- Future date filtering: Reject dates in the future (likely processing artifacts)
- Ancient date filtering: Reject unreasonably old dates (likely errors)
- Confidence thresholding: Filter events below confidence thresholds
- Duplicate content detection: Advanced duplicate event detection
- Context validation: Ensure events have meaningful context
- Entity validation: Verify entities are relevant to temporal events

QUALITY METRICS:
- Date extraction success rates
- Confidence score distributions  
- Event type distributions
- Timeline coherence scores
- Cross-video correlation quality

This ensures Timeline v2.0 produces meaningful, high-quality temporal intelligence :-)
"""

import logging
from typing import List, Dict, Optional, Set, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import re
from collections import defaultdict, Counter

from .models import (
    TemporalEvent, ConsolidatedTimeline, TimelineQualityMetrics,
    ExtractedDate, DatePrecision, EventType, ValidationStatus
)

logger = logging.getLogger(__name__)


@dataclass
class QualityThresholds:
    """Configurable quality thresholds for timeline filtering."""
    min_confidence: float = 0.6
    min_description_length: int = 10
    max_future_days: int = 30  # Reject dates more than 30 days in future
    min_historical_year: int = 1900  # Reject dates before 1900
    max_duplicate_similarity: float = 0.8  # Similarity threshold for duplicates
    min_entity_relevance: float = 0.5  # Minimum entity relevance score
    max_processing_date_days: int = 7  # Reject dates within 7 days of processing


@dataclass
class QualityReport:
    """Detailed quality analysis report."""
    total_events_input: int
    total_events_output: int
    filtered_counts: Dict[str, int]
    quality_score: float
    date_distribution: Dict[str, int]
    confidence_distribution: Dict[str, int]
    event_type_distribution: Dict[str, int]
    recommendations: List[str]


class TimelineQualityFilter:
    """Advanced quality filtering for Timeline Intelligence v2.0.
    
    QUALITY ASSURANCE APPROACH:
    - Multi-stage filtering pipeline with detailed reporting
    - Configurable thresholds for different quality aspects
    - Statistical analysis of timeline coherence
    - Context-aware validation using video metadata
    - Advanced duplicate detection beyond simple text matching
    
    Ensures Timeline v2.0 produces publication-ready temporal intelligence!
    """
    
    def __init__(self, thresholds: Optional[QualityThresholds] = None):
        """Initialize with configurable quality thresholds."""
        self.thresholds = thresholds or QualityThresholds()
        self.processing_date = datetime.now()
        
        # Pattern detection for common quality issues
        self.problematic_patterns = {
            'processing_artifacts': [
                r'\b(?:processing|downloaded|extracted|generated)\b',
                r'\b(?:timestamp|duration|file|export)\b',
                r'\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\b',  # ISO timestamps
            ],
            'technical_noise': [
                r'\b(?:error|exception|debug|log|trace)\b',
                r'\b(?:api|json|xml|http|url)\b',
                r'\b(?:buffer|cache|memory|disk)\b',
            ],
            'ui_elements': [
                r'\b(?:button|click|menu|dialog|window)\b',
                r'\b(?:next|previous|continue|submit)\b',
                r'\b(?:loading|waiting|please wait)\b',
            ]
        }
    
    async def filter_timeline_quality(
        self, 
        timeline: ConsolidatedTimeline
    ) -> Tuple[ConsolidatedTimeline, QualityReport]:
        """Apply comprehensive quality filtering to consolidated timeline.
        
        MULTI-STAGE FILTERING PIPELINE:
        1. Basic validation (confidence, length, content)
        2. Date validation (future, ancient, processing dates)
        3. Content quality (technical noise, UI elements)
        4. Advanced duplicate detection
        5. Entity relevance validation
        6. Timeline coherence analysis
        
        Returns:
            Tuple of (filtered_timeline, quality_report)
        """
        logger.info(f"🔍 Starting quality filtering for {len(timeline.events)} events")
        
        # Initialize filtering statistics
        filter_stats = defaultdict(int)
        filtered_events = timeline.events.copy()
        
        # Stage 1: Basic validation
        filtered_events, basic_filtered = await self._apply_basic_validation(filtered_events)
        filter_stats.update(basic_filtered)
        
        # Stage 2: Date validation  
        filtered_events, date_filtered = await self._apply_date_validation(filtered_events)
        filter_stats.update(date_filtered)
        
        # Stage 3: Content quality filtering
        filtered_events, content_filtered = await self._apply_content_quality_filter(filtered_events)
        filter_stats.update(content_filtered)
        
        # Stage 4: Advanced duplicate detection
        filtered_events, duplicate_filtered = await self._apply_advanced_duplicate_detection(filtered_events)
        filter_stats.update(duplicate_filtered)
        
        # Stage 5: Entity relevance validation
        filtered_events, entity_filtered = await self._apply_entity_relevance_filter(filtered_events)
        filter_stats.update(entity_filtered)
        
        # Stage 6: Timeline coherence analysis
        filtered_events, coherence_filtered = await self._apply_coherence_filter(filtered_events)
        filter_stats.update(coherence_filtered)
        
        # Generate quality report
        quality_report = await self._generate_quality_report(
            timeline.events, filtered_events, filter_stats
        )
        
        # Update timeline with filtered events and quality metrics
        # Using Timeline v2.0 ConsolidatedTimeline model structure
        quality_metrics = self._calculate_quality_metrics(filtered_events, filter_stats)
        
        filtered_timeline = ConsolidatedTimeline(
            events=filtered_events,
            video_sources=timeline.video_sources,
            quality_metrics=quality_metrics.model_dump(),  # Convert to dict
            correlation_analysis=getattr(timeline, 'correlation_analysis', {}),
            chapter_correlations=getattr(timeline, 'chapter_correlations', [])
        )
        
        logger.info(f"✅ Quality filtering complete: {len(timeline.events)} → {len(filtered_events)} events")
        logger.info(f"📊 Quality score: {quality_report.quality_score:.2f}")
        
        return filtered_timeline, quality_report
    
    async def _apply_basic_validation(
        self, events: List[TemporalEvent]
    ) -> Tuple[List[TemporalEvent], Dict[str, int]]:
        """Apply basic validation filters."""
        logger.info("🔍 Applying basic validation filters")
        
        valid_events = []
        filter_stats = defaultdict(int)
        
        for event in events:
            # Check confidence threshold
            if event.confidence < self.thresholds.min_confidence:
                filter_stats['low_confidence'] += 1
                continue
            
            # Check description length
            if len(event.description.strip()) < self.thresholds.min_description_length:
                filter_stats['short_description'] += 1
                continue
            
            # Check for empty or None fields
            if not event.description or not event.description.strip():
                filter_stats['empty_description'] += 1
                continue
            
            if not event.event_id:
                filter_stats['missing_event_id'] += 1
                continue
            
            valid_events.append(event)
        
        logger.info(f"✅ Basic validation: {len(events)} → {len(valid_events)} events")
        return valid_events, dict(filter_stats)
    
    async def _apply_date_validation(
        self, events: List[TemporalEvent]
    ) -> Tuple[List[TemporalEvent], Dict[str, int]]:
        """Apply date validation filters to fix wrong date crisis."""
        logger.info("📅 Applying date validation filters (fixing wrong date crisis)")
        
        valid_events = []
        filter_stats = defaultdict(int)
        
        for event in events:
            if not event.date:
                # Events without dates are OK - they can still be valuable
                valid_events.append(event)
                continue
            
            event_date = event.date
            
            # Filter future dates (likely processing artifacts)
            if event_date > self.processing_date + timedelta(days=self.thresholds.max_future_days):
                filter_stats['future_date'] += 1
                logger.debug(f"🚫 Filtered future date: {event_date} in '{event.description[:50]}...'")
                continue
            
            # Filter ancient dates (likely errors)
            if event_date.year < self.thresholds.min_historical_year:
                filter_stats['ancient_date'] += 1
                logger.debug(f"🚫 Filtered ancient date: {event_date} in '{event.description[:50]}...'")
                continue
            
            # Filter dates too close to processing date (likely processing artifacts)
            if abs((event_date - self.processing_date).days) <= self.thresholds.max_processing_date_days:
                # Check if this looks like a processing artifact
                if self._is_processing_artifact_date(event.description, event_date):
                    filter_stats['processing_artifact_date'] += 1
                    logger.debug(f"🚫 Filtered processing artifact: {event_date} in '{event.description[:50]}...'")
                    continue
            
            # Validate date makes sense in context
            if not self._validate_date_context(event):
                filter_stats['invalid_date_context'] += 1
                logger.debug(f"🚫 Filtered invalid date context: {event_date} in '{event.description[:50]}...'")
                continue
            
            valid_events.append(event)
        
        logger.info(f"✅ Date validation: {len(events)} → {len(valid_events)} events")
        return valid_events, dict(filter_stats)
    
    def _is_processing_artifact_date(self, description: str, date: datetime) -> bool:
        """Check if date appears to be a processing artifact."""
        description_lower = description.lower()
        
        # Check for processing-related keywords
        processing_keywords = [
            'processed', 'generated', 'created', 'downloaded', 'extracted',
            'timestamp', 'file', 'export', 'import', 'upload'
        ]
        
        return any(keyword in description_lower for keyword in processing_keywords)
    
    def _validate_date_context(self, event: TemporalEvent) -> bool:
        """Validate that extracted date makes sense in event context."""
        if not event.date:
            return True  # No date to validate
        
        # Check date precision vs description specificity
        description = event.description.lower()
        date_precision = event.date_precision
        
        # Vague descriptions shouldn't have precise dates
        if date_precision in [DatePrecision.DAY, DatePrecision.EXACT] and len(description.split()) < 5:
            return False
        
        # Historical references should have reasonable dates
        if any(word in description for word in ['history', 'historical', 'past', 'ago']):
            years_ago = (self.processing_date - event.date).days / 365
            if years_ago < 1:  # Historical reference less than 1 year ago
                return False
        
        return True
    
    async def _apply_content_quality_filter(
        self, events: List[TemporalEvent]
    ) -> Tuple[List[TemporalEvent], Dict[str, int]]:
        """Filter out low-quality content and technical noise."""
        logger.info("📝 Applying content quality filters")
        
        quality_events = []
        filter_stats = defaultdict(int)
        
        for event in events:
            description = event.description.lower()
            
            # Check for technical noise patterns
            is_technical_noise = False
            for pattern_type, patterns in self.problematic_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, description, re.IGNORECASE):
                        filter_stats[f'technical_noise_{pattern_type}'] += 1
                        is_technical_noise = True
                        logger.debug(f"🚫 Filtered {pattern_type}: '{event.description[:50]}...'")
                        break
                if is_technical_noise:
                    break
            
            if is_technical_noise:
                continue
            
            # Check for meaningful content
            if not self._has_meaningful_content(description):
                filter_stats['meaningless_content'] += 1
                continue
            
            # Check for redundant or repetitive content
            if self._is_redundant_content(description):
                filter_stats['redundant_content'] += 1
                continue
            
            quality_events.append(event)
        
        logger.info(f"✅ Content quality: {len(events)} → {len(quality_events)} events")
        return quality_events, dict(filter_stats)
    
    def _has_meaningful_content(self, description: str) -> bool:
        """Check if description contains meaningful content."""
        # Remove common stop words and check remaining content
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'between', 'among', 'this', 'that', 'these',
            'those', 'is', 'was', 'are', 'were', 'be', 'been', 'being', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'
        }
        
        words = description.split()
        meaningful_words = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Require at least 2 meaningful words
        return len(meaningful_words) >= 2
    
    def _is_redundant_content(self, description: str) -> bool:
        """Check for redundant or repetitive content."""
        words = description.split()
        
        # Check for excessive repetition
        word_counts = Counter(words)
        most_common_count = word_counts.most_common(1)[0][1] if word_counts else 0
        
        # If any word appears more than 3 times in a short description, it's likely redundant
        if len(words) <= 10 and most_common_count > 3:
            return True
        
        # Check for common redundant phrases
        redundant_phrases = [
            'said said', 'the the', 'and and', 'that that',
            'yeah yeah', 'um um', 'uh uh', 'so so'
        ]
        
        return any(phrase in description for phrase in redundant_phrases)
    
    async def _apply_advanced_duplicate_detection(
        self, events: List[TemporalEvent]
    ) -> Tuple[List[TemporalEvent], Dict[str, int]]:
        """Apply advanced duplicate detection beyond simple text matching."""
        logger.info("🔍 Applying advanced duplicate detection")
        
        unique_events = []
        filter_stats = defaultdict(int)
        seen_events = []
        
        for event in events:
            is_duplicate = False
            
            for existing_event in seen_events:
                if self._calculate_event_similarity(event, existing_event) > self.thresholds.max_duplicate_similarity:
                    filter_stats['advanced_duplicate'] += 1
                    is_duplicate = True
                    logger.debug(f"🚫 Filtered advanced duplicate: '{event.description[:50]}...'")
                    break
            
            if not is_duplicate:
                unique_events.append(event)
                seen_events.append(event)
        
        logger.info(f"✅ Duplicate detection: {len(events)} → {len(unique_events)} events")
        return unique_events, dict(filter_stats)
    
    def _calculate_event_similarity(self, event1: TemporalEvent, event2: TemporalEvent) -> float:
        """Calculate similarity between two events using multiple factors."""
        # Text similarity (Jaccard similarity)
        words1 = set(event1.description.lower().split())
        words2 = set(event2.description.lower().split())
        text_similarity = len(words1 & words2) / len(words1 | words2) if words1 | words2 else 0
        
        # Timestamp proximity (within 30 seconds = high similarity)
        # Get timestamps from the first video in each event's video_timestamps dict
        time1 = list(event1.video_timestamps.values())[0] if event1.video_timestamps else 0
        time2 = list(event2.video_timestamps.values())[0] if event2.video_timestamps else 0
        time_diff = abs(time1 - time2)
        time_similarity = max(0, 1 - (time_diff / 30))
        
        # Entity overlap
        entities1 = set(event1.involved_entities)
        entities2 = set(event2.involved_entities)
        entity_similarity = len(entities1 & entities2) / len(entities1 | entities2) if entities1 | entities2 else 0
        
        # Date similarity
        date_similarity = 0
        if event1.date and event2.date:
            date_diff = abs((event1.date - event2.date).days)
            date_similarity = max(0, 1 - (date_diff / 7))  # Within a week = high similarity
        
        # Weighted average
        return (text_similarity * 0.4 + time_similarity * 0.3 + 
                entity_similarity * 0.2 + date_similarity * 0.1)
    
    async def _apply_entity_relevance_filter(
        self, events: List[TemporalEvent]
    ) -> Tuple[List[TemporalEvent], Dict[str, int]]:
        """Filter events based on entity relevance."""
        logger.info("👥 Applying entity relevance filters")
        
        relevant_events = []
        filter_stats = defaultdict(int)
        
        for event in events:
            if not self._has_relevant_entities(event):
                filter_stats['irrelevant_entities'] += 1
                continue
            
            relevant_events.append(event)
        
        logger.info(f"✅ Entity relevance: {len(events)} → {len(relevant_events)} events")
        return relevant_events, dict(filter_stats)
    
    def _has_relevant_entities(self, event: TemporalEvent) -> bool:
        """Check if event has relevant entities."""
        if not event.involved_entities:
            return True  # Events without entities are OK
        
        # Filter out common irrelevant entities
        irrelevant_entities = {
            'i', 'me', 'you', 'he', 'she', 'it', 'they', 'we', 'us',
            'here', 'there', 'this', 'that', 'these', 'those',
            'now', 'then', 'today', 'yesterday', 'tomorrow',
            'yes', 'no', 'ok', 'okay', 'well', 'so', 'um', 'uh'
        }
        
        relevant_entities = [
            entity for entity in event.involved_entities 
            if entity.lower() not in irrelevant_entities and len(entity) > 2
        ]
        
        return len(relevant_entities) > 0
    
    async def _apply_coherence_filter(
        self, events: List[TemporalEvent]
    ) -> Tuple[List[TemporalEvent], Dict[str, int]]:
        """Apply timeline coherence filters."""
        logger.info("🔗 Applying timeline coherence filters")
        
        coherent_events = []
        filter_stats = defaultdict(int)
        
        # Sort events by date for coherence analysis
        dated_events = [e for e in events if e.date]
        undated_events = [e for e in events if not e.date]
        
        dated_events.sort(key=lambda e: e.date)
        
        # Check for temporal coherence in dated events
        for i, event in enumerate(dated_events):
            if self._is_temporally_coherent(event, dated_events, i):
                coherent_events.append(event)
            else:
                filter_stats['temporal_incoherence'] += 1
        
        # Include all undated events (they don't affect coherence)
        coherent_events.extend(undated_events)
        
        logger.info(f"✅ Coherence filtering: {len(events)} → {len(coherent_events)} events")
        return coherent_events, dict(filter_stats)
    
    def _is_temporally_coherent(
        self, event: TemporalEvent, sorted_events: List[TemporalEvent], index: int
    ) -> bool:
        """Check if event is temporally coherent with surrounding events."""
        if not event.date:
            return True
        
        # Check for extreme temporal jumps that might indicate errors
        window_size = 2
        start_idx = max(0, index - window_size)
        end_idx = min(len(sorted_events), index + window_size + 1)
        
        window_events = sorted_events[start_idx:end_idx]
        if len(window_events) < 3:
            return True  # Not enough context
        
        dates = [e.date for e in window_events if e.date]
        if len(dates) < 3:
            return True
        
        # Check if this event creates an unreasonable temporal gap
        date_diffs = []
        for i in range(len(dates) - 1):
            diff_days = abs((dates[i+1] - dates[i]).days)
            date_diffs.append(diff_days)
        
        # If this event creates a gap more than 10x the average, it might be an error
        if date_diffs:
            avg_diff = sum(date_diffs) / len(date_diffs)
            max_diff = max(date_diffs)
            
            if max_diff > avg_diff * 10 and max_diff > 365:  # More than a year and 10x average
                return False
        
        return True
    
    def _calculate_quality_metrics(
        self, filtered_events: List[TemporalEvent], filter_stats: Dict[str, int]
    ) -> TimelineQualityMetrics:
        """Calculate comprehensive quality metrics."""
        total_events = len(filtered_events)
        events_with_dates = len([e for e in filtered_events if e.date])
        high_confidence_events = len([e for e in filtered_events if e.confidence >= 0.8])
        chapter_segmented_events = len([e for e in filtered_events if e.chapter_context])
        
        # Calculate additional required fields
        deduplicated_events = total_events  # After deduplication
        
        # Prevent division by zero
        date_accuracy_score = 0.0
        if total_events > 0:
            date_accuracy_score = events_with_dates / total_events
        
        chapter_utilization_rate = 0.0
        if total_events > 0:
            chapter_utilization_rate = chapter_segmented_events / total_events
        
        return TimelineQualityMetrics(
            total_events=total_events,
            events_with_extracted_dates=events_with_dates,
            high_confidence_events=high_confidence_events,
            date_extraction_success_rate=events_with_dates / total_events if total_events > 0 else 0,
            average_confidence=sum(e.confidence for e in filtered_events) / total_events if total_events > 0 else 0,
            chapter_segmented_events=chapter_segmented_events,
            sponsorblock_filtered_events=filter_stats.get('sponsorblock_filtered', 0),
            duplicate_events_removed=sum(v for k, v in filter_stats.items() if 'duplicate' in k),
            # Add the missing required fields
            deduplicated_events=deduplicated_events,
            events_with_content_dates=events_with_dates,
            date_accuracy_score=date_accuracy_score,
            chapter_utilization_rate=chapter_utilization_rate
        )
    
    async def _generate_quality_report(
        self,
        original_events: List[TemporalEvent],
        filtered_events: List[TemporalEvent],
        filter_stats: Dict[str, int]
    ) -> QualityReport:
        """Generate comprehensive quality analysis report."""
        # Calculate quality score (0-1)
        filtering_efficiency = len(filtered_events) / len(original_events) if original_events else 1
        avg_confidence = sum(e.confidence for e in filtered_events) / len(filtered_events) if filtered_events else 0
        date_success_rate = len([e for e in filtered_events if e.date]) / len(filtered_events) if filtered_events else 0
        
        quality_score = (filtering_efficiency * 0.3 + avg_confidence * 0.4 + date_success_rate * 0.3)
        
        # Analyze distributions
        date_distribution = self._analyze_date_distribution(filtered_events)
        confidence_distribution = self._analyze_confidence_distribution(filtered_events)
        event_type_distribution = self._analyze_event_type_distribution(filtered_events)
        
        # Generate recommendations
        recommendations = self._generate_quality_recommendations(filter_stats, quality_score)
        
        return QualityReport(
            total_events_input=len(original_events),
            total_events_output=len(filtered_events),
            filtered_counts=filter_stats,
            quality_score=quality_score,
            date_distribution=date_distribution,
            confidence_distribution=confidence_distribution,
            event_type_distribution=event_type_distribution,
            recommendations=recommendations
        )
    
    def _analyze_date_distribution(self, events: List[TemporalEvent]) -> Dict[str, int]:
        """Analyze distribution of extracted dates."""
        distribution = defaultdict(int)
        
        for event in events:
            if event.date:
                year = event.date.year
                distribution[str(year)] += 1
            else:
                distribution['no_date'] += 1
        
        return dict(distribution)
    
    def _analyze_confidence_distribution(self, events: List[TemporalEvent]) -> Dict[str, int]:
        """Analyze distribution of confidence scores."""
        distribution = defaultdict(int)
        
        for event in events:
            if event.confidence >= 0.9:
                distribution['very_high'] += 1
            elif event.confidence >= 0.8:
                distribution['high'] += 1
            elif event.confidence >= 0.7:
                distribution['medium'] += 1
            elif event.confidence >= 0.6:
                distribution['low'] += 1
            else:
                distribution['very_low'] += 1
        
        return dict(distribution)
    
    def _analyze_event_type_distribution(self, events: List[TemporalEvent]) -> Dict[str, int]:
        """Analyze distribution of event types."""
        distribution = defaultdict(int)
        
        for event in events:
            distribution[event.event_type.value] += 1
        
        return dict(distribution)
    
    def _generate_quality_recommendations(
        self, filter_stats: Dict[str, int], quality_score: float
    ) -> List[str]:
        """Generate actionable quality recommendations."""
        recommendations = []
        
        if quality_score < 0.7:
            recommendations.append("Consider reviewing extraction parameters to improve overall quality")
        
        if filter_stats.get('low_confidence', 0) > 10:
            recommendations.append("High number of low-confidence events filtered - consider improving extraction confidence")
        
        if filter_stats.get('future_date', 0) > 5:
            recommendations.append("Multiple future dates detected - review date extraction logic")
        
        if filter_stats.get('ancient_date', 0) > 3:
            recommendations.append("Ancient dates detected - may indicate parsing errors")
        
        total_duplicates = sum(v for k, v in filter_stats.items() if 'duplicate' in k)
        if total_duplicates > 5:
            recommendations.append("High duplicate rate - consider improving event deduplication")
        
        technical_noise = sum(v for k, v in filter_stats.items() if 'technical_noise' in k)
        if technical_noise > 8:
            recommendations.append("Technical noise detected - review content extraction quality")
        
        if not recommendations:
            recommendations.append("Timeline quality is excellent - no immediate improvements needed")
        
        return recommendations 