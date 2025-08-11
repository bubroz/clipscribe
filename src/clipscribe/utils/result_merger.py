"""
result_merger.py

A utility for merging the results of multiple video chunks into a single,
cohesive VideoIntelligence object.
"""

from typing import List, Dict, Any
import logging
from ..models import VideoIntelligence, Entity

logger = logging.getLogger(__name__)


def merge_transcripts(results: List[Dict[str, Any]]) -> str:
    """Concatenates transcripts from a list of results."""
    full_transcript = ""
    for result in results:
        full_transcript += result.get("transcript", "") + "\n\n"
    return full_transcript.strip()


def merge_entities(results: List[Dict[str, Any]], timestamp_offsets: List[float]) -> List[Entity]:
    """Merges and de-duplicates entities, adjusting timestamps."""
    # TODO: Implement proper entity normalization and de-duplication
    all_entities = []
    for i, result in enumerate(results):
        for entity_data in result.get("entities", []):
            # This is a placeholder. We need to adjust timestamps and normalize.
            all_entities.append(Entity(**entity_data))
    return all_entities


def merge_relationships(
    results: List[Dict[str, Any]], timestamp_offsets: List[float]
) -> List[Dict[str, Any]]:
    """Merges relationships, adjusting timestamps."""
    # TODO: Implement relationship merging
    all_relationships = []
    for i, result in enumerate(results):
        all_relationships.extend(result.get("relationships", []))
    return all_relationships


def synthesize_summary(results: List[Dict[str, Any]]) -> str:
    """Synthesizes a new summary from individual chunk summaries."""
    # TODO: Use an LLM call to synthesize a high-quality summary.
    # For now, just concatenate them.
    full_summary = ""
    for result in results:
        full_summary += result.get("summary", "") + "\n\n"
    return full_summary.strip()


def merge_results(
    chunk_results: List[Dict[str, Any]], chunk_durations: List[float]
) -> Dict[str, Any]:
    """
    Merges the analysis results from multiple video chunks.

    Args:
        chunk_results: A list of the analysis dictionaries from each chunk.
        chunk_durations: A list of the duration of each chunk.

    Returns:
        A single, merged analysis dictionary.
    """
    if not chunk_results:
        return {}

    logger.info(f"Merging results from {len(chunk_results)} chunks.")

    # Calculate timestamp offsets for each chunk
    timestamp_offsets = [0.0]
    for i in range(len(chunk_durations) - 1):
        timestamp_offsets.append(timestamp_offsets[i] + chunk_durations[i])

    merged_transcript = merge_transcripts(chunk_results)
    merged_entities = merge_entities(chunk_results, timestamp_offsets)
    merged_relationships = merge_relationships(chunk_results, timestamp_offsets)
    merged_summary = synthesize_summary(chunk_results)

    total_cost = sum(r.get("processing_cost", 0.0) for r in chunk_results)

    # Use the metadata and other info from the first chunk as the base
    final_result = chunk_results[0].copy()
    final_result["transcript"] = merged_transcript
    final_result["summary"] = merged_summary
    final_result["entities"] = [e.dict() for e in merged_entities]
    final_result["relationships"] = merged_relationships
    final_result["processing_cost"] = total_cost
    final_result["key_points"] = [kp for r in chunk_results for kp in r.get("key_points", [])]
    final_result["topics"] = list(set([t for r in chunk_results for t in r.get("topics", [])]))

    logger.info("Successfully merged all chunk results.")
    return final_result
