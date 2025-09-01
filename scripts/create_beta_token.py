#!/usr/bin/env python3
"""
Create a beta token for ClipScribe API testing.
This script connects directly to Redis to create valid tokens.
"""

import os
import sys
import json
import secrets
import hashlib
from datetime import datetime
import redis

def create_token(email: str, name: str, reason: str = "Beta testing"):
    """Create a beta token in Redis."""
    
    # Get Redis connection details
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        # Try to get from Secret Manager
        import subprocess
        result = subprocess.run(
            ["gcloud", "secrets", "versions", "access", "latest", "--secret=REDIS_URL"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            redis_url = result.stdout.strip()
        else:
            print("Error: Could not get REDIS_URL from Secret Manager")
            sys.exit(1)
    
    # Parse Redis URL
    # redis://10.253.175.203:6379/0
    import re
    match = re.match(r'redis://([^:]+):(\d+)/(\d+)', redis_url)
    if not match:
        print(f"Error: Invalid Redis URL format: {redis_url}")
        sys.exit(1)
    
    host, port, db = match.groups()
    
    # Connect to Redis via VPC connector
    # Note: This needs to be run from a Cloud Run job or Cloud Function
    # that has access to the VPC network
    print(f"Connecting to Redis at {host}:{port} db={db}")
    
    try:
        r = redis.Redis(
            host=host,
            port=int(port),
            db=int(db),
            decode_responses=True,
            socket_connect_timeout=5
        )
        
        # Test connection
        r.ping()
        print("✓ Connected to Redis")
        
        # Generate token
        token = f"cs_beta_{secrets.token_urlsafe(16)}"
        
        # Store token data
        token_key = f"cs:token:{token}"
        token_data = {
            "email": email,
            "name": name,
            "tier": "beta",
            "created": datetime.utcnow().isoformat() + "Z",
            "reason": reason,
            "monthly_limit": "100",
            "videos_used": "0",
            "status": "active"
        }
        
        r.hset(token_key, mapping=token_data)
        r.expire(token_key, 30 * 24 * 3600)  # 30 days
        
        # Also add to valid tokens set
        r.sadd("cs:valid_tokens", token)
        
        print(f"✓ Created token: {token}")
        print(f"  Email: {email}")
        print(f"  Name: {name}")
        print(f"  Expires: 30 days")
        
        return token
        
    except redis.ConnectionError as e:
        print(f"Error: Could not connect to Redis: {e}")
        print("\nThis script needs to be run from an environment with VPC access:")
        print("1. Cloud Run Job with VPC connector")
        print("2. Cloud Function with VPC connector")
        print("3. Compute Engine VM in the same VPC")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python create_beta_token.py <email> <name> [reason]")
        sys.exit(1)
    
    email = sys.argv[1]
    name = sys.argv[2]
    reason = sys.argv[3] if len(sys.argv) > 3 else "Beta testing"
    
    token = create_token(email, name, reason)
