"""
Streaming Extractor - Process transcripts in chunks to avoid token limits.

This approach processes the transcript in smaller, independent pieces :-)
"""

import asyncio
import logging
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
import json

import google.generativeai as genai
from google.generativeai.types import RequestOptions

logger = logging.getLogger(__name__)


@dataclass
class ChunkResult:
    """Results from processing a single chunk."""
    entities: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    key_points: List[Dict[str, Any]]
    chunk_summary: str
    start_time: float
    end_time: float


class StreamingExtractor:
    """
    Process transcripts in streaming chunks to avoid token limits.
    
    Instead of sending the entire transcript repeatedly, we process it
    in smaller chunks and aggregate the results. This is perfect for
    long videos that would otherwise hit token limits :-)
    """
    
    def __init__(
        self, 
        model_name: str = "gemini-2.5-flash",
        chunk_duration: int = 300,  # 5 minutes per chunk
        max_concurrent: int = 3     # Process 3 chunks at once
    ):
        """Initialize the streaming extractor."""
        self.model_name = model_name
        self.chunk_duration = chunk_duration
        self.max_concurrent = max_concurrent
        
        # Configure Gemini
        genai.configure(api_key=None)
        self.model = genai.GenerativeModel(model_name)
        
    async def extract_from_segments(
        self,
        segments: List[Dict[str, Any]],
        total_duration: int
    ) -> Dict[str, Any]:
        """
        Extract intelligence from transcript segments in chunks.
        
        This avoids token limits by processing smaller pieces independently.
        """
        # Group segments into chunks
        chunks = self._create_chunks(segments, self.chunk_duration)
        logger.info(f"Processing {len(chunks)} chunks from {len(segments)} segments")
        
        # Process chunks with concurrency limit
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def process_chunk_with_limit(chunk_data):
            async with semaphore:
                return await self._process_chunk(chunk_data)
        
        # Process all chunks in parallel (with limit)
        chunk_results = await asyncio.gather(
            *[process_chunk_with_limit(chunk) for chunk in chunks]
        )
        
        # Aggregate results
        return self._aggregate_results(chunk_results, total_duration)
        
    def _create_chunks(
        self, 
        segments: List[Dict[str, Any]], 
        chunk_duration: int
    ) -> List[Tuple[List[Dict], float, float]]:
        """Group segments into time-based chunks."""
        chunks = []
        current_chunk = []
        chunk_start = 0
        
        for segment in segments:
            seg_start = segment.get('start', 0)
            seg_end = segment.get('end', seg_start + 30)
            
            # If this segment would make chunk too long, save current chunk
            if current_chunk and (seg_end - chunk_start) > chunk_duration:
                chunk_end = current_chunk[-1].get('end', chunk_start + 30)
                chunks.append((current_chunk, chunk_start, chunk_end))
                current_chunk = [segment]
                chunk_start = seg_start
            else:
                current_chunk.append(segment)
        
        # Add final chunk
        if current_chunk:
            chunk_end = current_chunk[-1].get('end', chunk_start + 30)
            chunks.append((current_chunk, chunk_start, chunk_end))
            
        return chunks
        
    async def _process_chunk(
        self,
        chunk_data: Tuple[List[Dict], float, float]
    ) -> ChunkResult:
        """Process a single chunk of transcript."""
        segments, start_time, end_time = chunk_data
        
        # Combine segment texts
        chunk_text = " ".join(seg.get('text', '') for seg in segments)
        
        # Create focused prompt for this chunk
        prompt = f"""
Analyze this {int(end_time - start_time)} second portion of a transcript (from {start_time:.0f}s to {end_time:.0f}s).

Transcript chunk:
{chunk_text}

Extract the following in JSON format:

{{
    "entities": [
        {{
            "name": "Entity name",
            "type": "PERSON|ORGANIZATION|LOCATION|EVENT|TECHNOLOGY|PRODUCT",
            "confidence": 0.95
        }}
    ],
    "relationships": [
        {{
            "subject": "Entity1",
            "predicate": "specific action",
            "object": "Entity2",
            "confidence": 0.9
        }}
    ],
    "key_points": [
        {{
            "text": "Important point from this chunk",
            "importance": 0.9
        }}
    ],
    "chunk_summary": "Brief summary of this chunk's content"
}}

Focus on extracting concrete, specific information from this portion.
"""
        
        try:
            response = await self.model.generate_content_async(
                prompt,
                generation_config={"response_mime_type": "application/json"},
                request_options=RequestOptions(timeout=300)
            )
            
            result = json.loads(response.text)
            
            return ChunkResult(
                entities=result.get('entities', []),
                relationships=result.get('relationships', []),
                key_points=result.get('key_points', []),
                chunk_summary=result.get('chunk_summary', ''),
                start_time=start_time,
                end_time=end_time
            )
            
        except Exception as e:
            logger.warning(f"Failed to process chunk {start_time}-{end_time}: {e}")
            # Return empty result for failed chunk
            return ChunkResult([], [], [], '', start_time, end_time)
            
    def _aggregate_results(
        self,
        chunk_results: List[ChunkResult],
        total_duration: int
    ) -> Dict[str, Any]:
        """Aggregate results from all chunks."""
        # Collect all entities
        all_entities = []
        entity_mentions = {}
        
        for chunk in chunk_results:
            for entity in chunk.entities:
                name = entity['name']
                if name in entity_mentions:
                    entity_mentions[name]['count'] += 1
                else:
                    entity_mentions[name] = {
                        'entity': entity,
                        'count': 1,
                        'first_seen': chunk.start_time
                    }
        
        # Deduplicate entities, keeping highest confidence
        for name, data in entity_mentions.items():
            entity = data['entity']
            entity['mentions'] = data['count']
            entity['first_timestamp'] = data['first_seen']
            all_entities.append(entity)
        
        # Collect all relationships
        all_relationships = []
        seen_rels = set()
        
        for chunk in chunk_results:
            for rel in chunk.relationships:
                # Create unique key
                key = (rel['subject'], rel['predicate'], rel['object'])
                if key not in seen_rels:
                    rel['timestamp'] = chunk.start_time
                    all_relationships.append(rel)
                    seen_rels.add(key)
        
        # Collect key points with timestamps
        all_key_points = []
        for chunk in chunk_results:
            for kp in chunk.key_points:
                kp['timestamp'] = chunk.start_time
                all_key_points.append(kp)
        
        # Sort key points by importance
        all_key_points.sort(key=lambda x: x.get('importance', 0), reverse=True)
        
        # Generate overall summary from chunk summaries
        chunk_summaries = [c.chunk_summary for c in chunk_results if c.chunk_summary]
        
        return {
            'entities': all_entities,
            'relationships': all_relationships,
            'key_points': all_key_points[:50],  # Top 50 key points
            'topics': self._extract_topics_from_entities(all_entities),
            'summary': ' '.join(chunk_summaries),
            'processing_stats': {
                'chunks_processed': len(chunk_results),
                'chunk_duration': self.chunk_duration,
                'total_entities': len(all_entities),
                'total_relationships': len(all_relationships),
                'total_key_points': len(all_key_points)
            }
        }
        
    def _extract_topics_from_entities(self, entities: List[Dict]) -> List[str]:
        """Extract topics from entity types and names."""
        topics = set()
        
        # Group by type
        type_counts = {}
        for entity in entities:
            entity_type = entity.get('type', 'unknown')
            type_counts[entity_type] = type_counts.get(entity_type, 0) + 1
        
        # Add prominent entity types as topics
        for entity_type, count in type_counts.items():
            if count > 2:  # Mentioned more than twice
                topics.add(entity_type.lower().replace('_', ' '))
        
        return list(topics) 