"""
Gemini Date Processor for Timeline Intelligence v2.0

Processes dates extracted by Gemini from both transcript and visual sources,
merging multimodal date information for enhanced temporal intelligence.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dateutil import parser
import re

from ..models import ExtractedDate
from .models import TemporalEvent

logger = logging.getLogger(__name__)


class GeminiDateProcessor:
    """Process dates extracted by Gemini from transcript and visual cues."""
    
    def __init__(self, video_publish_date: Optional[datetime] = None):
        """
        Initialize the date processor.
        
        Args:
            video_publish_date: Publication date for resolving relative dates
        """
        self.video_publish_date = video_publish_date or datetime.now()
        
    def merge_multimodal_dates(
        self, 
        transcript_dates: List[Dict],
        visual_dates: List[Dict],
        video_metadata: Dict
    ) -> List[ExtractedDate]:
        """
        Merge dates from transcript and visual sources.
        
        Strategy:
        1. Deduplicate dates that appear in both sources
        2. Boost confidence when dates appear in multiple sources
        3. Resolve conflicts (visual usually more accurate)
        4. Convert relative dates using video publish date
        
        Args:
            transcript_dates: Dates extracted from combined analysis
            visual_dates: Dates extracted from visual temporal cues
            video_metadata: Video metadata including publish date
            
        Returns:
            List of merged and processed ExtractedDate objects
        """
        logger.info(f"Merging {len(transcript_dates)} transcript dates with {len(visual_dates)} visual dates")
        
        # Update video publish date if available
        if video_metadata.get('publish_date'):
            self.video_publish_date = self._parse_date(video_metadata['publish_date'])
        
        merged_dates = {}
        
        # Process transcript dates
        for date in transcript_dates:
            key = self._generate_date_key(date)
            extracted = self._convert_to_extracted_date(date, source="transcript")
            
            if key in merged_dates:
                # Boost confidence if already seen
                merged_dates[key].confidence = min(1.0, merged_dates[key].confidence + 0.1)
                merged_dates[key].source = "both"
            else:
                merged_dates[key] = extracted
        
        # Process visual dates (higher priority)
        for date in visual_dates:
            # Convert visual date format
            visual_dict = {
                'original_text': date.get('date_text', ''),
                'normalized_date': date.get('normalized_date', ''),
                'precision': self._infer_precision(date.get('date_text', '')),
                'confidence': date.get('confidence', 0.9),
                'timestamp': date.get('timestamp', 0),
                'visual_description': date.get('screen_location', ''),
                'source': 'visual'
            }
            
            key = self._generate_date_key(visual_dict)
            extracted = self._convert_to_extracted_date(visual_dict, source="visual")
            
            if key in merged_dates:
                # Visual dates override transcript dates for same date
                if merged_dates[key].source == "transcript":
                    logger.debug(f"Visual date overriding transcript date: {key}")
                    extracted.confidence = min(1.0, extracted.confidence + 0.15)
                    extracted.source = "both"
                    merged_dates[key] = extracted
                else:
                    # Both visual - boost confidence
                    merged_dates[key].confidence = min(1.0, merged_dates[key].confidence + 0.1)
            else:
                merged_dates[key] = extracted
        
        # Convert to list and sort by timestamp
        result = list(merged_dates.values())
        result.sort(key=lambda x: x.timestamp)
        
        logger.info(f"Merged into {len(result)} unique dates")
        
        # Log source distribution
        source_counts = {"transcript": 0, "visual": 0, "both": 0}
        for date in result:
            source_counts[date.source] += 1
        logger.info(f"Date sources: {source_counts}")
        
        return result
    
    def associate_dates_with_events(
        self,
        temporal_events: List[TemporalEvent],
        extracted_dates: List[ExtractedDate],
        window_seconds: float = 30.0
    ) -> List[TemporalEvent]:
        """
        Smart association of dates with temporal events.
        
        Strategy:
        1. Match by temporal proximity (±window_seconds)
        2. Match by entity mentions
        3. Match by contextual similarity
        4. Fall back to nearest date
        
        Args:
            temporal_events: Events to associate dates with
            extracted_dates: Dates extracted from content
            window_seconds: Time window for proximity matching
            
        Returns:
            Temporal events with associated dates
        """
        logger.info(f"Associating {len(extracted_dates)} dates with {len(temporal_events)} events")
        
        dates_used = 0
        
        for event in temporal_events:
            # Skip if event already has a good date (not default/pending)
            if hasattr(event, 'date_source') and event.date_source != "pending_extraction":
                continue
            
            # Find best matching date
            best_date = self._find_best_date_for_event(
                event, extracted_dates, window_seconds
            )
            
            if best_date:
                # Update event date fields
                try:
                    # Parse the normalized date to datetime
                    from dateutil import parser
                    event.date = parser.parse(best_date.normalized_date)
                except:
                    logger.warning(f"Failed to parse date: {best_date.normalized_date}")
                    continue
                    
                event.date_confidence = best_date.confidence
                event.date_source = best_date.source
                event.extracted_date_text = best_date.original_text
                dates_used += 1
                
                # Get video timestamp for logging
                video_timestamp = list(event.video_timestamps.values())[0] if event.video_timestamps else 0
                logger.debug(f"Associated date {best_date.normalized_date} with event at {video_timestamp}s")
        
        logger.info(f"Successfully associated {dates_used} dates with events")
        return temporal_events
    
    def _find_best_date_for_event(
        self,
        event: TemporalEvent,
        dates: List[ExtractedDate],
        window_seconds: float
    ) -> Optional[ExtractedDate]:
        """Find the best matching date for an event."""
        candidates = []
        
        # Get event timestamp from first video
        event_timestamp = list(event.video_timestamps.values())[0] if event.video_timestamps else 0
        
        for date in dates:
            # Calculate proximity score
            time_diff = abs(event_timestamp - date.timestamp)
            if time_diff <= window_seconds:
                proximity_score = 1.0 - (time_diff / window_seconds)
            else:
                proximity_score = 0.1 / (1 + time_diff / window_seconds)
            
            # Calculate entity overlap score
            entity_score = self._calculate_entity_overlap(event, date)
            
            # Calculate context similarity score
            context_score = self._calculate_context_similarity(event, date)
            
            # Combined score
            total_score = (
                proximity_score * 0.4 +
                entity_score * 0.3 +
                context_score * 0.2 +
                date.confidence * 0.1
            )
            
            # Boost visual dates
            if date.source in ["visual", "both"]:
                total_score *= 1.2
            
            candidates.append((date, total_score))
        
        # Sort by score and return best
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        if candidates and candidates[0][1] > 0.3:  # Minimum threshold
            return candidates[0][0]
        
        return None
    
    def _calculate_entity_overlap(self, event: TemporalEvent, date: ExtractedDate) -> float:
        """Calculate overlap between event entities and date context."""
        if not event.involved_entities or not date.context:
            return 0.0
        
        event_entities = set(e.lower() for e in event.involved_entities)
        date_context = date.context.lower()
        
        overlap_count = sum(1 for entity in event_entities if entity in date_context)
        
        return min(1.0, overlap_count / len(event_entities))
    
    def _calculate_context_similarity(self, event: TemporalEvent, date: ExtractedDate) -> float:
        """Calculate contextual similarity between event and date."""
        if not date.context:
            return 0.0
        
        # Simple keyword overlap for now
        event_keywords = set(event.description.lower().split())
        date_keywords = set(date.context.lower().split())
        
        if not event_keywords or not date_keywords:
            return 0.0
        
        intersection = event_keywords & date_keywords
        union = event_keywords | date_keywords
        
        return len(intersection) / len(union)
    
    def _generate_date_key(self, date_dict: Dict) -> str:
        """Generate a unique key for date deduplication."""
        normalized = date_dict.get('normalized_date', '')
        if normalized:
            return normalized
        
        # Fall back to original text
        return date_dict.get('original_text', '').lower().strip()
    
    def _convert_to_extracted_date(self, date_dict: Dict, source: str) -> ExtractedDate:
        """Convert dictionary to ExtractedDate object."""
        # Resolve relative dates
        normalized_date = date_dict.get('normalized_date', '')
        if not normalized_date and date_dict.get('original_text'):
            normalized_date = self._resolve_relative_date(date_dict['original_text'])
        
        return ExtractedDate(
            original_text=date_dict.get('original_text', ''),
            normalized_date=normalized_date or "Unknown",
            precision=date_dict.get('precision', 'unknown'),
            confidence=date_dict.get('confidence', 0.5),
            context=date_dict.get('context', ''),
            source=date_dict.get('source', source),
            visual_description=date_dict.get('visual_description', ''),
            timestamp=date_dict.get('timestamp', 0)
        )
    
    def _resolve_relative_date(self, text: str) -> str:
        """Resolve relative dates like 'last year' to actual dates."""
        text_lower = text.lower()
        
        # Simple relative date patterns
        patterns = {
            r'last year': lambda: (self.video_publish_date - timedelta(days=365)).strftime('%Y'),
            r'(\d+) years? ago': lambda m: (self.video_publish_date - timedelta(days=365*int(m.group(1)))).strftime('%Y'),
            r'last month': lambda: (self.video_publish_date - timedelta(days=30)).strftime('%Y-%m'),
            r'(\d+) months? ago': lambda m: (self.video_publish_date - timedelta(days=30*int(m.group(1)))).strftime('%Y-%m'),
            r'yesterday': lambda: (self.video_publish_date - timedelta(days=1)).strftime('%Y-%m-%d'),
            r'(\d+) days? ago': lambda m: (self.video_publish_date - timedelta(days=int(m.group(1)))).strftime('%Y-%m-%d'),
        }
        
        for pattern, resolver in patterns.items():
            match = re.search(pattern, text_lower)
            if match:
                try:
                    if match.groups():
                        return resolver(match)
                    else:
                        return resolver()
                except:
                    pass
        
        # Try parsing with dateutil
        try:
            parsed = parser.parse(text, fuzzy=True, default=self.video_publish_date)
            return parsed.strftime('%Y-%m-%d')
        except:
            return ""
    
    def _infer_precision(self, date_text: str) -> str:
        """Infer precision level from date text."""
        if re.search(r'\d{4}-\d{2}-\d{2}', date_text):
            return "day"
        elif re.search(r'\d{4}-\d{2}', date_text):
            return "month"
        elif re.search(r'\d{4}', date_text):
            return "year"
        elif any(word in date_text.lower() for word in ['early', 'late', 'mid', 'around', 'approximately']):
            return "approximate"
        else:
            return "unknown"
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse a date string to datetime."""
        try:
            return parser.parse(date_str)
        except:
            return datetime.now() 