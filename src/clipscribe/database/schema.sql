-- Station10 Intelligence Platform Database Schema

-- Users (Station10 team members)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    username TEXT,
    full_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    monthly_budget_usd REAL DEFAULT 50.0,
    is_active BOOLEAN DEFAULT TRUE
);

-- Videos processed
CREATE TABLE IF NOT EXISTS videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT UNIQUE NOT NULL,
    url TEXT NOT NULL,
    title TEXT,
    channel TEXT,
    duration INTEGER,
    processed_by_user_id INTEGER,
    processing_cost REAL,
    entity_count INTEGER,
    relationship_count INTEGER,
    output_path TEXT,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (processed_by_user_id) REFERENCES users(id)
);

-- Entities (for search)
CREATE TABLE IF NOT EXISTS entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL,
    name TEXT NOT NULL,
    entity_type TEXT,
    mention_count INTEGER DEFAULT 1,
    FOREIGN KEY (video_id) REFERENCES videos(video_id)
);

-- Cost tracking
CREATE TABLE IF NOT EXISTS costs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    video_id TEXT NOT NULL,
    cost REAL NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (video_id) REFERENCES videos(video_id)
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);
CREATE INDEX IF NOT EXISTS idx_entities_video ON entities(video_id);
CREATE INDEX IF NOT EXISTS idx_videos_processed_by ON videos(processed_by_user_id);
CREATE INDEX IF NOT EXISTS idx_costs_user ON costs(user_id);
