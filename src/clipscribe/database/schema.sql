-- ClipScribe Local Intelligence Database Schema
-- Single-user database for entity search and cost tracking

-- Videos processed
CREATE TABLE IF NOT EXISTS videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT UNIQUE NOT NULL,
    url TEXT NOT NULL,
    title TEXT,
    channel TEXT,
    duration INTEGER,
    processing_cost REAL,
    entity_count INTEGER,
    relationship_count INTEGER,
    output_path TEXT,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Entities (for search across all videos)
CREATE TABLE IF NOT EXISTS entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL,
    name TEXT NOT NULL,
    entity_type TEXT,
    mention_count INTEGER DEFAULT 1,
    confidence REAL,
    FOREIGN KEY (video_id) REFERENCES videos(video_id)
);

-- Relationships (for cross-video relationship search)
CREATE TABLE IF NOT EXISTS relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL,
    source_entity TEXT NOT NULL,
    target_entity TEXT NOT NULL,
    relationship_type TEXT,
    evidence TEXT,
    FOREIGN KEY (video_id) REFERENCES videos(video_id)
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entities_video ON entities(video_id);
CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships(source_entity);
CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships(target_entity);
CREATE INDEX IF NOT EXISTS idx_videos_processed_at ON videos(processed_at);
