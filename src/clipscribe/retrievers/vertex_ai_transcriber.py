"""Vertex AI-based transcriber implementation for ClipScribe."""

# Load environment variables FIRST, before ANY Google imports
import os
from dotenv import load_dotenv
load_dotenv()

# Set credentials if available in env
if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS") and os.path.exists("/Users/base/.config/gcloud/clipscribe-service-account.json"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/base/.config/gcloud/clipscribe-service-account.json"

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

import vertexai
from vertexai.generative_models import GenerativeModel, Part, Content
from google.cloud import storage
from google.api_core import exceptions as google_exceptions
from google.api_core import retry

from ..models import (
    VideoIntelligence, 
    TranscriptSegment,
    TemporalIntelligence,
    Entity,
    Relationship
)
from ..config.vertex_ai_config import (
    VERTEX_AI_PROJECT_ID,
    VERTEX_AI_LOCATION,
    VERTEX_AI_MODEL_NAME,
    VERTEX_AI_GENERATION_CONFIG,
    VERTEX_AI_REQUEST_CONFIG,
    VERTEX_AI_SAFETY_SETTINGS,
    VERTEX_AI_STAGING_BUCKET
)

logger = logging.getLogger(__name__)


class VertexAITranscriber:
    """Transcriber using Vertex AI for robust video processing."""
    
    def __init__(self, gemini_pool=None):
        """Initialize Vertex AI transcriber."""
        # Set credentials if available
        if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS") and os.path.exists("/Users/base/.config/gcloud/clipscribe-service-account.json"):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/base/.config/gcloud/clipscribe-service-account.json"
        
        self.project_id = VERTEX_AI_PROJECT_ID
        self.location = VERTEX_AI_LOCATION
        self.model_name = VERTEX_AI_MODEL_NAME
        self.bucket_name = VERTEX_AI_STAGING_BUCKET.replace("gs://", "")
        self.auto_cleanup = True  # Automatically clean up GCS files after processing
        
        # Initialize Vertex AI
        vertexai.init(project=self.project_id, location=self.location)
        
        # Initialize model
        self.model = GenerativeModel(self.model_name)
        
        # Initialize storage client
        self.storage_client = storage.Client(project=self.project_id)
        
        logger.info(f"Initialized Vertex AI transcriber with model: {self.model_name}")
    
    async def upload_to_gcs(self, video_path: Path) -> str:
        """Upload video to GCS for Vertex AI processing."""
        bucket_name = VERTEX_AI_STAGING_BUCKET.replace("gs://", "")
        blob_name = f"videos/{datetime.now().isoformat()}/{video_path.name}"
        
        try:
            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            
            # Upload with retry
            blob.upload_from_filename(str(video_path), retry=retry.Retry())
            
            gcs_uri = f"gs://{bucket_name}/{blob_name}"
            logger.info(f"Uploaded video to GCS: {gcs_uri}")
            return gcs_uri
            
        except Exception as e:
            logger.error(f"Failed to upload video to GCS: {e}")
            raise
    
    async def transcribe_with_vertex(
        self,
        video_path: Path,
        enhance_transcript: bool = False,
        mode: str = "video"
    ) -> Dict[str, Any]:
        """Process video using Vertex AI."""
        try:
            # Upload to GCS
            gcs_uri = await self.upload_to_gcs(video_path)
            logger.info(f"Uploaded video to GCS: {gcs_uri}")
            
            # Build prompt
            prompt = self._build_comprehensive_prompt(enhance_transcript)
            
            # Create content with video file reference
            video_part = Part.from_uri(
                uri=gcs_uri,
                mime_type=self._get_mime_type(video_path)
            )
            
            # Create contents list with prompt and video
            contents = [prompt, video_part]
            
            # Configure generation with JSON response
            generation_config = {
                "temperature": 0.1,
                "top_p": 0.95,
                "max_output_tokens": 8192,
                "response_mime_type": "application/json",  # Request JSON response
            }
            
            # Generate with retry
            response = await self._generate_with_retry(contents, generation_config)
            
            # Parse response
            result = self._parse_response(response.text)
            
            # Clean up GCS file if needed
            if self.auto_cleanup:
                await self._cleanup_gcs_file(gcs_uri)
            
            return result
            
        except Exception as e:
            logger.error(f"Vertex AI transcription failed: {e}")
            raise
    
    async def _generate_with_retry(self, contents, generation_config):
        """Generate content with exponential backoff retry logic."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.model.generate_content(
                contents=contents,
                generation_config=generation_config
            )
        )
    
    def _build_comprehensive_prompt(self, enhance_transcript: bool) -> str:
        """Build the comprehensive prompt for video analysis."""
        base_prompt = """Analyze this video comprehensively and extract:

1. Full transcript with accurate timestamps
2. All entities (people, organizations, locations, events) with context
3. Relationships between entities
4. Key insights and summary points
5. Temporal intelligence including dates, timeline events, and chronological references

Return the response as a valid JSON object with this structure:
{
  "transcript": {
    "segments": [
      {
        "text": "segment text",
        "start_time": 0.0,
        "end_time": 1.0,
        "speaker": "optional speaker id"
      }
    ],
    "full_text": "complete transcript text"
  },
  "entities": [
    {
      "name": "entity name",
      "type": "PERSON/ORGANIZATION/LOCATION/EVENT",
      "description": "context about the entity",
      "confidence": 0.95
    }
  ],
  "relationships": [
    {
      "source": "entity1",
      "target": "entity2",
      "type": "relationship type",
      "description": "relationship context",
      "confidence": 0.90
    }
  ],
  "key_insights": [
    "insight 1",
    "insight 2"
  ],
  "temporal_intelligence": {
    "temporal_events": [
      {
        "timestamp": 0.0,
        "description": "event description",
        "type": "date_reference/timeline_event"
      }
    ],
    "visual_timestamps": [
      {
        "timestamp": 0.0,
        "description": "visual date/time reference",
        "text": "extracted text"
      }
    ],
    "dates_mentioned": [
      {
        "date": "2024-01-01",
        "context": "context of date mention",
        "timestamp": 0.0
      }
    ]
  },
  "processing_cost": 0.01,
  "model_used": "vertex-ai-gemini-2.5-flash"
}

IMPORTANT: Return ONLY valid JSON, no markdown formatting or additional text."""
        
        if enhance_transcript:
            base_prompt += "\n\nProvide enhanced temporal intelligence with detailed timeline analysis."
            
        return base_prompt
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the Vertex AI response into our expected format."""
        try:
            # Log the raw response for debugging
            logger.debug(f"Raw Vertex AI response (first 500 chars): {response_text[:500]}")
            
            # Handle empty response
            if not response_text or response_text.strip() == "":
                logger.error("Vertex AI returned empty response")
                return self._create_fallback_response("Vertex AI returned empty response")
            
            # Try to parse as JSON
            try:
                data = json.loads(response_text)
            except json.JSONDecodeError:
                # If not JSON, treat as plain text transcript
                logger.warning("Vertex AI response is not JSON, treating as plain text")
                return {
                    "transcript": response_text,
                    "processing_cost": 0.01,  # Estimate
                    "model_used": "vertex-ai-gemini-2.5-flash",
                    "temporal_intelligence": {
                        "timeline_events": [],
                        "visual_temporal_cues": [],
                        "visual_dates": [],
                        "chronological_references": []
                    }
                }
            
            # Extract transcript segments
            segments = []
            for seg in data.get("transcript", {}).get("segments", []):
                segments.append(TranscriptSegment(
                    text=seg["text"],
                    start_time=seg["start_time"],
                    end_time=seg["end_time"],
                    speaker=seg.get("speaker")
                ))
            
            # Build VideoIntelligence object
            return {
                "transcript": {
                    "segments": segments,
                    "full_text": data.get("transcript", {}).get("full_text", "")
                },
                "temporal_intelligence": {
                    "temporal_events": data.get("temporal_intelligence", {}).get("temporal_events", []),
                    "visual_timestamps": data.get("temporal_intelligence", {}).get("visual_timestamps", []),
                    "dates_mentioned": data.get("temporal_intelligence", {}).get("dates_mentioned", [])
                },
                "entities": [Entity(**e) for e in data.get("entities", [])],
                "relationships": [Relationship(**r) for r in data.get("relationships", [])],
                "key_insights": data.get("key_insights", []),
                "processing_cost": data.get("processing_cost", 0.01),
                "model_used": data.get("model_used", "vertex-ai-gemini-2.5-flash")
            }
            
        except Exception as e:
            logger.error(f"Failed to parse Vertex AI response: {e}")
            raise
    
    def _create_fallback_response(self, error_message: str) -> Dict[str, Any]:
        """Create a fallback response when parsing fails."""
        return {
            "transcript": {
                "segments": [],
                "full_text": f"[Error: {error_message}]"
            },
            "temporal_intelligence": {
                "temporal_events": [],
                "visual_timestamps": [],
                "dates_mentioned": []
            },
            "entities": [],
            "relationships": [],
            "key_insights": [],
            "processing_cost": 0.01,
            "model_used": "vertex-ai-gemini-2.5-flash-error"
        }
    
    def _get_mime_type(self, video_path: Path) -> str:
        """Get MIME type for video file."""
        ext = video_path.suffix.lower()
        mime_types = {
            ".mp4": "video/mp4",
            ".avi": "video/x-msvideo",
            ".mov": "video/quicktime",
            ".webm": "video/webm",
            ".mkv": "video/x-matroska"
        }
        return mime_types.get(ext, "video/mp4")
    
    async def _cleanup_gcs_file(self, gcs_uri: str):
        """Clean up uploaded file from GCS."""
        try:
            # Extract bucket and blob name from URI
            # Format: gs://bucket-name/path/to/file
            parts = gcs_uri.replace("gs://", "").split("/", 1)
            if len(parts) != 2:
                logger.warning(f"Invalid GCS URI format: {gcs_uri}")
                return
                
            bucket_name, blob_name = parts
            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            
            blob.delete()
            logger.info(f"Cleaned up GCS file: {gcs_uri}")
        except Exception as e:
            logger.warning(f"Failed to clean up GCS file {gcs_uri}: {e}") 