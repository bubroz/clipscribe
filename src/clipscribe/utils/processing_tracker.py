"""
Track processed videos to avoid duplicates and enable resume.

Multi-level tracking:
1. Video IDs (avoid re-downloading)
2. Processing status (completed, failed, in-progress)
3. Output locations (quick retrieval)
4. Processing metadata (cost, time, quality)
"""

import json
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ProcessingStatus(str, Enum):
    """Status of video processing."""

    PENDING = "pending"
    DOWNLOADING = "downloading"
    TRANSCRIBING = "transcribing"
    EXTRACTING = "extracting"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingTracker:
    """
    Track all processed videos to avoid duplicates.

    Features:
    - Persistent state (JSON file)
    - Video ID → output location mapping
    - Processing status tracking
    - Quick lookup (O(1) for "have we processed this?")
    - Metadata storage (cost, time, entity count)

    Use cases:
    - Skip already-processed videos
    - Resume failed processing
    - Find output for previously processed video
    - Track processing history
    """

    def __init__(self, db_file: Optional[Path] = None):
        """
        Initialize processing tracker.

        Args:
            db_file: Path to tracking database (default: ~/.clipscribe_processing.json)
        """
        self.db_file = db_file or Path.home() / ".clipscribe_processing.json"
        self.db: Dict[str, Dict] = self._load_db()

        logger.info(f"ProcessingTracker initialized: {len(self.db)} videos tracked")

    def _load_db(self) -> Dict[str, Dict]:
        """Load processing database from file."""
        if self.db_file.exists():
            try:
                with open(self.db_file) as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load processing DB: {e}")

        return {}

    def _save_db(self):
        """Save processing database to file."""
        try:
            # Create backup before saving
            if self.db_file.exists():
                backup_file = self.db_file.with_suffix(".json.bak")
                self.db_file.rename(backup_file)

            with open(self.db_file, "w") as f:
                json.dump(self.db, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save processing DB: {e}")

    def is_processed(self, video_id: str) -> bool:
        """
        Check if video has been successfully processed.

        Args:
            video_id: YouTube video ID

        Returns:
            True if processed and completed, False otherwise
        """
        if video_id not in self.db:
            return False

        status = self.db[video_id].get("status")
        return status == ProcessingStatus.COMPLETED

    def get_output_location(self, video_id: str) -> Optional[str]:
        """
        Get output directory for processed video.

        Args:
            video_id: YouTube video ID

        Returns:
            Output directory path if processed, None otherwise
        """
        if video_id in self.db and self.db[video_id].get("status") == ProcessingStatus.COMPLETED:
            return self.db[video_id].get("output_dir")

        return None

    def mark_processing(
        self, video_id: str, url: str, status: ProcessingStatus = ProcessingStatus.PENDING
    ):
        """
        Mark video as being processed.

        Args:
            video_id: YouTube video ID
            url: Full video URL
            status: Current processing status
        """
        if video_id not in self.db:
            self.db[video_id] = {
                "video_id": video_id,
                "url": url,
                "status": status,
                "first_seen": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "attempts": 0,
            }
        else:
            self.db[video_id]["status"] = status
            self.db[video_id]["last_updated"] = datetime.now().isoformat()
            self.db[video_id]["attempts"] += 1

        self._save_db()

    def mark_completed(self, video_id: str, output_dir: str, metadata: Optional[Dict] = None):
        """
        Mark video as successfully processed.

        Args:
            video_id: YouTube video ID
            output_dir: Where outputs were saved
            metadata: Optional processing metadata (cost, time, entity count, etc.)
        """
        if video_id not in self.db:
            logger.warning(f"Marking completion for untracked video: {video_id}")
            self.db[video_id] = {}

        self.db[video_id].update(
            {
                "status": ProcessingStatus.COMPLETED,
                "output_dir": output_dir,
                "completed_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
            }
        )

        # Add optional metadata
        if metadata:
            self.db[video_id]["metadata"] = metadata

        self._save_db()
        logger.info(f"Marked {video_id} as completed: {output_dir}")

    def mark_failed(self, video_id: str, error: str):
        """
        Mark video processing as failed.

        Args:
            video_id: YouTube video ID
            error: Error message
        """
        if video_id in self.db:
            self.db[video_id].update(
                {
                    "status": ProcessingStatus.FAILED,
                    "error": error,
                    "failed_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                }
            )
            self._save_db()

    def get_processed_count(self) -> int:
        """Get count of successfully processed videos."""
        return sum(1 for v in self.db.values() if v.get("status") == ProcessingStatus.COMPLETED)

    def get_failed_count(self) -> int:
        """Get count of failed processing attempts."""
        return sum(1 for v in self.db.values() if v.get("status") == ProcessingStatus.FAILED)

    def get_stats(self) -> Dict:
        """Get processing statistics."""
        total = len(self.db)
        completed = self.get_processed_count()
        failed = self.get_failed_count()
        in_progress = sum(
            1
            for v in self.db.values()
            if v.get("status") not in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]
        )

        return {
            "total_tracked": total,
            "completed": completed,
            "failed": failed,
            "in_progress": in_progress,
            "success_rate": f"{completed / total * 100:.1f}%" if total > 0 else "0%",
        }

    def get_failed_videos(self) -> list:
        """Get list of failed video IDs for retry."""
        return [
            vid for vid, data in self.db.items() if data.get("status") == ProcessingStatus.FAILED
        ]

    def clear_failed(self):
        """Clear failed videos to allow retry."""
        for video_id in list(self.db.keys()):
            if self.db[video_id].get("status") == ProcessingStatus.FAILED:
                del self.db[video_id]

        self._save_db()
        logger.info("Cleared all failed videos from tracker")
