"""Video Intelligence Models for Chimera Integration."""

from __future__ import annotations
from typing import List, Dict, Any, Optional, Union, TYPE_CHECKING
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum

class VideoChapter(BaseModel):
    """Video chapter/section with timing."""
    start_time: int = Field(..., description="Start time in seconds")
    end_time: int = Field(..., description="End time in seconds")
    title: str = Field(..., description="Chapter title")
    summary: Optional[str] = Field(None, description="Chapter summary")


class TranscriptSegment(BaseModel):
    """Individual transcript segment with timing information."""
    text: str = Field(..., description="Segment text")
    start_time: float = Field(..., description="Start time in seconds")
    end_time: float = Field(..., description="End time in seconds") 
    speaker: Optional[str] = Field(None, description="Speaker identifier")


class TemporalIntelligence(BaseModel):
    """Enhanced temporal intelligence extracted from video content."""
    timeline_events: List[Dict[str, Any]] = Field(default_factory=list, description="Timeline events with timestamps")
    visual_temporal_cues: List[Dict[str, Any]] = Field(default_factory=list, description="Visual temporal cues from video")
    visual_dates: List[Dict[str, Any]] = Field(default_factory=list, description="Dates extracted from visual content")
    temporal_patterns: List[Dict[str, Any]] = Field(default_factory=list, description="Temporal patterns and sequences")


class KeyPoint(BaseModel):
    """Important point from video with temporal context."""
    timestamp: float = Field(..., description="Seconds from start")  # Changed from int to float
    text: str = Field(..., description="Key point text")
    importance: float = Field(ge=0, le=1, description="Importance score 0-1")
    context: Optional[str] = Field(None, description="Surrounding context")


class Entity(BaseModel):
    """Represents a single extracted entity."""

    entity: str
    type: str
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    confidence: Optional[float] = None
    source: Optional[str] = None


class EntityContext(BaseModel):
    """Context window for an entity mention."""

    text: str = Field(..., description="Surrounding text (±50 chars)")
    timestamp: str = Field(..., description="When mentioned (HH:MM:SS)")
    confidence: float = Field(..., description="Context-specific confidence")
    speaker: Optional[str] = Field(None, description="Who mentioned it")
    visual_present: bool = Field(False, description="Entity visible on screen")


class TemporalMention(BaseModel):
    """When and how an entity is mentioned."""

    timestamp: str = Field(..., description="HH:MM:SS format")
    duration: float = Field(..., description="How long discussed (seconds)")
    context_type: str = Field(..., description="spoken, visual, or both")


class EnhancedEntity(Entity):
    """Enhanced entity with confidence and attribution."""

    extraction_sources: List[str] = Field(..., description="Which methods found this")
    mention_count: int = Field(..., description="Total occurrences in video")
    context_windows: List[EntityContext] = Field(default_factory=list)
    aliases: List[str] = Field(default_factory=list)
    canonical_form: str = Field(..., description="Normalized primary form")
    source_confidence: Dict[str, float] = Field(default_factory=dict)
    temporal_distribution: List[TemporalMention] = Field(default_factory=list)


class RelationshipEvidence(BaseModel):
    """Evidence supporting a relationship - Phase 2 enhancement."""
    direct_quote: str = Field(..., description="Direct quote supporting the relationship")
    timestamp: str = Field(..., description="When evidence occurs (HH:MM:SS)")
    speaker: Optional[str] = Field(None, description="Who provided the evidence")
    visual_context: Optional[str] = Field(None, description="Visual context description")
    confidence: float = Field(default=0.8, description="Confidence in this evidence")
    context_window: str = Field(default="", description="Surrounding context")
    evidence_type: str = Field(default="spoken", description="Type: spoken, visual, document")


class Relationship(BaseModel):
    """Represents a relationship between two entities."""
    subject: str
    predicate: str
    object: str
    confidence: Optional[float] = None
    source: Optional[str] = None
    
    # Phase 2: Evidence Chain Support (optional for backward compatibility)
    evidence_chain: List[RelationshipEvidence] = Field(default_factory=list, description="Supporting evidence")
    supporting_mentions: int = Field(default=0, description="Number of supporting mentions")
    contradictions: List[str] = Field(default_factory=list, description="Contradictory statements")
    visual_correlation: bool = Field(default=False, description="Has visual correlation")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class VideoTranscript(BaseModel):
    """Represents the transcript of a video, including text and segments."""
    full_text: str
    segments: List[Dict[str, Any]]
    language: Optional[str] = None
    raw_transcript: Optional[Any] = None
    confidence: Optional[float] = Field(default=0.9, description="Confidence in transcript accuracy")


class VideoMetadata(BaseModel):
    """YouTube video metadata."""
    video_id: str
    url: Optional[str] = None
    title: Optional[str] = None
    channel: str
    channel_id: str
    published_at: datetime
    duration: int
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    comment_count: Optional[int] = None
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    entities: List[EnhancedEntity] = Field(
        default_factory=list, description="List of enhanced extracted entities."
    )
    relationships: List[Relationship] = Field(
        default_factory=list, description="List of extracted relationships."
    )


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


class VideoIntelligence(BaseModel):
    """Represents the complete set of intelligence extracted from a video."""
    metadata: VideoMetadata
    transcript: "VideoTranscript"
    entities: List[EnhancedEntity] = Field(
        default_factory=list, description="List of enhanced extracted entities."
    )
    relationships: List[Relationship] = Field(
        default_factory=list, description="List of extracted relationships."
    )
    key_points: List["KeyPoint"] = Field(default_factory=list)
    topics: List[Topic] = Field(default_factory=list, description="Topics identified in the video")
    summary: str = Field(..., description="Executive summary")
    sentiment: Optional[float] = Field(default=None, description="Overall sentiment score (-1 to 1)")
    knowledge_graph: Optional[Dict[str, Any]] = None
    dates: List[Dict[str, Any]] = Field(default_factory=list)
    temporal_references: List[TemporalReference] = Field(default_factory=list, description="Resolved temporal references from video content")
    processing_stats: Dict[str, Any] = Field(default_factory=dict, description="Processing statistics and metadata")
    processing_cost: float = Field(default=0.0, description="Total processing cost in USD")
    processing_time: float = Field(default=0.0, description="Total processing time in seconds")
    timeline_v2: Optional[Dict[str, Any]] = Field(default=None, description="Timeline Intelligence v2.0 data")
    # ... other fields


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
    """Represents a date extracted from text or visual content by Gemini."""
    original_text: str = Field(..., description="The original text the date was extracted from")
    normalized_date: str = Field(..., description="Normalized date in ISO format (YYYY-MM-DD)")
    precision: str = Field(..., description="Precision level: exact, day, month, year, approximate, unknown")
    confidence: float = Field(default=0.8, description="The model's confidence in the extraction")
    context: str = Field(default="", description="Context in which the date was mentioned")
    source: str = Field(..., description="Source of date: transcript, visual, or both")
    visual_description: str = Field(default="", description="Description if date was visual (e.g., 'lower third')")
    timestamp: float = Field(default=0.0, description="Timestamp in video when date was shown/mentioned")
    
    # Additional fields for compatibility
    parsed_date: Optional[datetime] = Field(None, description="Parsed datetime object (for backward compatibility)")
    date_source: Optional[str] = Field(None, description="Additional source info")


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
    
    information_flow_map: Optional['InformationFlowMap'] = None
    
    # Processing metadata
    processing_stats: Dict[str, Any] = Field(default_factory=dict)
    total_processing_cost: float = Field(default=0.0)
    total_processing_time: float = Field(default=0.0)
    
    # Quality metrics
    entity_resolution_quality: float = Field(default=0.0, description="Quality of cross-video entity resolution")
    narrative_coherence: float = Field(default=0.0, description="How coherent the narrative is")
    information_completeness: float = Field(default=0.0, description="How complete the information is")
    consolidated_timeline: Optional[List[Any]] = Field(default=None, description="Consolidated timeline across videos")


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


class TemporalReference(BaseModel):
    """A resolved temporal reference from video content."""
    reference_text: str = Field(..., description="Original temporal reference text")
    resolved_date: str = Field(..., description="Resolved date in YYYY-MM-DD format")
    confidence: float = Field(..., description="Confidence in resolution")
    resolution_method: str = Field(..., description="Method used for resolution")
    context: str = Field(..., description="Immediate context")
    original_context: str = Field("", description="Original surrounding text")
    date_source: str = Field("", description="Source of the date (content/publication)")
    content_vs_publication_delta: int = Field(0, description="Days between content and publication")


class ConceptMaturityLevel(str, Enum):
    """Maturity levels for concept evolution."""
    MENTIONED = "mentioned"
    INTRODUCED = "introduced"
    DEFINED = "defined"
    EXPLAINED = "explained"
    EXPLORED = "explored"
    ANALYZED = "analyzed"
    SYNTHESIZED = "synthesized"
    EVOLVED = "evolved"
    CRITICIZED = "criticized"


class ConceptNode(BaseModel):
    """A single concept or idea identified in a video."""
    node_id: str
    concept_name: str
    video_id: str
    video_title: str
    timestamp: int = 0
    maturity_level: str = ConceptMaturityLevel.MENTIONED
    context: str = ''
    explanation_depth: float = 0.0
    key_points: List[str] = Field(default_factory=list)
    related_entities: List[str] = Field(default_factory=list)
    sentiment: float = 0.0
    confidence: float = 0.0
    information_density: float = 0.0
    video_sequence_position: int = 0

class InformationFlow(BaseModel):
    """The flow of information between two concept nodes."""
    flow_id: str
    source_node: ConceptNode
    target_node: ConceptNode
    flow_type: str
    information_transferred: str
    transformation_type: str
    flow_quality: float
    coherence_score: float
    temporal_gap: float
    bridge_entities: List[str]
    supporting_evidence: List[str]

class ConceptDependency(BaseModel):
    """A dependency between two concepts."""
    dependent_concept: str
    prerequisite_concept: str
    dependency_type: str
    strength: float

class ConceptEvolutionPath(BaseModel):
    """The evolution of a single concept across multiple videos."""
    concept_name: str
    initial_maturity: str
    final_maturity: str
    progression_steps: List[Dict[str, Any]]
    key_dependencies: List[ConceptDependency]
    evolution_nodes: List[ConceptNode] = Field(default_factory=list, description="Nodes in this evolution path")
    evolution_coherence: float = Field(default=0.0, description="Coherence score of the evolution path")
    completeness_score: float = Field(default=0.0, description="Completeness score of the evolution path")
    understanding_depth: float = Field(default=0.0, description="Depth of understanding achieved")
    evolution_summary: Optional[str] = Field(default=None, description="Summary of the evolution")
    key_transformations: List[str] = Field(default_factory=list, description="Key transformations in the evolution")

class ConceptCluster(BaseModel):
    """A cluster of related concepts."""
    cluster_name: str
    core_concepts: List[str]
    cluster_evolution: Optional[str] = None
    coherence_score: float

class InformationFlowMap(BaseModel):
    """A map of how information and concepts evolve across a collection."""
    map_id: str
    collection_id: str
    collection_title: str
    created_at: datetime = Field(default_factory=datetime.now)
    concept_nodes: List[ConceptNode]
    information_flows: List[InformationFlow]
    concept_dependencies: List[ConceptDependency]
    evolution_paths: List[ConceptEvolutionPath]
    concept_clusters: List[ConceptCluster]
    primary_information_pathways: List[str]
    knowledge_bottlenecks: List[str]
    information_gaps: List[str]
    flow_summary: str
    learning_progression: str
    concept_complexity: str
    strategic_insights: List[str]
    overall_coherence: float
    pedagogical_quality: float
    information_density: float
    total_concepts: int
    total_flows: int
    synthesis_quality: str


# Rebuild models to resolve forward references
VideoIntelligence.model_rebuild()
VideoMetadata.model_rebuild()
MultiVideoIntelligence.model_rebuild()
MultiVideoIntelligence.model_rebuild(force=True)