"""
Temporal Reference Resolver - Phase 3 of Enhanced Metadata.

Resolves relative temporal references ("last Tuesday", "yesterday") to absolute dates
using explicit video publication date context for LLM processing.
"""

import logging
import re
from datetime import datetime
from typing import List, Optional

from ..models import TemporalReference, VideoIntelligence

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

        # Method 2: Date extraction moved to HybridProcessor (Grok)
        logger.info("Date extraction moved to HybridProcessor with Grok")

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

    def _get_content_date(
        self, video_intel: VideoIntelligence, publication_date: datetime
    ) -> Optional[datetime]:
        """Get content date - method deprecated (Gemini removed)."""
        # Method deprecated - date extraction moved to HybridProcessor
        return None
