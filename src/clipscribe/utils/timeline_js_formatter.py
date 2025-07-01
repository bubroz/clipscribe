"""TimelineJS3 Formatter for ClipScribe Timeline Intelligence v2.0.

Converts Timeline v2.0 temporal events into TimelineJS3 format for
beautiful, interactive timeline visualizations.

TimelineJS3 format reference: https://timeline.knightlab.com/docs/json-format.html
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import re
from pathlib import Path

from clipscribe.timeline.models import (
    ConsolidatedTimeline,
    TemporalEvent,
    DatePrecision,
    ExtractedDate
)
import logging

logger = logging.getLogger(__name__)


class TimelineJSFormatter:
    """Convert Timeline v2.0 data to TimelineJS3 format."""
    
    def __init__(self):
        """Initialize the formatter."""
        self.media_base_url = "https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        
    def format_timeline(
        self, 
        timeline_data: ConsolidatedTimeline,
        title: str = "Video Timeline",
        description: str = ""
    ) -> Dict[str, Any]:
        """
        Convert consolidated timeline to TimelineJS3 JSON format.
        
        Args:
            timeline_data: The Timeline v2.0 consolidated timeline
            title: Title for the timeline
            description: Description for the timeline
            
        Returns:
            Dictionary in TimelineJS3 format
        """
        logger.info(f"Converting {len(timeline_data.events)} events to TimelineJS3 format")
        
        # Build the timeline structure
        timeline_js = {
            "title": {
                "text": {
                    "headline": title,
                    "text": description or f"Timeline generated from {len(timeline_data.video_sources)} videos"
                }
            },
            "events": []
        }
        
        # Convert each temporal event
        for event in timeline_data.events:
            js_event = self._convert_event(event, timeline_data.video_sources)
            if js_event:  # Only add valid events
                timeline_js["events"].append(js_event)
                
        # Sort events by date
        timeline_js["events"].sort(key=lambda e: self._parse_date_string(e["start_date"]))
        
        logger.info(f"Successfully converted {len(timeline_js['events'])} events to TimelineJS3")
        return timeline_js
    
    def _convert_event(self, event: TemporalEvent, video_sources: List[str]) -> Optional[Dict[str, Any]]:
        """
        Convert a single temporal event to TimelineJS3 event format.
        
        Args:
            event: The temporal event to convert
            video_sources: List of source video URLs/IDs
            
        Returns:
            Dictionary representing a TimelineJS3 event or None if invalid
        """
        try:
            # Format the date based on precision
            date_dict = self._format_date(event.date, event.date_precision)
            if not date_dict:
                logger.warning(f"Could not format date for event {event.event_id}")
                return None
            
            # Build the event text
            headline = self._create_headline(event)
            text = self._create_event_text(event)
            
            # Create the event structure
            js_event = {
                "start_date": date_dict,
                "text": {
                    "headline": headline,
                    "text": text
                }
            }
            
            # Add media if available
            media = self._create_media(event, video_sources)
            if media:
                js_event["media"] = media
                
            # Add group for event type
            js_event["group"] = event.event_type.value
            
            return js_event
            
        except Exception as e:
            logger.error(f"Error converting event {event.event_id}: {e}")
            return None
    
    def _format_date(self, date: datetime, precision: DatePrecision) -> Optional[Dict[str, str]]:
        """
        Format a datetime object for TimelineJS3 based on precision.
        
        Args:
            date: The datetime to format
            precision: The precision level of the date
            
        Returns:
            Dictionary with date components or None
        """
        try:
            date_dict = {}
            
            # Always include year
            date_dict["year"] = str(date.year)
            
            # Add month if precision allows
            if precision in [DatePrecision.EXACT, DatePrecision.DAY, DatePrecision.MONTH]:
                date_dict["month"] = str(date.month)
                
            # Add day if precision allows
            if precision in [DatePrecision.EXACT, DatePrecision.DAY]:
                date_dict["day"] = str(date.day)
                
            # Add time for exact precision
            if precision == DatePrecision.EXACT:
                date_dict["hour"] = str(date.hour)
                date_dict["minute"] = str(date.minute)
                
            return date_dict
            
        except Exception as e:
            logger.error(f"Error formatting date {date}: {e}")
            return None
    
    def _create_headline(self, event: TemporalEvent) -> str:
        """
        Create a concise headline for the event.
        
        Args:
            event: The temporal event
            
        Returns:
            A headline string (max 100 chars)
        """
        # Extract key entities
        entities = event.involved_entities[:2]  # Top 2 entities
        entity_str = " & ".join(entities) if entities else "Event"
        
        # Create headline based on event type
        if event.event_type.value == "factual":
            headline = f"{entity_str}: {event.description[:60]}"
        else:
            headline = f"[{event.event_type.value.title()}] {event.description[:50]}"
            
        # Ensure max length
        if len(headline) > 100:
            headline = headline[:97] + "..."
            
        return headline
    
    def _create_event_text(self, event: TemporalEvent) -> str:
        """
        Create detailed text for the event.
        
        Args:
            event: The temporal event
            
        Returns:
            HTML-formatted text for the event
        """
        text_parts = []
        
        # Main description
        text_parts.append(f"<p>{self._escape_html(event.description)}</p>")
        
        # Add entities if present
        if event.involved_entities:
            entities_html = ", ".join(f"<strong>{self._escape_html(e)}</strong>" 
                                     for e in event.involved_entities)
            text_parts.append(f"<p><em>Entities:</em> {entities_html}</p>")
        
        # Add source information
        if event.extracted_date_text:
            text_parts.append(f"<p><em>Date reference:</em> \"{self._escape_html(event.extracted_date_text)}\"</p>")
            
        # Add confidence indicator
        confidence_level = "High" if event.confidence >= 0.8 else "Medium" if event.confidence >= 0.6 else "Low"
        text_parts.append(f"<p><small>Confidence: {confidence_level} ({event.confidence:.2f})</small></p>")
        
        # Add chapter context if available
        if event.chapter_context:
            text_parts.append(f"<p><small>Chapter: {self._escape_html(event.chapter_context)}</small></p>")
        
        return "\n".join(text_parts)
    
    def _create_media(self, event: TemporalEvent, video_sources: List[str]) -> Optional[Dict[str, str]]:
        """
        Create media object for the event.
        
        Args:
            event: The temporal event
            video_sources: List of source videos
            
        Returns:
            Media dictionary or None
        """
        # Extract video ID from first source
        if not event.source_videos:
            return None
            
        video_url = event.source_videos[0]
        video_id = self._extract_video_id(video_url)
        
        if not video_id:
            return None
            
        # Get timestamp for this video
        timestamp = event.video_timestamps.get(video_url, 0)
        
        return {
            "url": self.media_base_url.format(video_id=video_id),
            "caption": f"From video at {self._format_timestamp(timestamp)}",
            "link": f"{video_url}&t={int(timestamp)}s",
            "link_target": "_blank"
        }
    
    def _extract_video_id(self, video_url: str) -> Optional[str]:
        """Extract YouTube video ID from URL."""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
            r'([a-zA-Z0-9_-]{11})$'  # Just the ID
        ]
        
        for pattern in patterns:
            match = re.search(pattern, video_url)
            if match:
                return match.group(1)
        return None
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds to MM:SS or HH:MM:SS."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\"", "&quot;")
                .replace("'", "&#39;"))
    
    def _parse_date_string(self, date_dict: Dict[str, str]) -> str:
        """Convert date dict back to sortable string for sorting."""
        year = date_dict.get("year", "0000")
        month = date_dict.get("month", "01").zfill(2)
        day = date_dict.get("day", "01").zfill(2)
        return f"{year}-{month}-{day}"
    
    def save_timeline(self, timeline_js: Dict[str, Any], output_path: Path) -> None:
        """
        Save TimelineJS3 data to file.
        
        Args:
            timeline_js: The TimelineJS3 formatted data
            output_path: Path to save the JSON file
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(timeline_js, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved TimelineJS3 data to {output_path}")
        except Exception as e:
            logger.error(f"Error saving TimelineJS3 data: {e}")
            raise 