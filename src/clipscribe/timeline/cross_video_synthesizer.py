"""Cross-Video Timeline Synthesizer - Multi-Video Temporal Intelligence.

This module implements advanced cross-video temporal correlation and timeline synthesis,
enabling Timeline Intelligence v2.0 to build comprehensive timelines from multiple videos:

CROSS-VIDEO CAPABILITIES:
- Temporal event correlation across multiple videos
- Date range analysis and timeline merging
- Entity relationship mapping across videos
- Narrative flow synthesis and chronological ordering
- Cross-video duplicate detection and resolution
- Timeline gap analysis and interpolation

SYNTHESIS STRATEGIES:
- Chronological: Order events purely by extracted dates
- Narrative: Consider storytelling flow and context
- Entity-based: Group events by related entities
- Hybrid: Combine multiple strategies for optimal results

CORRELATION TECHNIQUES:
- Temporal proximity analysis (events close in time)
- Entity overlap correlation (shared entities between videos)
- Content similarity matching (similar descriptions)
- Context validation (ensure logical connections)

This transforms isolated video timelines into comprehensive temporal intelligence :-)
"""

import logging
from typing import List, Dict, Optional, Tuple, Set, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, Counter
import hashlib
import asyncio

from .models import (
    TemporalEvent, ConsolidatedTimeline, TimelineQualityMetrics,
    ExtractedDate, EventType, ValidationStatus
)
from .quality_filter import TimelineQualityFilter, QualityReport

logger = logging.getLogger(__name__)


class SynthesisStrategy(Enum):
    """Timeline synthesis strategies for multi-video correlation."""
    CHRONOLOGICAL = "chronological"        # Pure date-based ordering
    NARRATIVE = "narrative"                # Story flow consideration
    ENTITY_BASED = "entity_based"          # Group by related entities
    HYBRID = "hybrid"                      # Combine multiple strategies
    ADAPTIVE = "adaptive"                  # Choose best strategy


class CorrelationType(Enum):
    """Types of cross-video correlations."""
    TEMPORAL_PROXIMITY = "temporal_proximity"    # Events close in time
    ENTITY_OVERLAP = "entity_overlap"           # Shared entities
    CONTENT_SIMILARITY = "content_similarity"   # Similar descriptions
    CAUSAL_RELATIONSHIP = "causal_relationship" # Cause-and-effect
    REFERENCE_LINK = "reference_link"           # One event references another


@dataclass
class CrossVideoCorrelation:
    """Represents a correlation between events in different videos."""
    correlation_id: str
    correlation_type: CorrelationType
    source_event: TemporalEvent
    target_event: TemporalEvent
    correlation_strength: float  # 0-1 confidence in correlation
    time_difference: Optional[timedelta] = None
    shared_entities: List[str] = field(default_factory=list)
    context_similarity: float = 0.0
    narrative_connection: str = ""


@dataclass
class SynthesisResult:
    """Result of cross-video timeline synthesis."""
    consolidated_timeline: ConsolidatedTimeline
    correlations: List[CrossVideoCorrelation]
    synthesis_strategy: SynthesisStrategy
    quality_report: QualityReport
    timeline_gaps: List[Dict[str, Any]]
    recommendations: List[str]
    processing_metadata: Dict[str, Any]


@dataclass
class VideoTimelineGroup:
    """Group of related video timelines."""
    group_id: str
    video_urls: List[str]
    events: List[TemporalEvent]
    date_range: Tuple[Optional[datetime], Optional[datetime]]
    dominant_entities: List[str]
    narrative_theme: str
    coherence_score: float


class CrossVideoSynthesizer:
    """Advanced cross-video timeline synthesis for Timeline Intelligence v2.0.
    
    MULTI-VIDEO INTELLIGENCE:
    - Correlates temporal events across multiple videos
    - Builds comprehensive timelines spanning multiple sources
    - Identifies narrative flows and causal relationships
    - Resolves cross-video duplicates and conflicts
    - Fills timeline gaps using cross-video context
    - Generates quality-assured consolidated timelines
    
    This enables Timeline v2.0 to provide comprehensive temporal intelligence
    from collections of related videos rather than isolated processing!
    """
    
    def __init__(self, enable_advanced_correlation: bool = True):
        """Initialize with configurable correlation capabilities."""
        self.enable_advanced_correlation = enable_advanced_correlation
        self.quality_filter = TimelineQualityFilter()
        
        # Correlation thresholds
        self.correlation_thresholds = {
            'temporal_proximity_hours': 24,      # Events within 24 hours
            'entity_overlap_min': 2,             # At least 2 shared entities
            'content_similarity_min': 0.6,       # 60% content similarity
            'correlation_strength_min': 0.5,     # Minimum correlation strength
            'max_time_gap_days': 365             # Maximum gap to consider
        }
        
        # Entity relationship patterns
        self.entity_relationship_patterns = {
            'person_organization': [
                r'(?P<person>\w+(?:\s+\w+)*)\s+(?:from|at|with|of)\s+(?P<org>\w+(?:\s+\w+)*)',
                r'(?P<org>\w+(?:\s+\w+)*)\s+(?:employee|member|representative)\s+(?P<person>\w+(?:\s+\w+)*)'
            ],
            'causal_relationships': [
                r'(?:because|due to|caused by|resulted from)\s+(.{10,50})',
                r'(?:led to|resulted in|caused|triggered)\s+(.{10,50})',
                r'(?:after|following|subsequent to)\s+(.{10,50})'
            ],
            'temporal_references': [
                r'(?:earlier|previously|before)\s+(.{10,50})',
                r'(?:later|afterwards|subsequently)\s+(.{10,50})',
                r'(?:during|while|when)\s+(.{10,50})'
            ]
        }
    
    async def synthesize_multi_video_timeline(
        self,
        video_timelines: Dict[str, List[TemporalEvent]],
        strategy: SynthesisStrategy = SynthesisStrategy.ADAPTIVE
    ) -> SynthesisResult:
        """Synthesize comprehensive timeline from multiple video timelines.
        
        SYNTHESIS PIPELINE:
        1. Analyze video timeline characteristics
        2. Choose optimal synthesis strategy
        3. Perform cross-video correlation analysis
        4. Merge and order events chronologically
        5. Apply quality filtering and validation
        6. Generate timeline gap analysis
        7. Provide synthesis recommendations
        
        Args:
            video_timelines: Dict mapping video URLs to their temporal events
            strategy: Synthesis strategy to use
            
        Returns:
            Complete synthesis result with consolidated timeline
        """
        logger.info(f"🔗 Starting cross-video timeline synthesis")
        logger.info(f"📺 Videos: {len(video_timelines)}")
        logger.info(f"📋 Total events: {sum(len(events) for events in video_timelines.values())}")
        
        # Step 1: Analyze video timeline characteristics
        timeline_characteristics = await self._analyze_timeline_characteristics(video_timelines)
        
        # Step 2: Choose optimal synthesis strategy
        if strategy == SynthesisStrategy.ADAPTIVE:
            strategy = self._choose_optimal_synthesis_strategy(timeline_characteristics)
        
        logger.info(f"🎯 Using synthesis strategy: {strategy.value}")
        
        # Step 3: Perform cross-video correlation analysis
        correlations = await self._perform_correlation_analysis(video_timelines)
        logger.info(f"🔗 Found {len(correlations)} cross-video correlations")
        
        # Step 4: Merge and order events using chosen strategy
        consolidated_timeline = await self._merge_timelines(
            video_timelines, correlations, strategy
        )
        
        # Step 5: Apply quality filtering
        filtered_timeline, quality_report = await self.quality_filter.filter_timeline_quality(
            consolidated_timeline
        )
        
        # Step 6: Generate timeline gap analysis
        timeline_gaps = await self._analyze_timeline_gaps(filtered_timeline, correlations)
        
        # Step 7: Generate synthesis recommendations
        recommendations = await self._generate_synthesis_recommendations(
            filtered_timeline, correlations, quality_report, timeline_gaps
        )
        
        # Create synthesis result
        synthesis_result = SynthesisResult(
            consolidated_timeline=filtered_timeline,
            correlations=correlations,
            synthesis_strategy=strategy,
            quality_report=quality_report,
            timeline_gaps=timeline_gaps,
            recommendations=recommendations,
            processing_metadata={
                'total_input_videos': len(video_timelines),
                'total_input_events': sum(len(events) for events in video_timelines.values()),
                'synthesis_timestamp': datetime.now().isoformat(),
                'correlation_count': len(correlations),
                'quality_score': quality_report.quality_score
            }
        )
        
        logger.info(f"✅ Cross-video synthesis complete:")
        logger.info(f"   📊 Final events: {len(filtered_timeline.events)}")
        logger.info(f"   🔗 Correlations: {len(correlations)}")
        logger.info(f"   📈 Quality score: {quality_report.quality_score:.2f}")
        
        return synthesis_result
    
    async def _analyze_timeline_characteristics(
        self, video_timelines: Dict[str, List[TemporalEvent]]
    ) -> Dict[str, Any]:
        """Analyze characteristics of input video timelines."""
        logger.info("📊 Analyzing timeline characteristics")
        
        characteristics = {
            'total_videos': len(video_timelines),
            'total_events': 0,
            'date_coverage': {},
            'entity_overlap': {},
            'event_type_distribution': defaultdict(int),
            'confidence_distribution': defaultdict(int),
            'temporal_density': {}
        }
        
        all_entities = set()
        all_dates = []
        
        for video_url, events in video_timelines.items():
            characteristics['total_events'] += len(events)
            
            # Analyze date coverage
            video_dates = []
            for event in events:
                if event.date:
                    video_dates.append(event.date)
                    all_dates.append(event.date)
                
                # Collect entities
                all_entities.update(event.involved_entities)
                
                # Event type distribution
                characteristics['event_type_distribution'][event.event_type.value] += 1
                
                # Confidence distribution
                if event.confidence >= 0.8:
                    characteristics['confidence_distribution']['high'] += 1
                elif event.confidence >= 0.6:
                    characteristics['confidence_distribution']['medium'] += 1
                else:
                    characteristics['confidence_distribution']['low'] += 1
            
            # Date range for this video
            if video_dates:
                characteristics['date_coverage'][video_url] = {
                    'start': min(video_dates),
                    'end': max(video_dates),
                    'span_days': (max(video_dates) - min(video_dates)).days,
                    'event_count': len(video_dates)
                }
            
            # Temporal density (events per day)
            if video_dates:
                span_days = max(1, (max(video_dates) - min(video_dates)).days)
                characteristics['temporal_density'][video_url] = len(events) / span_days
        
        # Overall date range
        if all_dates:
            characteristics['overall_date_range'] = {
                'start': min(all_dates),
                'end': max(all_dates),
                'span_days': (max(all_dates) - min(all_dates)).days
            }
        
        # Entity overlap analysis
        video_entities = {}
        for video_url, events in video_timelines.items():
            video_entities[video_url] = set()
            for event in events:
                video_entities[video_url].update(event.involved_entities)
        
        # Calculate pairwise entity overlap
        video_urls = list(video_timelines.keys())
        for i, url1 in enumerate(video_urls):
            for url2 in video_urls[i+1:]:
                entities1 = video_entities[url1]
                entities2 = video_entities[url2]
                overlap = len(entities1 & entities2)
                total = len(entities1 | entities2)
                overlap_ratio = overlap / total if total > 0 else 0
                
                characteristics['entity_overlap'][f"{url1}+{url2}"] = {
                    'shared_entities': overlap,
                    'overlap_ratio': overlap_ratio,
                    'entities': list(entities1 & entities2)
                }
        
        logger.info(f"📊 Analysis complete: {characteristics['total_events']} events across {characteristics['total_videos']} videos")
        return characteristics
    
    def _choose_optimal_synthesis_strategy(
        self, characteristics: Dict[str, Any]
    ) -> SynthesisStrategy:
        """Choose optimal synthesis strategy based on timeline characteristics."""
        
        total_events = characteristics['total_events']
        total_videos = characteristics['total_videos']
        
        # Calculate decision factors
        date_coverage_quality = self._assess_date_coverage_quality(characteristics)
        entity_overlap_strength = self._assess_entity_overlap_strength(characteristics)
        temporal_coherence = self._assess_temporal_coherence(characteristics)
        
        logger.info(f"📊 Strategy decision factors:")
        logger.info(f"   Date coverage quality: {date_coverage_quality:.2f}")
        logger.info(f"   Entity overlap strength: {entity_overlap_strength:.2f}")
        logger.info(f"   Temporal coherence: {temporal_coherence:.2f}")
        
        # Strategy selection logic
        if date_coverage_quality >= 0.8 and temporal_coherence >= 0.7:
            return SynthesisStrategy.CHRONOLOGICAL
        elif entity_overlap_strength >= 0.7:
            return SynthesisStrategy.ENTITY_BASED
        elif total_events >= 50 and total_videos >= 3:
            return SynthesisStrategy.HYBRID
        else:
            return SynthesisStrategy.NARRATIVE
    
    def _assess_date_coverage_quality(self, characteristics: Dict[str, Any]) -> float:
        """Assess quality of date coverage across videos."""
        date_coverage = characteristics.get('date_coverage', {})
        
        if not date_coverage:
            return 0.0
        
        # Check percentage of events with dates
        total_events = characteristics['total_events']
        events_with_dates = sum(
            coverage['event_count'] for coverage in date_coverage.values()
        )
        date_percentage = events_with_dates / total_events if total_events > 0 else 0
        
        # Check temporal overlap between videos
        video_ranges = list(date_coverage.values())
        if len(video_ranges) <= 1:
            return date_percentage
        
        # Calculate overlap score
        overlap_score = 0.0
        for i, range1 in enumerate(video_ranges):
            for range2 in video_ranges[i+1:]:
                # Check if date ranges overlap
                start1, end1 = range1['start'], range1['end']
                start2, end2 = range2['start'], range2['end']
                
                overlap_start = max(start1, start2)
                overlap_end = min(end1, end2)
                
                if overlap_start <= overlap_end:
                    overlap_days = (overlap_end - overlap_start).days
                    total_span = max((end1 - start1).days, (end2 - start2).days)
                    overlap_score += overlap_days / max(total_span, 1)
        
        avg_overlap = overlap_score / max(len(video_ranges) * (len(video_ranges) - 1) / 2, 1)
        
        return (date_percentage * 0.7 + avg_overlap * 0.3)
    
    def _assess_entity_overlap_strength(self, characteristics: Dict[str, Any]) -> float:
        """Assess strength of entity overlap between videos."""
        entity_overlap = characteristics.get('entity_overlap', {})
        
        if not entity_overlap:
            return 0.0
        
        overlap_ratios = [overlap['overlap_ratio'] for overlap in entity_overlap.values()]
        shared_counts = [overlap['shared_entities'] for overlap in entity_overlap.values()]
        
        # Average overlap ratio weighted by number of shared entities
        if not overlap_ratios:
            return 0.0
        
        weighted_ratio = sum(
            ratio * min(count / 5, 1.0)  # Weight by shared count (cap at 5)
            for ratio, count in zip(overlap_ratios, shared_counts)
        ) / len(overlap_ratios)
        
        return min(weighted_ratio, 1.0)
    
    def _assess_temporal_coherence(self, characteristics: Dict[str, Any]) -> float:
        """Assess temporal coherence across videos."""
        date_coverage = characteristics.get('date_coverage', {})
        temporal_density = characteristics.get('temporal_density', {})
        
        if len(date_coverage) <= 1:
            return 1.0  # Single video is always coherent
        
        # Check consistency of temporal density
        densities = list(temporal_density.values())
        if not densities:
            return 0.0
        
        avg_density = sum(densities) / len(densities)
        density_variance = sum((d - avg_density) ** 2 for d in densities) / len(densities)
        density_coherence = max(0, 1 - (density_variance / max(avg_density, 0.1)))
        
        # Check temporal gap consistency
        ranges = list(date_coverage.values())
        gaps = []
        for i in range(len(ranges) - 1):
            for j in range(i + 1, len(ranges)):
                range1, range2 = ranges[i], ranges[j]
                if range1['end'] < range2['start']:
                    gap = (range2['start'] - range1['end']).days
                elif range2['end'] < range1['start']:
                    gap = (range1['start'] - range2['end']).days
                else:
                    gap = 0  # Overlapping
                gaps.append(gap)
        
        if gaps:
            avg_gap = sum(gaps) / len(gaps)
            gap_coherence = max(0, 1 - (avg_gap / 365))  # Penalize gaps > 1 year
        else:
            gap_coherence = 1.0
        
        return (density_coherence * 0.6 + gap_coherence * 0.4)
    
    async def _perform_correlation_analysis(
        self, video_timelines: Dict[str, List[TemporalEvent]]
    ) -> List[CrossVideoCorrelation]:
        """Perform comprehensive cross-video correlation analysis."""
        logger.info("🔗 Performing cross-video correlation analysis")
        
        correlations = []
        video_urls = list(video_timelines.keys())
        
        # Perform pairwise correlation analysis
        for i, url1 in enumerate(video_urls):
            for url2 in video_urls[i+1:]:
                events1 = video_timelines[url1]
                events2 = video_timelines[url2]
                
                pair_correlations = await self._find_event_correlations(
                    events1, events2, url1, url2
                )
                correlations.extend(pair_correlations)
        
        # Filter correlations by strength threshold
        strong_correlations = [
            corr for corr in correlations 
            if corr.correlation_strength >= self.correlation_thresholds['correlation_strength_min']
        ]
        
        logger.info(f"🔗 Correlation analysis complete: {len(strong_correlations)} strong correlations found")
        return strong_correlations
    
    async def _find_event_correlations(
        self,
        events1: List[TemporalEvent],
        events2: List[TemporalEvent],
        url1: str,
        url2: str
    ) -> List[CrossVideoCorrelation]:
        """Find correlations between events in two videos."""
        correlations = []
        
        for event1 in events1:
            for event2 in events2:
                correlation = await self._analyze_event_pair(event1, event2)
                
                if correlation and correlation.correlation_strength > 0:
                    correlations.append(correlation)
        
        return correlations
    
    async def _analyze_event_pair(
        self, event1: TemporalEvent, event2: TemporalEvent
    ) -> Optional[CrossVideoCorrelation]:
        """Analyze potential correlation between two events."""
        
        # Skip if events are from the same video
        # Check if they share any source videos
        if set(event1.source_videos) & set(event2.source_videos):
            return None
        
        correlations_found = []
        
        # Check temporal proximity
        temporal_corr = self._check_temporal_proximity(event1, event2)
        if temporal_corr:
            correlations_found.append(temporal_corr)
        
        # Check entity overlap
        entity_corr = self._check_entity_overlap(event1, event2)
        if entity_corr:
            correlations_found.append(entity_corr)
        
        # Check content similarity
        content_corr = self._check_content_similarity(event1, event2)
        if content_corr:
            correlations_found.append(content_corr)
        
        if self.enable_advanced_correlation:
            # Check causal relationships
            causal_corr = self._check_causal_relationship(event1, event2)
            if causal_corr:
                correlations_found.append(causal_corr)
            
            # Check reference links
            reference_corr = self._check_reference_link(event1, event2)
            if reference_corr:
                correlations_found.append(reference_corr)
        
        # Return the strongest correlation found
        if correlations_found:
            return max(correlations_found, key=lambda c: c.correlation_strength)
        
        return None
    
    def _check_temporal_proximity(
        self, event1: TemporalEvent, event2: TemporalEvent
    ) -> Optional[CrossVideoCorrelation]:
        """Check if events are temporally proximate."""
        
        # Both events need dates for temporal correlation
        if not event1.date or not event2.date:
            return None
        
        date1 = event1.date
        date2 = event2.date
        
        time_diff = abs((date1 - date2).total_seconds())
        max_diff = self.correlation_thresholds['temporal_proximity_hours'] * 3600
        
        if time_diff <= max_diff:
            # Calculate strength based on proximity
            strength = max(0, 1 - (time_diff / max_diff))
            
            return CrossVideoCorrelation(
                correlation_id=self._generate_correlation_id(event1, event2, "temporal"),
                correlation_type=CorrelationType.TEMPORAL_PROXIMITY,
                source_event=event1,
                target_event=event2,
                correlation_strength=strength,
                time_difference=timedelta(seconds=time_diff),
                narrative_connection=f"Events occurred within {time_diff/3600:.1f} hours"
            )
        
        return None
    
    def _check_entity_overlap(
        self, event1: TemporalEvent, event2: TemporalEvent
    ) -> Optional[CrossVideoCorrelation]:
        """Check if events share entities."""
        
        entities1 = set(event1.involved_entities)
        entities2 = set(event2.involved_entities)
        shared = entities1 & entities2
        
        if len(shared) >= self.correlation_thresholds['entity_overlap_min']:
            # Calculate strength based on overlap ratio
            total_entities = len(entities1 | entities2)
            overlap_ratio = len(shared) / total_entities if total_entities > 0 else 0
            
            # Boost strength for more shared entities
            entity_boost = min(len(shared) / 5, 1.0)  # Up to 5 entities
            strength = (overlap_ratio * 0.7 + entity_boost * 0.3)
            
            return CrossVideoCorrelation(
                correlation_id=self._generate_correlation_id(event1, event2, "entity"),
                correlation_type=CorrelationType.ENTITY_OVERLAP,
                source_event=event1,
                target_event=event2,
                correlation_strength=strength,
                shared_entities=list(shared),
                narrative_connection=f"Shared entities: {', '.join(list(shared)[:3])}"
            )
        
        return None
    
    def _check_content_similarity(
        self, event1: TemporalEvent, event2: TemporalEvent
    ) -> Optional[CrossVideoCorrelation]:
        """Check if events have similar content."""
        
        # Simple content similarity using word overlap
        words1 = set(event1.description.lower().split())
        words2 = set(event2.description.lower().split())
        
        if not words1 or not words2:
            return None
        
        overlap = words1 & words2
        total = words1 | words2
        similarity = len(overlap) / len(total) if total else 0
        
        if similarity >= self.correlation_thresholds['content_similarity_min']:
            return CrossVideoCorrelation(
                correlation_id=self._generate_correlation_id(event1, event2, "content"),
                correlation_type=CorrelationType.CONTENT_SIMILARITY,
                source_event=event1,
                target_event=event2,
                correlation_strength=similarity,
                context_similarity=similarity,
                narrative_connection=f"Content similarity: {similarity:.1%}"
            )
        
        return None
    
    def _check_causal_relationship(
        self, event1: TemporalEvent, event2: TemporalEvent
    ) -> Optional[CrossVideoCorrelation]:
        """Check for potential causal relationships between events."""
        
        desc1 = event1.description.lower()
        desc2 = event2.description.lower()
        
        # Look for causal language patterns
        causal_patterns = self.entity_relationship_patterns['causal_relationships']
        
        causal_strength = 0.0
        connection_text = ""
        
        for pattern in causal_patterns:
            # Check if event1 description contains causal reference to event2 concepts
            if any(word in desc1 for word in desc2.split()[:5]):  # Check first 5 words
                import re
                matches = re.findall(pattern, desc1, re.IGNORECASE)
                if matches:
                    causal_strength = 0.7
                    connection_text = f"Causal reference detected: {matches[0][:50]}"
                    break
        
        if causal_strength > 0:
            return CrossVideoCorrelation(
                correlation_id=self._generate_correlation_id(event1, event2, "causal"),
                correlation_type=CorrelationType.CAUSAL_RELATIONSHIP,
                source_event=event1,
                target_event=event2,
                correlation_strength=causal_strength,
                narrative_connection=connection_text
            )
        
        return None
    
    def _check_reference_link(
        self, event1: TemporalEvent, event2: TemporalEvent
    ) -> Optional[CrossVideoCorrelation]:
        """Check if one event references the other."""
        
        # Look for temporal reference patterns
        reference_patterns = self.entity_relationship_patterns['temporal_references']
        
        desc1 = event1.description.lower()
        desc2 = event2.description.lower()
        
        reference_strength = 0.0
        connection_text = ""
        
        # Check if event descriptions contain temporal references
        for pattern in reference_patterns:
            import re
            matches1 = re.findall(pattern, desc1, re.IGNORECASE)
            matches2 = re.findall(pattern, desc2, re.IGNORECASE)
            
            if matches1 or matches2:
                # Check if the referenced content relates to the other event
                for match in matches1 + matches2:
                    if any(word in match for word in (desc1 + desc2).split()[:10]):
                        reference_strength = 0.6
                        connection_text = f"Temporal reference: {match[:50]}"
                        break
        
        if reference_strength > 0:
            return CrossVideoCorrelation(
                correlation_id=self._generate_correlation_id(event1, event2, "reference"),
                correlation_type=CorrelationType.REFERENCE_LINK,
                source_event=event1,
                target_event=event2,
                correlation_strength=reference_strength,
                narrative_connection=connection_text
            )
        
        return None
    
    def _generate_correlation_id(
        self, event1: TemporalEvent, event2: TemporalEvent, corr_type: str
    ) -> str:
        """Generate unique correlation ID."""
        content = f"{event1.event_id}_{event2.event_id}_{corr_type}"
        return f"corr_{hashlib.md5(content.encode()).hexdigest()[:8]}"
    
    async def _merge_timelines(
        self,
        video_timelines: Dict[str, List[TemporalEvent]],
        correlations: List[CrossVideoCorrelation],
        strategy: SynthesisStrategy
    ) -> ConsolidatedTimeline:
        """Merge timelines using the specified synthesis strategy."""
        logger.info(f"🔀 Merging timelines using {strategy.value} strategy")
        
        # Collect all events
        all_events = []
        for video_url, events in video_timelines.items():
            all_events.extend(events)
        
        # Apply strategy-specific ordering
        if strategy == SynthesisStrategy.CHRONOLOGICAL:
            ordered_events = self._order_chronologically(all_events)
        elif strategy == SynthesisStrategy.ENTITY_BASED:
            ordered_events = self._order_by_entities(all_events, correlations)
        elif strategy == SynthesisStrategy.NARRATIVE:
            ordered_events = self._order_narratively(all_events, correlations)
        elif strategy == SynthesisStrategy.HYBRID:
            ordered_events = self._order_hybrid(all_events, correlations)
        else:
            ordered_events = self._order_chronologically(all_events)  # Default
        
        # Create consolidated timeline
        # Convert TimelineQualityMetrics to dict for storage
        quality_metrics_obj = self._calculate_preliminary_quality_metrics(ordered_events)
        quality_metrics_dict = quality_metrics_obj.model_dump()  # Use model_dump() for Pydantic v2
        
        timeline = ConsolidatedTimeline(
            timeline_id=f"consolidated_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            events=ordered_events,
            video_sources=list(video_timelines.keys()),
            creation_date=datetime.now(),
            quality_metrics=quality_metrics_dict,
            cross_video_correlations=correlations,
            metadata={
                'synthesis_strategy': strategy.value,
                'total_input_videos': len(video_timelines),
                'correlation_count': len(correlations),
                'merge_timestamp': datetime.now().isoformat()
            }
        )
        
        logger.info(f"🔀 Timeline merge complete: {len(ordered_events)} events ordered")
        return timeline
    
    def _order_chronologically(self, events: List[TemporalEvent]) -> List[TemporalEvent]:
        """Order events chronologically by extracted dates."""
        
        # Separate events with and without dates
        dated_events = [e for e in events if e.date]
        undated_events = [e for e in events if not e.date]
        
        # Sort dated events by date, then by first video timestamp
        dated_events.sort(key=lambda e: (
            e.date, 
            list(e.video_timestamps.values())[0] if e.video_timestamps else 0
        ))
        
        # Sort undated events by first video timestamp
        undated_events.sort(key=lambda e: list(e.video_timestamps.values())[0] if e.video_timestamps else 0)
        
        # Combine: dated events first, then undated
        return dated_events + undated_events
    
    def _order_by_entities(
        self, events: List[TemporalEvent], correlations: List[CrossVideoCorrelation]
    ) -> List[TemporalEvent]:
        """Order events by entity relationships."""
        
        # Group events by dominant entities
        entity_groups = defaultdict(list)
        
        for event in events:
            if event.involved_entities:
                # Use first entity as primary grouping key
                primary_entity = event.involved_entities[0]
                entity_groups[primary_entity].append(event)
            else:
                entity_groups['_no_entities'].append(event)
        
        # Order groups by entity frequency (most common first)
        entity_counts = Counter()
        for event in events:
            for entity in event.involved_entities:
                entity_counts[entity] += 1
        
        ordered_events = []
        for entity, count in entity_counts.most_common():
            group_events = entity_groups[entity]
            # Within each group, order chronologically
            group_events = self._order_chronologically(group_events)
            ordered_events.extend(group_events)
        
        # Add events without entities at the end
        if '_no_entities' in entity_groups:
            no_entity_events = self._order_chronologically(entity_groups['_no_entities'])
            ordered_events.extend(no_entity_events)
        
        return ordered_events
    
    def _order_narratively(
        self, events: List[TemporalEvent], correlations: List[CrossVideoCorrelation]
    ) -> List[TemporalEvent]:
        """Order events considering narrative flow."""
        
        # Start with chronological order as base
        ordered_events = self._order_chronologically(events)
        
        # Apply narrative adjustments based on correlations
        correlation_map = defaultdict(list)
        for corr in correlations:
            if corr.correlation_type in [CorrelationType.CAUSAL_RELATIONSHIP, CorrelationType.REFERENCE_LINK]:
                correlation_map[corr.source_event.event_id].append(corr.target_event)
        
        # Adjust order to respect causal/reference relationships
        for i, event in enumerate(ordered_events):
            if event.event_id in correlation_map:
                related_events = correlation_map[event.event_id]
                # Ensure related events come after this event
                for related_event in related_events:
                    if related_event in ordered_events[i:]:
                        current_pos = ordered_events.index(related_event)
                        if current_pos <= i:
                            # Move related event after current event
                            ordered_events.remove(related_event)
                            ordered_events.insert(i + 1, related_event)
        
        return ordered_events
    
    def _order_hybrid(
        self, events: List[TemporalEvent], correlations: List[CrossVideoCorrelation]
    ) -> List[TemporalEvent]:
        """Order events using hybrid approach (chronological + narrative + entities)."""
        
        # Start with chronological order
        chronological = self._order_chronologically(events)
        
        # Apply narrative adjustments
        narrative = self._order_narratively(chronological, correlations)
        
        # Group related events by entity while preserving narrative flow
        final_order = []
        processed = set()
        
        for event in narrative:
            if event.event_id in processed:
                continue
            
            # Find all events with shared entities
            related_events = [event]
            for other_event in narrative:
                if (other_event.event_id != event.event_id and 
                    other_event.event_id not in processed and
                    set(event.involved_entities) & set(other_event.involved_entities)):
                    related_events.append(other_event)
            
            # Order related events chronologically
            related_events = self._order_chronologically(related_events)
            final_order.extend(related_events)
            
            for related_event in related_events:
                processed.add(related_event.event_id)
        
        return final_order
    
    def _calculate_preliminary_quality_metrics(
        self, events: List[TemporalEvent]
    ) -> TimelineQualityMetrics:
        """Calculate preliminary quality metrics before filtering."""
        total_events = len(events)
        events_with_extracted_dates = len([e for e in events if e.date])
        events_with_content_dates = len([e for e in events if e.date_source != "fallback_video_published_date"])
        
        # Calculate date accuracy score
        date_accuracy_score = 0.0
        if total_events > 0:
            # Score based on: extracted dates, content dates, and confidence
            date_scores = []
            for event in events:
                if event.date:
                    if event.date_source != "fallback_video_published_date":
                        date_scores.append(event.date_confidence)
                    else:
                        date_scores.append(0.1)  # Low score for fallback dates
                else:
                    date_scores.append(0.0)
            date_accuracy_score = sum(date_scores) / len(date_scores) if date_scores else 0.0
        
        # Calculate chapter utilization rate
        chapter_utilization_rate = 0.0
        if total_events > 0:
            chapter_events = len([e for e in events if e.chapter_context])
            chapter_utilization_rate = chapter_events / total_events
        
        return TimelineQualityMetrics(
            total_events=total_events,
            deduplicated_events=total_events,  # Will be updated after deduplication
            events_with_extracted_dates=events_with_extracted_dates,
            events_with_content_dates=events_with_content_dates,
            average_confidence=sum(e.confidence for e in events) / total_events if total_events > 0 else 0,
            date_accuracy_score=date_accuracy_score,
            chapter_utilization_rate=chapter_utilization_rate
        )
    
    async def _analyze_timeline_gaps(
        self, timeline: ConsolidatedTimeline, correlations: List[CrossVideoCorrelation]
    ) -> List[Dict[str, Any]]:
        """Analyze gaps in the consolidated timeline."""
        logger.info("🔍 Analyzing timeline gaps")
        
        gaps = []
        
        # Find temporal gaps between dated events
        dated_events = [e for e in timeline.events if e.date]
        dated_events.sort(key=lambda e: e.date)
        
        for i in range(len(dated_events) - 1):
            current_event = dated_events[i]
            next_event = dated_events[i + 1]
            
            gap_days = (next_event.date - current_event.date).days
            
            if gap_days > 7:  # Gaps longer than a week
                gap_info = {
                    'gap_id': f"gap_{i}",
                    'start_event': current_event.event_id,
                    'end_event': next_event.event_id,
                    'gap_duration_days': gap_days,
                    'start_date': current_event.date.isoformat(),
                    'end_date': next_event.date.isoformat(),
                    'potential_fill_sources': [],
                    'gap_significance': self._assess_gap_significance(gap_days, current_event, next_event)
                }
                
                # Look for events that might fill this gap
                for event in timeline.events:
                    if (event.date and
                        current_event.date < event.date < next_event.date):
                        gap_info['potential_fill_sources'].append(event.event_id)
                
                gaps.append(gap_info)
        
        logger.info(f"🔍 Found {len(gaps)} significant timeline gaps")
        return gaps
    
    def _assess_gap_significance(
        self, gap_days: int, before_event: TemporalEvent, after_event: TemporalEvent
    ) -> str:
        """Assess the significance of a timeline gap."""
        
        if gap_days > 365:
            return "critical"  # More than a year
        elif gap_days > 90:
            return "major"     # More than 3 months
        elif gap_days > 30:
            return "moderate"  # More than a month
        else:
            return "minor"     # 1-4 weeks
    
    async def _generate_synthesis_recommendations(
        self,
        timeline: ConsolidatedTimeline,
        correlations: List[CrossVideoCorrelation],
        quality_report: QualityReport,
        timeline_gaps: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations for timeline synthesis improvement."""
        
        recommendations = []
        
        # Quality-based recommendations
        if quality_report.quality_score < 0.7:
            recommendations.append("Timeline quality is below optimal - consider improving source video selection")
        
        # Correlation-based recommendations
        strong_correlations = len([c for c in correlations if c.correlation_strength >= 0.8])
        if strong_correlations / max(len(correlations), 1) < 0.3:
            recommendations.append("Low correlation strength - videos may not be closely related")
        
        # Gap-based recommendations
        critical_gaps = len([g for g in timeline_gaps if g['gap_significance'] == 'critical'])
        if critical_gaps > 0:
            recommendations.append(f"{critical_gaps} critical timeline gaps detected - consider additional source videos")
        
        # Event distribution recommendations
        events_with_dates = len([e for e in timeline.events if e.extracted_date and e.extracted_date.date])
        date_percentage = events_with_dates / len(timeline.events) if timeline.events else 0
        
        if date_percentage < 0.5:
            recommendations.append("Low percentage of events have extracted dates - review date extraction quality")
        
        # Video source recommendations
        if len(timeline.video_sources) < 3:
            recommendations.append("Timeline based on few videos - additional sources could improve comprehensiveness")
        
        if not recommendations:
            recommendations.append("Timeline synthesis quality is excellent - ready for use")
        
        return recommendations 