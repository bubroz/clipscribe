#!/usr/bin/env python3
"""Setup script for Vertex AI integration."""

import os
import sys
from pathlib import Path
from google.cloud import storage
from google.api_core import exceptions

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.clipscribe.config.vertex_ai_config import (
    VERTEX_AI_PROJECT_ID,
    VERTEX_AI_LOCATION,
    VERTEX_AI_STAGING_BUCKET
)


def create_staging_bucket():
    """Create GCS staging bucket for video uploads."""
    bucket_name = VERTEX_AI_STAGING_BUCKET.replace("gs://", "")
    
    try:
        client = storage.Client(project=VERTEX_AI_PROJECT_ID)
        bucket = client.bucket(bucket_name)
        
        if bucket.exists():
            print(f"✅ Bucket {bucket_name} already exists")
            return
        
        # Create bucket
        bucket = client.create_bucket(bucket_name, location=VERTEX_AI_LOCATION)
        
        # Set lifecycle rule to delete videos after 1 day
        rule = storage.lifecycle_rules.LifecycleRule(
            action={'type': 'Delete'},
            condition={'age': 1}
        )
        bucket.add_lifecycle_rule(rule)
        bucket.patch()
        
        print(f"✅ Created bucket {bucket_name} with 1-day lifecycle rule")
        
    except exceptions.Forbidden:
        print(f"❌ Permission denied. Make sure you have storage.buckets.create permission")
        print(f"   Run: gcloud projects add-iam-policy-binding {VERTEX_AI_PROJECT_ID} \\")
        print(f"        --member=user:YOUR_EMAIL --role=roles/storage.admin")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error creating bucket: {e}")
        sys.exit(1)


def check_vertex_ai_setup():
    """Check if Vertex AI is properly configured."""
    print(f"🔍 Checking Vertex AI setup...")
    print(f"   Project ID: {VERTEX_AI_PROJECT_ID}")
    print(f"   Location: {VERTEX_AI_LOCATION}")
    print(f"   Staging Bucket: {VERTEX_AI_STAGING_BUCKET}")
    
    # Check if gcloud is authenticated
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        print("\n⚠️  GOOGLE_APPLICATION_CREDENTIALS not set")
        print("   Run: gcloud auth application-default login")
    else:
        print(f"\n✅ Using credentials from: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")


if __name__ == "__main__":
    print("🚀 Setting up Vertex AI for ClipScribe\n")
    
    check_vertex_ai_setup()
    print()
    create_staging_bucket()
    
    print("\n✅ Vertex AI setup complete!")
    print("\n📝 Next steps:")
    print("1. Update .env with: USE_VERTEX_AI=true")
    print("2. Run: poetry run clipscribe transcribe <video_url>") 