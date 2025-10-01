"""
Hybrid processing: Voxtral for transcription, Grok-4 for intelligence.
This provides the best of both worlds - no censorship on BOTH transcription and extraction.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import time
import os
import httpx
import json

from ..retrievers.voxtral_transcriber import VoxtralTranscriber
from ..utils.voxtral_chunker import VoxtralChunker
from ..models import VideoIntelligence, VideoTranscript, VideoMetadata, EnhancedEntity, Relationship, Topic
from ..config.settings import Settings

logger = logging.getLogger(__name__)


class HybridProcessor:
    """
    Optimal video processing using Voxtral + Grok-4.
    
    Workflow:
    1. Voxtral transcribes (no censorship, cheaper, accurate)
    2. Full transcript passed to Grok-4 for intelligence extraction
    3. Zero censorship throughout the entire pipeline
    """
    
    def __init__(
        self,
        voxtral_model: str = "voxtral-mini-2507",
        grok_model: str = "grok-4-0709",  # Use Grok-4!
        cache_transcripts: bool = True
    ):
        """
        Initialize hybrid processor.
        
        Args:
            voxtral_model: Voxtral model for transcription
            grok_model: Grok model for extraction (default: grok-4)
            cache_transcripts: Cache transcripts to avoid re-processing
        """
        self.settings = Settings()
        self.voxtral_model = voxtral_model
        self.grok_model = grok_model
        self.cache_transcripts = cache_transcripts
        
        # Get API key
        self.xai_api_key = os.getenv("XAI_API_KEY", "").strip('"').strip("'")
        if not self.xai_api_key:
            raise ValueError("XAI_API_KEY environment variable is required for Grok extraction")
        
        # Initialize components
        self.voxtral = VoxtralTranscriber(model=voxtral_model)
        self.chunker = VoxtralChunker(model=voxtral_model)
        
        # API settings for Grok
        self.grok_base_url = "https://api.x.ai/v1"
        self.grok_headers = {
            "Authorization": f"Bearer {self.xai_api_key}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"HybridProcessor initialized: {voxtral_model} + {grok_model} (uncensored pipeline)")
    
    async def process_video(
        self,
        audio_path: str,
        metadata: Dict[str, Any],
        force_reprocess: bool = False
    ) -> VideoIntelligence:
        """
        Process video with optimal hybrid approach.
        
        Args:
            audio_path: Path to audio file
            metadata: Video metadata
            force_reprocess: Skip cache and reprocess
            
        Returns:
            Complete VideoIntelligence object
        """
        start_time = time.time()
        
        # Step 1: Get transcript (from cache or Voxtral)
        transcript_result = await self._get_transcript(
            audio_path,
            metadata,
            force_reprocess
        )
        
        # Step 2: Extract intelligence with Grok-4
        intelligence = await self._extract_intelligence(
            transcript_result["text"],
            metadata
        )
        
        # Step 2.5: Generate executive summary
        executive_summary = await self._generate_summary(
            transcript_result["text"],
            intelligence.get("entities", []),
            intelligence.get("relationships", [])
        )
        
        # Step 3: Combine into VideoIntelligence
        processing_time = time.time() - start_time
        
        # Create VideoMetadata object
        from datetime import datetime
        
        video_metadata = VideoMetadata(
            video_id=metadata.get("video_id", "unknown"),
            title=metadata.get("title", "Untitled"),
            channel=metadata.get("channel", "Unknown"),
            channel_id=metadata.get("channel_id", "unknown"),
            duration=metadata.get("duration", 0),
            url=metadata.get("url", ""),
            platform="youtube",  # Default platform
            published_at=metadata.get("published_at", datetime.now())
        )
        
        video_intelligence = VideoIntelligence(
            metadata=video_metadata,
            transcript=VideoTranscript(
                full_text=transcript_result["text"],
                segments=transcript_result.get("segments", []),
                language=transcript_result.get("language", "en"),
                confidence_score=transcript_result.get("confidence", 0.95)
            ),
            entities=intelligence.get("entities", []),
            relationships=intelligence.get("relationships", []),
            topics=[Topic(name=t if isinstance(t, str) else t.get("name", ""), confidence=t.get("relevance", 0.8) if isinstance(t, dict) else 0.8) for t in intelligence.get("topics", []) if (t if isinstance(t, str) else t.get("name", ""))],
            key_points=[],  # Using key_points instead of key_moments
            summary=executive_summary,
            sentiment=intelligence.get("overall_sentiment", 0.0),
            processing_time=processing_time,
            processing_cost=transcript_result["cost"] + intelligence.get("cost", 0),
            processing_stats={
                "extraction_method": "hybrid_voxtral_grok4",
                "extraction_confidence": intelligence.get("confidence", 0.85),
                "voxtral_model": self.voxtral_model,
                "chunks_processed": transcript_result.get("chunks", 1)
            }
        )
        
        # Step 4: Build knowledge graph from entities and relationships
        try:
            from ..retrievers.knowledge_graph_builder import KnowledgeGraphBuilder
            kg_builder = KnowledgeGraphBuilder()
            video_intelligence = kg_builder.build_knowledge_graph(video_intelligence)
            logger.info(f"Built knowledge graph with {video_intelligence.knowledge_graph.get('node_count', 0)} nodes")
        except Exception as e:
            logger.warning(f"Could not build knowledge graph: {e}")
        
        logger.info(
            f"Hybrid processing complete: "
            f"{len(video_intelligence.entities)} entities, "
            f"{len(video_intelligence.relationships)} relationships, "
            f"${video_intelligence.processing_cost:.4f} cost, "
            f"{processing_time:.1f}s time"
        )
        
        return video_intelligence
    
    async def _get_transcript(
        self,
        audio_path: str,
        metadata: Dict[str, Any],
        force_reprocess: bool
    ) -> Dict[str, Any]:
        """
        Get transcript from Voxtral with smart chunking.
        
        Args:
            audio_path: Path to audio file
            metadata: Video metadata
            force_reprocess: Skip cache
            
        Returns:
            Transcript with text, segments, cost
        """
        duration = metadata.get("duration", 0)
        
        # Check if chunking is needed
        if duration <= 840:  # Under 14 minutes
            # Direct transcription
            logger.info(f"Direct Voxtral transcription for {duration}s video")
            result = await self.voxtral.transcribe_audio(audio_path)
            
            return {
                "text": result.text,
                "segments": result.segments or [],
                "language": result.language,
                "confidence": result.confidence,
                "cost": result.cost,
                "chunks": 1
            }
        
        else:
            # Chunked transcription with context preservation
            logger.info(f"Chunked Voxtral transcription for {duration}s video")
            
            # Split audio into optimal chunks
            chunks = await self.chunker.split_audio(audio_path)
            logger.info(f"Processing {len(chunks)} chunks")
            
            # Transcribe chunks in parallel (with rate limiting)
            chunk_results = await self._transcribe_chunks_parallel(chunks)
            
            # Merge with context preservation
            merged = self.chunker.merge_chunk_transcripts(chunk_results)
            
            total_cost = sum(r.get("cost", 0) for r in chunk_results)
            
            return {
                "text": merged["text"],
                "segments": merged.get("segments", []),
                "language": chunk_results[0].get("language", "en") if chunk_results else "en",
                "confidence": 0.95,  # High confidence with Voxtral
                "cost": total_cost,
                "chunks": len(chunks)
            }
    
    async def _transcribe_chunks_parallel(
        self,
        chunks: List[Dict[str, Any]],
        max_concurrent: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Transcribe chunks in parallel with rate limiting.
        
        Args:
            chunks: List of chunk metadata
            max_concurrent: Max concurrent API calls
            
        Returns:
            List of transcription results
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def transcribe_chunk(chunk):
            async with semaphore:
                logger.info(f"Transcribing chunk {chunk['chunk_index'] + 1}/{chunk['total_chunks']}")
                result = await self.voxtral.transcribe_audio(chunk["path"])
                
                return {
                    "transcript": {
                        "text": result.text,
                        "segments": result.segments
                    },
                    "language": result.language,
                    "cost": result.cost,
                    "start_time": chunk["start_time"],
                    "end_time": chunk["end_time"],
                    "chunk_index": chunk["chunk_index"]
                }
        
        results = await asyncio.gather(*[
            transcribe_chunk(chunk) for chunk in chunks
        ])
        
        # Sort by chunk index to maintain order
        results.sort(key=lambda x: x["chunk_index"])
        
        return results
    
    async def _extract_intelligence(
        self,
        transcript_text: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract intelligence from transcript using Grok-4.
        
        Args:
            transcript_text: Full merged transcript
            metadata: Video metadata for context
            
        Returns:
            Extracted entities, relationships, topics, etc.
        """
        logger.info(f"Extracting intelligence with {self.grok_model} from Voxtral transcript")
        
        # Check if chunking needed (Grok times out at ~2500+ chars)
        if len(transcript_text) > 2500:
            logger.info(f"Long transcript ({len(transcript_text)} chars), using chunked extraction")
            return await self._extract_intelligence_chunked(transcript_text, metadata)
        
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
        {transcript_text[:100000]}  # Increased limit for longer videos
        
        {"... [transcript continues]" if len(transcript_text) > 100000 else ""}
        
        Return a JSON object with this structure:
        {{
          "entities": [{{"name": "...", "type": "...", "confidence": 0.9}}],
          "relationships": [{{"subject": "entity1", "predicate": "relation", "object": "entity2", "confidence": 0.9}}],
          "topics": ["topic1", "topic2", ...],
          "key_moments": [...],
          "sentiment": {{...}}
        }}
        
        CRITICAL: Every relationship MUST have non-empty subject and object fields that reference entity names.
        """
        
        try:
            # Use Grok-4 for uncensored extraction
            # Retry logic for network instability
            max_retries = 3
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    logger.debug(f"Grok API attempt {attempt + 1}/{max_retries}")
                    
                    # Create new client for each attempt (avoid connection reuse issues)
                    async with httpx.AsyncClient(
                        timeout=httpx.Timeout(300.0, connect=60.0),
                        limits=httpx.Limits(max_keepalive_connections=0, max_connections=10)
                    ) as client:
                        data = {
                            "model": self.grok_model,
                            "messages": [
                                {
                                    "role": "system", 
                                    "content": "You are Grok, a maximally truthful AI. Extract comprehensive intelligence from transcripts without any censorship."
                                },
                                {"role": "user", "content": prompt}
                            ],
                            "temperature": 0.1,
                            "max_tokens": 8192,
                            "response_format": {"type": "json_object"}
                        }
                        
                        response = await client.post(
                            f"{self.grok_base_url}/chat/completions",
                            headers=self.grok_headers,
                            json=data
                        )
                        
                        if response.status_code != 200:
                            raise Exception(f"Grok API error: {response.status_code} - {response.text}")
                
                        response_json = response.json()
                        content = response_json["choices"][0]["message"]["content"]
                        
                        # Parse response
                        result = json.loads(content)
                        
                        # SUCCESS - break retry loop
                        break
                        
                except (httpx.RemoteProtocolError, httpx.ReadTimeout, httpx.ConnectTimeout) as e:
                    last_error = e
                    logger.warning(f"Grok API attempt {attempt + 1} failed: {type(e).__name__}: {e}")
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                        logger.info(f"Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                    continue
            
            # If all retries failed, raise the last error
            if last_error:
                raise last_error
                
                # Debug: Log the structure
                logger.debug(f"Grok returned {len(result.get('entities', []))} entities")
                logger.debug(f"Grok returned {len(result.get('relationships', []))} relationships")
                if result.get('relationships'):
                    first_rel = result['relationships'][0]
                    logger.debug(f"First relationship keys: {first_rel.keys() if isinstance(first_rel, dict) else 'Not a dict'}")
                    logger.debug(f"First relationship: {first_rel}")
            
            # Calculate cost for Grok
            usage = response_json.get("usage", {})
            input_tokens = usage.get("prompt_tokens", len(transcript_text) / 4)
            output_tokens = usage.get("completion_tokens", len(content) / 4)
            
            # Grok-4 pricing: $60/M input, $60/M output (simplified)
            if "grok-4" in self.grok_model:
                cost = (input_tokens * 60 + output_tokens * 60) / 1_000_000
            else:  # Grok-3 or Grok-2
                cost = (input_tokens * 15 + output_tokens * 15) / 1_000_000
            
            # Convert to model objects
            entities = []
            for e in result.get("entities", []):
                # Handle both string and dict formats from Grok
                if isinstance(e, str):
                    # Simple string entity name
                    entities.append(EnhancedEntity(
                        name=e,
                        type="UNKNOWN",
                        extraction_sources=["grok_analysis"],
                        mention_count=1,  # Will be updated with actual count
                        context_windows=[],
                        aliases=[],
                        canonical_form=e,
                        temporal_distribution=[],
                        properties={"evidence": e.get("evidence", []),
                                   "quotes": e.get("quotes", [])}
                    ))
                else:
                    # Full entity dict
                    entities.append(EnhancedEntity(
                        name=e.get("name", ""),
                        type=e.get("type", "UNKNOWN"),
                        extraction_sources=["grok_analysis"],
                        mention_count=1,  # Will be updated with actual count
                        context_windows=[],
                        aliases=[],
                        canonical_form=e.get("name", ""),
                        temporal_distribution=[],
                        properties={"evidence": e.get("evidence", []),
                                   "quotes": e.get("quotes", [])}
                    ))

            # Count actual mentions in transcript
            entities = self._count_entity_mentions(entities, transcript_text)

            relationships = []
            for r in result.get("relationships", []):
                # Create evidence chain from Grok's evidence
                evidence_chain = []
                evidence_text = r.get("evidence", "")
                if evidence_text:
                    from ..models import RelationshipEvidence
                    evidence_chain.append(RelationshipEvidence(
                        direct_quote=evidence_text,
                        timestamp="00:00:00",  # Grok doesn't provide timestamps
                        speaker=None,
                        visual_context=None,
                        context_window="",
                        evidence_type="extraction"
                    ))
                
                # Add quotes as additional evidence
                for quote in r.get("quotes", []):
                    if quote:
                        evidence_chain.append(RelationshipEvidence(
                            direct_quote=quote,
                            timestamp="00:00:00",  # Grok doesn't provide timestamps
                            speaker=None,
                            visual_context=None,
                            context_window="",
                            evidence_type="spoken"
                        ))
                
                relationships.append(Relationship(
                    subject=r.get("subject", r.get("source", "")),
                    predicate=r.get("predicate", r.get("type", "RELATED_TO")),
                    object=r.get("object", r.get("target", "")),
                    source="grok_analysis",
                    evidence_chain=evidence_chain,
                    supporting_mentions=len(evidence_chain) if evidence_chain else 1,
                    contradictions=[],
                    visual_correlation=False,
                    properties={"confidence": r.get("confidence", 0.5),
                               "evidence": r.get("evidence", ""),
                               "quotes": r.get("quotes", [])}
                ))
            
            # Process topics - handle both string and dict formats
            topics = []
            for t in result.get("topics", []):
                if isinstance(t, str) and t.strip():  # Non-empty string
                    topics.append({"name": t, "relevance": 0.8})
                elif isinstance(t, dict):
                    topics.append(t)
            
            return {
                "entities": entities,
                "relationships": relationships,
                "topics": topics,
                "key_moments": result.get("key_moments", []),
                "sentiment": result.get("sentiment", {}),
                "confidence": 0.9,  # High confidence with full context
                "cost": cost
            }

        except Exception as e:
            logger.error(f"Grok intelligence extraction failed: {e}")
            # Fallback to empty results
            return {
                "entities": [],
                "relationships": [],
                "topics": [],
                "key_moments": [],
                "sentiment": {},
                "confidence": 0,
                "cost": 0
            }

    async def _extract_intelligence_chunked(
        self,
        transcript_text: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract intelligence from long transcript using chunking."""
        chunks = self._split_into_chunks(transcript_text, max_chars=2000, overlap=200)
        logger.info(f"Split transcript into {len(chunks)} chunks for Grok processing")
        
        all_entities = []
        all_relationships = []
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}")
            result = await self._extract_from_chunk(chunk, metadata, i+1, len(chunks))
            all_entities.extend(result.get('entities', []))
            all_relationships.extend(result.get('relationships', []))
        
        # Deduplicate entities by name
        unique_entities = {}
        for entity in all_entities:
            name = entity.get('name', '')
            if name and name not in unique_entities:
                unique_entities[name] = entity
        
        logger.info(f"Merged {len(all_entities)} entities into {len(unique_entities)} unique")
        
        return {
            'entities': list(unique_entities.values()),
            'relationships': all_relationships,
            'topics': [],
            'key_moments': [],
            'sentiment': {},
            'confidence': 0.85,
            'cost': len(chunks) * 0.02
        }
    
    def _split_into_chunks(self, text: str, max_chars: int, overlap: int) -> List[str]:
        """Split text into overlapping chunks."""
        if len(text) <= max_chars:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + max_chars
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap
        
        return chunks
    
    async def _extract_from_chunk(
        self,
        chunk_text: str,
        metadata: Dict[str, Any],
        chunk_num: int,
        total_chunks: int
    ) -> Dict[str, Any]:
        """Extract intelligence from a single chunk."""
        prompt = f"""Analyze chunk {chunk_num}/{total_chunks} from "{metadata.get('title')}":

{chunk_text}

Extract entities and relationships. Return JSON:
{{"entities": [{{"name": "...", "type": "...", "confidence": 0.9}}], "relationships": [{{"subject": "...", "predicate": "...", "object": "...", "confidence": 0.9}}]}}
"""
        
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=30.0), limits=httpx.Limits(max_keepalive_connections=0)) as client:
                data = {
                    "model": self.grok_model,
                    "messages": [{"role": "system", "content": "Extract entities and relationships."}, {"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 2048,
                    "response_format": {"type": "json_object"}
                }
                
                response = await client.post(f"{self.grok_base_url}/chat/completions", headers=self.grok_headers, json=data)
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    return json.loads(content)
        except Exception as e:
            logger.warning(f"Chunk {chunk_num} extraction failed: {e}")
        
        return {'entities': [], 'relationships': []}
    
    def _count_entity_mentions(self, entities: List[EnhancedEntity], transcript_text: str) -> List[EnhancedEntity]:
        """Count actual mentions of entities in the transcript text."""
        import re

        for entity in entities:
            # Use word boundaries and case-insensitive matching
            pattern = r'\b' + re.escape(entity.name) + r'\b'
            matches = re.findall(pattern, transcript_text, re.IGNORECASE)
            entity.mention_count = len(matches)

        return entities


class SeamlessTranscriptAnalyzer:
    """
    Ensures seamless transition from Voxtral transcript to Grok analysis.
    """
    
    @staticmethod
    def prepare_transcript_for_grok(
        transcript: str,
        segments: Optional[List[Dict]] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Prepare transcript with optimal formatting for Grok analysis.
        
        Args:
            transcript: Raw transcript text
            segments: Optional segment data with timestamps
            metadata: Optional video metadata
            
        Returns:
            Formatted transcript optimized for Grok
        """
        # Add timestamp markers if segments available
        if segments and len(segments) > 0:
            formatted_lines = []
            for segment in segments:
                timestamp = f"[{segment.get('start', 0):.1f}s]"
                text = segment.get('text', '')
                formatted_lines.append(f"{timestamp} {text}")
            
            return "\n".join(formatted_lines)
        
        # Return clean transcript if no segments
        return transcript.strip()
    
    @staticmethod
    def validate_transition(
        voxtral_result: Dict[str, Any],
        formatted_input: str
    ) -> bool:
        """
        Validate that transcript transition preserves content.
        
        Args:
            voxtral_result: Original Voxtral result
            formatted_input: Formatted input for Grok
            
        Returns:
            True if transition is valid
        """
        # Check text preservation
        voxtral_text = voxtral_result.get("text", "").strip()
        
        # Remove timestamps from formatted_input for comparison
        import re
        formatted_text = re.sub(r'\[\d+\.\d+s\]\s*', '', formatted_input).strip()
        
        # Basic validation - at least 90% of content preserved
        if len(formatted_text) < len(voxtral_text) * 0.9:
            logger.warning("Transcript transition may have lost content")
            return False
        
        return True


    async def _generate_summary(
        self,
        transcript: str,
        entities: list,
        relationships: list
    ) -> str:
        """Generate 100-200 word executive summary."""
        
        # Extract entity names
        entity_names = [e.get('name', '') for e in entities[:10]]
        
        # Extract key relationships
        rel_texts = [
            f"{r.get('subject')} {r.get('predicate')} {r.get('object')}"
            for r in relationships[:5]
        ]
        
        prompt = f"""Create a 100-200 word executive summary:

Transcript preview: {transcript[:1000]}
Key entities: {', '.join(entity_names)}
Key relationships: {'; '.join(rel_texts)}

Format:
- Overview (what this is about)
- Key entities and their roles
- Main relationships/connections
- Implications or significance

Tone: Informative, objective, professional
Length: 100-200 words
"""
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                data = {
                    "model": self.grok_model,
                    "messages": [
                        {"role": "system", "content": "Create concise executive summaries."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 300
                }
                
                response = await client.post(
                    f"{self.grok_base_url}/chat/completions",
                    headers=self.grok_headers,
                    json=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    summary = result["choices"][0]["message"]["content"].strip()
                    logger.info(f"Generated executive summary: {len(summary)} chars")
                    return summary
        
        except Exception as e:
            logger.warning(f"Summary generation failed: {e}")
        
        # Fallback
        return f"Analysis of video content covering {len(entities)} key entities and {len(relationships)} relationships."
