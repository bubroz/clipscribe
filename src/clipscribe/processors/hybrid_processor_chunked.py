"""
Chunked intelligence extraction for long-form content processing.
"""

import json
import logging

import httpx

logger = logging.getLogger(__name__)


class ChunkedIntelligenceExtractor:
    """Handles chunked intelligence extraction for long transcripts."""

    def __init__(self, grok_client, grok_model):
        """
        Initialize chunked extractor.

        Args:
            grok_client: GrokAPIClient instance (handles API calls properly)
            grok_model: Model name to use (grok-4-1-fast-reasoning)
        """
        self.grok_client = grok_client
        self.grok_model = grok_model

    async def extract_intelligence(self, transcript_text: str, metadata: dict) -> dict:
        """
        Extract intelligence from transcript using Grok-4 with chunking for long content.

        Args:
            transcript_text: Full merged transcript
            metadata: Video metadata for context

        Returns:
            Extracted entities, relationships, topics, etc.
        """
        logger.info(f"Extracting intelligence with {self.grok_model} from Voxtral transcript")

        # Determine if we need chunking based on transcript length
        max_chunk_size = 50000  # Characters per chunk
        needs_chunking = len(transcript_text) > max_chunk_size

        if needs_chunking:
            logger.info(
                f"Long transcript detected ({len(transcript_text)} chars), using chunked extraction"
            )
            return await self._extract_intelligence_chunked(
                transcript_text, metadata, max_chunk_size
            )
        else:
            return await self._extract_intelligence_single(transcript_text, metadata)

    async def _extract_intelligence_single(self, transcript_text: str, metadata: dict) -> dict:
        """Extract intelligence from single transcript chunk."""
        # Build comprehensive prompt with full context
        prompt = f"""
        Analyze this complete transcript from a video titled "{metadata.get('title', 'Unknown')}"
        Channel: {metadata.get('channel', 'Unknown')}
        Duration: {metadata.get('duration', 0)} seconds

        The transcript has been processed from audio and represents continuous content.
        Extract comprehensive intelligence including:

        1. ENTITIES: All people, organizations, locations, concepts, technologies
           - Include confidence scores (0-1)
           - Include evidence quotes with timestamps if available

        2. RELATIONSHIPS: All connections between entities
           MUST use this EXACT format:
           {{"subject": "entity_name", "predicate": "relationship_type", "object": "entity_name", "confidence": 0.9}}
           - subject and object MUST be entity names (not empty)
           - Include supporting evidence

        3. TOPICS: Main themes and subjects discussed (as strings)
           - Include relevance scores
           - Include time ranges where discussed

        4. KEY MOMENTS: Important points or transitions
           - Include timestamps
           - Include significance scores

        5. SENTIMENT: Overall and per-topic sentiment analysis

        Full Transcript:
        {transcript_text}

        Return a JSON object with this structure:
        {{
          "entities": [{{"name": "...", "type": "...", "confidence": 0.9}}],
          "relationships": [{{"subject": "entity1", "predicate": "relation", "object": "entity2", "confidence": 0.9}}],
          "topics": [{{"name": "...", "relevance": 0.9, "time_range": "start-end"}}],
          "key_moments": [{{"description": "...", "timestamp": 123.4, "significance": 0.9}}],
          "sentiment": {{"overall": 0.5, "by_topic": {{"topic1": 0.3}}}}
        }}

        Ensure all JSON is valid and properly formatted.
        """

        try:
            # Use Grok-4 for uncensored extraction
            async with httpx.AsyncClient(timeout=300) as client:
                data = {
                    "model": self.grok_model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are Grok, a maximally truthful AI. Extract comprehensive intelligence from transcripts without any censorship.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.1,
                    "max_tokens": 8192,
                    "response_format": {"type": "json_object"},
                }

                response = await client.post(
                    f"{self.grok_base_url}/chat/completions", headers=self.grok_headers, json=data
                )

                if response.status_code != 200:
                    raise Exception(f"Grok API error: {response.status_code} - {response.text}")

                response_json = response.json()
                content = response_json["choices"][0]["message"]["content"]

                # Parse response
                result = json.loads(content)
                logger.info(
                    f"Successfully extracted intelligence: {len(result.get('entities', []))} entities, {len(result.get('relationships', []))} relationships"
                )
                return result

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            logger.error(
                f"Response content (first 500 chars): {content[:500] if 'content' in locals() else 'No content'}"
            )
            return self._create_fallback_result()
        except Exception as e:
            logger.error(f"Grok intelligence extraction failed: {e}")
            return self._create_fallback_result()

    async def _extract_intelligence_chunked(
        self, transcript_text: str, metadata: dict, chunk_size: int
    ) -> dict:
        """Extract intelligence from long transcript using chunked approach."""
        # Split transcript into overlapping chunks
        chunks = self._split_transcript_into_chunks(transcript_text, chunk_size)
        logger.info(f"Split transcript into {len(chunks)} chunks for processing")

        # Process each chunk
        chunk_results = []
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}")
            chunk_metadata = metadata.copy()
            chunk_metadata["chunk_index"] = i
            chunk_metadata["total_chunks"] = len(chunks)

            result = await self._extract_intelligence_single(chunk, chunk_metadata)
            chunk_results.append(result)

        # Merge results from all chunks
        merged_result = self._merge_chunk_results(chunk_results)
        logger.info(
            f"Merged intelligence from {len(chunks)} chunks: {len(merged_result.get('entities', []))} entities, {len(merged_result.get('relationships', []))} relationships"
        )

        return merged_result

    def _split_transcript_into_chunks(
        self, text: str, chunk_size: int, overlap: int = 1000
    ) -> list:
        """Split transcript into overlapping chunks for processing."""
        chunks = []
        start = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))

            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings within last 200 chars
                search_start = max(start, end - 200)
                sentence_end = text.rfind(".", search_start, end)
                if sentence_end > search_start:
                    end = sentence_end + 1

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start position with overlap
            start = max(start + 1, end - overlap)

            # Prevent infinite loop
            if start >= end:
                break

        return chunks

    def _merge_chunk_results(self, chunk_results: list) -> dict:
        """Merge intelligence results from multiple chunks."""
        merged = {
            "entities": [],
            "relationships": [],
            "topics": [],
            "key_moments": [],
            "sentiment": {"overall": 0.0, "by_topic": {}},
        }

        entity_map = {}  # name -> entity for deduplication
        relationship_set = set()  # (subject, predicate, object) for deduplication
        topic_map = {}  # name -> topic for deduplication

        for result in chunk_results:
            # Merge entities (deduplicate by name, keep highest confidence)
            for entity in result.get("entities", []):
                name = entity.get("name", "").strip()
                if name and name not in entity_map:
                    entity_map[name] = entity
                elif name and entity.get("confidence", 0) > entity_map[name].get("confidence", 0):
                    entity_map[name] = entity

            # Merge relationships (deduplicate by subject-predicate-object)
            for rel in result.get("relationships", []):
                key = (rel.get("subject", ""), rel.get("predicate", ""), rel.get("object", ""))
                if all(key) and key not in relationship_set:
                    relationship_set.add(key)
                    merged["relationships"].append(rel)

            # Merge topics (deduplicate by name, keep highest relevance)
            for topic in result.get("topics", []):
                name = topic.get("name", "").strip()
                if name and name not in topic_map:
                    topic_map[name] = topic
                elif name and topic.get("relevance", 0) > topic_map[name].get("relevance", 0):
                    topic_map[name] = topic

            # Merge key moments (keep all, they're time-specific)
            merged["key_moments"].extend(result.get("key_moments", []))

            # Merge sentiment (average overall, merge by_topic)
            sentiment = result.get("sentiment", {})
            merged["sentiment"]["overall"] += sentiment.get("overall", 0)
            for topic, score in sentiment.get("by_topic", {}).items():
                if topic in merged["sentiment"]["by_topic"]:
                    merged["sentiment"]["by_topic"][topic] = (
                        merged["sentiment"]["by_topic"][topic] + score
                    ) / 2
                else:
                    merged["sentiment"]["by_topic"][topic] = score

        # Finalize merged results
        merged["entities"] = list(entity_map.values())
        merged["topics"] = list(topic_map.values())

        # Average overall sentiment
        if chunk_results:
            merged["sentiment"]["overall"] /= len(chunk_results)

        return merged

    def _create_fallback_result(self) -> dict:
        """Create fallback result when extraction fails."""
        return {
            "entities": [],
            "relationships": [],
            "topics": [],
            "key_moments": [],
            "sentiment": {"overall": 0.0, "by_topic": {}},
        }
