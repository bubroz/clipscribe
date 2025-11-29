"""
Topic Search API - End-to-End Integration Tests

Validates complete flow: Database → API → Response
"""

import sqlite3
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.clipscribe.api.topic_search import TopicSearchRequest, search_topics  # noqa: E402

# Skip all tests in this module if the database doesn't exist or is empty
DB_PATH = project_root / "data/station10.db"


def _db_has_topics() -> bool:
    """Check if the database exists and has topics."""
    if not DB_PATH.exists():
        return False
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM topics")
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _db_has_topics(),
    reason="station10.db database not found or empty (required for topic search tests)",
)


@pytest.mark.integration
async def test_topic_database_populated():
    """Verify topics are in database."""
    db_path = project_root / "data/station10.db"

    assert db_path.exists(), "Database file not found"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM topics")
    count = cursor.fetchone()[0]

    assert count >= 13, f"Expected at least 13 topics, found {count}"

    # Verify structure
    cursor.execute("SELECT name, relevance, time_range FROM topics LIMIT 1")
    row = cursor.fetchone()

    assert row is not None, "No topics found"
    assert row[0], "Topic name is empty"
    assert 0 <= row[1] <= 1.0, f"Invalid relevance: {row[1]}"

    conn.close()


@pytest.mark.integration
async def test_topic_search_all():
    """Test searching all topics."""
    request = TopicSearchRequest(min_relevance=0.0, limit=50)

    response = await search_topics(request)

    assert response.total >= 13, f"Expected >=13 topics, got {response.total}"
    assert len(response.topics) >= 13
    assert response.query_time_ms > 0

    # Verify first topic structure
    topic = response.topics[0]
    assert topic.name
    assert topic.video_id
    assert 0 <= topic.relevance <= 1.0


@pytest.mark.integration
async def test_topic_search_by_query():
    """Test text search in topics."""
    request = TopicSearchRequest(query="ceasefire", min_relevance=0.0)

    response = await search_topics(request)

    assert response.total >= 1, "Expected at least 1 ceasefire topic"

    # Verify all results contain query
    for topic in response.topics:
        assert "ceasefire" in topic.name.lower(), f"Topic {topic.name} doesn't match query"


@pytest.mark.integration
async def test_topic_search_by_relevance():
    """Test relevance filtering."""
    request = TopicSearchRequest(min_relevance=0.95)

    response = await search_topics(request)

    # Should have high-relevance topics
    assert response.total >= 1, "Expected high-relevance topics"

    # Verify all have relevance >= 0.95
    for topic in response.topics:
        assert topic.relevance >= 0.95, f"Topic {topic.name} has relevance {topic.relevance} < 0.95"


@pytest.mark.integration
async def test_topic_search_by_video():
    """Test filtering by video ID."""
    request = TopicSearchRequest(video_id="P-2")  # All-In Podcast

    response = await search_topics(request)

    assert response.total == 5, f"All-In should have 5 topics, got {response.total}"

    # Verify all are from correct video
    for topic in response.topics:
        assert topic.video_id == "P-2"


@pytest.mark.integration
async def test_topic_search_performance():
    """Test API response time."""
    request = TopicSearchRequest(limit=50)

    response = await search_topics(request)

    # Should be fast (< 100ms)
    assert response.query_time_ms < 100, f"Slow query: {response.query_time_ms}ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
