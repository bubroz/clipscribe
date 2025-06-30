"""
Event Deduplicator - Fixes the 44-Duplicate Crisis

This module addresses the critical architectural flaw in Timeline v1.0 where the same
real-world event (evt_6ZVj1_SE4Mo_0) was duplicated 44 times due to entity combination
explosion. 

PROBLEM FIXED:
- Same event with ["Pegasus"] 
- Same event with ["Pegasus", "NSO Group"]
- Same event with ["Pegasus", "NSO Group", "Israel"]
= 3 duplicate timeline entries!

SOLUTION:
- One event with all entities: ["Pegasus", "NSO Group", "Israel"]
= 1 timeline entry

The rule is simple: One real event = one timeline entry. Period.
"""

import hashlib
import logging
from collections import defaultdict
from typing import List, Dict, Set
from difflib import SequenceMatcher

from .models import TemporalEvent, DatePrecision

logger = logging.getLogger(__name__)


class EventDeduplicator:
    """
    Fixes the 44-duplicate event crisis through intelligent event consolidation.
    
    The core principle: Real-world events should appear exactly once in the timeline,
    regardless of how many different entity combinations are associated with them.
    """
    
    def __init__(self, similarity_threshold: float = 0.8, time_proximity_threshold: float = 3600):
        """
        Initialize the deduplicator.
        
        Args:
            similarity_threshold: Minimum similarity (0-1) to consider events the same
            time_proximity_threshold: Maximum time difference (seconds) for similar events
        """
        self.similarity_threshold = similarity_threshold
        self.time_proximity_threshold = time_proximity_threshold
    
    def deduplicate_events(self, events: List[TemporalEvent]) -> List[TemporalEvent]:
        """
        MAIN FUNCTION: Eliminate duplicate events and consolidate entities.
        
        This is the breakthrough fix for Timeline Intelligence v2.0.
        
        Args:
            events: List of potentially duplicate temporal events
            
        Returns:
            List of deduplicated temporal events with consolidated entities
        """
        if not events:
            return []
            
        logger.info(f"🔧 Starting event deduplication: {len(events)} input events")
        
        # Group events that represent the same real-world occurrence
        event_groups = self._group_similar_events(events)
        
        logger.info(f"📊 Grouped {len(events)} events into {len(event_groups)} unique occurrences")
        
        # Merge each group into a single consolidated event
        deduplicated = []
        for i, group in enumerate(event_groups):
            if len(group) == 1:
                # Single event, no deduplication needed
                deduplicated.append(group[0])
                logger.debug(f"Event {i+1}: Single event, no merging needed")
            else:
                # Multiple events representing same occurrence - merge them
                merged_event = self._merge_event_group(group)
                deduplicated.append(merged_event)
                logger.info(f"Event {i+1}: Merged {len(group)} duplicates into single event")
        
        logger.info(f"✅ Deduplication complete: {len(events)} → {len(deduplicated)} events ({len(events)-len(deduplicated)} duplicates removed)")
        
        return deduplicated
    
    def _group_similar_events(self, events: List[TemporalEvent]) -> List[List[TemporalEvent]]:
        """
        Group events that represent the same real-world occurrence.
        
        Events are considered the same if they have:
        1. Similar descriptions (>80% similarity)
        2. Similar timing (within 1 hour of video time)
        3. Overlapping entities
        """
        groups = []
        
        for event in events:
            added_to_group = False
            
            for group in groups:
                representative = group[0]
                
                # Check if this event belongs to this group
                if self._are_same_event(event, representative):
                    group.append(event)
                    added_to_group = True
                    break
            
            if not added_to_group:
                # Start a new group
                groups.append([event])
        
        return groups
    
    def _are_same_event(self, event1: TemporalEvent, event2: TemporalEvent) -> bool:
        """
        Determine if two events represent the same real-world occurrence.
        
        This is the core logic that fixes the duplicate crisis.
        """
        # 1. Description similarity check
        description_similarity = self._calculate_similarity(
            event1.description, 
            event2.description
        )
        
        if description_similarity < self.similarity_threshold:
            return False
        
        # 2. Temporal proximity check (using video timestamps)
        if event1.video_timestamps and event2.video_timestamps:
            # Check if events occur around the same time in any shared video
            shared_videos = set(event1.video_timestamps.keys()) & set(event2.video_timestamps.keys())
            
            for video_id in shared_videos:
                time_diff = abs(
                    event1.video_timestamps[video_id] - 
                    event2.video_timestamps[video_id]
                )
                if time_diff <= self.time_proximity_threshold:
                    # Same timing in shared video - likely same event
                    logger.debug(f"Temporal match: {time_diff:.0f}s difference in video {video_id}")
                    return True
        
        # 3. Entity overlap check
        entities1 = set(event1.involved_entities)
        entities2 = set(event2.involved_entities)
        
        if entities1 and entities2:
            # Calculate Jaccard similarity of entity sets
            intersection = len(entities1 & entities2)
            union = len(entities1 | entities2)
            entity_similarity = intersection / union if union > 0 else 0
            
            # If entities significantly overlap and descriptions are similar, it's the same event
            if entity_similarity > 0.5:
                logger.debug(f"Entity overlap match: {entity_similarity:.2f} similarity")
                return True
        
        return False
    
    def _merge_event_group(self, events: List[TemporalEvent]) -> TemporalEvent:
        """
        Merge multiple events representing the same occurrence into one consolidated event.
        
        This implements the fix: consolidate ALL entities instead of creating separate events.
        """
        if len(events) == 1:
            return events[0]
        
        logger.debug(f"Merging {len(events)} duplicate events")
        
        # Use the event with the highest confidence as the base
        base_event = max(events, key=lambda e: e.confidence)
        
        # Consolidate all entities from all events (the key fix!)
        all_entities = set()
        for event in events:
            all_entities.update(event.involved_entities)
        
        # Consolidate source videos and timestamps
        all_source_videos = set()
        consolidated_timestamps = {}
        
        for event in events:
            all_source_videos.update(event.source_videos)
            consolidated_timestamps.update(event.video_timestamps)
        
        # Choose the best date (highest confidence)
        best_date_event = max(events, key=lambda e: e.date_confidence)
        
        # Build merged description that mentions all key aspects
        merged_description = self._merge_descriptions([e.description for e in events])
        
        # Generate new content hash for the merged event
        content_for_hash = f"{merged_description}_{best_date_event.date.isoformat()}"
        new_content_hash = hashlib.md5(content_for_hash.encode()).hexdigest()
        
        # Create consolidated event
        merged_event = TemporalEvent(
            event_id=f"merged_{base_event.event_id}",
            content_hash=new_content_hash,
            
            # Use best date information
            date=best_date_event.date,
            date_precision=best_date_event.date_precision,
            date_confidence=best_date_event.date_confidence,
            extracted_date_text=best_date_event.extracted_date_text,
            date_source=best_date_event.date_source,
            
            # Enhanced event information
            description=merged_description,
            event_type=base_event.event_type,
            involved_entities=sorted(list(all_entities)),  # ALL entities consolidated!
            
            # Enhanced source information
            source_videos=sorted(list(all_source_videos)),
            video_timestamps=consolidated_timestamps,
            chapter_context=base_event.chapter_context,
            extraction_method=f"merged_from_{len(events)}_duplicates",
            
            # Quality metrics (average confidence)
            confidence=sum(e.confidence for e in events) / len(events),
            validation_status=base_event.validation_status,
            validation_notes=f"Merged from {len(events)} duplicate events"
        )
        
        logger.debug(f"✅ Merged event created: {len(all_entities)} entities, {len(all_source_videos)} videos")
        
        return merged_event
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text descriptions."""
        if not text1 or not text2:
            return 0.0
        
        # Use SequenceMatcher for text similarity
        matcher = SequenceMatcher(None, text1.lower(), text2.lower())
        return matcher.ratio()
    
    def _merge_descriptions(self, descriptions: List[str]) -> str:
        """
        Merge multiple descriptions into one comprehensive description.
        
        Takes the longest description as base and enhances with unique elements from others.
        """
        if not descriptions:
            return ""
        
        if len(descriptions) == 1:
            return descriptions[0]
        
        # Use the longest description as base
        base_description = max(descriptions, key=len)
        
        # For now, just return the best description
        # Future enhancement: intelligently merge unique elements
        return base_description
    
    def get_deduplication_stats(self, original_events: List[TemporalEvent], 
                              deduplicated_events: List[TemporalEvent]) -> Dict[str, int]:
        """Get statistics about the deduplication process."""
        return {
            "original_count": len(original_events),
            "deduplicated_count": len(deduplicated_events),
            "duplicates_removed": len(original_events) - len(deduplicated_events),
            "deduplication_rate": round(
                (len(original_events) - len(deduplicated_events)) / len(original_events) * 100, 1
            ) if original_events else 0
        } 