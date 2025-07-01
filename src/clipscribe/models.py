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
    timestamp: float = Field(..., description="Seconds from start")  # Changed from int to float
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


class ExtractedDate(BaseModel):
    """Represents a date extracted from text by an LLM."""
    parsed_date: datetime = Field(..., description="The fully resolved datetime object")
    original_text: str = Field(..., description="The original text the date was extracted from")
    confidence: float = Field(default=0.8, description="The model's confidence in the extraction")
    source: str = Field(..., description="Where the date was found (e.g., 'title', 'description', 'content')")


class TimelineEvent(BaseModel):
    """A single, timestamped event that occurred across a collection of videos."""
    event_id: str = Field(..., description="Unique identifier for the event")
    timestamp: datetime = Field(..., description="The absolute timestamp when the event occurred")
    description: str = Field(..., description="A description of the event")
    source_video_id: str = Field(..., description="The video ID where this event was identified")
    source_video_title: str = Field(..., description="The title of the source video")
    video_timestamp_seconds: int = Field(..., description="The timestamp of the event within its source video, in seconds")
    involved_entities: List[str] = Field(default_factory=list, description="Names of entities involved in this event")
    confidence: float = Field(default=0.8, description="Confidence score for the event's accuracy and relevance")
    extracted_date: Optional[ExtractedDate] = Field(None, description="Detailed info if date was extracted from text")
    date_source: str = Field("video_published_date", description="Source of the event's timestamp")


class ConsolidatedTimeline(BaseModel):
    """A chronologically sorted sequence of events synthesized from multiple videos."""
    timeline_id: str = Field(..., description="Unique identifier for this timeline")
    collection_id: str = Field(..., description="The ID of the video collection this timeline belongs to")
    events: List[TimelineEvent] = Field(default_factory=list)
    summary: Optional[str] = Field(None, description="An AI-generated summary of the entire timeline")


class EntityActivity(BaseModel):
    """A specific activity or mention of an entity in a video."""
    activity_id: str = Field(..., description="Unique identifier for this activity")
    video_id: str = Field(..., description="Source video ID")
    video_title: str = Field(..., description="Source video title") 
    timestamp: int = Field(..., description="Timestamp in video (seconds)")
    description: str = Field(..., description="Description of the activity or mention")
    context: str = Field(..., description="Surrounding context from the video")
    activity_type: str = Field(..., description="Type of activity (action, mention, quote, etc.)")
    confidence: float = Field(default=0.8, description="Confidence in this activity")
    related_entities: List[str] = Field(default_factory=list, description="Other entities involved")


class EntityQuote(BaseModel):
    """A direct quote from or about an entity."""
    quote_id: str = Field(..., description="Unique identifier for this quote")
    video_id: str = Field(..., description="Source video ID")
    timestamp: int = Field(..., description="Timestamp in video (seconds)")
    quote_text: str = Field(..., description="The actual quote text")
    speaker: Optional[str] = Field(None, description="Who said the quote (if known)")
    about_entity: bool = Field(default=False, description="True if quote is about the entity, False if by the entity")
    context: str = Field(..., description="Context surrounding the quote")
    significance: float = Field(default=0.5, description="How significant/revealing this quote is")


class EntityRelationshipSummary(BaseModel):
    """Summary of an entity's relationship with another entity across videos."""
    related_entity: str = Field(..., description="Name of the related entity")
    relationship_type: str = Field(..., description="Nature of the relationship")
    relationship_strength: float = Field(default=0.5, description="Strength of relationship (0-1)")
    examples: List[str] = Field(default_factory=list, description="Examples of their interactions")
    video_sources: List[str] = Field(default_factory=list, description="Videos where relationship appears")
    evolution_summary: Optional[str] = Field(None, description="How relationship evolved across videos")


class EntityAttributeEvolution(BaseModel):
    """How an entity's attributes or portrayal changed across videos."""
    attribute_name: str = Field(..., description="Name of the attribute (role, position, etc.)")
    initial_value: str = Field(..., description="Initial value in earliest video")
    final_value: str = Field(..., description="Final value in latest video")
    evolution_timeline: List[Dict[str, Any]] = Field(default_factory=list, description="How it changed over time")
    significance: str = Field(..., description="Why this change is significant")


# Knowledge panel models removed - functionality moved to Chimera


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
    
    # NEW: Consolidated timeline from synthesis engine
    consolidated_timeline: Optional[ConsolidatedTimeline] = None
    
    # Knowledge panels feature removed - moved to Chimera
    
    # NEW: Information Flow Maps - concept evolution tracking
    information_flow_map: Optional['InformationFlowMap'] = None
    
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
    
    # NEW: Timeline v2.0 data
    timeline_v2: Optional[Dict[str, Any]] = Field(None, description="Timeline Intelligence v2.0 data")
    
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


# NEW: Information Flow Maps Models

class ConceptMaturityLevel(str, Enum):
    """Levels of concept development and understanding."""
    MENTIONED = "mentioned"           # Basic mention or introduction
    DEFINED = "defined"              # Concept is explained or defined
    EXPLORED = "explored"            # Detailed discussion or analysis
    SYNTHESIZED = "synthesized"      # Integrated with other concepts
    CRITICIZED = "criticized"        # Evaluated or challenged
    EVOLVED = "evolved"              # Concept has changed or developed


class ConceptNode(BaseModel):
    """A concept at a specific point in time within a video collection."""
    
    node_id: str = Field(..., description="Unique identifier for this concept node")
    concept_name: str = Field(..., description="Name of the concept")
    video_id: str = Field(..., description="Video where this concept appears")
    video_title: str = Field(..., description="Title of the source video")
    timestamp: int = Field(..., description="Timestamp in video (seconds)")
    
    # Concept development
    maturity_level: ConceptMaturityLevel = Field(..., description="How developed the concept is")
    context: str = Field(..., description="Context in which concept appears")
    explanation_depth: float = Field(default=0.5, description="How deeply the concept is explained (0-1)")
    
    # Content analysis
    key_points: List[str] = Field(default_factory=list, description="Key points about this concept")
    related_entities: List[str] = Field(default_factory=list, description="Entities associated with concept")
    sentiment: float = Field(default=0.0, description="Sentiment toward concept (-1 to 1)")
    
    # Meta information
    confidence: float = Field(default=0.8, description="Confidence in concept extraction")
    information_density: float = Field(default=0.5, description="How much new information is provided")
    video_sequence_position: int = Field(..., description="Position of video in collection")


class ConceptDependency(BaseModel):
    """Dependencies between concepts showing information flow."""
    
    dependency_id: str = Field(..., description="Unique identifier for this dependency")
    prerequisite_concept: str = Field(..., description="Concept that must be understood first")
    dependent_concept: str = Field(..., description="Concept that builds on the prerequisite")
    
    # Dependency characteristics
    dependency_type: str = Field(..., description="Type of dependency (builds_on, contradicts, refines, etc.)")
    dependency_strength: float = Field(default=0.5, description="Strength of dependency (0-1)")
    
    # Evidence
    video_evidence: List[str] = Field(default_factory=list, description="Videos that demonstrate this dependency")
    textual_evidence: List[str] = Field(default_factory=list, description="Text quotes showing dependency")
    
    # Analysis
    explanation: str = Field(..., description="Why this dependency exists")
    confidence: float = Field(default=0.8, description="Confidence in dependency detection")


class InformationFlow(BaseModel):
    """A flow of information between concept nodes across videos."""
    
    flow_id: str = Field(..., description="Unique identifier for this information flow")
    source_node: ConceptNode = Field(..., description="Source concept node")
    target_node: ConceptNode = Field(..., description="Target concept node")
    
    # Flow characteristics
    flow_type: str = Field(..., description="Type of information flow (development, contradiction, synthesis)")
    information_transferred: str = Field(..., description="What information flows between concepts")
    transformation_type: str = Field(..., description="How information is transformed")
    
    # Quality metrics
    flow_quality: float = Field(default=0.5, description="Quality of information flow (0-1)")
    coherence_score: float = Field(default=0.5, description="How coherent the flow is")
    temporal_gap: int = Field(..., description="Time between concept appearances (seconds)")
    
    # Analysis
    bridge_entities: List[str] = Field(default_factory=list, description="Entities that bridge the concepts")
    supporting_evidence: List[str] = Field(default_factory=list, description="Evidence supporting this flow")


class ConceptEvolutionPath(BaseModel):
    """How a specific concept evolves across multiple videos."""
    
    path_id: str = Field(..., description="Unique identifier for this evolution path")
    concept_name: str = Field(..., description="Name of the evolving concept")
    
    # Evolution sequence
    evolution_nodes: List[ConceptNode] = Field(default_factory=list, description="Nodes in evolution order")
    maturity_progression: List[ConceptMaturityLevel] = Field(default_factory=list, description="Maturity levels over time")
    
    # Evolution analysis
    evolution_summary: str = Field(..., description="Summary of how concept evolved")
    key_transformations: List[str] = Field(default_factory=list, description="Major changes in understanding")
    breakthrough_moments: List[Dict[str, Any]] = Field(default_factory=list, description="Significant developments")
    
    # Quality metrics
    evolution_coherence: float = Field(default=0.5, description="How coherent the evolution is")
    completeness_score: float = Field(default=0.5, description="How complete the evolution is")
    understanding_depth: float = Field(default=0.5, description="Final depth of understanding")


class ConceptCluster(BaseModel):
    """A cluster of related concepts that evolve together."""
    
    cluster_id: str = Field(..., description="Unique identifier for this cluster")
    cluster_name: str = Field(..., description="Name of the concept cluster")
    core_concepts: List[str] = Field(default_factory=list, description="Main concepts in cluster")
    
    # Cluster evolution
    cluster_evolution: str = Field(..., description="How the cluster develops over time")
    internal_relationships: List[ConceptDependency] = Field(default_factory=list, description="Relationships within cluster")
    external_connections: List[str] = Field(default_factory=list, description="Connections to other clusters")
    
    # Analysis
    coherence_score: float = Field(default=0.5, description="Internal coherence of cluster")
    influence_score: float = Field(default=0.5, description="Influence on other concepts")
    completeness: float = Field(default=0.5, description="How complete the cluster understanding is")


class InformationFlowMap(BaseModel):
    """Complete map of information flow and concept evolution across a video collection."""
    
    map_id: str = Field(..., description="Unique identifier for this flow map")
    collection_id: str = Field(..., description="Video collection this map belongs to")
    collection_title: str = Field(..., description="Title of the video collection")
    
    # Core components
    concept_nodes: List[ConceptNode] = Field(default_factory=list, description="All concept nodes")
    information_flows: List[InformationFlow] = Field(default_factory=list, description="All information flows")
    concept_dependencies: List[ConceptDependency] = Field(default_factory=list, description="All concept dependencies")
    evolution_paths: List[ConceptEvolutionPath] = Field(default_factory=list, description="Concept evolution paths")
    concept_clusters: List[ConceptCluster] = Field(default_factory=list, description="Related concept clusters")
    
    # Flow analysis
    primary_information_pathways: List[str] = Field(default_factory=list, description="Main information pathways")
    knowledge_bottlenecks: List[str] = Field(default_factory=list, description="Concepts that block understanding")
    information_gaps: List[str] = Field(default_factory=list, description="Missing information or broken flows")
    
    # Map-level insights
    flow_summary: str = Field(..., description="Summary of information flow patterns")
    learning_progression: str = Field(..., description="How understanding progresses through videos")
    concept_complexity: str = Field(..., description="Analysis of concept complexity evolution")
    strategic_insights: List[str] = Field(default_factory=list, description="Strategic insights from flow analysis")
    
    # Quality metrics
    overall_coherence: float = Field(default=0.5, description="Overall coherence of information flow")
    pedagogical_quality: float = Field(default=0.5, description="How well structured for learning")
    information_density: float = Field(default=0.5, description="Information density across collection")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    total_concepts: int = Field(default=0, description="Total number of concepts tracked")
    total_flows: int = Field(default=0, description="Total number of information flows")
    synthesis_quality: str = Field(default="STANDARD", description="Quality level of synthesis") 


# Update forward references after all models are defined
MultiVideoIntelligence.model_rebuild()