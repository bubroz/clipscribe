# ClipScribe API Reference

**Last Updated:** November 4, 2025  
**Version:** v2.61.0  
**Status:** Topic Search and Entity Search APIs validated (14/14 tests passing)

---

## Available APIs

### Topic Search API

**Endpoint:** `POST /api/topics/search`

**Purpose:** Search for topics across processed videos

**Request:**
```python
from src.clipscribe.api.topic_search import TopicSearchRequest, search_topics

request = TopicSearchRequest(
    query="ceasefire",           # Optional: text search in topic names
    min_relevance=0.8,           # Optional: minimum relevance threshold (0-1)
    schema_type="PoliticalEvent", # Optional: filter by Schema.org type
    video_id="P-2",              # Optional: filter by specific video
    limit=50                      # Optional: max results (default 50)
)

response = await search_topics(request)
```

**Response:**
```python
{
    "topics": [
        {
            "id": "uuid",
            "video_id": "P-2",
            "video_title": "All-In Podcast",
            "name": "Israel-Hamas Ceasefire",
            "relevance": 0.95,
            "time_range": "00:00-15:00",
            "schema_type": "Event",
            "schema_subtype": "PoliticalEvent"
        }
    ],
    "total": 1,
    "query_time_ms": 0.8
}
```

**Examples:**
```python
# Find all high-relevance topics
request = TopicSearchRequest(min_relevance=0.95)
response = await search_topics(request)

# Find topics about specific subject
request = TopicSearchRequest(query="Gaza")
response = await search_topics(request)

# Get all topics for a video
request = TopicSearchRequest(video_id="P-2")
response = await search_topics(request)
```

---

### Entity Search API

**Endpoint:** `POST /api/entities/search`

**Purpose:** Search for entities across processed videos

**Request:**
```python
from src.clipscribe.api.entity_search import EntitySearchRequest, search_entities

request = EntitySearchRequest(
    query="Trump",              # Optional: text search in entity names
    entity_type="PERSON",       # Optional: filter by spaCy type
    min_confidence=0.9,         # Optional: minimum confidence (0-1)
    video_id="P-2",            # Optional: filter by video
    limit=100                   # Optional: max results (default 100)
)

response = await search_entities(request)
```

**Response:**
```python
{
    "entities": [
        {
            "id": "uuid",
            "video_id": "P-2",
            "video_title": "All-In Podcast",
            "name": "Donald Trump",
            "type": "PERSON",
            "confidence": 1.0,
            "evidence": "Thanks to President Trump, who announced it just yesterday.",
            "timestamp": null,
            "mention_count": 1
        }
    ],
    "total": 3,
    "query_time_ms": 0.5
}
```

**Examples:**
```python
# Find all people
request = EntitySearchRequest(entity_type="PERSON")
response = await search_entities(request)

# Find specific entity across all videos
request = EntitySearchRequest(query="Biden")
response = await search_entities(request)

# High-confidence entities only
request = EntitySearchRequest(min_confidence=1.0, limit=500)
response = await search_entities(request)
```

---

### Additional Endpoints

**Get Entity Types:**
```python
from src.clipscribe.api.entity_search import get_entity_types

types = await get_entity_types()
# Returns: ['PERSON', 'ORG', 'GPE', 'EVENT', ...]
```

**Get Topics for Video:**
```python
GET /api/topics/video/{video_id}
# Returns all topics for that video
```

**Get Entities for Video:**
```python
GET /api/entities/video/{video_id}
# Returns all entities for that video
```

---

## Database Schema

### Topics Table
```sql
CREATE TABLE topics (
    id TEXT PRIMARY KEY,
    video_id TEXT NOT NULL,
    video_title TEXT,
    name TEXT NOT NULL,
    relevance REAL NOT NULL,  -- 0.0-1.0
    time_range TEXT,          -- "MM:SS-MM:SS"
    schema_type TEXT DEFAULT 'Event',
    schema_subtype TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_video_id ON topics(video_id);
CREATE INDEX idx_name ON topics(name);
CREATE INDEX idx_relevance ON topics(relevance);
```

### Entities Table
```sql
CREATE TABLE entities (
    id TEXT PRIMARY KEY,
    video_id TEXT NOT NULL,
    video_title TEXT,
    name TEXT NOT NULL,
    type TEXT NOT NULL,         -- spaCy entity type
    confidence REAL NOT NULL,   -- 0.0-1.0
    evidence TEXT,              -- Supporting quote
    timestamp REAL,             -- First mention timestamp
    mention_count INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_entity_video ON entities(video_id);
CREATE INDEX idx_entity_name ON entities(name);
CREATE INDEX idx_entity_type ON entities(type);
CREATE INDEX idx_entity_confidence ON entities(confidence);
```

---

## Performance

**Query Times (Validated):**
- Topic search: <1ms average
- Entity search: <1ms average
- 14/14 tests passing with <100ms threshold

**Database Size:**
- 13 topics: ~20KB
- 287 entities: ~150KB
- Fast queries even with thousands of videos

---

## Usage Examples

### Complete Topic Search Example:
```python
import asyncio
from src.clipscribe.api.topic_search import TopicSearchRequest, search_topics

async def main():
    # Find all topics about healthcare
    request = TopicSearchRequest(
        query="healthcare",
        min_relevance=0.8
    )
    
    response = await search_topics(request)
    
    print(f"Found {response.total} topics in {response.query_time_ms:.2f}ms")
    
    for topic in response.topics:
        print(f"\n{topic.name}")
        print(f"  Video: {topic.video_title}")
        print(f"  Relevance: {topic.relevance:.2f}")
        print(f"  Time: {topic.time_range}")

asyncio.run(main())
```

### Complete Entity Search Example:
```python
import asyncio
from src.clipscribe.api.entity_search import EntitySearchRequest, search_entities

async def main():
    # Find all organizations mentioned
    request = EntitySearchRequest(
        entity_type="ORG",
        min_confidence=0.9,
        limit=50
    )
    
    response = await search_entities(request)
    
    print(f"Found {response.total} organizations in {response.query_time_ms:.2f}ms")
    
    for entity in response.entities:
        print(f"\n{entity.name} ({entity.type})")
        print(f"  Video: {entity.video_title}")
        print(f"  Confidence: {entity.confidence:.2f}")
        print(f"  Evidence: \"{entity.evidence[:60]}...\"")

asyncio.run(main())
```

---

**This documents the actual working APIs as of November 4, 2025.**

