"""Video Intelligence Models for Chimera Integration."""

from typing import List, Dict, Any, Optional, Union, TYPE_CHECKING
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum

if TYPE_CHECKING:
    from typing import ForwardRef


class VideoChapter(BaseModel):
    """Video chapter/section with timing."""
    start_time: int = Field(..., description="Start time in seconds")
    end_time: int = Field(..., description="End time in seconds")
    title: str = Field(..., description="Chapter title")
    summary: Optional[str] = Field(None, description="Chapter summary")


class KeyPoint(BaseModel):
    """Important point from video with temporal context."""
    timestamp: int = Field(..., description="Seconds from start")
    text: str = Field(..., description="Key point text")
    importance: float = Field(..., ge=0, le=1, description="Importance score 0-1")
    context: Optional[str] = Field(None, description="Surrounding context")


class Entity(BaseModel):
    """Entity extracted from video - compatible with Chimera's entity model."""
    name: str
    type: str  # PERSON, ORGANIZATION, LOCATION, EVENT, CONCEPT, TECHNOLOGY
    properties: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(1.0, ge=0, le=1)
    timestamp: Optional[int] = Field(None, description="When mentioned in video")


class VideoTranscript(BaseModel):
    """Raw transcription output from Gemini."""
    full_text: str
    segments: List[Dict[str, Any]] = Field(default_factory=list)
    language: str = Field("en", description="Detected language")
    confidence: float = Field(1.0, ge=0, le=1)


class VideoMetadata(BaseModel):
    """YouTube video metadata."""
    video_id: str
    title: str
    channel: str
    channel_id: str
    duration: float  # seconds
    url: str
    published_at: datetime
    view_count: Optional[int] = None
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class Topic(BaseModel):
    """A topic identified in the video."""
    name: str
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)


class Segment(BaseModel):
    """A segment of the video transcript with timing."""
    start_time: float = Field(ge=0.0)
    end_time: float = Field(ge=0.0)
    text: str
    speaker: Optional[str] = None


class Relationship(BaseModel):
    """A relationship between entities extracted from the video."""
    subject: str
    predicate: str
    object: str
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    context: Optional[str] = None


# NEW: Multi-Video Intelligence Models

class VideoCollectionType(str, Enum):
    """Types of video collections for multi-video intelligence."""
    SERIES = "series"
    TOPIC_RESEARCH = "topic_research"
    CHANNEL_ANALYSIS = "channel_analysis"
    CROSS_SOURCE_TOPIC = "cross_source_topic"
    TEMPORAL_SEQUENCE = "temporal_sequence"
    CUSTOM_COLLECTION = "custom_collection"


class SeriesMetadata(BaseModel):
    """Metadata for video series detection and organization."""
    series_id: str = Field(..., description="Unique identifier for the series")
    series_title: str = Field(..., description="Human-readable series title")
    part_number: Optional[int] = Field(None, description="Part number in series")
    total_parts: Optional[int] = Field(None, description="Total parts if known")
    series_pattern: Optional[str] = Field(None, description="Detected naming pattern")
    confidence: float = Field(default=0.9, description="Confidence in series detection")


class CrossVideoEntity(BaseModel):
    """Entity that appears across multiple videos with aggregated information."""
    name: str
    type: str
    canonical_name: str = Field(..., description="Normalized canonical name")
    aliases: List[str] = Field(default_factory=list, description="All name variations found")
    video_appearances: List[str] = Field(default_factory=list, description="Video IDs where entity appears")
    aggregated_confidence: float = Field(..., description="Confidence aggregated across videos")
    first_mentioned: Optional[datetime] = Field(None, description="First appearance timestamp")
    last_mentioned: Optional[datetime] = Field(None, description="Last appearance timestamp")
    mention_count: int = Field(default=1, description="Total mentions across all videos")
    properties: Dict[str, Any] = Field(default_factory=dict)
    source_videos: List[Dict[str, Any]] = Field(default_factory=list, description="Per-video source info")


class CrossVideoRelationship(BaseModel):
    """Relationship that spans or is confirmed across multiple videos."""
    subject: str
    predicate: str
    object: str
    confidence: float = Field(..., description="Aggregated confidence across videos")
    video_sources: List[str] = Field(default_factory=list, description="Videos where relationship appears")
    first_mentioned: Optional[datetime] = Field(None)
    mention_count: int = Field(default=1)
    context_examples: List[str] = Field(default_factory=list, description="Context from different videos")
    properties: Dict[str, Any] = Field(default_factory=dict)


class NarrativeSegment(BaseModel):
    """A segment of narrative flow across videos in a series."""
    segment_id: str
    title: str
    video_id: str
    start_time: int
    end_time: int
    summary: str
    key_entities: List[str] = Field(default_factory=list)
    key_relationships: List[str] = Field(default_factory=list)
    narrative_importance: float = Field(default=0.5, description="Importance to overall narrative")
    connects_to: List[str] = Field(default_factory=list, description="Connected segment IDs")


class TopicEvolution(BaseModel):
    """How a topic evolves across multiple videos."""
    topic_name: str
    video_sequence: List[str] = Field(default_factory=list, description="Videos in chronological order")
    evolution_summary: str = Field(..., description="How the topic develops")
    key_milestones: List[Dict[str, Any]] = Field(default_factory=list)
    sentiment_evolution: List[float] = Field(default_factory=list, description="Sentiment over time")
    entity_changes: Dict[str, List[str]] = Field(default_factory=dict, description="How entities change")


class MultiVideoIntelligence(BaseModel):
    """Intelligence extracted from multiple related videos."""
    
    # Collection metadata
    collection_id: str = Field(..., description="Unique identifier for this collection")
    collection_type: VideoCollectionType
    collection_title: str = Field(..., description="Human-readable collection title")
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Video references
    video_ids: List[str] = Field(default_factory=list, description="Individual video IDs in collection")
    videos: List['VideoIntelligence'] = Field(default_factory=list, description="Full video intelligence objects")
    
    # Series-specific metadata (if applicable)
    series_metadata: Optional[SeriesMetadata] = None
    narrative_flow: List[NarrativeSegment] = Field(default_factory=list)
    
    # Cross-video intelligence
    unified_entities: List[CrossVideoEntity] = Field(default_factory=list)
    cross_video_relationships: List[CrossVideoRelationship] = Field(default_factory=list)
    unified_topics: List[Topic] = Field(default_factory=list)
    topic_evolution: List[TopicEvolution] = Field(default_factory=list)
    
    # Aggregated analysis
    collection_summary: str = Field(..., description="Summary of the entire collection")
    key_insights: List[str] = Field(default_factory=list, description="Cross-video insights")
    unified_knowledge_graph: Optional[Dict[str, Any]] = None
    
    # Processing metadata
    processing_stats: Dict[str, Any] = Field(default_factory=dict)
    total_processing_cost: float = Field(default=0.0)
    total_processing_time: float = Field(default=0.0)
    
    # Quality metrics
    entity_resolution_quality: float = Field(default=0.0, description="Quality of cross-video entity resolution")
    narrative_coherence: float = Field(default=0.0, description="How coherent the narrative is")
    information_completeness: float = Field(default=0.0, description="How complete the information is")


class SeriesDetectionResult(BaseModel):
    """Result of automatic series detection."""
    is_series: bool
    confidence: float
    suggested_grouping: List[List[str]] = Field(default_factory=list, description="Suggested video groupings")
    detection_method: str = Field(..., description="How the series was detected")
    series_patterns: List[str] = Field(default_factory=list, description="Detected patterns")
    user_confirmation_needed: bool = Field(default=True)


class VideoSimilarity(BaseModel):
    """Similarity analysis between two videos."""
    video1_id: str
    video2_id: str
    overall_similarity: float = Field(ge=0.0, le=1.0)
    topic_similarity: float = Field(ge=0.0, le=1.0)
    entity_overlap: float = Field(ge=0.0, le=1.0)
    temporal_proximity: float = Field(ge=0.0, le=1.0)
    channel_match: bool = Field(default=False)
    title_similarity: float = Field(ge=0.0, le=1.0)
    shared_entities: List[str] = Field(default_factory=list)
    shared_topics: List[str] = Field(default_factory=list)


# Enhanced VideoIntelligence with multi-video awareness
class VideoIntelligence(BaseModel):
    """Complete video analysis output compatible with Chimera."""
    
    # Metadata
    metadata: VideoMetadata
    
    # Transcript data
    transcript: VideoTranscript
    chapters: List[VideoChapter] = Field(default_factory=list)
    
    # Extracted intelligence
    key_points: List[KeyPoint] = Field(default_factory=list)
    summary: str = Field(..., description="Executive summary")
    entities: List[Entity] = Field(default_factory=list)
    
    # For news monitoring
    topics: List[Topic] = Field(default_factory=list, description="Main topics discussed")
    sentiment: Optional[Dict[str, float]] = Field(None, description="Sentiment analysis")
    
    # Metrics
    confidence_score: float = Field(1.0, ge=0, le=1)
    processing_cost: float = Field(0.0, description="Cost in USD")
    processing_time: float = Field(0.0, description="Time in seconds")
    
    # Relationships and Knowledge Graph
    relationships: List[Relationship] = Field(default_factory=list)
    knowledge_graph: Optional[Dict[str, Any]] = None
    
    # Key Moments
    key_moments: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Processing Stats
    processing_stats: Dict[str, Any] = Field(default_factory=dict)
    
    # NEW: Multi-video context
    collection_context: Optional[Dict[str, Any]] = Field(None, description="Context if part of a collection")
    series_metadata: Optional[SeriesMetadata] = None
    related_videos: List[str] = Field(default_factory=list, description="IDs of related videos")
    
    def to_chimera_format(self) -> Dict[str, Any]:
        """Convert to format expected by Chimera's research agent."""
        return {
            "title": f"Video: {self.metadata.title}",
            "href": self.metadata.url,
            "body": self.summary,
            "metadata": {
                "source": "youtube",
                "video_id": self.metadata.video_id,
                "channel": self.metadata.channel,
                "duration": self.metadata.duration,
                "key_points": [kp.dict() for kp in self.key_points],
                "entities": [e.dict() for e in self.entities],
                "collection_context": self.collection_context
            }
        } 

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            HttpUrl: lambda v: str(v)
        }


# Update forward references
MultiVideoIntelligence.model_rebuild() 