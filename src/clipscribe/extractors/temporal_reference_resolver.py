"""
Temporal Reference Resolver - Phase 3 of Enhanced Metadata.

Resolves relative temporal references ("last Tuesday", "yesterday") to absolute dates
using explicit video publication date context for LLM processing.
"""

import logging
import re
from typing import List, Optional
from datetime import datetime, timedelta

from ..models import VideoIntelligence, VideoMetadata, TemporalReference

logger = logging.getLogger(__name__)


class TemporalReferenceResolver:
    """Resolve relative temporal references using explicit video context."""

    def __init__(self):
        # Regex patterns for temporal references
        self.temporal_patterns = [
            # Relative weekdays
            r"\b(?:last|previous)\s+(\w+day)\b",
            r"\bnext\s+(\w+day)\b",
            # Relative days
            r"\byesterday\b",
            r"\btoday\b",
            r"\btomorrow\b",
            r"\b(\d+)\s+days?\s+ago\b",
            r"\bin\s+(\d+)\s+days?\b",
            # Relative weeks/months
            r"\blast\s+(week|month|year)\b",
            r"\bnext\s+(week|month|year)\b",
            r"\bthis\s+(week|month|year)\b",
            # Relative time periods
            r"\b(\d+)\s+(weeks?|months?|years?)\s+ago\b",
            r"\bin\s+(\d+)\s+(weeks?|months?|years?)\b",
        ]

        # Weekday mapping
        self.weekday_map = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }

    def resolve_temporal_references(
        self, video_intel: VideoIntelligence
    ) -> List[TemporalReference]:
        """
        Resolve temporal references in video transcript using intelligent date detection.

        Enhanced to handle cases where content date ≠ publication date.

        Args:
            video_intel: Complete video intelligence with metadata and transcript

        Returns:
            List of resolved temporal references
        """
        transcript_text = video_intel.transcript.full_text
        video_metadata = video_intel.metadata

        # Step 1: Get publication date as fallback
        publication_date = video_metadata.published_at
        if not publication_date:
            logger.warning("No publication date available, using current date")
            publication_date = datetime.now()

        # Step 2: ENHANCED - Detect actual content date
        content_date = self._detect_content_date(video_intel, publication_date)

        if content_date != publication_date:
            logger.info(
                f"Content date ({content_date.date()}) differs from publication date ({publication_date.date()})"
            )
            logger.info("Using content date for temporal reference resolution")

        reference_date = content_date
        logger.info(f"Resolving temporal references using reference date: {reference_date.date()}")

        resolved_references = []

        # Find and resolve each temporal pattern
        for pattern in self.temporal_patterns:
            matches = list(re.finditer(pattern, transcript_text, re.IGNORECASE))

            for match in matches:
                resolved = self._resolve_match(match, reference_date, transcript_text)
                if resolved:
                    # Add metadata about date source
                    resolved.date_source = (
                        "content_date" if content_date != publication_date else "publication_date"
                    )
                    resolved.content_vs_publication_delta = (publication_date - content_date).days
                    resolved_references.append(resolved)

        # Deduplicate similar references
        deduplicated = self._deduplicate_references(resolved_references)

        logger.info(
            f"Resolved {len(deduplicated)} temporal references from {len(resolved_references)} matches"
        )

        return deduplicated

    def _detect_content_date(
        self, video_intel: VideoIntelligence, publication_date: datetime
    ) -> datetime:
        """
        Detect the actual content date vs publication date.

        Uses multiple signals to determine when content was actually created/filmed.
        """
        transcript_text = video_intel.transcript.full_text

        # Method 1: Check for explicit date mentions in transcript
        explicit_date = self._extract_explicit_content_date(transcript_text, publication_date)
        if explicit_date:
            confidence = 0.9
            logger.info(
                f"Found explicit content date: {explicit_date.date()} (confidence: {confidence})"
            )
            return explicit_date

        # Method 2: Check for Gemini-extracted dates
        gemini_date = self._get_gemini_content_date(video_intel, publication_date)
        if gemini_date:
            confidence = 0.8
            logger.info(
                f"Using Gemini-extracted content date: {gemini_date.date()} (confidence: {confidence})"
            )
            return gemini_date

        # Method 3: Analyze temporal context clues
        contextual_date = self._analyze_temporal_context_clues(transcript_text, publication_date)
        if contextual_date:
            confidence = 0.6
            logger.info(
                f"Inferred content date from context: {contextual_date.date()} (confidence: {confidence})"
            )
            return contextual_date

        # Method 4: Check video metadata for recording date
        metadata_date = self._check_metadata_recording_date(video_intel.metadata)
        if metadata_date:
            confidence = 0.7
            logger.info(
                f"Using metadata recording date: {metadata_date.date()} (confidence: {confidence})"
            )
            return metadata_date

        # Fallback: Use publication date
        logger.info("No content date detected, using publication date")
        return publication_date

    def _extract_explicit_content_date(
        self, transcript_text: str, publication_date: datetime
    ) -> Optional[datetime]:
        """Extract explicit date mentions that indicate content creation date."""

        # Patterns for explicit date mentions
        date_patterns = [
            # "This is March 15th, 2023"
            r"this is (\w+)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})",
            # "Today is March 15, 2023"
            r"today is (\w+)\s+(\d{1,2}),?\s+(\d{4})",
            # "It's March 15th, 2023"
            r"it's (\w+)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})",
            # "March 15, 2023" (standalone)
            r"(\w+)\s+(\d{1,2}),?\s+(\d{4})",
            # "2023-03-15" format
            r"(\d{4})-(\d{1,2})-(\d{1,2})",
        ]

        month_map = {
            "january": 1,
            "february": 2,
            "march": 3,
            "april": 4,
            "may": 5,
            "june": 6,
            "july": 7,
            "august": 8,
            "september": 9,
            "october": 10,
            "november": 11,
            "december": 12,
            "jan": 1,
            "feb": 2,
            "mar": 3,
            "apr": 4,
            "jun": 6,
            "jul": 7,
            "aug": 8,
            "sep": 9,
            "oct": 10,
            "nov": 11,
            "dec": 12,
        }

        for pattern in date_patterns:
            matches = re.finditer(pattern, transcript_text, re.IGNORECASE)
            for match in matches:
                try:
                    groups = match.groups()

                    if len(groups) == 3:
                        # Handle different formats
                        if groups[0].isdigit():  # YYYY-MM-DD format
                            year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                        else:  # Month Day, Year format
                            month_name = groups[0].lower()
                            if month_name in month_map:
                                month = month_map[month_name]
                                day = int(groups[1])
                                year = int(groups[2])
                            else:
                                continue

                        content_date = datetime(year, month, day)

                        # Sanity check: content date should be before or near publication date
                        days_diff = (publication_date - content_date).days
                        if 0 <= days_diff <= 3650:  # Within 10 years
                            return content_date

                except (ValueError, IndexError):
                    continue

        return None

    def _get_gemini_content_date(
        self, video_intel: VideoIntelligence, publication_date: datetime
    ) -> Optional[datetime]:
        """Get content date from Gemini-extracted dates."""

        # Check if we have Gemini-extracted dates
        if hasattr(video_intel, "dates") and video_intel.dates:
            dates = video_intel.dates
        elif hasattr(video_intel, "processing_stats") and "dates" in video_intel.processing_stats:
            dates = video_intel.processing_stats["dates"]
        else:
            return None

        # Look for dates that seem to indicate content creation
        content_indicators = [
            "today",
            "this is",
            "recording",
            "filming",
            "broadcast",
            "live",
            "current",
            "now",
            "present",
        ]

        for date_info in dates:
            context = date_info.get("context", "").lower()
            original_text = date_info.get("original_text", "").lower()

            # Check if this date indicates content creation time
            if any(
                indicator in context or indicator in original_text
                for indicator in content_indicators
            ):
                try:
                    normalized_date = date_info.get("normalized_date")
                    if normalized_date:
                        content_date = datetime.fromisoformat(
                            normalized_date.replace("Z", "+00:00")
                        ).replace(tzinfo=None)

                        # Sanity check
                        days_diff = (publication_date - content_date).days
                        if 0 <= days_diff <= 3650:  # Within 10 years
                            return content_date
                except (ValueError, AttributeError):
                    continue

        return None

    def _analyze_temporal_context_clues(
        self, transcript_text: str, publication_date: datetime
    ) -> Optional[datetime]:
        """Analyze context clues to infer content date."""

        # Look for phrases that indicate old content
        archive_indicators = [
            r"archive footage",
            r"recorded (\w+) (\d{1,2}),? (\d{4})",
            r"filmed in (\d{4})",
            r"from our (\d{4}) interview",
            r"back in (\d{4})",
            r"(\d{4}) recording",
        ]

        for pattern in archive_indicators:
            matches = re.finditer(pattern, transcript_text, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                if groups:
                    try:
                        # Extract year and estimate content date
                        year = int(groups[-1])  # Last group is usually the year
                        if 1990 <= year <= publication_date.year:
                            # Estimate middle of the year
                            content_date = datetime(year, 6, 15)
                            return content_date
                    except (ValueError, IndexError):
                        continue

        return None

    def _check_metadata_recording_date(self, metadata: VideoMetadata) -> Optional[datetime]:
        """Check video metadata for recording date information."""

        # Some platforms provide recording date separate from publication date
        # This would need platform-specific implementation

        # For now, return None - could be enhanced with platform-specific logic
        return None

    def _resolve_match(
        self, match: re.Match, reference_date: datetime, transcript_text: str
    ) -> Optional[TemporalReference]:
        """Resolve a specific temporal reference match."""

        reference_text = match.group(0).lower()
        context = self._extract_context(match, transcript_text)

        # Resolve based on pattern type
        if "yesterday" in reference_text:
            resolved_date = reference_date - timedelta(days=1)
            return TemporalReference(
                reference_text=match.group(0),
                resolved_date=resolved_date.strftime("%Y-%m-%d"),
                confidence=0.95,
                resolution_method=f"yesterday_from_{reference_date.date()}",
                context=context,
                original_context=transcript_text[max(0, match.start() - 50) : match.end() + 50],
            )

        elif "today" in reference_text:
            return TemporalReference(
                reference_text=match.group(0),
                resolved_date=reference_date.strftime("%Y-%m-%d"),
                confidence=0.95,
                resolution_method=f"today_as_{reference_date.date()}",
                context=context,
                original_context=transcript_text[max(0, match.start() - 50) : match.end() + 50],
            )

        elif "tomorrow" in reference_text:
            resolved_date = reference_date + timedelta(days=1)
            return TemporalReference(
                reference_text=match.group(0),
                resolved_date=resolved_date.strftime("%Y-%m-%d"),
                confidence=0.95,
                resolution_method=f"tomorrow_from_{reference_date.date()}",
                context=context,
                original_context=transcript_text[max(0, match.start() - 50) : match.end() + 50],
            )

        elif "last" in reference_text and any(
            day in reference_text for day in self.weekday_map.keys()
        ):
            return self._resolve_last_weekday(match, reference_date, context, transcript_text)

        elif "next" in reference_text and any(
            day in reference_text for day in self.weekday_map.keys()
        ):
            return self._resolve_next_weekday(match, reference_date, context, transcript_text)

        elif "days ago" in reference_text:
            return self._resolve_days_ago(match, reference_date, context, transcript_text)

        elif "last week" in reference_text:
            resolved_date = reference_date - timedelta(weeks=1)
            return TemporalReference(
                reference_text=match.group(0),
                resolved_date=resolved_date.strftime("%Y-%m-%d"),
                confidence=0.80,  # Week references are less precise
                resolution_method=f"last_week_from_{reference_date.date()}",
                context=context,
                original_context=transcript_text[max(0, match.start() - 50) : match.end() + 50],
            )

        elif "last month" in reference_text:
            # Approximate - go back 30 days
            resolved_date = reference_date - timedelta(days=30)
            return TemporalReference(
                reference_text=match.group(0),
                resolved_date=resolved_date.strftime("%Y-%m-%d"),
                confidence=0.70,  # Month references are approximate
                resolution_method=f"last_month_approximate_from_{reference_date.date()}",
                context=context,
                original_context=transcript_text[max(0, match.start() - 50) : match.end() + 50],
            )

        # Add more resolution patterns as needed
        return None

    def _resolve_last_weekday(
        self, match: re.Match, reference_date: datetime, context: str, transcript_text: str
    ) -> Optional[TemporalReference]:
        """Resolve 'last Tuesday' style references."""

        # Extract weekday name
        weekday_match = re.search(
            r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
            match.group(0),
            re.IGNORECASE,
        )
        if not weekday_match:
            return None

        weekday_name = weekday_match.group(1).lower()
        target_weekday = self.weekday_map[weekday_name]

        # Calculate days back to last occurrence
        current_weekday = reference_date.weekday()
        days_back = (current_weekday - target_weekday + 7) % 7
        if days_back == 0:  # Same day, go back a week
            days_back = 7

        resolved_date = reference_date - timedelta(days=days_back)

        return TemporalReference(
            reference_text=match.group(0),
            resolved_date=resolved_date.strftime("%Y-%m-%d"),
            confidence=0.85,
            resolution_method=f"last_{weekday_name}_from_{reference_date.date()}",
            context=context,
            original_context=transcript_text[max(0, match.start() - 50) : match.end() + 50],
        )

    def _resolve_next_weekday(
        self, match: re.Match, reference_date: datetime, context: str, transcript_text: str
    ) -> Optional[TemporalReference]:
        """Resolve 'next Friday' style references."""

        # Extract weekday name
        weekday_match = re.search(
            r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
            match.group(0),
            re.IGNORECASE,
        )
        if not weekday_match:
            return None

        weekday_name = weekday_match.group(1).lower()
        target_weekday = self.weekday_map[weekday_name]

        # Calculate days forward to next occurrence
        current_weekday = reference_date.weekday()
        days_forward = (target_weekday - current_weekday) % 7
        if days_forward == 0:  # Same day, go forward a week
            days_forward = 7

        resolved_date = reference_date + timedelta(days=days_forward)

        return TemporalReference(
            reference_text=match.group(0),
            resolved_date=resolved_date.strftime("%Y-%m-%d"),
            confidence=0.85,
            resolution_method=f"next_{weekday_name}_from_{reference_date.date()}",
            context=context,
            original_context=transcript_text[max(0, match.start() - 50) : match.end() + 50],
        )

    def _resolve_days_ago(
        self, match: re.Match, reference_date: datetime, context: str, transcript_text: str
    ) -> Optional[TemporalReference]:
        """Resolve '3 days ago' style references."""

        # Extract number of days
        days_match = re.search(r"(\d+)", match.group(0))
        if not days_match:
            return None

        days_back = int(days_match.group(1))
        resolved_date = reference_date - timedelta(days=days_back)

        return TemporalReference(
            reference_text=match.group(0),
            resolved_date=resolved_date.strftime("%Y-%m-%d"),
            confidence=0.90,
            resolution_method=f"{days_back}_days_ago_from_{reference_date.date()}",
            context=context,
            original_context=transcript_text[max(0, match.start() - 50) : match.end() + 50],
        )

    def _extract_context(self, match: re.Match, text: str, window: int = 30) -> str:
        """Extract context around a temporal reference."""
        start = max(0, match.start() - window)
        end = min(len(text), match.end() + window)
        return text[start:end].strip()

    def _deduplicate_references(
        self, references: List[TemporalReference]
    ) -> List[TemporalReference]:
        """Remove duplicate temporal references."""
        seen = set()
        deduplicated = []

        for ref in references:
            # Create key based on reference text and resolved date
            key = (ref.reference_text.lower(), ref.resolved_date)
            if key not in seen:
                seen.add(key)
                deduplicated.append(ref)

        return deduplicated

    def build_explicit_context_prompt(
        self, transcript_text: str, video_metadata: VideoMetadata
    ) -> str:
        """
        Build prompt with explicit temporal context for LLM processing.

        This is the key method that provides explicit datetime context to LLMs.
        """
        reference_date = video_metadata.published_at
        if not reference_date:
            reference_date = datetime.now()

        # Build comprehensive temporal context
        prompt = f"""
        TEMPORAL REFERENCE RESOLUTION TASK
        
        CRITICAL CONTEXT - USE THIS AS YOUR REFERENCE POINT:
        - Video published on: {reference_date.strftime('%A, %B %d, %Y')}
        - Reference date: {reference_date.date()}
        - Day of week: {reference_date.strftime('%A')}
        
        RESOLUTION RULES:
        - "yesterday" = {(reference_date - timedelta(days=1)).date()}
        - "today" = {reference_date.date()}
        - "tomorrow" = {(reference_date + timedelta(days=1)).date()}
        - "last Tuesday" = the Tuesday before {reference_date.date()}
        - "next Friday" = the Friday after {reference_date.date()}
        
        VIDEO CONTEXT:
        - Title: {video_metadata.title}
        - Channel: {video_metadata.channel}
        - Duration: {video_metadata.duration} seconds
        
        TRANSCRIPT TO ANALYZE:
        {transcript_text}
        
        Find all temporal references and resolve them to absolute dates (YYYY-MM-DD format).
        Return confidence scores for each resolution.
        """

        return prompt
