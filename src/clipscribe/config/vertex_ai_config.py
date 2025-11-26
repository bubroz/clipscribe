"""Vertex AI configuration for ClipScribe."""

import os
from pathlib import Path
from typing import Optional

# Vertex AI Configuration
VERTEX_AI_PROJECT_ID = os.getenv("VERTEX_AI_PROJECT_ID", "your-project-id")
VERTEX_AI_LOCATION = os.getenv("VERTEX_AI_LOCATION", "us-central1")
VERTEX_AI_STAGING_BUCKET = os.getenv(
    "VERTEX_AI_STAGING_BUCKET", f"gs://{VERTEX_AI_PROJECT_ID}-clipscribe-staging"
)

# Model Configuration
# Gemini model constants removed - using Voxtral-Grok pipeline
VERTEX_AI_MODEL_TIMEOUT = 14400  # 4 hours for long videos

# Request Configuration
VERTEX_AI_REQUEST_CONFIG = {
    "max_retries": 3,
    "initial_retry_delay": 5.0,
    "retry_multiplier": 2.0,
    "max_retry_delay": 60.0,
    "timeout": VERTEX_AI_MODEL_TIMEOUT,
}

# Generation Configuration Defaults
VERTEX_AI_GENERATION_CONFIG = {
    "temperature": 0.1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 16384,
    "candidate_count": 1,
}

# Safety Settings
VERTEX_AI_SAFETY_SETTINGS = {
    "HARM_CATEGORY_HATE_SPEECH": "BLOCK_ONLY_HIGH",
    "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_ONLY_HIGH",
    "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_ONLY_HIGH",
    "HARM_CATEGORY_HARASSMENT": "BLOCK_ONLY_HIGH",
}


def get_vertex_ai_credentials_path() -> Optional[Path]:
    """Get the path to Google Cloud credentials file."""
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path:
        return Path(creds_path)

    # Check common locations
    default_paths = [
        Path.home() / ".config/gcloud/application_default_credentials.json",
        Path.home() / ".config/gcloud/credentials.json",
    ]

    for path in default_paths:
        if path.exists():
            return path

    return None
