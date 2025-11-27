"""CSV export system for ClipScribe intelligence data.

Generates CSV files that open perfectly in:
- Google Sheets
- Microsoft Excel
- Apple Numbers
- Any CSV-compatible tool
"""

import csv
from pathlib import Path


def export_to_csv(intelligence_result, transcript_result, output_path: Path):
    """Export intelligence and transcript data to CSV files.

    Args:
        intelligence_result: IntelligenceResult from provider
        transcript_result: TranscriptResult from provider
        output_path: Directory to save CSV files

    Returns:
        Dict with paths to generated CSV files
    """
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    csv_files = {}

    # Entities CSV
    if intelligence_result.entities:
        entities_path = output_path / "entities.csv"
        # Use UTF-8 with BOM for Excel compatibility
        with open(entities_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["name", "type", "confidence", "evidence"])
            writer.writeheader()

            for entity in intelligence_result.entities:
                writer.writerow(
                    {
                        "name": entity.get("name", ""),
                        "type": entity.get("type", ""),
                        "confidence": entity.get("confidence", 0),
                        "evidence": entity.get("evidence", "")[:500],  # Truncate very long evidence
                    }
                )
        csv_files["entities"] = entities_path

    # Relationships CSV
    if intelligence_result.relationships:
        rels_path = output_path / "relationships.csv"
        # Use UTF-8 with BOM for Excel compatibility
        with open(rels_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(
                f, fieldnames=["subject", "predicate", "object", "evidence", "confidence"]
            )
            writer.writeheader()

            for rel in intelligence_result.relationships:
                writer.writerow(
                    {
                        "subject": rel.get("subject", ""),
                        "predicate": rel.get("predicate", ""),
                        "object": rel.get("object", ""),
                        "evidence": rel.get("evidence", "")[:500],
                        "confidence": rel.get("confidence", 0),
                    }
                )
        csv_files["relationships"] = rels_path

    # Topics CSV
    if intelligence_result.topics:
        topics_path = output_path / "topics.csv"
        # Use UTF-8 with BOM for Excel compatibility
        with open(topics_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["name", "relevance", "time_range"])
            writer.writeheader()

            for topic in intelligence_result.topics:
                writer.writerow(
                    {
                        "name": topic.get("name", ""),
                        "relevance": topic.get("relevance", 0),
                        "time_range": topic.get("time_range", ""),
                    }
                )
        csv_files["topics"] = topics_path

    # Key Moments CSV
    if intelligence_result.key_moments:
        moments_path = output_path / "key_moments.csv"
        # Use UTF-8 with BOM for Excel compatibility
        with open(moments_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(
                f, fieldnames=["timestamp", "description", "significance", "quote"]
            )
            writer.writeheader()

            for moment in intelligence_result.key_moments:
                writer.writerow(
                    {
                        "timestamp": moment.get("timestamp", ""),
                        "description": moment.get("description", ""),
                        "significance": moment.get("significance", 0),
                        "quote": moment.get("quote", "")[:500],
                    }
                )
        csv_files["key_moments"] = moments_path

    # Segments CSV (speaker-attributed transcript)
    if transcript_result.segments:
        segments_path = output_path / "segments.csv"
        # Use UTF-8 with BOM for Excel compatibility
        with open(segments_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["start", "end", "speaker", "text", "confidence"])
            writer.writeheader()

            for segment in transcript_result.segments:
                writer.writerow(
                    {
                        "start": segment.start,
                        "end": segment.end,
                        "speaker": segment.speaker or "",
                        "text": segment.text,
                        "confidence": segment.confidence,
                    }
                )
        csv_files["segments"] = segments_path

    return csv_files
