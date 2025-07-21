"""Vertex AI-based transcriber implementation for ClipScribe."""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

# Load environment variables FIRST
from dotenv import load_dotenv
load_dotenv()

import vertexai
from vertexai.generative_models import GenerativeModel, Part, Content
from google.cloud import storage
from google.api_core import exceptions as google_exceptions

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
    
    def __init__(self):
        """Initialize Vertex AI transcriber."""
        self.project_id = VERTEX_AI_PROJECT_ID
        self.location = VERTEX_AI_LOCATION
        self.model_name = VERTEX_AI_MODEL_NAME
        
        # Initialize Vertex AI
        vertexai.init(project=self.project_id, location=self.location)
        
        # Initialize the model
        self.model = GenerativeModel(self.model_name)
        
        # Initialize GCS client for video uploads
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
            blob.upload_from_filename(str(video_path), retry=google_exceptions.retry.Retry())
            
            gcs_uri = f"gs://{bucket_name}/{blob_name}"
            logger.info(f"Uploaded video to GCS: {gcs_uri}")
            return gcs_uri
            
        except Exception as e:
            logger.error(f"Failed to upload video to GCS: {e}")
            raise
    
    async def transcribe_with_vertex(
        self, 
        video_path: Path,
        enhance_transcript: bool = True,
        mode: str = "video"
    ) -> VideoIntelligence:
        """Transcribe video using Vertex AI with retry logic."""
        
        # Upload video to GCS
        gcs_uri = await self.upload_to_gcs(video_path)
        
        # Build the prompt
        prompt = self._build_comprehensive_prompt(enhance_transcript)
        
        # Create video part
        video_part = Part.from_uri(
            mime_type=self._get_mime_type(video_path),
            uri=gcs_uri
        )
        
        # Generate content with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await self._generate_with_retry(
                    [prompt, video_part],
                    generation_config=VERTEX_AI_GENERATION_CONFIG
                )
                
                # Parse response
                result = self._parse_response(response.text)
                
                # Clean up GCS file
                await self._cleanup_gcs_file(gcs_uri)
                
                return result
                
            except Exception as e:
                if "503" in str(e) and attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 10
                    logger.warning(f"503 error, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    # Clean up GCS file even on error
                    await self._cleanup_gcs_file(gcs_uri)
                    raise
    
    async def _generate_with_retry(self, contents, generation_config):
        """Generate content with Vertex AI using retry logic."""
        # Convert to sync for now (Vertex AI SDK doesn't have async yet)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.model.generate_content,
            contents,
            generation_config
        )
    
    def _build_comprehensive_prompt(self, enhance_transcript: bool) -> str:
        """Build the comprehensive prompt for video analysis."""
        base_prompt = """Analyze this video comprehensively and extract:

1. **Accurate Transcript**: Include all spoken words with timestamps
2. **Temporal Intelligence**: 
   - Temporal events and chronological references
   - Visual timestamps (documents, calendars, screens)
   - Dates mentioned or shown
3. **Entities**: People, organizations, locations, events with confidence scores
4. **Relationships**: Who said what about whom, when, and context
5. **Key Insights**: Main points and takeaways

Return a JSON response with this structure:
{
  "transcript": {
    "segments": [
      {
        "text": "segment text",
        "start_time": 0.0,
        "end_time": 5.2,
        "speaker": "Speaker 1"
      }
    ],
    "full_text": "complete transcript"
  },
  "temporal_intelligence": {
    "temporal_events": [...],
    "visual_timestamps": [...],
    "dates_mentioned": [...]
  },
  "entities": [...],
  "relationships": [...],
  "key_insights": [...]
}"""
        
        if enhance_transcript:
            base_prompt += "\n\nProvide enhanced temporal intelligence with high confidence scores."
        
        return base_prompt
    
    def _parse_response(self, response_text: str) -> VideoIntelligence:
        """Parse Vertex AI response into VideoIntelligence object."""
        try:
            data = json.loads(response_text)
            
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
            return VideoIntelligence(
                transcript_segments=segments,
                transcript_text=data.get("transcript", {}).get("full_text", ""),
                entities=[Entity(**e) for e in data.get("entities", [])],
                relationships=[Relationship(**r) for r in data.get("relationships", [])],
                key_insights=data.get("key_insights", []),
                temporal_intelligence=TemporalIntelligence(**data.get("temporal_intelligence", {}))
            )
            
        except Exception as e:
            logger.error(f"Failed to parse Vertex AI response: {e}")
            raise
    
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
            bucket_name = gcs_uri.split("/")[2]
            blob_name = "/".join(gcs_uri.split("/")[3:])
            
            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            blob.delete()
            
            logger.debug(f"Cleaned up GCS file: {gcs_uri}")
        except Exception as e:
            logger.warning(f"Failed to clean up GCS file: {e}") 