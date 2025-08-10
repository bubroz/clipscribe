"""Vertex AI implementation for transcription and intelligence extraction."""

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
import tenacity

from ..models import (
    VideoIntelligence, 
    TranscriptSegment,
    TemporalIntelligence,
    Entity,
    Relationship
)
from ..config.settings import Settings
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
    """Vertex AI implementation for video transcription and analysis."""

    def __init__(self, performance_monitor: Optional[Any] = None):
        self.settings = Settings()
        self.performance_monitor = performance_monitor
        self.project_id = self.settings.vertex_ai_project or VERTEX_AI_PROJECT_ID
        self.location = self.settings.vertex_ai_location or VERTEX_AI_LOCATION
        self.model_name = VERTEX_AI_MODEL_NAME
        self.auto_cleanup = False

        # Set credentials if available in env
        if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            logger.warning("GOOGLE_APPLICATION_CREDENTIALS not set. Attempting to use default credentials")

        # Initialize Vertex AI
        vertexai.init(project=self.project_id, location=self.location)
        
        # Initialize model
        self.model = GenerativeModel(self.model_name)
        
        # Initialize storage client
        self.storage_client = storage.Client(project=self.project_id)
        
        logger.info(f"Initialized Vertex AI transcriber with model: {self.model_name}")
    
    async def upload_to_gcs(self, video_path: Path) -> str:
        """Upload video to GCS for Vertex AI processing with increased timeout."""
        bucket_name = VERTEX_AI_STAGING_BUCKET.replace("gs://", "")
        blob_name = f"videos/{datetime.now().isoformat()}/{video_path.name}"
        
        try:
            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            
            # Upload with increased timeout and retry
            try:
                with open(video_path, 'rb') as f:
                    blob.upload_from_file(f, content_type=self._get_mime_type(str(video_path)))
            except BrokenPipeError:
                await asyncio.sleep(10)
                raise
            
            gcs_uri = f"gs://{bucket_name}/{blob_name}"
            logger.info(f"Uploaded video to GCS: {gcs_uri}")
            return gcs_uri
            
        except Exception as e:
            logger.error(f"Failed to upload video to GCS: {e}")
            raise
    
    async def transcribe_with_vertex(
        self,
        video_path: Optional[Path] = None,
        gcs_uri: Optional[str] = None,
        enhance_transcript: bool = False,
        mode: str = "video"
    ) -> Dict[str, Any]:
        """Process video using Vertex AI.
        
        Args:
            video_path: Local path to video file (will be uploaded to GCS)
            gcs_uri: Direct GCS URI to use (skips upload)
            enhance_transcript: Whether to enhance the transcript
            mode: Processing mode ('video' or 'audio')
        """
        try:
            # Either use provided GCS URI or upload video
            if gcs_uri:
                logger.info(f"Using provided GCS URI: {gcs_uri}")
                # Extract mime type from URI
                if gcs_uri.endswith('.mp4'):
                    mime_type = "video/mp4"
                elif gcs_uri.endswith('.mp3'):
                    mime_type = "audio/mpeg"
                else:
                    mime_type = "video/mp4"  # Default
            elif video_path:
                # Upload to GCS
                gcs_uri = await self.upload_to_gcs(video_path)
                logger.info(f"Uploaded video to GCS: {gcs_uri}")
                mime_type = self._get_mime_type(str(video_path))
            else:
                raise ValueError("Either video_path or gcs_uri must be provided")
            
            # Build prompt based on mode
            prompt = self._build_comprehensive_prompt(enhance_transcript, mode)
            
            # Create content with video/audio file reference
            media_part = Part.from_uri(
                uri=gcs_uri,
                mime_type=mime_type
            )
            
            # Create contents with proper Content/Part structure
            contents = [
                Content(
                    role="user",
                    parts=[
                        Part.from_text(prompt),
                        media_part,
                    ],
                )
            ]
            
            # Configure generation with JSON response
            generation_config = {
                "temperature": 0.1,
                "top_p": 0.95,
                "max_output_tokens": 32768,  # Increased to avoid truncation
            }
            
            # First try a single request (no retries) so we can detect 400 and fall back quickly
            try:
                response = await self._generate_once(contents, generation_config)
            except Exception as e:
                if "invalid argument" in str(e).lower() and gcs_uri:
                    logger.info("Vertex rejected gs:// URI; attempting inline bytes fallback")
                    try:
                        parts = gcs_uri.replace("gs://", "").split("/", 1)
                        bucket_name, blob_name = parts[0], parts[1]
                        bucket = self.storage_client.bucket(bucket_name)
                        blob = bucket.blob(blob_name)
                        media_bytes = blob.download_as_bytes()
                        inline_media_part = Part.from_data(mime_type=mime_type, data=media_bytes)
                        contents = [
                            Content(
                                role="user",
                                parts=[Part.from_text(prompt), inline_media_part],
                            )
                        ]
                        response = await self._generate_with_retry(contents, generation_config)
                    except Exception:
                        raise
                else:
                    # For non-400 errors, use retry strategy
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
    
    @tenacity.retry(stop=tenacity.stop_after_attempt(10), wait=tenacity.wait_exponential(min=5, max=300))
    async def _generate_with_retry(self, contents, generation_config):
        """Generate content with exponential backoff retry logic."""
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(
                    contents=contents,
                    generation_config=generation_config
                )
            )
        except Exception as e:
            logger.error(f'Vertex AI generate failed: {str(e)}')
            logger.error(f'Request contents: {contents}')
            logger.error(f'Generation config: {generation_config}')
            raise

    async def _generate_once(self, contents, generation_config):
        """Single attempt generate without retries to detect fast-fail errors."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.model.generate_content(
                contents=contents,
                generation_config=generation_config
            )
        )
    
    def _build_comprehensive_prompt(self, enhance_transcript: bool = False, mode: str = "video") -> str:
        """Build the comprehensive prompt for video or audio analysis."""
        content_type = "video" if mode == "video" else "audio"
        
        base_prompt = f"""Analyze this {content_type} comprehensively and extract:

1. Full transcript with accurate timestamps
2. All entities (people, organizations, locations, events) with context
3. Relationships between entities
4. Key insights and summary points
5. Temporal intelligence including dates, timeline events, and chronological references"""
        
        if mode == "video":
            base_prompt += """\n6. Visual intelligence: on-screen text, dates, and temporal cues"""
        
        base_prompt += """\n
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
            logger.info(f"Raw Vertex AI response length: {len(response_text)} chars")
            logger.info(f"First 2000 chars of response: {response_text[:2000]}")
            logger.debug(f"Full Vertex AI response: {response_text}")
            
            # Handle empty response
            if not response_text or response_text.strip() == "":
                logger.error("Vertex AI returned empty response")
                return self._create_fallback_response("Vertex AI returned empty response")
            
            # Try to parse as JSON
            try:
                data = json.loads(response_text)
                logger.info(f"Parsed JSON with keys: {list(data.keys())}")
                if "entities" in data:
                    logger.info(f"Found {len(data['entities'])} entities")
                    if data['entities']:
                        logger.info(f"First entity example: {data['entities'][0]}")
            except json.JSONDecodeError as e:
                # If not JSON, treat as plain text transcript
                logger.warning(f"Vertex AI response is not valid JSON: {e}")
                logger.warning(f"JSON error position: {e.pos}")
                logger.warning(f"Error around: ...{response_text[max(0, e.pos-50):min(len(response_text), e.pos+50)]}...")
                return {
                    "transcript": {
                        "full_text": response_text,
                        "segments": []  # No segments for plain text
                    },
                    "entities": [],
                    "relationships": [],
                    "key_insights": [],
                    "processing_cost": 0.01,  # Estimate
                    "model_used": "vertex-ai-gemini-2.5-flash",
                    "temporal_intelligence": {
                        "temporal_events": [],
                        "visual_timestamps": [],
                        "dates_mentioned": []
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
            
            # Build entities list - handle field name mapping
            entities = []
            for e in data.get("entities", []):
                # Map 'name' to 'entity' field
                entity_data = {
                    "entity": e.get("name", e.get("entity", "")),  # Support both 'name' and 'entity'
                    "type": e.get("type", ""),
                    "confidence": e.get("confidence", 0.0),
                    "source": "vertex-ai"
                }
                entities.append(Entity(**entity_data))
            
            # Build relationships list - handle field name mapping
            relationships = []
            for r in data.get("relationships", []):
                rel_data = {
                    "subject": r.get("source", r.get("source_entity", "")),
                    "predicate": r.get("type", r.get("relationship_type", "")),
                    "object": r.get("target", r.get("target_entity", "")),
                    "confidence": r.get("confidence", 0.0),
                    "source": "vertex-ai"
                }
                relationships.append(Relationship(**rel_data))
            
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
                "entities": entities,
                "relationships": relationships,
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
    
    def _get_mime_type(self, file_path: str) -> str:
        """Get MIME type based on file extension."""
        if file_path.endswith('.mp3'):
            return 'audio/mpeg'  # Correct MIME type for MP3
        elif file_path.endswith('.mp4'):
            return 'video/mp4'
        elif file_path.endswith('.wav'):
            return 'audio/wav'
        else:
            return 'audio/mpeg'  # Default to audio for audio processing
    
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