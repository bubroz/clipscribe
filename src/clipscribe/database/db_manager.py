"""
ClipScribe Local Intelligence Database

Single-user database for entity search, relationship tracking, and cost management.
"""

import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ClipScribeDatabase:
    """Manage ClipScribe local intelligence database."""

    def __init__(self, db_path: str = "clipscribe.db"):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.conn = None
        self._initialize()

    def _initialize(self):
        """Create database and tables from schema."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # Dict-like access

        # Read and execute schema
        schema_path = Path(__file__).parent / "schema.sql"
        if schema_path.exists():
            with open(schema_path) as f:
                self.conn.executescript(f.read())

        logger.info(f"Database initialized: {self.db_path}")

    # VIDEO MANAGEMENT

    def add_video(
        self,
        video_id: str,
        url: str,
        title: str,
        cost: float,
        entity_count: int,
        relationship_count: int,
        output_path: str,
        **kwargs,
    ) -> int:
        """
        Record processed video. If video_id exists, updates the record.

        Args:
            video_id: Unique video identifier
            url: Video URL or source
            title: Video title
            cost: Processing cost in USD
            entity_count: Number of entities extracted
            relationship_count: Number of relationships found
            output_path: Path to output directory
            **kwargs: Optional fields (channel, duration)

        Returns:
            Row ID of inserted/updated video
        """
        cursor = self.conn.execute(
            """
            INSERT OR REPLACE INTO videos (
                video_id, url, title, processing_cost,
                entity_count, relationship_count, output_path,
                channel, duration, processed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
            (
                video_id,
                url,
                title,
                cost,
                entity_count,
                relationship_count,
                output_path,
                kwargs.get("channel"),
                kwargs.get("duration"),
            ),
        )

        self.conn.commit()
        logger.info(f"Video recorded: {video_id} ({entity_count} entities, ${cost:.4f})")
        return cursor.lastrowid

    def get_video(self, video_id: str) -> Optional[Dict]:
        """Get video by ID."""
        cursor = self.conn.execute("SELECT * FROM videos WHERE video_id = ?", (video_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_recent_videos(self, limit: int = 10) -> List[Dict]:
        """Get most recent videos."""
        cursor = self.conn.execute(
            """
            SELECT * FROM videos
            ORDER BY processed_at DESC
            LIMIT ?
        """,
            (limit,),
        )

        return [dict(row) for row in cursor.fetchall()]

    def get_video_count(self) -> int:
        """Get total number of processed videos."""
        cursor = self.conn.execute("SELECT COUNT(*) as count FROM videos")
        return cursor.fetchone()["count"]

    # ENTITY MANAGEMENT

    def add_entities(self, video_id: str, entities: List[Dict]):
        """
        Add entities for a video. Clears old entities if video is reprocessed.

        Args:
            video_id: Video identifier
            entities: List of entity dicts with keys: name, type, mention_count, confidence
        """
        # Clear existing entities for this video
        self.conn.execute("DELETE FROM entities WHERE video_id = ?", (video_id,))

        # Add new entities
        for entity in entities:
            self.conn.execute(
                """
                INSERT INTO entities (video_id, name, entity_type, mention_count, confidence)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    video_id,
                    entity.get("name"),
                    entity.get("type"),
                    entity.get("mention_count", 1),
                    entity.get("confidence", 1.0),
                ),
            )

        self.conn.commit()
        logger.debug(f"Added {len(entities)} entities for video: {video_id}")

    def search_entities(self, query: str, limit: int = 50) -> List[Dict]:
        """
        Search entities by name.

        Args:
            query: Search term (partial match)
            limit: Maximum results

        Returns:
            List of entity matches with video context
        """
        cursor = self.conn.execute(
            """
            SELECT
                e.name,
                e.entity_type,
                e.mention_count,
                e.confidence,
                v.title,
                v.url,
                v.video_id,
                v.processed_at
            FROM entities e
            JOIN videos v ON e.video_id = v.video_id
            WHERE e.name LIKE ?
            ORDER BY e.mention_count DESC, v.processed_at DESC
            LIMIT ?
        """,
            (f"%{query}%", limit),
        )

        return [dict(row) for row in cursor.fetchall()]

    def get_entity_stats(self) -> Dict[str, int]:
        """Get entity statistics."""
        cursor = self.conn.execute(
            """
            SELECT
                COUNT(DISTINCT name) as unique_entities,
                COUNT(*) as total_mentions,
                COUNT(DISTINCT entity_type) as entity_types,
                COUNT(DISTINCT video_id) as videos_with_entities
            FROM entities
        """
        )
        return dict(cursor.fetchone())

    # RELATIONSHIP MANAGEMENT

    def add_relationships(self, video_id: str, relationships: List[Dict]):
        """
        Add relationships for a video. Clears old relationships if video is reprocessed.

        Args:
            video_id: Video identifier
            relationships: List of relationship dicts
        """
        # Clear existing relationships for this video
        self.conn.execute("DELETE FROM relationships WHERE video_id = ?", (video_id,))

        # Add new relationships
        for rel in relationships:
            self.conn.execute(
                """
                INSERT INTO relationships (
                    video_id, source_entity, target_entity,
                    relationship_type, evidence
                )
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    video_id,
                    rel.get("source"),
                    rel.get("target"),
                    rel.get("type"),
                    rel.get("evidence", ""),
                ),
            )

        self.conn.commit()
        logger.debug(f"Added {len(relationships)} relationships for video: {video_id}")

    def search_relationships(
        self, entity: str, relationship_type: Optional[str] = None, limit: int = 50
    ) -> List[Dict]:
        """
        Search relationships involving an entity.

        Args:
            entity: Entity name to search for
            relationship_type: Optional filter by relationship type
            limit: Maximum results

        Returns:
            List of relationships with video context
        """
        if relationship_type:
            query = """
                SELECT
                    r.*,
                    v.title,
                    v.url,
                    v.processed_at
                FROM relationships r
                JOIN videos v ON r.video_id = v.video_id
                WHERE (r.source_entity LIKE ? OR r.target_entity LIKE ?)
                  AND r.relationship_type = ?
                ORDER BY v.processed_at DESC
                LIMIT ?
            """
            params = (f"%{entity}%", f"%{entity}%", relationship_type, limit)
        else:
            query = """
                SELECT
                    r.*,
                    v.title,
                    v.url,
                    v.processed_at
                FROM relationships r
                JOIN videos v ON r.video_id = v.video_id
                WHERE r.source_entity LIKE ? OR r.target_entity LIKE ?
                ORDER BY v.processed_at DESC
                LIMIT ?
            """
            params = (f"%{entity}%", f"%{entity}%", limit)

        cursor = self.conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    # COST TRACKING & STATS

    def get_cost_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        Get cost statistics for last N days.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with cost stats
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        cursor = self.conn.execute(
            """
            SELECT
                COUNT(*) as video_count,
                SUM(processing_cost) as total_cost,
                AVG(processing_cost) as avg_cost_per_video,
                MIN(processing_cost) as min_cost,
                MAX(processing_cost) as max_cost,
                SUM(entity_count) as total_entities,
                AVG(entity_count) as avg_entities_per_video
            FROM videos
            WHERE processed_at >= ?
        """,
            (cutoff_date.isoformat(),),
        )

        return dict(cursor.fetchone())

    def get_daily_costs(self, days: int = 30) -> List[Dict]:
        """Get daily cost breakdown."""
        cutoff_date = datetime.now() - timedelta(days=days)

        cursor = self.conn.execute(
            """
            SELECT
                DATE(processed_at) as date,
                COUNT(*) as video_count,
                SUM(processing_cost) as daily_cost,
                SUM(entity_count) as entities_extracted
            FROM videos
            WHERE processed_at >= ?
            GROUP BY DATE(processed_at)
            ORDER BY date DESC
        """,
            (cutoff_date.isoformat(),),
        )

        return [dict(row) for row in cursor.fetchall()]

    # UTILITY METHODS

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.debug("Database connection closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
