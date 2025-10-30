"""
Grokipedia Integration for Entity Resolution

Checks if Grokipedia pages exist for entities and provides links for quick research.
Grokipedia is an AI-curated knowledge base (part of the Grok ecosystem).
"""

import httpx
from typing import Optional
import sqlite3
from pathlib import Path
from datetime import datetime


def check_grokipedia_url(entity_name: str, entity_type: str) -> Optional[str]:
    """
    Check if a Grokipedia page exists for the given entity.
    
    Args:
        entity_name: Name of the entity (e.g., "Donald Trump")
        entity_type: spaCy type (PERSON, ORG, GPE, etc.)
        
    Returns:
        URL if page exists, None otherwise
    """
    # Only check for entities that typically have pages
    if entity_type not in ['PERSON', 'ORG', 'GPE', 'NORP', 'EVENT', 'WORK_OF_ART']:
        return None
    
    # Construct URL (replace spaces with underscores)
    url_name = entity_name.replace(" ", "_").replace("'", "").replace('"', '')
    url = f"https://grokipedia.com/{url_name}"
    
    try:
        # Quick HEAD request to check if page exists
        with httpx.Client(timeout=2.0, follow_redirects=True) as client:
            response = client.head(url)
            
            # 200 = page exists, 404 = doesn't exist
            if response.status_code == 200:
                return url
            elif response.status_code == 404:
                return None
            else:
                # Unknown status, assume might exist
                return url
                
    except httpx.TimeoutException:
        # Timeout, assume might exist (don't block on slow network)
        return url
    except Exception:
        # Any other error, skip
        return None


def update_entity_grokipedia_links(db_path: Path):
    """
    Background job: Check Grokipedia links for all entities in database.
    
    Updates entities table with grokipedia_url where pages exist.
    Only checks entities without existing links or older than 7 days.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Add columns if they don't exist
    try:
        cursor.execute("ALTER TABLE entities ADD COLUMN grokipedia_url TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute("ALTER TABLE entities ADD COLUMN grokipedia_verified_at TIMESTAMP")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Get entities to check (no link yet, or link older than 7 days)
    cursor.execute("""
        SELECT id, name, type
        FROM entities
        WHERE type IN ('PERSON', 'ORG', 'GPE', 'NORP', 'EVENT', 'WORK_OF_ART')
        AND (
            grokipedia_url IS NULL 
            OR grokipedia_verified_at IS NULL
            OR grokipedia_verified_at < datetime('now', '-7 days')
        )
        LIMIT 50
    """)
    
    entities_to_check = cursor.fetchall()
    
    print(f"Checking Grokipedia links for {len(entities_to_check)} entities...")
    
    checked = 0
    found = 0
    
    for entity_id, name, entity_type in entities_to_check:
        url = check_grokipedia_url(name, entity_type)
        
        # Update database
        cursor.execute("""
            UPDATE entities
            SET grokipedia_url = ?, grokipedia_verified_at = ?
            WHERE id = ?
        """, (url, datetime.now(), entity_id))
        
        checked += 1
        if url:
            found += 1
            print(f"  ✓ {name}: {url}")
        
        # Commit every 10 to avoid losing progress
        if checked % 10 == 0:
            conn.commit()
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Checked {checked} entities, found {found} Grokipedia pages ({found/checked*100:.0f}%)")


def open_grokipedia_in_browser(url: str):
    """
    Open Grokipedia URL in default browser.
    
    Args:
        url: Grokipedia URL to open
    """
    import webbrowser
    webbrowser.open(url)


if __name__ == "__main__":
    # Test the checker
    db_path = Path("data/station10.db")
    
    if db_path.exists():
        update_entity_grokipedia_links(db_path)
    else:
        print("Database not found. Run load_validated_entities.py first.")

