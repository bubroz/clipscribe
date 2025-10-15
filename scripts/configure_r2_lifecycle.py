#!/usr/bin/env python3
"""
Configure Cloudflare R2 lifecycle rules for Station10.

Rules:
- raw/ folder: delete after 30 days
- raw/sensitive/ folder: delete after 7 days  
- keep/ folder: never delete
- All other folders: keep indefinitely (transcripts, entities, outputs)
"""

import boto3
import os
from pathlib import Path

# Load environment from env.production
env_file = Path.home() / "env.production"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

# R2 credentials
account_id = os.getenv('R2_ACCOUNT_ID')
access_key = os.getenv('R2_ACCESS_KEY_ID')
secret_key = os.getenv('R2_SECRET_ACCESS_KEY')
bucket_name = os.getenv('R2_BUCKET_NAME', 'station10-intelligence')

# Create S3 client for R2
s3 = boto3.client(
    's3',
    endpoint_url=f'https://{account_id}.r2.cloudflarestorage.com',
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    region_name='auto'  # R2 uses 'auto' region
)

# Define lifecycle configuration
lifecycle_config = {
    'Rules': [
        {
            'ID': 'delete-raw-after-30-days',
            'Prefix': 'raw/',
            'Status': 'Enabled',
            'Expiration': {
                'Days': 30
            }
        },
        {
            'ID': 'delete-sensitive-after-7-days',
            'Prefix': 'raw/sensitive/',
            'Status': 'Enabled',
            'Expiration': {
                'Days': 7
            }
        },
        # Note: No rule for 'keep/' means objects are retained indefinitely
    ]
}

try:
    # Apply lifecycle configuration
    s3.put_bucket_lifecycle_configuration(
        Bucket=bucket_name,
        LifecycleConfiguration=lifecycle_config
    )
    print(f"✓ Lifecycle rules configured for {bucket_name}")
    print("  - raw/ folder: delete after 30 days")
    print("  - raw/sensitive/ folder: delete after 7 days")
    print("  - keep/ folder: retain indefinitely")
    print("  - All other folders: retain indefinitely")
    
    # Verify configuration
    response = s3.get_bucket_lifecycle_configuration(Bucket=bucket_name)
    print(f"\n✓ Verified {len(response['Rules'])} lifecycle rules active")
    
except Exception as e:
    print(f"✗ Failed to configure lifecycle rules: {e}")
    print("\nNote: R2 lifecycle rules may need to be configured via Cloudflare dashboard")
    print("Go to: R2 → station10-intelligence → Settings → Lifecycle Rules")
