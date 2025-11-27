"""
Prompt templates for Grok-4 intelligence extraction.

Following xAI best practices:
- Quality over quantity
- Evidence-based extraction
- Clear guidance without forced minimums
- Metadata context for disambiguation
"""


def create_intelligence_extraction_prompt(transcript_text: str, metadata: dict) -> str:
    """
    Create prompt for comprehensive intelligence extraction.

    Following xAI best practices from docs.x.ai:
    - Emphasize quality and evidence (not quantity targets)
    - Include video metadata for context
    - Clear structure guidance
    - Let Grok decide how many based on content

    Args:
        transcript_text: Full video transcript
        metadata: Video metadata (title, duration, channel, etc.)

    Returns:
        Prompt string optimized for Grok-4 Fast Reasoning
    """

    title = metadata.get("title", "Unknown")
    duration_sec = metadata.get("duration", 0)
    duration_min = duration_sec / 60 if duration_sec > 0 else 0
    channel = metadata.get("channel", "Unknown")
    visual_mode = metadata.get("visual_mode", False)

    visual_section = ""
    if visual_mode:
        visual_section = """
6. VISUAL OBSERVATIONS (GEOINT):
   You are acting as a visual observer analyzing surveillance footage.
   Identify specific visual sightings, movements, or activities described or implied in the transcript.

   Requirements:
   - Extract "Visual Observations" where the speaker describes seeing something.
   - Focus on physical objects (vehicles, people, infrastructure) and actions.
   - Timestamp: Best estimate from context (MM:SS).
   - Description: Clear description of what is seen.
   - Evidence: Quote supporting the observation.

   Example: "I see a red truck moving west" -> Observation: Red Truck moving West.
"""

    prompt = f"""Extract comprehensive intelligence from this video transcript.

Video Context:
- Title: {title}
- Duration: {duration_min:.0f} minutes
- Source: {channel}

EXTRACTION GUIDELINES (Quality Over Quantity):

1. ENTITIES:
   Extract ALL named people, organizations, places, and events that are clearly mentioned.

   Requirements:
   - Only extract if explicitly named in transcript (not generic references)
   - Each entity MUST have supporting quote as evidence
   - Confidence score (0-1) based on clarity of mention
   - Use spaCy standard types: PERSON, ORG, GPE, EVENT, PRODUCT, etc.

   Quality bar: Named and specific > generic and vague
   Example good: "Donald Trump" (PERSON)
   Example bad: "the president" (too generic)

2. RELATIONSHIPS:
   Extract ALL relationships between entities where connection is explicitly stated.

   Requirements:
   - Subject and object MUST be actual entity names from transcript
   - Predicate should be specific action/connection (e.g., "announced", "criticized", "invested_in")
   - MUST include exact supporting quote as evidence
   - Only extract if relationship is clearly stated (don't infer unstated connections)
   - Confidence based on clarity of relationship

   Quality bar: Explicit and evidenced > inferred and vague
   Example good: "Trump announced ceasefire" (clear action)
   Example bad: "Trump knows Biden" (inferred, not stated)

3. TOPICS:
   Identify main themes or subjects discussed in the video.

   Requirements:
   - Topics should be specific (e.g., "Israel-Hamas Ceasefire" not just "Middle East")
   - Provide time range where topic is discussed (MM:SS-MM:SS format)
   - Relevance score (0-1): how central this topic is to the video
   - Topic should be substantive (not passing mentions)

   Quality bar: Specific and substantial > generic and brief

4. KEY MOMENTS:
   Identify moments that are particularly significant or worth highlighting.

   Requirements:
   - Exact timestamp (MM:SS format, estimate from context if needed)
   - Clear description of what makes this moment significant
   - Significance score (0-1) based on importance to video content
   - Include exact quote from that moment

   Quality bar: Objectively significant > subjectively interesting
   Examples: Major announcements, key debates, important revelations

5. SENTIMENT:
   Analyze overall tone and per-topic sentiment.

   Requirements:
   - Overall: positive, negative, neutral, or mixed
   - Per-topic sentiment if topics have distinctly different tones
   - Confidence in overall assessment

   Quality bar: Based on actual tone > assumed/stereotyped
{visual_section}

CRITICAL PRINCIPLES:
- Evidence is mandatory for entities and relationships (prevents hallucinations)
- Quality is more important than quantity (5 perfect > 20 questionable)
- Only extract what is clearly present (don't infer or assume)
- Confidence scores should reflect actual certainty (be honest about ambiguity)
- Specific is better than generic (names > pronouns, actions > "related to")

Transcript:
{transcript_text}
"""

    return prompt


def create_relationship_focused_prompt(transcript_text: str, entities: list, metadata: dict) -> str:
    """
    Create prompt specifically for relationship extraction.

    Use this for a second pass if initial extraction has too few relationships.
    Focuses Grok entirely on finding connections between known entities.

    Args:
        transcript_text: Full transcript
        entities: List of already-extracted entities
        metadata: Video metadata

    Returns:
        Relationship-focused prompt
    """

    entity_names = [e.get("name", e) if isinstance(e, dict) else e for e in entities[:50]]
    entity_list = ", ".join(entity_names)

    prompt = f"""Given this transcript and list of entities, extract ALL relationships between them.

Video: {metadata.get('title', 'Unknown')}

Known Entities: {entity_list}

RELATIONSHIP EXTRACTION GUIDELINES:

Extract relationships where:
1. Both subject and object are from the entity list above
2. The connection is explicitly stated in the transcript
3. You can provide an exact supporting quote as evidence

Requirements:
- Subject: Must be an entity name from the list
- Predicate: Specific action or connection (e.g., "announced", "met_with", "criticized")
- Object: Must be an entity name from the list
- Evidence: Exact quote from transcript showing this relationship
- Confidence: 0-1 based on clarity of connection

Only extract relationships that are clearly stated. Don't infer connections that aren't explicitly mentioned.

Better to extract 10 clear relationships than 30 questionable ones.

Transcript:
{transcript_text}
"""

    return prompt
