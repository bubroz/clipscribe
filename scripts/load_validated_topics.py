#!/usr/bin/env python3
"""
Load validated topics from Grok-4 validation into database.

Uses the 13 topics from our Oct 29 validation (All-In, The View, MTG).
"""

import sys
from pathlib import Path
import sqlite3
import json
from google.cloud import storage
import uuid

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

DB_PATH = project_root / "data/station10.db"

def load_topics_from_gcs():
    """Load validated topics from GCS transcripts."""
    
    client = storage.Client()
    bucket = client.bucket('clipscribe-validation')
    
    videos = [
        ('P-2', 'All-In Podcast', 'validation/grok4_results/P-2//transcript.json'),
        ('View-1', 'The View Oct 14', 'validation/grok4_results/View-1//transcript.json'),
        ('P-1', 'MTG Interview', 'validation/grok4_results/P-1//transcript.json'),
    ]
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    total_loaded = 0
    
    for video_id, video_title, gcs_path in videos:
        print(f"\nLoading topics from {video_title}...")
        
        blob = bucket.blob(gcs_path)
        if not blob.exists():
            print(f"  ⚠ Transcript not found: {gcs_path}")
            continue
        
        data = json.loads(blob.download_as_text())
        topics = data.get('topics', [])
        
        print(f"  Found {len(topics)} topics")
        
        for topic in topics:
            topic_id = str(uuid.uuid4())
            name = topic.get('name', topic) if isinstance(topic, dict) else topic
            relevance = topic.get('relevance', 1.0) if isinstance(topic, dict) else 1.0
            time_range = topic.get('time_range') if isinstance(topic, dict) else None
            
            # Categorize as PoliticalEvent for now (can refine later)
            schema_type = "Event"
            schema_subtype = "PoliticalEvent"
            
            cursor.execute("""
                INSERT INTO topics (id, video_id, video_title, name, relevance, time_range, schema_type, schema_subtype)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (topic_id, video_id, video_title, name, relevance, time_range, schema_type, schema_subtype))
            
            print(f"    ✓ {name} (relevance: {relevance})")
            total_loaded += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Loaded {total_loaded} topics into database")
    print(f"   Database: {DB_PATH}")

if __name__ == "__main__":
    load_topics_from_gcs()

