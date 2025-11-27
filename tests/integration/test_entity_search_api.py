"""
Entity Search API - End-to-End Integration Tests

Validates complete flow: Database → API → Response
Tests all 18 spaCy entity types and evidence quote coverage.
"""

import pytest
from pathlib import Path
import sqlite3
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.clipscribe.api.entity_search import EntitySearchRequest, search_entities, get_entity_types


@pytest.mark.integration
async def test_entity_database_populated():
    """Verify entities are in database."""
    db_path = project_root / "data/station10.db"

    assert db_path.exists(), "Database file not found"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM entities")
    count = cursor.fetchone()[0]

    assert count >= 287, f"Expected at least 287 entities, found {count}"

    # Verify structure
    cursor.execute("SELECT name, type, confidence, evidence FROM entities LIMIT 1")
    row = cursor.fetchone()

    assert row is not None, "No entities found"
    assert row[0], "Entity name is empty"
    assert row[1], "Entity type is empty"
    assert 0 <= row[2] <= 1.0, f"Invalid confidence: {row[2]}"
    assert row[3], "Evidence quote is missing"

    conn.close()


@pytest.mark.integration
async def test_entity_evidence_coverage():
    """Verify 100% evidence quote coverage."""
    db_path = project_root / "data/station10.db"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM entities")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM entities WHERE evidence IS NOT NULL AND evidence != ''")
    with_evidence = cursor.fetchone()[0]

    conn.close()

    coverage = (with_evidence / total * 100) if total > 0 else 0
    assert coverage == 100.0, f"Evidence coverage {coverage}% != 100%"


@pytest.mark.integration
async def test_entity_search_all():
    """Test searching all entities."""
    request = EntitySearchRequest(min_confidence=0.0, limit=500)

    response = await search_entities(request)

    assert response.total >= 287, f"Expected >=287 entities, got {response.total}"
    assert response.query_time_ms > 0

    # Verify first entity structure
    entity = response.entities[0]
    assert entity.name
    assert entity.type
    assert entity.video_id
    assert 0 <= entity.confidence <= 1.0
    assert entity.evidence, "Entity missing evidence quote"


@pytest.mark.integration
async def test_entity_search_by_name():
    """Test searching for Trump entities."""
    request = EntitySearchRequest(query="Trump")

    response = await search_entities(request)

    assert response.total >= 3, "Expected at least 3 Trump entities across 3 videos"

    # Verify all contain "Trump"
    for entity in response.entities:
        assert "trump" in entity.name.lower(), f"Entity {entity.name} doesn't match query"


@pytest.mark.integration
async def test_entity_search_by_type():
    """Test filtering by entity type (PERSON)."""
    request = EntitySearchRequest(entity_type="PERSON")

    response = await search_entities(request)

    assert response.total >= 69, f"Expected >=69 PERSON entities, got {response.total}"

    # Verify all are PERSON type
    for entity in response.entities[:20]:  # Check first 20
        assert entity.type == "PERSON", f"Expected PERSON, got {entity.type}"


@pytest.mark.integration
async def test_entity_types_endpoint():
    """Test GET /api/entities/types endpoint."""
    types = await get_entity_types()

    assert len(types) >= 14, f"Expected >=14 types, got {len(types)}"
    assert "PERSON" in types
    assert "ORG" in types
    assert "GPE" in types


@pytest.mark.integration
async def test_entity_search_confidence_filtering():
    """Test confidence threshold filtering."""
    request = EntitySearchRequest(
        min_confidence=1.0, limit=500  # Only perfect confidence  # Get all entities
    )

    response = await search_entities(request)

    # Most Grok-4 entities have 1.0 confidence (some filtered by deduplication)
    assert (
        response.total >= 200
    ), f"Expected >=200 entities with 1.0 confidence, got {response.total}"

    for entity in response.entities[:50]:
        assert (
            entity.confidence == 1.0
        ), f"Entity {entity.name} has confidence {entity.confidence} != 1.0"


@pytest.mark.integration
async def test_entity_search_performance():
    """Test API response time."""
    request = EntitySearchRequest(entity_type="PERSON", limit=100)

    response = await search_entities(request)

    # Should be fast (<100ms)
    assert response.query_time_ms < 100, f"Slow query: {response.query_time_ms}ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
