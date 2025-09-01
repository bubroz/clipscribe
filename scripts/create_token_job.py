#!/usr/bin/env python3
"""Simple token creation for Cloud Run Job."""
import redis
import secrets
from datetime import datetime

# Connect to Redis
r = redis.from_url('redis://10.253.175.203:6379/0', decode_responses=True)

# Generate token
token = 'cs_test_' + secrets.token_urlsafe(12)

# Store token
r.hset(f'cs:token:{token}', mapping={
    'email': 'zforristall@gmail.com',
    'name': 'Zac Forristall',
    'tier': 'beta',
    'created': datetime.utcnow().isoformat() + 'Z',
    'monthly_limit': '100',
    'videos_used': '0',
    'status': 'active'
})

# Set expiry
r.expire(f'cs:token:{token}', 30*24*3600)

print(f'Token created: {token}')
print('Use this token with: Authorization: Bearer ' + token)
