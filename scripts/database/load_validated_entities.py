#!/usr/bin/env python3
"""
Load validated entities from Grok-4 validation into database.

Uses the 287 entities from our Oct 29 validation (All-In, The View, MTG).
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

def load_entities_from_gcs():
    """Load validated entities from GCS transcripts."""
    
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
        print(f"\nLoading entities from {video_title}...")
        
        blob = bucket.blob(gcs_path)
        if not blob.exists():
            print(f"  ⚠ Transcript not found: {gcs_path}")
            continue
        
        data = json.loads(blob.download_as_text())
        entities = data.get('entities', [])
        
        print(f"  Found {len(entities)} entities")
        
        # Count by type
        type_counts = {}
        for entity in entities:
            entity_type = entity.get('type', 'UNKNOWN')
            type_counts[entity_type] = type_counts.get(entity_type, 0) + 1
        
        print(f"  Types: {dict(sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:5])}")
        
        for entity in entities:
            entity_id = str(uuid.uuid4())
            name = entity.get('name', '')
            entity_type = entity.get('type', 'UNKNOWN')
            confidence = entity.get('confidence', 1.0)
            evidence = entity.get('evidence', '')
            
            # Estimate timestamp (would need actual implementation)
            timestamp = None
            
            cursor.execute("""
                INSERT INTO entities (
                    id, video_id, video_title, name, type, confidence, 
                    evidence, timestamp, mention_count
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entity_id, video_id, video_title, name, entity_type, 
                confidence, evidence, timestamp, 1
            ))
            
            total_loaded += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Loaded {total_loaded} entities into database")
    print(f"   Database: {DB_PATH}")
    
    # Show summary by type
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT type, COUNT(*) as count
        FROM entities
        GROUP BY type
        ORDER BY count DESC
    """)
    
    print(f"\n📊 Entity Distribution:")
    for row in cursor.fetchall():
        print(f"   {row[0]}: {row[1]}")
    
    conn.close()

if __name__ == "__main__":
    load_entities_from_gcs()

