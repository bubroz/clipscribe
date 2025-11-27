"""Series analysis for cross-video intelligence extraction.

This is ClipScribe's premium feature - analyze entities, relationships, and topics
across multiple videos to find patterns, trends, and insights.
"""

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List


class SeriesAnalyzer:
    """Analyze multiple videos as a corpus for aggregate intelligence."""

    def __init__(self, series_name: str):
        self.series_name = series_name
        self.videos = []

    def add_video(self, video_result: Dict[str, Any], video_filename: str):
        """Add a processed video to the series.

        Args:
            video_result: Dict with 'transcript' and 'intelligence' keys
            video_filename: Original filename
        """
        self.videos.append({"filename": video_filename, "result": video_result})

    def analyze(self) -> Dict[str, Any]:
        """Perform comprehensive series analysis.

        Returns:
            Dict with aggregate statistics, insights, and cross-video intelligence
        """
        if not self.videos:
            return {}

        # Collect all entities
        entity_mentions = defaultdict(list)
        all_entities = []

        for video_idx, video in enumerate(self.videos):
            intelligence = video["result"].get("intelligence", {})
            for entity in intelligence.get("entities", []):
                entity_name = entity.get("name", "Unknown")
                entity_mentions[entity_name].append(
                    {
                        "video_index": video_idx,
                        "video_filename": video["filename"],
                        "type": entity.get("type", "UNKNOWN"),
                        "confidence": entity.get("confidence", 0),
                        "evidence": entity.get("evidence", ""),
                    }
                )
                all_entities.append(entity)

        # Entity frequency analysis
        entity_frequency = {}
        for name, mentions in entity_mentions.items():
            entity_frequency[name] = {
                "count": len(mentions),
                "videos": list(set(m["video_index"] for m in mentions)),
                "video_filenames": list(set(m["video_filename"] for m in mentions)),
                "type": mentions[0]["type"],
                "avg_confidence": sum(m["confidence"] for m in mentions) / len(mentions),
                "evidences": [m["evidence"] for m in mentions],
            }

        # Top entities by frequency
        top_entities = sorted(entity_frequency.items(), key=lambda x: x[1]["count"], reverse=True)[
            :20
        ]

        # Collect all relationships
        all_relationships = []
        relationship_patterns = defaultdict(list)

        for video_idx, video in enumerate(self.videos):
            intelligence = video["result"].get("intelligence", {})
            for rel in intelligence.get("relationships", []):
                all_relationships.append(rel)
                # Track relationship patterns
                pattern = (rel.get("subject", ""), rel.get("predicate", ""), rel.get("object", ""))
                relationship_patterns[pattern].append(
                    {
                        "video_index": video_idx,
                        "video_filename": video["filename"],
                        "evidence": rel.get("evidence", ""),
                        "confidence": rel.get("confidence", 0),
                    }
                )

        # Recurring relationships
        recurring_relationships = {
            pattern: {
                "count": len(occurrences),
                "videos": list(set(o["video_index"] for o in occurrences)),
                "evidences": [o["evidence"] for o in occurrences],
                "avg_confidence": sum(o["confidence"] for o in occurrences) / len(occurrences),
            }
            for pattern, occurrences in relationship_patterns.items()
            if len(occurrences) > 1
        }

        # Topic evolution
        topic_timeline = defaultdict(list)
        for video_idx, video in enumerate(self.videos):
            intelligence = video["result"].get("intelligence", {})
            for topic in intelligence.get("topics", []):
                topic_name = topic.get("name", "Unknown")
                topic_timeline[topic_name].append(
                    {
                        "video_index": video_idx,
                        "video_filename": video["filename"],
                        "relevance": topic.get("relevance", 0),
                        "time_range": topic.get("time_range", ""),
                    }
                )

        # Topic trends
        topic_trends = {}
        for topic_name, appearances in topic_timeline.items():
            if len(appearances) > 1:
                topic_trends[topic_name] = {
                    "appearances": len(appearances),
                    "videos": [a["video_index"] for a in appearances],
                    "relevance_trend": [a["relevance"] for a in appearances],
                    "avg_relevance": sum(a["relevance"] for a in appearances) / len(appearances),
                }

        # Generate insights
        insights = self._generate_insights(
            entity_frequency, recurring_relationships, topic_trends, len(self.videos)
        )

        # Aggregate statistics
        total_duration = sum(
            v["result"].get("transcript", {}).get("duration", 0) for v in self.videos
        )

        total_cost = sum(
            v["result"].get("file_metadata", {}).get("total_cost", 0) for v in self.videos
        )

        return {
            "series_name": self.series_name,
            "total_videos": len(self.videos),
            "total_duration_minutes": total_duration / 60,
            "total_cost": total_cost,
            "unique_entities": len(entity_frequency),
            "total_entity_mentions": len(all_entities),
            "total_relationships": len(all_relationships),
            "top_entities": [
                {
                    "name": name,
                    "count": data["count"],
                    "frequency_percent": (data["count"] / len(all_entities)) * 100,
                    "videos": len(data["videos"]),
                    "type": data["type"],
                }
                for name, data in top_entities
            ],
            "entity_frequency": entity_frequency,
            "recurring_relationships": recurring_relationships,
            "topic_timeline": dict(topic_timeline),
            "topic_trends": topic_trends,
            "insights": insights,
            "processed_at": datetime.now().isoformat(),
        }

    def _generate_insights(
        self,
        entity_frequency: Dict,
        recurring_relationships: Dict,
        topic_trends: Dict,
        total_videos: int,
    ) -> List[str]:
        """Generate automated insights from series data.

        Returns:
            List of insight strings (ready for executive summary)
        """
        insights = []

        # Top entity insights
        if entity_frequency:
            top_entity = max(entity_frequency.items(), key=lambda x: x[1]["count"])
            entity_name, entity_data = top_entity
            video_count = len(entity_data["videos"])
            mention_count = entity_data["count"]

            insights.append(
                f"{entity_name} appeared in {video_count}/{total_videos} videos "
                f"({(video_count/total_videos)*100:.0f}% presence) with {mention_count} total mentions"
            )

        # Relationship patterns
        if recurring_relationships:
            top_rel = max(recurring_relationships.items(), key=lambda x: x[1]["count"])
            (subj, pred, obj), rel_data = top_rel
            rel_count = rel_data["count"]
            rel_videos = len(rel_data["videos"])

            insights.append(
                f"'{subj} {pred} {obj}' relationship confirmed in {rel_videos} videos "
                f"({rel_count} mentions)"
            )

        # Topic trends
        if topic_trends:
            # Find increasing topics
            for topic, trend_data in topic_trends.items():
                relevances = trend_data["relevance_trend"]
                if len(relevances) >= 2:
                    change = ((relevances[-1] - relevances[0]) / relevances[0]) * 100
                    if abs(change) > 50:  # Significant change
                        direction = "increased" if change > 0 else "decreased"
                        insights.append(
                            f"Topic '{topic}' {direction} {abs(change):.0f}% from first to last video"
                        )
                        break  # One trend insight is enough

        # Coverage insight
        entities_per_video = len(entity_frequency) / total_videos
        insights.append(
            f"Average {entities_per_video:.1f} unique entities per video "
            f"(corpus richness indicator)"
        )

        # Add generic insight if we have few specific ones
        if len(insights) < 3:
            insights.append(f"Analyzed {total_videos} videos for comprehensive corpus intelligence")

        return insights[:5]  # Top 5 insights max
