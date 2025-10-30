"""
Topic Search API for Station10.media

Enables searching for topics across processed videos with relevance filtering.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import sqlite3
from pathlib import Path

router = APIRouter(prefix="/api/topics", tags=["topics"])


class Topic(BaseModel):
    """Topic model with Schema.org typing."""
    id: str
    video_id: str
    video_title: Optional[str] = None
    name: str
    relevance: float = Field(ge=0.0, le=1.0, description="Relevance score 0-1")
    time_range: Optional[str] = Field(None, description="Time range in video (MM:SS-MM:SS)")
    schema_type: Optional[str] = Field("Event", description="Schema.org type")
    schema_subtype: Optional[str] = Field(None, description="Schema.org subtype")
    created_at: Optional[datetime] = None


class TopicSearchRequest(BaseModel):
    """Topic search request parameters."""
    query: Optional[str] = Field(None, description="Text search in topic names")
    min_relevance: float = Field(0.0, ge=0.0, le=1.0, description="Minimum relevance threshold")
    schema_type: Optional[str] = Field(None, description="Filter by Schema.org type")
    video_id: Optional[str] = Field(None, description="Filter by specific video")
    limit: int = Field(50, ge=1, le=500, description="Maximum results")


class TopicSearchResponse(BaseModel):
    """Topic search response."""
    topics: List[Topic]
    total: int
    query_time_ms: float


# Database initialization
DB_PATH = Path("data/station10.db")


def init_database():
    """Initialize topics database with Schema.org taxonomy."""
    DB_PATH.parent.mkdir(exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id TEXT PRIMARY KEY,
            video_id TEXT NOT NULL,
            video_title TEXT,
            name TEXT NOT NULL,
            relevance REAL NOT NULL,
            time_range TEXT,
            schema_type TEXT DEFAULT 'Event',
            schema_subtype TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create indexes for search performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_id ON topics(video_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_name ON topics(name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_relevance ON topics(relevance)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_schema_type ON topics(schema_type)")
    
    conn.commit()
    conn.close()


@router.post("/search", response_model=TopicSearchResponse)
async def search_topics(request: TopicSearchRequest):
    """
    Search for topics across processed videos.
    
    Examples:
        - Find all ceasefire topics: {"query": "ceasefire", "min_relevance": 0.8}
        - Find political events: {"schema_type": "PoliticalEvent"}
        - Find high-relevance topics: {"min_relevance": 0.9}
    """
    import time
    start_time = time.time()
    
    # Build SQL query
    query_parts = []
    params = []
    
    if request.query:
        query_parts.append("name LIKE ?")
        params.append(f"%{request.query}%")
    
    if request.min_relevance > 0:
        query_parts.append("relevance >= ?")
        params.append(request.min_relevance)
    
    if request.schema_type:
        query_parts.append("schema_type = ?")
        params.append(request.schema_type)
    
    if request.video_id:
        query_parts.append("video_id = ?")
        params.append(request.video_id)
    
    where_clause = " AND ".join(query_parts) if query_parts else "1=1"
    
    sql = f"""
        SELECT id, video_id, video_title, name, relevance, time_range, 
               schema_type, schema_subtype, created_at
        FROM topics
        WHERE {where_clause}
        ORDER BY relevance DESC
        LIMIT ?
    """
    params.append(request.limit)
    
    # Execute query
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(sql, params)
    
    rows = cursor.fetchall()
    conn.close()
    
    # Convert to Topic objects
    topics = []
    for row in rows:
        topics.append(Topic(
            id=row[0],
            video_id=row[1],
            video_title=row[2],
            name=row[3],
            relevance=row[4],
            time_range=row[5],
            schema_type=row[6],
            schema_subtype=row[7],
            created_at=row[8]
        ))
    
    query_time = (time.time() - start_time) * 1000
    
    return TopicSearchResponse(
        topics=topics,
        total=len(topics),
        query_time_ms=query_time
    )


@router.get("/video/{video_id}", response_model=List[Topic])
async def get_video_topics(video_id: str):
    """Get all topics for a specific video."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, video_id, video_title, name, relevance, time_range,
               schema_type, schema_subtype, created_at
        FROM topics
        WHERE video_id = ?
        ORDER BY relevance DESC
    """, (video_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    topics = []
    for row in rows:
        topics.append(Topic(
            id=row[0],
            video_id=row[1],
            video_title=row[2],
            name=row[3],
            relevance=row[4],
            time_range=row[5],
            schema_type=row[6],
            schema_subtype=row[7],
            created_at=row[8]
        ))
    
    return topics


# Initialize database on module import
init_database()

