"""
Series Detection for ClipScribe Multi-Video Intelligence.

Automatically detects video series and suggests intelligent groupings
using title patterns, temporal analysis, and content similarity.
"""

import logging
import re
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from collections import defaultdict, Counter
import asyncio

from ..models import VideoIntelligence, SeriesDetectionResult, SeriesMetadata, VideoSimilarity

logger = logging.getLogger(__name__)


class SeriesDetector:
    """
    Detects video series and suggests intelligent groupings.

    Features:
    - Title pattern analysis (Part 1, Part 2, Episode 1, etc.)
    - Temporal proximity analysis
    - Content similarity analysis
    - Channel consistency checking
    - AI-powered pattern recognition
    """

    def __init__(self, similarity_threshold: float = 0.7):
        """
        Initialize series detector.

        Args:
            similarity_threshold: Minimum similarity to consider videos related
        """
        self.similarity_threshold = similarity_threshold

        # Common series patterns
        self.series_patterns = [
            # Part-based patterns
            r"part\s*(\d+)",
            r"pt\.?\s*(\d+)",
            r"episode\s*(\d+)",
            r"ep\.?\s*(\d+)",
            r"chapter\s*(\d+)",
            r"ch\.?\s*(\d+)",
            r"volume\s*(\d+)",
            r"vol\.?\s*(\d+)",
            r"session\s*(\d+)",
            r"lesson\s*(\d+)",
            # Ordinal patterns
            r"(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)",
            r"(\d+)(st|nd|rd|th)",
            # Sequential patterns
            r"(\d+)\s*of\s*(\d+)",
            r"(\d+)/(\d+)",
            # Documentary-specific patterns
            r":\s*(.*?)\s*-\s*part\s*(\d+)",
            r"(.*?)\s*\|\s*part\s*(\d+)",
            # News/briefing patterns
            r"(daily|weekly|monthly)\s*(briefing|update|report)",
            r"(\d{4}-\d{2}-\d{2})",  # Date patterns
            r"(january|february|march|april|may|june|july|august|september|october|november|december)\s*(\d{1,2})",
        ]

        # Compile patterns for efficiency
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.series_patterns
        ]

        # Words that indicate continuation
        self.continuation_words = {
            "continues",
            "continued",
            "continuation",
            "part",
            "episode",
            "chapter",
            "follow-up",
            "followup",
            "sequel",
            "next",
            "previous",
            "update",
            "revisited",
            "extended",
            "expanded",
            "deep dive",
            "analysis",
        }

    async def detect_series(self, videos: List[VideoIntelligence]) -> SeriesDetectionResult:
        """
        Detect if videos form a series and suggest groupings.

        Args:
            videos: List of VideoIntelligence objects to analyze

        Returns:
            SeriesDetectionResult with detection confidence and suggested groupings
        """
        if len(videos) < 2:
            return SeriesDetectionResult(
                is_series=False,
                confidence=0.0,
                detection_method="insufficient_videos",
                user_confirmation_needed=False,
            )

        logger.info(f"Analyzing {len(videos)} videos for series patterns...")

        # Step 1: Title pattern analysis
        title_analysis = self._analyze_title_patterns(videos)

        # Step 2: Temporal analysis
        temporal_analysis = self._analyze_temporal_patterns(videos)

        # Step 3: Content similarity analysis
        content_analysis = await self._analyze_content_similarity(videos)

        # Step 4: Channel consistency analysis
        channel_analysis = self._analyze_channel_consistency(videos)

        # Step 5: Combine analyses and make decision
        detection_result = self._combine_analyses(
            videos, title_analysis, temporal_analysis, content_analysis, channel_analysis
        )

        logger.info(
            f"Series detection complete: {detection_result.is_series} (confidence: {detection_result.confidence:.2f})"
        )
        return detection_result

    def _analyze_title_patterns(self, videos: List[VideoIntelligence]) -> Dict[str, Any]:
        """Analyze title patterns for series indicators."""
        titles = [video.metadata.title for video in videos]
        pattern_matches = defaultdict(list)

        # Check each pattern against all titles
        for i, pattern in enumerate(self.compiled_patterns):
            for j, title in enumerate(titles):
                matches = pattern.findall(title.lower())
                if matches:
                    pattern_matches[i].append(
                        {
                            "video_index": j,
                            "title": title,
                            "matches": matches,
                            "pattern": self.series_patterns[i],
                        }
                    )

        # Find the most promising pattern
        best_pattern = None
        best_score = 0

        for pattern_idx, matches in pattern_matches.items():
            if len(matches) >= 2:  # At least 2 videos match
                # Score based on coverage and sequential nature
                coverage = len(matches) / len(videos)

                # Check if matches are sequential
                sequential_score = self._check_sequential_pattern(matches)

                total_score = coverage * 0.6 + sequential_score * 0.4

                if total_score > best_score:
                    best_score = total_score
                    best_pattern = {
                        "pattern": self.series_patterns[pattern_idx],
                        "matches": matches,
                        "score": total_score,
                        "coverage": coverage,
                        "sequential_score": sequential_score,
                    }

        # Check for common base titles
        base_title_analysis = self._analyze_base_titles(titles)

        return {
            "best_pattern": best_pattern,
            "pattern_score": best_score,
            "base_title_analysis": base_title_analysis,
            "total_patterns_found": len(pattern_matches),
        }

    def _check_sequential_pattern(self, matches: List[Dict]) -> float:
        """Check if pattern matches are sequential (Part 1, Part 2, etc.)."""
        if len(matches) < 2:
            return 0.0

        # Extract numbers from matches
        numbers = []
        for match in matches:
            for match_group in match["matches"]:
                if isinstance(match_group, tuple):
                    # Handle tuple matches (like "1 of 3")
                    for item in match_group:
                        if item.isdigit():
                            numbers.append(int(item))
                            break
                elif isinstance(match_group, str) and match_group.isdigit():
                    numbers.append(int(match_group))

        if not numbers:
            return 0.0

        # Check if numbers are sequential
        numbers.sort()
        expected_sequence = list(range(numbers[0], numbers[0] + len(numbers)))

        # Calculate how close to sequential the numbers are
        sequential_score = sum(
            1
            for i, num in enumerate(numbers)
            if i < len(expected_sequence) and num == expected_sequence[i]
        ) / len(numbers)

        return sequential_score

    def _analyze_base_titles(self, titles: List[str]) -> Dict[str, Any]:
        """Analyze if videos share a common base title."""
        if len(titles) < 2:
            return {"has_common_base": False, "similarity": 0.0}

        # Find longest common substring among all titles
        common_base = titles[0]
        total_similarity = 0

        for i in range(1, len(titles)):
            similarity = SequenceMatcher(None, common_base.lower(), titles[i].lower()).ratio()
            total_similarity += similarity

            # Update common base to intersection
            matcher = SequenceMatcher(None, common_base.lower(), titles[i].lower())
            matching_blocks = matcher.get_matching_blocks()
            if matching_blocks:
                # Get the longest matching block
                longest_match = max(matching_blocks, key=lambda x: x.size)
                if longest_match.size > 10:  # Minimum meaningful length
                    common_base = common_base[
                        longest_match.a : longest_match.a + longest_match.size
                    ]

        avg_similarity = total_similarity / (len(titles) - 1)

        return {
            "has_common_base": avg_similarity > 0.6,
            "common_base": common_base.strip() if avg_similarity > 0.6 else "",
            "average_similarity": avg_similarity,
            "title_similarities": [
                SequenceMatcher(None, titles[0].lower(), title.lower()).ratio()
                for title in titles[1:]
            ],
        }

    def _analyze_temporal_patterns(self, videos: List[VideoIntelligence]) -> Dict[str, Any]:
        """Analyze temporal patterns (upload dates, duration consistency)."""
        # Sort videos by publication date
        sorted_videos = sorted(videos, key=lambda v: v.metadata.published_at)

        # Calculate time gaps between videos
        time_gaps = []
        for i in range(1, len(sorted_videos)):
            gap = (
                sorted_videos[i].metadata.published_at - sorted_videos[i - 1].metadata.published_at
            )
            time_gaps.append(gap.total_seconds() / 86400)  # Convert to days

        # Analyze duration consistency
        durations = [video.metadata.duration for video in videos]
        avg_duration = sum(durations) / len(durations)
        duration_variance = sum((d - avg_duration) ** 2 for d in durations) / len(durations)
        duration_consistency = 1.0 / (1.0 + duration_variance / (avg_duration**2))

        # Analyze temporal clustering
        temporal_score = 0.0
        if time_gaps:
            avg_gap = sum(time_gaps) / len(time_gaps)
            gap_variance = sum((gap - avg_gap) ** 2 for gap in time_gaps) / len(time_gaps)

            # Regular intervals suggest series
            if avg_gap < 30 and gap_variance < (avg_gap**2):  # Within 30 days, consistent intervals
                temporal_score = 0.8
            elif avg_gap < 90:  # Within 3 months
                temporal_score = 0.5
            else:
                temporal_score = 0.2

        return {
            "time_gaps_days": time_gaps,
            "average_gap_days": sum(time_gaps) / len(time_gaps) if time_gaps else 0,
            "duration_consistency": duration_consistency,
            "temporal_score": temporal_score,
            "publication_span_days": (
                sorted_videos[-1].metadata.published_at - sorted_videos[0].metadata.published_at
            ).total_seconds()
            / 86400,
        }

    async def _analyze_content_similarity(self, videos: List[VideoIntelligence]) -> Dict[str, Any]:
        """Analyze content similarity between videos."""
        similarities = []

        # Compare each pair of videos
        for i in range(len(videos)):
            for j in range(i + 1, len(videos)):
                similarity = await self._calculate_video_similarity(videos[i], videos[j])
                similarities.append(similarity)

        if not similarities:
            return {"average_similarity": 0.0, "similarities": []}

        # Calculate average similarity metrics
        avg_overall = sum(s.overall_similarity for s in similarities) / len(similarities)
        avg_topic = sum(s.topic_similarity for s in similarities) / len(similarities)
        avg_entity = sum(s.entity_overlap for s in similarities) / len(similarities)

        return {
            "average_similarity": avg_overall,
            "average_topic_similarity": avg_topic,
            "average_entity_overlap": avg_entity,
            "similarities": similarities,
            "high_similarity_pairs": [s for s in similarities if s.overall_similarity > 0.7],
        }

    async def _calculate_video_similarity(
        self, video1: VideoIntelligence, video2: VideoIntelligence
    ) -> VideoSimilarity:
        """Calculate similarity between two videos."""
        # Topic similarity
        topics1 = {topic.name.lower() for topic in video1.topics}
        topics2 = {topic.name.lower() for topic in video2.topics}
        topic_intersection = len(topics1 & topics2)
        topic_union = len(topics1 | topics2)
        topic_similarity = topic_intersection / topic_union if topic_union > 0 else 0.0

        # Entity overlap
        entities1 = {entity.name.lower() for entity in video1.entities}
        entities2 = {entity.name.lower() for entity in video2.entities}
        entity_intersection = len(entities1 & entities2)
        entity_union = len(entities1 | entities2)
        entity_overlap = entity_intersection / entity_union if entity_union > 0 else 0.0

        # Temporal proximity (closer in time = higher score)
        time_diff = abs(
            (video1.metadata.published_at - video2.metadata.published_at).total_seconds()
        )
        max_time_diff = 365 * 24 * 3600  # 1 year in seconds
        temporal_proximity = max(0, 1 - (time_diff / max_time_diff))

        # Channel match
        channel_match = video1.metadata.channel == video2.metadata.channel

        # Title similarity
        title_similarity = SequenceMatcher(
            None, video1.metadata.title.lower(), video2.metadata.title.lower()
        ).ratio()

        # Overall similarity (weighted combination)
        overall_similarity = (
            topic_similarity * 0.3
            + entity_overlap * 0.3
            + title_similarity * 0.2
            + temporal_proximity * 0.1
            + (1.0 if channel_match else 0.0) * 0.1
        )

        return VideoSimilarity(
            video1_id=video1.metadata.video_id,
            video2_id=video2.metadata.video_id,
            overall_similarity=overall_similarity,
            topic_similarity=topic_similarity,
            entity_overlap=entity_overlap,
            temporal_proximity=temporal_proximity,
            channel_match=channel_match,
            title_similarity=title_similarity,
            shared_entities=list(entities1 & entities2),
            shared_topics=list(topics1 & topics2),
        )

    def _analyze_channel_consistency(self, videos: List[VideoIntelligence]) -> Dict[str, Any]:
        """Analyze channel consistency across videos."""
        channels = [video.metadata.channel for video in videos]
        channel_counts = Counter(channels)

        # Check if all videos are from the same channel
        same_channel = len(channel_counts) == 1
        dominant_channel = channel_counts.most_common(1)[0] if channel_counts else None

        channel_score = (
            1.0
            if same_channel
            else (dominant_channel[1] / len(videos) if dominant_channel else 0.0)
        )

        return {
            "same_channel": same_channel,
            "channel_consistency_score": channel_score,
            "channel_distribution": dict(channel_counts),
            "dominant_channel": dominant_channel[0] if dominant_channel else None,
        }

    def _combine_analyses(
        self,
        videos: List[VideoIntelligence],
        title_analysis: Dict[str, Any],
        temporal_analysis: Dict[str, Any],
        content_analysis: Dict[str, Any],
        channel_analysis: Dict[str, Any],
    ) -> SeriesDetectionResult:
        """Combine all analyses to make final series detection decision."""

        # Calculate weighted confidence score
        title_weight = 0.4
        content_weight = 0.3
        temporal_weight = 0.2
        channel_weight = 0.1

        title_score = title_analysis["pattern_score"] if title_analysis["best_pattern"] else 0.0
        content_score = content_analysis["average_similarity"]
        temporal_score = temporal_analysis["temporal_score"]
        channel_score = channel_analysis["channel_consistency_score"]

        overall_confidence = (
            title_score * title_weight
            + content_score * content_weight
            + temporal_score * temporal_weight
            + channel_score * channel_weight
        )

        # Determine if it's a series
        is_series = overall_confidence > self.similarity_threshold

        # Generate suggested groupings
        suggested_groupings = self._generate_groupings(videos, title_analysis, content_analysis)

        # Determine detection method
        detection_methods = []
        if title_score > 0.5:
            detection_methods.append("title_patterns")
        if content_score > 0.6:
            detection_methods.append("content_similarity")
        if temporal_score > 0.5:
            detection_methods.append("temporal_patterns")
        if channel_score > 0.8:
            detection_methods.append("channel_consistency")

        detection_method = (
            "+".join(detection_methods) if detection_methods else "insufficient_evidence"
        )

        # Determine if user confirmation is needed
        user_confirmation_needed = overall_confidence < 0.9 or len(suggested_groupings) > 1

        # Extract detected patterns
        series_patterns = []
        if title_analysis["best_pattern"]:
            series_patterns.append(title_analysis["best_pattern"]["pattern"])
        if content_analysis["high_similarity_pairs"]:
            series_patterns.append("high_content_similarity")

        return SeriesDetectionResult(
            is_series=is_series,
            confidence=overall_confidence,
            suggested_grouping=suggested_groupings,
            detection_method=detection_method,
            series_patterns=series_patterns,
            user_confirmation_needed=user_confirmation_needed,
        )

    def _generate_groupings(
        self,
        videos: List[VideoIntelligence],
        title_analysis: Dict[str, Any],
        content_analysis: Dict[str, Any],
    ) -> List[List[str]]:
        """Generate suggested video groupings."""
        video_ids = [video.metadata.video_id for video in videos]

        # If we have a strong title pattern, group by that
        if title_analysis["best_pattern"] and title_analysis["pattern_score"] > 0.7:
            # Group videos that match the pattern
            pattern_videos = [
                video_ids[match["video_index"]]
                for match in title_analysis["best_pattern"]["matches"]
            ]

            # Add any remaining videos as separate groups or ungrouped
            remaining_videos = [vid for vid in video_ids if vid not in pattern_videos]

            groupings = [pattern_videos]
            if remaining_videos:
                groupings.extend([[vid] for vid in remaining_videos])

            return groupings

        # Otherwise, group by content similarity
        elif content_analysis["high_similarity_pairs"]:
            # Use graph clustering based on similarity
            groups = self._cluster_by_similarity(video_ids, content_analysis["similarities"])
            return groups

        # Default: treat all as one group if moderate similarity
        elif content_analysis["average_similarity"] > 0.5:
            return [video_ids]

        # No clear grouping
        else:
            return [[vid] for vid in video_ids]

    def _cluster_by_similarity(
        self, video_ids: List[str], similarities: List[VideoSimilarity]
    ) -> List[List[str]]:
        """Cluster videos by similarity using simple graph clustering."""
        # Build adjacency list
        graph = defaultdict(set)
        for sim in similarities:
            if sim.overall_similarity > self.similarity_threshold:
                graph[sim.video1_id].add(sim.video2_id)
                graph[sim.video2_id].add(sim.video1_id)

        # Find connected components
        visited = set()
        clusters = []

        for video_id in video_ids:
            if video_id not in visited:
                cluster = []
                stack = [video_id]

                while stack:
                    current = stack.pop()
                    if current not in visited:
                        visited.add(current)
                        cluster.append(current)
                        stack.extend(graph[current] - visited)

                clusters.append(cluster)

        return clusters

    def create_series_metadata(
        self, videos: List[VideoIntelligence], detection_result: SeriesDetectionResult
    ) -> SeriesMetadata:
        """Create series metadata from detection results."""
        if not detection_result.is_series:
            raise ValueError("Cannot create series metadata for non-series videos")

        # Generate series ID and title
        first_video = videos[0]
        series_id = f"series_{first_video.metadata.channel_id}_{len(videos)}_{datetime.now().strftime('%Y%m%d')}"

        # Try to extract series title from common base
        base_title = ""
        if len(videos) > 1:
            titles = [v.metadata.title for v in videos]
            base_analysis = self._analyze_base_titles(titles)
            if base_analysis["has_common_base"]:
                base_title = base_analysis["common_base"]
            else:
                # Use first video title with part info removed
                base_title = re.sub(
                    r"\s*(part|pt\.?|episode|ep\.?)\s*\d+.*$", "", titles[0], flags=re.IGNORECASE
                ).strip()

        series_title = base_title or f"{first_video.metadata.channel} Video Series"

        # Detect pattern
        pattern = (
            detection_result.series_patterns[0]
            if detection_result.series_patterns
            else "content_similarity"
        )

        return SeriesMetadata(
            series_id=series_id,
            series_title=series_title,
            total_parts=len(videos),
            series_pattern=pattern,
            confidence=detection_result.confidence,
        )
