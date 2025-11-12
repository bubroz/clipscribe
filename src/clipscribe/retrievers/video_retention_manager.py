"""Video Retention System for ClipScribe v2.17.0.

Smart video retention management with cost optimization.
Balances storage costs vs reprocessing costs for optimal efficiency.
"""

import json
import logging
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

from ..config.settings import Settings, VideoRetentionPolicy
from ..models import VideoIntelligence

logger = logging.getLogger(__name__)


class RetentionCostAnalysis:
    """Analysis of retention costs vs reprocessing costs."""

    def __init__(
        self,
        storage_cost_monthly: float,
        storage_cost_yearly: float,
        reprocessing_cost: float,
        breakeven_months: float,
        recommendation: str,
        confidence: float = 0.8,
    ):
        self.storage_cost_monthly = storage_cost_monthly
        self.storage_cost_yearly = storage_cost_yearly
        self.reprocessing_cost = reprocessing_cost
        self.breakeven_months = breakeven_months
        self.recommendation = recommendation  # "retain", "delete", "conditional"
        self.confidence = confidence


class VideoRetentionManager:
    """Manage video retention with intelligent cost optimization."""

    def __init__(self, settings: Optional[Settings] = None):
        """Initialize the retention manager."""
        self.settings = settings or Settings()
        self.retention_config = self.settings.get_video_retention_config()

        # Setup archive directory
        self.archive_dir = Path(self.retention_config["archive_directory"])
        self.archive_dir.mkdir(parents=True, exist_ok=True)

        # Retention tracking
        self.retention_log_file = self.archive_dir / "retention_log.json"
        self.retention_history = self._load_retention_history()

        logger.info(f"Video retention policy: {self.retention_config['policy']}")
        logger.info(f"Archive directory: {self.archive_dir}")

    def _load_retention_history(self) -> Dict[str, Any]:
        """Load retention history from disk."""
        if self.retention_log_file.exists():
            try:
                with open(self.retention_log_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load retention history: {e}")

        return {
            "retained_videos": {},
            "deleted_videos": {},
            "retention_stats": {
                "total_saved_cost": 0.0,
                "total_storage_cost": 0.0,
                "videos_retained": 0,
                "videos_deleted": 0,
            },
        }

    def _save_retention_history(self):
        """Save retention history to disk."""
        try:
            with open(self.retention_log_file, "w") as f:
                json.dump(self.retention_history, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Could not save retention history: {e}")

    def _get_video_hash(self, video_path: Path) -> str:
        """Generate stable ID for video file path (non-security)."""
        from ..utils.stable_id import generate_unversioned_digest

        return generate_unversioned_digest(str(video_path), algo="sha256", length=24)

    async def handle_video_retention(
        self,
        video_path: Path,
        processing_result: VideoIntelligence,
        force_policy: Optional[VideoRetentionPolicy] = None,
    ) -> Dict[str, Any]:
        """
        Handle video retention based on policy and cost analysis.

        Args:
            video_path: Path to the source video file
            processing_result: Results from video processing
            force_policy: Optional policy override

        Returns:
            Dictionary with retention decision and details
        """
        policy = force_policy or self.retention_config["policy"]

        logger.info(f"Handling video retention for: {video_path.name}")
        logger.info(f"Using policy: {policy}")

        # Check if video exists
        if not video_path.exists():
            logger.warning(f"Video file not found: {video_path}")
            return {
                "action": "not_found",
                "video_path": str(video_path),
                "reason": "Video file not found",
            }

        # Analyze retention costs
        cost_analysis = self._analyze_retention_costs(video_path, processing_result)

        # Make retention decision
        decision = self._make_retention_decision(policy, cost_analysis, processing_result)

        # Execute retention action
        result = await self._execute_retention_action(
            video_path, processing_result, decision, cost_analysis
        )

        # Update retention history
        self._update_retention_history(video_path, result, cost_analysis)

        return result

    def _analyze_retention_costs(
        self, video_path: Path, processing_result: VideoIntelligence
    ) -> RetentionCostAnalysis:
        """Analyze the costs of retention vs reprocessing."""

        # Get file size and duration
        file_size_bytes = video_path.stat().st_size
        file_size_gb = file_size_bytes / (1024**3)
        duration_seconds = processing_result.metadata.duration

        # Calculate storage costs (estimated)
        # Using typical cloud storage pricing: $0.023/GB/month
        storage_cost_monthly = file_size_gb * 0.023
        storage_cost_yearly = storage_cost_monthly * 12

        # Calculate reprocessing cost
        reprocessing_cost = self.settings.estimate_cost(
            duration_seconds, self.settings.temporal_intelligence_level
        )

        # Add overhead for download and processing time
        reprocessing_overhead = reprocessing_cost * 0.1  # 10% overhead
        total_reprocessing_cost = reprocessing_cost + reprocessing_overhead

        # Calculate breakeven point
        if storage_cost_monthly > 0:
            breakeven_months = total_reprocessing_cost / storage_cost_monthly
        else:
            breakeven_months = float("inf")

        # Make recommendation
        if breakeven_months < 3:
            recommendation = "delete"  # Storage more expensive than frequent reprocessing
        elif breakeven_months > 24:
            recommendation = "retain"  # Storage cheaper than infrequent reprocessing
        else:
            recommendation = "conditional"  # Depends on usage patterns

        confidence = min(0.9, 0.5 + (abs(breakeven_months - 12) / 24))

        return RetentionCostAnalysis(
            storage_cost_monthly=storage_cost_monthly,
            storage_cost_yearly=storage_cost_yearly,
            reprocessing_cost=total_reprocessing_cost,
            breakeven_months=breakeven_months,
            recommendation=recommendation,
            confidence=confidence,
        )

    def _make_retention_decision(
        self,
        policy: VideoRetentionPolicy,
        cost_analysis: RetentionCostAnalysis,
        processing_result: VideoIntelligence,
    ) -> Dict[str, Any]:
        """Make the retention decision based on policy and cost analysis."""

        if policy == VideoRetentionPolicy.DELETE:
            return {"action": "delete", "reason": "Policy: Always delete source videos"}

        elif policy == VideoRetentionPolicy.KEEP_ALL:
            return {"action": "archive", "reason": "Policy: Keep all source videos"}

        elif policy == VideoRetentionPolicy.KEEP_PROCESSED:
            # Use cost optimization if enabled
            if self.retention_config["cost_optimization"]:
                if cost_analysis.recommendation == "retain":
                    return {
                        "action": "archive",
                        "reason": f"Cost optimization: Storage cheaper (breakeven: {cost_analysis.breakeven_months:.1f} months)",
                    }
                elif cost_analysis.recommendation == "delete":
                    return {
                        "action": "delete",
                        "reason": f"Cost optimization: Reprocessing cheaper (breakeven: {cost_analysis.breakeven_months:.1f} months)",
                    }
                else:
                    # Conditional - use other factors
                    video_quality = getattr(processing_result, "confidence_score", 0.0)
                    if video_quality > 0.9:
                        return {
                            "action": "archive",
                            "reason": "High quality processing results worth retaining",
                        }
                    else:
                        return {
                            "action": "delete",
                            "reason": "Moderate quality results, reprocessing acceptable",
                        }
            else:
                return {
                    "action": "archive",
                    "reason": "Policy: Keep processed videos (no cost optimization)",
                }

        else:
            return {"action": "delete", "reason": "Unknown policy, defaulting to delete"}

    async def _execute_retention_action(
        self,
        video_path: Path,
        processing_result: VideoIntelligence,
        decision: Dict[str, Any],
        cost_analysis: RetentionCostAnalysis,
    ) -> Dict[str, Any]:
        """Execute the retention action."""

        action = decision["action"]
        video_hash = self._get_video_hash(video_path)

        if action == "delete":
            try:
                # Delete the source video
                os.remove(video_path)
                logger.info(f"Deleted source video: {video_path.name}")

                return {
                    "action": "deleted",
                    "video_path": str(video_path),
                    "video_hash": video_hash,
                    "reason": decision["reason"],
                    "cost_savings": {
                        "storage_cost_avoided": cost_analysis.storage_cost_yearly,
                        "reprocessing_cost": cost_analysis.reprocessing_cost,
                    },
                    "timestamp": datetime.now().isoformat(),
                }

            except Exception as e:
                logger.error(f"Failed to delete video {video_path}: {e}")
                return {
                    "action": "delete_failed",
                    "video_path": str(video_path),
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }

        elif action == "archive":
            try:
                # Create archive subdirectory based on date
                archive_subdir = self.archive_dir / datetime.now().strftime("%Y/%m")
                archive_subdir.mkdir(parents=True, exist_ok=True)

                # Move video to archive
                archive_path = archive_subdir / video_path.name
                shutil.move(str(video_path), str(archive_path))

                logger.info(f"Archived video: {video_path.name} -> {archive_path}")

                return {
                    "action": "archived",
                    "original_path": str(video_path),
                    "archive_path": str(archive_path),
                    "video_hash": video_hash,
                    "reason": decision["reason"],
                    "cost_implications": {
                        "storage_cost_yearly": cost_analysis.storage_cost_yearly,
                        "reprocessing_cost_avoided": cost_analysis.reprocessing_cost,
                    },
                    "timestamp": datetime.now().isoformat(),
                }

            except Exception as e:
                logger.error(f"Failed to archive video {video_path}: {e}")
                return {
                    "action": "archive_failed",
                    "video_path": str(video_path),
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }

        else:
            return {
                "action": "no_action",
                "video_path": str(video_path),
                "reason": "Unknown action",
                "timestamp": datetime.now().isoformat(),
            }

    def _update_retention_history(
        self,
        video_path: Path,
        retention_result: Dict[str, Any],
        cost_analysis: RetentionCostAnalysis,
    ):
        """Update the retention history with this decision."""

        video_hash = self._get_video_hash(video_path)
        action = retention_result["action"]

        # Update specific retention records
        if action == "archived":
            self.retention_history["retained_videos"][video_hash] = {
                "original_path": str(video_path),
                "archive_path": retention_result.get("archive_path"),
                "timestamp": retention_result["timestamp"],
                "reason": retention_result["reason"],
                "cost_analysis": {
                    "storage_cost_yearly": cost_analysis.storage_cost_yearly,
                    "reprocessing_cost": cost_analysis.reprocessing_cost,
                    "breakeven_months": cost_analysis.breakeven_months,
                },
            }
            self.retention_history["retention_stats"]["videos_retained"] += 1
            self.retention_history["retention_stats"][
                "total_storage_cost"
            ] += cost_analysis.storage_cost_yearly

        elif action == "deleted":
            self.retention_history["deleted_videos"][video_hash] = {
                "original_path": str(video_path),
                "timestamp": retention_result["timestamp"],
                "reason": retention_result["reason"],
                "cost_analysis": {
                    "storage_cost_avoided": cost_analysis.storage_cost_yearly,
                    "reprocessing_cost": cost_analysis.reprocessing_cost,
                    "breakeven_months": cost_analysis.breakeven_months,
                },
            }
            self.retention_history["retention_stats"]["videos_deleted"] += 1
            self.retention_history["retention_stats"][
                "total_saved_cost"
            ] += cost_analysis.storage_cost_yearly

        # Save updated history
        self._save_retention_history()

    def cleanup_archive(self, max_age_days: int = 365) -> Dict[str, Any]:
        """Clean up old archived videos based on age."""

        logger.info(f"Cleaning up archive older than {max_age_days} days")

        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        cleaned_files = []
        total_size_freed = 0

        # Walk through archive directory
        for video_file in self.archive_dir.rglob("*"):
            if video_file.is_file() and video_file.suffix in [
                ".mp4",
                ".mkv",
                ".avi",
                ".mov",
                ".wmv",
            ]:
                # Check file age
                file_time = datetime.fromtimestamp(video_file.stat().st_mtime)

                if file_time < cutoff_date:
                    file_size = video_file.stat().st_size
                    try:
                        os.remove(video_file)
                        cleaned_files.append(str(video_file))
                        total_size_freed += file_size
                        logger.info(f"Cleaned up old archive: {video_file.name}")
                    except Exception as e:
                        logger.error(f"Failed to clean up {video_file}: {e}")

        # Remove empty directories
        for dir_path in self.archive_dir.rglob("*"):
            if dir_path.is_dir() and not any(dir_path.iterdir()):
                try:
                    dir_path.rmdir()
                    logger.info(f"Removed empty directory: {dir_path}")
                except Exception as e:
                    logger.warning(f"Could not remove directory {dir_path}: {e}")

        return {
            "cleaned_files": len(cleaned_files),
            "size_freed_gb": total_size_freed / (1024**3),
            "cutoff_date": cutoff_date.isoformat(),
            "files": cleaned_files,
        }

    def get_retention_stats(self) -> Dict[str, Any]:
        """Get comprehensive retention statistics."""

        stats = self.retention_history["retention_stats"].copy()

        # Calculate current archive size
        archive_size = 0
        archive_file_count = 0

        for video_file in self.archive_dir.rglob("*"):
            if video_file.is_file():
                archive_size += video_file.stat().st_size
                archive_file_count += 1

        stats.update(
            {
                "current_archive_size_gb": archive_size / (1024**3),
                "current_archive_files": archive_file_count,
                "max_archive_size_gb": self.retention_config["max_archive_size_gb"],
                "archive_utilization": (archive_size / (1024**3))
                / self.retention_config["max_archive_size_gb"],
                "policy": self.retention_config["policy"],
                "cost_optimization_enabled": self.retention_config["cost_optimization"],
            }
        )

        return stats

    def recommend_policy_optimization(self) -> Dict[str, Any]:
        """Recommend policy optimizations based on usage patterns."""

        stats = self.get_retention_stats()
        recommendations = []

        # Analyze retention patterns
        total_videos = stats["videos_retained"] + stats["videos_deleted"]

        if total_videos > 0:
            retention_rate = stats["videos_retained"] / total_videos

            if retention_rate > 0.8 and stats["total_storage_cost"] > 100:
                recommendations.append(
                    {
                        "type": "policy_change",
                        "recommendation": "Consider changing to KEEP_PROCESSED with cost optimization",
                        "reason": f"High retention rate ({retention_rate:.1%}) with significant storage costs",
                    }
                )

            elif (
                retention_rate < 0.2
                and self.retention_config["policy"] != VideoRetentionPolicy.DELETE
            ):
                recommendations.append(
                    {
                        "type": "policy_change",
                        "recommendation": "Consider changing to DELETE policy",
                        "reason": f"Low retention rate ({retention_rate:.1%}) suggests videos are rarely needed",
                    }
                )

        # Check archive utilization
        if stats["archive_utilization"] > 0.9:
            recommendations.append(
                {
                    "type": "cleanup",
                    "recommendation": "Archive cleanup needed",
                    "reason": f"Archive is {stats['archive_utilization']:.1%} full",
                }
            )

        return {
            "recommendations": recommendations,
            "current_stats": stats,
            "confidence": 0.8 if total_videos > 10 else 0.5,
        }
