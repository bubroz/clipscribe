"""
Station10 Intelligence Platform - Database Manager

Multi-user database for video intelligence tracking.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class Station10Database:
    """Manage Station10 multi-user intelligence database."""
    
    def __init__(self, db_path: str = "station10.db"):
        """Initialize database connection."""
        self.db_path = Path(db_path)
        self.conn = None
        self._initialize()
    
    def _initialize(self):
        """Create database and tables."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # Dict-like access
        
        # Read and execute schema
        schema_path = Path(__file__).parent / "schema.sql"
        if schema_path.exists():
            with open(schema_path) as f:
                self.conn.executescript(f.read())
        
        logger.info(f"Database initialized: {self.db_path}")
    
    # USER MANAGEMENT
    
    def register_user(self, telegram_id: int, username: str = None, full_name: str = None) -> int:
        """Register new user or return existing."""
        cursor = self.conn.execute(
            "SELECT id FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        existing = cursor.fetchone()
        
        if existing:
            return existing['id']
        
        cursor = self.conn.execute(
            "INSERT INTO users (telegram_id, username, full_name) VALUES (?, ?, ?)",
            (telegram_id, username, full_name)
        )
        self.conn.commit()
        logger.info(f"Registered user: {username} ({telegram_id})")
        return cursor.lastrowid
    
    def get_user(self, telegram_id: int) -> Optional[Dict]:
        """Get user by Telegram ID."""
        cursor = self.conn.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    
    # VIDEO MANAGEMENT
    
    def add_video(self, video_id: str, url: str, title: str, user_id: int, 
                  cost: float, entity_count: int, relationship_count: int,
                  output_path: str, **kwargs) -> int:
        """Record processed video."""
        cursor = self.conn.execute("""
            INSERT INTO videos (video_id, url, title, processed_by_user_id, 
                              processing_cost, entity_count, relationship_count, output_path,
                              channel, duration)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (video_id, url, title, user_id, cost, entity_count, relationship_count, 
              output_path, kwargs.get('channel'), kwargs.get('duration')))
        
        # Track cost
        self.conn.execute(
            "INSERT INTO costs (user_id, video_id, cost) VALUES (?, ?, ?)",
            (user_id, video_id, cost)
        )
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_recent_videos(self, limit: int = 10) -> List[Dict]:
        """Get most recent videos from all users."""
        cursor = self.conn.execute("""
            SELECT v.*, u.username 
            FROM videos v 
            JOIN users u ON v.processed_by_user_id = u.id 
            ORDER BY v.processed_at DESC 
            LIMIT ?
        """, (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    # ENTITY SEARCH
    
    def add_entities(self, video_id: str, entities: List[Dict]):
        """Add entities for a video."""
        for entity in entities:
            self.conn.execute("""
                INSERT INTO entities (video_id, name, entity_type, mention_count)
                VALUES (?, ?, ?, ?)
            """, (video_id, entity.get('name'), entity.get('type'), 
                  entity.get('mention_count', 1)))
        
        self.conn.commit()
    
    def search_entities(self, query: str, limit: int = 20) -> List[Dict]:
        """Search entities by name."""
        cursor = self.conn.execute("""
            SELECT e.*, v.title, v.url, v.processed_at, u.username
            FROM entities e
            JOIN videos v ON e.video_id = v.video_id
            JOIN users u ON v.processed_by_user_id = u.id
            WHERE e.name LIKE ?
            ORDER BY e.mention_count DESC, v.processed_at DESC
            LIMIT ?
        """, (f"%{query}%", limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    # COST TRACKING
    
    def get_user_costs(self, user_id: int, days: int = 30) -> Dict:
        """Get user costs for last N days."""
        cursor = self.conn.execute("""
            SELECT 
                COUNT(*) as video_count,
                SUM(cost) as total_cost,
                AVG(cost) as avg_cost
            FROM costs
            WHERE user_id = ?
            AND timestamp >= datetime('now', '-' || ? || ' days')
        """, (user_id, days))
        
        return dict(cursor.fetchone())
    
    def check_budget(self, user_id: int) -> tuple[float, float, bool]:
        """Check if user within budget. Returns (used, limit, within_budget)."""
        user = self.conn.execute(
            "SELECT monthly_budget_usd FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
        
        if not user:
            return (0, 0, False)
        
        costs = self.get_user_costs(user_id, days=30)
        used = costs.get('total_cost', 0) or 0
        limit = user['monthly_budget_usd']
        
        return (used, limit, used < limit)
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
