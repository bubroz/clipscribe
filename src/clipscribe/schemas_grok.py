"""
Pydantic schemas for Grok-4 Structured Outputs.

Following xAI best practices:
- NO min_items or min_length (prevents hallucinations)
- Clear descriptions (guide Grok's understanding)
- Let Grok decide quantity based on actual content
- Type-safe, guaranteed structure
"""

from enum import Enum
from typing import Dict, List

from pydantic import BaseModel, Field


class EntityType(str, Enum):
    """spaCy standard entity types."""

    PERSON = "PERSON"
    ORG = "ORG"
    GPE = "GPE"
    LOC = "LOC"
    EVENT = "EVENT"
    PRODUCT = "PRODUCT"
    MONEY = "MONEY"
    DATE = "DATE"
    TIME = "TIME"
    FAC = "FAC"
    NORP = "NORP"
    LANGUAGE = "LANGUAGE"
    LAW = "LAW"
    WORK_OF_ART = "WORK_OF_ART"
    CARDINAL = "CARDINAL"
    ORDINAL = "ORDINAL"
    QUANTITY = "QUANTITY"
    PERCENT = "PERCENT"


class Entity(BaseModel):
    """
    Named entity extracted from video transcript.

    Following xAI best practices:
    - Only extract if clearly present in transcript
    - Evidence quote required (prevents hallucinations)
    - Confidence reflects actual certainty
    """

    name: str = Field(description="Entity name exactly as mentioned in transcript")
    type: EntityType = Field(description="spaCy standard entity type")
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence in this extraction based on clarity in transcript"
    )
    evidence: str = Field(description="Exact quote from transcript where this entity is mentioned")


class Relationship(BaseModel):
    """
    Relationship between two entities.

    Following xAI best practices:
    - Only extract if explicitly stated in transcript
    - Subject and object must be actual entity names
    - Evidence quote prevents hallucinations
    """

    subject: str = Field(
        description="Subject entity name (must be an entity mentioned in transcript)"
    )
    predicate: str = Field(
        description="Specific action or relationship (e.g., 'announced', 'criticized', 'invested_in')"
    )
    object: str = Field(
        description="Object entity name (must be an entity mentioned in transcript)"
    )
    evidence: str = Field(description="Exact quote from transcript supporting this relationship")
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence based on clarity of relationship in transcript"
    )


class Topic(BaseModel):
    """
    Main topic or theme discussed in video.

    Following xAI best practices:
    - Topics should be specific, not generic
    - Time range shows where discussed
    - Relevance based on how central to video
    """

    name: str = Field(
        description="Specific topic name (e.g., 'Israel-Hamas Ceasefire' not just 'Politics')"
    )
    relevance: float = Field(
        ge=0.0,
        le=1.0,
        description="How central this topic is to the video (0=mentioned briefly, 1=main focus)",
    )
    time_range: str = Field(
        description="Time range where this topic is discussed (MM:SS-MM:SS format)"
    )


class KeyMoment(BaseModel):
    """
    Significant moment in video worth highlighting.

    Following xAI best practices:
    - Moments should be objectively significant
    - Exact timestamp and quote required
    - Significance based on importance to content
    """

    timestamp: str = Field(description="Exact timestamp of moment (MM:SS format, e.g., '03:45')")
    description: str = Field(description="What makes this moment significant")
    significance: float = Field(
        ge=0.0, le=1.0, description="How important this moment is (0=minor, 1=critical)"
    )
    quote: str = Field(description="Exact quote from this moment in transcript")


class Sentiment(BaseModel):
    """
    Sentiment analysis of video content.

    Following xAI best practices:
    - Overall sentiment of entire video
    - Per-topic sentiment if topics have distinct tones
    - Confidence in sentiment assessment
    """

    overall: str = Field(
        description="Overall video sentiment: 'positive', 'negative', 'neutral', or 'mixed'"
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence in overall sentiment assessment"
    )
    per_topic: Dict[str, str] = Field(
        description="Sentiment for each topic (topic_name: sentiment)"
    )


class VideoIntelligence(BaseModel):
    """
    Complete intelligence extraction from video.

    Following xAI best practices:
    - No min_items constraints (prevents hallucinations)
    - Clear descriptions guide extraction quality
    - Grok decides quantity based on actual content
    - All fields have evidence requirements
    """

    entities: List[Entity] = Field(
        description="All named entities found in transcript (people, orgs, places, events). Extract only if clearly present."
    )
    relationships: List[Relationship] = Field(
        description="All relationships between entities that are explicitly stated in transcript. Each must have supporting evidence."
    )
    topics: List[Topic] = Field(
        description="Main topics or themes discussed in video. Should be specific, not generic."
    )
    key_moments: List[KeyMoment] = Field(
        description="Significant moments worth highlighting. Only extract truly important moments."
    )
    sentiment: Sentiment = Field(
        description="Sentiment analysis of video content (overall and per-topic)"
    )


# ==============================================================================
# STRUCTURED OUTPUTS HELPER FUNCTIONS (November 2025)
# ==============================================================================


def get_video_intelligence_schema() -> Dict:
    """
    Get JSON Schema for VideoIntelligence structured outputs.

    Returns structured output schema for Grok API (November 2025).
    This uses json_schema mode (not basic json_object) for type safety.

    Returns:
        Dict with response_format for Grok API
    """
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "video_intelligence_extraction",
            "strict": True,
            "schema": VideoIntelligence.model_json_schema(),
        },
    }


def get_entity_schema() -> Dict:
    """
    Get JSON Schema for Entity extraction only.

    Returns:
        Dict with response_format for Grok API
    """

    # Create a wrapper model for list of entities
    class EntityList(BaseModel):
        entities: List[Entity] = Field(description="All named entities found in transcript")

    return {
        "type": "json_schema",
        "json_schema": {
            "name": "entity_extraction",
            "strict": True,
            "schema": EntityList.model_json_schema(),
        },
    }


def get_relationship_schema() -> Dict:
    """
    Get JSON Schema for Relationship extraction only.

    Returns:
        Dict with response_format for Grok API
    """

    class RelationshipList(BaseModel):
        relationships: List[Relationship] = Field(description="All relationships between entities")

    return {
        "type": "json_schema",
        "json_schema": {
            "name": "relationship_extraction",
            "strict": True,
            "schema": RelationshipList.model_json_schema(),
        },
    }


def get_topic_schema() -> Dict:
    """
    Get JSON Schema for Topic extraction only.

    Returns:
        Dict with response_format for Grok API
    """

    class TopicList(BaseModel):
        topics: List[Topic] = Field(description="Main topics discussed in video")

    return {
        "type": "json_schema",
        "json_schema": {
            "name": "topic_extraction",
            "strict": True,
            "schema": TopicList.model_json_schema(),
        },
    }
