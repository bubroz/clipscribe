"""Enhanced Temporal Data Models for Timeline Intelligence v2.0."""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class DatePrecision(str, Enum):
    """Precision level of extracted dates."""
    EXACT = "exact"        # Full date and time
    DAY = "day"           # Specific day
    MONTH = "month"       # Month and year
    YEAR = "year"         # Year only
    APPROXIMATE = "approximate"  # Rough timeframe


class EventType(str, Enum):
    """Type of temporal event."""
    FACTUAL = "factual"           # Confirmed fact
    CLAIMED = "claimed"           # Someone's claim
    REPORTED = "reported"         # News report
    INFERRED = "inferred"         # Inferred from context


class ValidationStatus(str, Enum):
    """Validation status of timeline event."""
    VERIFIED = "verified"         # Externally validated
    UNVERIFIED = "unverified"     # Not yet validated
    DISPUTED = "disputed"         # Conflicts found
    VALIDATED_LOCAL = "validated_local"  # Locally consistent


class TemporalEvent(BaseModel):
    """
    Represents a temporal event in Timeline Intelligence v2.0.
    
    CRITICAL FIX: This model addresses the 44-duplicate crisis by:
    - Using content hashes for deduplication
    - Consolidating entities instead of creating separate events
    - Focusing on actual temporal events, not entity mentions
    """
    # Identity (addresses duplicate crisis)
    event_id: str = Field(..., description="Unique event identifier")
    content_hash: str = Field(..., description="Hash of description + date for deduplication")
    
    # Temporal Information (addresses wrong date crisis)
    date: datetime = Field(..., description="Actual date of event (NOT video publish date)")
    date_precision: DatePrecision = Field(..., description="Precision level of date")
    date_confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in date extraction")
    extracted_date_text: str = Field(..., description="Original text that led to date")
    date_source: str = Field(..., description="Source of date (never 'video_published_date')")
    
    # Event Information
    description: str = Field(..., description="What actually happened")
    event_type: EventType = Field(..., description="Type of event")
    involved_entities: List[str] = Field(default_factory=list, description="All entities (consolidated)")
    
    # Source Information
    source_videos: List[str] = Field(default_factory=list, description="Can come from multiple videos")
    video_timestamps: Dict[str, float] = Field(default_factory=dict, description="Timestamp per video")
    chapter_context: Optional[str] = Field(None, description="Chapter where event was mentioned")
    extraction_method: str = Field(..., description="How this was extracted")
    
    # Quality Metrics
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence")
    validation_status: ValidationStatus = Field(default=ValidationStatus.UNVERIFIED)
    validation_notes: Optional[str] = Field(None, description="Validation details")


class ConsolidatedTimeline(BaseModel):
    """Enhanced timeline with cross-video temporal correlation."""
    events: List[TemporalEvent] = Field(default_factory=list)
    video_sources: List[str] = Field(default_factory=list)
    temporal_span: Optional[Dict[str, datetime]] = Field(None, description="Start and end dates")
    quality_metrics: Dict[str, Any] = Field(default_factory=dict)
    correlation_analysis: Dict[str, Any] = Field(default_factory=dict)
    chapter_correlations: List[Dict[str, Any]] = Field(default_factory=list)


class ExtractedDate(BaseModel):
    """Represents a date extracted from content with confidence."""
    date: datetime
    original_text: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    source: str  # "transcript_content", "video_title", etc.
    extraction_method: str  # "dateparser_with_chapter_context", etc.
    chapter_context: Optional[str] = None


class ChapterSegment(BaseModel):
    """Represents a video chapter with temporal context."""
    title: str
    start_time: float
    end_time: float
    content_type: str = "content"  # "content", "intro", "outro", "sponsor"
    entities_mentioned: List[str] = Field(default_factory=list)
    temporal_events: List[TemporalEvent] = Field(default_factory=list)


class TimelineQualityMetrics(BaseModel):
    """Quality metrics for timeline validation."""
    total_events: int
    deduplicated_events: int
    events_with_extracted_dates: int
    events_with_content_dates: int  # NOT video publish dates
    average_confidence: float
    date_accuracy_score: float
    chapter_utilization_rate: float


class ResearchResult(BaseModel):
    """Result from web research validation."""
    query: str
    sources_found: int
    validation_confidence: float = Field(..., ge=0.0, le=1.0)
    conflicting_information: List[str] = Field(default_factory=list)
    supporting_evidence: List[str] = Field(default_factory=list)
    research_notes: str = ""


class TimelineEnrichment(BaseModel):
    """Enhanced timeline event with research validation."""
    original_event: TemporalEvent
    research_result: Optional[ResearchResult] = None
    enriched_description: str = ""
    additional_context: List[str] = Field(default_factory=list)
    confidence_boost: float = 0.0  # Research-based confidence increase 