"""
Entity Search API for Station10.media

Search for entities across processed videos with 18 spaCy type filtering.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/entities", tags=["entities"])


class Entity(BaseModel):
    """Entity model with spaCy standard types."""

    id: str
    video_id: str
    video_title: Optional[str] = None
    name: str
    type: str = Field(description="spaCy entity type (PERSON, ORG, GPE, etc.)")
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: Optional[str] = Field(None, description="Supporting quote from transcript")
    timestamp: Optional[float] = Field(None, description="First mention timestamp")
    mention_count: int = Field(1, description="Times mentioned in video")
    created_at: Optional[datetime] = None


class EntitySearchRequest(BaseModel):
    """Entity search request parameters."""

    query: Optional[str] = Field(None, description="Search in entity names")
    entity_type: Optional[str] = Field(None, description="spaCy type (PERSON, ORG, GPE, etc.)")
    min_confidence: float = Field(0.7, ge=0.0, le=1.0)
    video_id: Optional[str] = Field(None, description="Filter by video")
    limit: int = Field(100, ge=1, le=1000)


class EntitySearchResponse(BaseModel):
    """Entity search response."""

    entities: List[Entity]
    total: int
    query_time_ms: float


# Database
DB_PATH = Path("data/station10.db")


def init_database():
    """Initialize entities database."""
    DB_PATH.parent.mkdir(exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS entities (
            id TEXT PRIMARY KEY,
            video_id TEXT NOT NULL,
            video_title TEXT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            confidence REAL NOT NULL,
            evidence TEXT,
            timestamp REAL,
            mention_count INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Indexes for search
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_video ON entities(video_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_name ON entities(name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_type ON entities(type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_confidence ON entities(confidence)")

    conn.commit()
    conn.close()


@router.post("/search", response_model=EntitySearchResponse)
async def search_entities(request: EntitySearchRequest):
    """
    Search for entities across processed videos.

    Examples:
        - Find all Trump mentions: {"query": "Trump", "min_confidence": 0.9}
        - Find all people: {"entity_type": "PERSON"}
        - Find organizations in video: {"entity_type": "ORG", "video_id": "P-2"}
    """
    import time

    start_time = time.time()

    # Build SQL
    query_parts = []
    params = []

    if request.query:
        query_parts.append("name LIKE ?")
        params.append(f"%{request.query}%")

    if request.entity_type:
        query_parts.append("type = ?")
        params.append(request.entity_type)

    if request.min_confidence > 0:
        query_parts.append("confidence >= ?")
        params.append(request.min_confidence)

    if request.video_id:
        query_parts.append("video_id = ?")
        params.append(request.video_id)

    where_clause = " AND ".join(query_parts) if query_parts else "1=1"

    sql = f"""
        SELECT id, video_id, video_title, name, type, confidence, 
               evidence, timestamp, mention_count, created_at
        FROM entities
        WHERE {where_clause}
        ORDER BY confidence DESC, mention_count DESC
        LIMIT ?
    """
    params.append(request.limit)

    # Execute
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(sql, params)

    rows = cursor.fetchall()
    conn.close()

    # Convert to Entity objects
    entities = []
    for row in rows:
        entities.append(
            Entity(
                id=row[0],
                video_id=row[1],
                video_title=row[2],
                name=row[3],
                type=row[4],
                confidence=row[5],
                evidence=row[6],
                timestamp=row[7],
                mention_count=row[8],
                created_at=row[9],
            )
        )

    query_time = (time.time() - start_time) * 1000

    return EntitySearchResponse(entities=entities, total=len(entities), query_time_ms=query_time)


@router.get("/types", response_model=List[str])
async def get_entity_types():
    """Get all unique entity types in database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT type FROM entities ORDER BY type")
    types = [row[0] for row in cursor.fetchall()]

    conn.close()
    return types


@router.get("/video/{video_id}", response_model=List[Entity])
async def get_video_entities(
    video_id: str, entity_type: Optional[str] = None, min_confidence: float = 0.7
):
    """Get all entities for a specific video."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    sql = """
        SELECT id, video_id, video_title, name, type, confidence,
               evidence, timestamp, mention_count, created_at
        FROM entities
        WHERE video_id = ? AND confidence >= ?
    """
    params = [video_id, min_confidence]

    if entity_type:
        sql += " AND type = ?"
        params.append(entity_type)

    sql += " ORDER BY confidence DESC"

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()

    entities = []
    for row in rows:
        entities.append(
            Entity(
                id=row[0],
                video_id=row[1],
                video_title=row[2],
                name=row[3],
                type=row[4],
                confidence=row[5],
                evidence=row[6],
                timestamp=row[7],
                mention_count=row[8],
                created_at=row[9],
            )
        )

    return entities


# Initialize database
init_database()
