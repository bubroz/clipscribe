"""Video Intelligence Models for Chimera Integration."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl


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
    duration: int  # seconds
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
                "entities": [e.dict() for e in self.entities]
            }
        } 

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            HttpUrl: lambda v: str(v)
        } 