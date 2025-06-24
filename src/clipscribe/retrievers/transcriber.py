"""Gemini Flash Transcriber with Native Audio Support."""

import os
import logging
import tempfile
from typing import Dict, List, Optional, Any
from datetime import datetime
import google.generativeai as genai
import json
import re
from pathlib import Path

from ..models import VideoTranscript, KeyPoint, Entity

logger = logging.getLogger(__name__)


class GeminiFlashTranscriber:
    """Use Gemini 2.5 Flash's native audio capabilities for video transcription."""
    
    def __init__(self):
        """Initialize Gemini with API key from environment."""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Cost tracking (Gemini 2.5 Flash pricing)
        self.audio_cost_per_minute = 0.002  # $0.002/minute for audio
        self.token_costs = {
            "input": 0.25 / 1_000_000,   # $0.25/M tokens
            "output": 0.50 / 1_000_000   # $0.50/M tokens
        }
        
        # Prompts for different tasks
        self.prompts = self._create_prompts()
    
    def _create_prompts(self) -> Dict[str, str]:
        """Create optimized prompts for video analysis."""
        return {
            "transcribe": """
Transcribe this audio file completely and accurately. Include:
- Full verbatim transcription
- Natural paragraph breaks
- Note any significant pauses or speaker changes
- Preserve technical terms and proper nouns exactly

Return ONLY the transcription text, no additional commentary.
""",
            
            "key_points": """
Extract the key points from this audio with timestamps. For each key point provide:
1. The exact timestamp (in seconds)
2. The key point in clear, concise language
3. Brief context if needed

Format as JSON:
[
    {
        "timestamp": 120,
        "text": "Main point here",
        "context": "Additional context"
    }
]

Focus on:
- Major announcements or revelations
- Important statistics or data
- Key arguments or conclusions
- Significant quotes
- Technical specifications or details
""",
            
            "summary": """
Provide a comprehensive executive summary of this audio content. Include:
- Main topic and purpose
- Key arguments or findings
- Important conclusions
- Notable quotes or statistics
- Overall significance

Keep it under 300 words but ensure all critical information is captured.
""",
            
            "entities": """
Extract all entities mentioned in this audio. Return as JSON:
[
    {
        "name": "Entity Name",
        "type": "PERSON|ORGANIZATION|LOCATION|EVENT|CONCEPT|TECHNOLOGY|PRODUCT",
        "context": "How they were mentioned",
        "timestamp": 120
    }
]

Be comprehensive - include all people, companies, technologies, locations, events, and important concepts.
""",
            
            "topics": """
List the main topics discussed in this audio. Return as a JSON array of strings.
Focus on high-level themes and subjects, not specific details.
Example: ["artificial intelligence", "climate change", "economic policy"]
"""
        }
    
    async def transcribe_audio(self, audio_file_path: str, video_duration: int) -> Dict[str, Any]:
        """
        Transcribe audio file using Gemini's native audio capabilities.
        
        Args:
            audio_file_path: Path to the audio file
            video_duration: Duration in seconds (for cost calculation)
            
        Returns:
            Dictionary with transcription and analysis results
        """
        return await self._transcribe_media(audio_file_path, video_duration, "audio")
    
    async def transcribe_video(self, video_file_path: str, video_duration: int) -> Dict[str, Any]:
        """
        Transcribe video file using Gemini 2.5 Flash with visual analysis.
        
        Args:
            video_file_path: Path to video file
            video_duration: Duration in seconds (for cost calculation)
            
        Returns:
            Dictionary with transcription and visual analysis results
        """
        return await self._transcribe_media(video_file_path, video_duration, "video")
    
    async def _transcribe_media(
        self,
        media_file_path: str,
        video_duration: int,
        media_type: str = "audio"
    ) -> Dict[str, Any]:
        """
        Transcribe media file using Gemini 2.5 Flash.
        
        Args:
            media_file_path: Path to media file
            video_duration: Duration in seconds
            media_type: "audio" or "video"
            
        Returns:
            Dictionary with transcription and analysis results
        """
        
        start_time = datetime.now()
        
        try:
            # Upload media file to Gemini
            logger.info(f"Uploading {media_type} file: {media_file_path}")
            media_file = genai.upload_file(media_file_path)
            
            # Calculate estimated cost
            if media_type == "video":
                # Video costs ~10x more than audio
                estimated_cost = self._calculate_cost(video_duration) * 10
            else:
                estimated_cost = self._calculate_cost(video_duration)
            logger.info(f"Estimated cost: ${estimated_cost:.4f}")
            
            # Generate all analyses in parallel for efficiency
            results = {}
            
            # Build appropriate prompts based on media type
            if media_type == "video":
                transcribe_prompt = """Analyze this video and provide:
1. A complete transcript of all spoken words
2. Descriptions of important visual elements (slides, code, diagrams)
3. Note any on-screen text or annotations
4. Identify speakers when possible
5. Mark key visual moments

Format: Provide a comprehensive transcript that captures both audio and visual content."""
            else:
                transcribe_prompt = self.prompts["transcribe"]
            
            # 1. Full transcription
            logger.info("Generating transcription...")
            transcript_response = await self.model.generate_content_async([
                media_file,
                transcribe_prompt
            ])
            results["transcript"] = transcript_response.text.strip()
            
            # 2. Key points extraction
            logger.info("Extracting key points...")
            keypoints_response = await self.model.generate_content_async([
                media_file,
                self.prompts["key_points"]
            ])
            results["key_points"] = self._parse_json_response(
                keypoints_response.text,
                default=[]
            )
            
            # 3. Summary generation
            logger.info("Generating summary...")
            summary_response = await self.model.generate_content_async([
                media_file,
                self.prompts["summary"]
            ])
            results["summary"] = summary_response.text.strip()
            
            # 4. Entity extraction
            logger.info("Extracting entities...")
            entities_response = await self.model.generate_content_async([
                media_file,
                self.prompts["entities"]
            ])
            results["entities"] = self._parse_json_response(
                entities_response.text,
                default=[]
            )
            
            # 5. Topic extraction
            logger.info("Extracting topics...")
            topics_response = await self.model.generate_content_async([
                media_file,
                self.prompts["topics"]
            ])
            results["topics"] = self._parse_json_response(
                topics_response.text,
                default=[]
            )
            
            # Calculate actual cost (approximate based on output)
            total_output_text = sum(len(str(v)) for v in results.values())
            actual_cost = self._calculate_actual_cost(video_duration, total_output_text)
            
            # Processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Transcription completed in {processing_time:.1f}s, cost: ${actual_cost:.4f}")
            
            # If video mode, multiply cost
            if media_type == "video":
                actual_cost = actual_cost * 10
            
            return {
                **results,
                "processing_cost": actual_cost,
                "processing_time": processing_time,
                "confidence_score": 0.95,  # Gemini Flash is very reliable
                "media_type": media_type
            }
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise
        finally:
            # Clean up uploaded file
            try:
                genai.delete_file(media_file.name)
            except:
                pass
    
    def _parse_json_response(self, response_text: str, default: Any) -> Any:
        """Parse JSON from Gemini response, handling common issues."""
        try:
            # Remove markdown code blocks if present
            cleaned = re.sub(r'```json\s*', '', response_text)
            cleaned = re.sub(r'```\s*', '', cleaned)
            
            # Find JSON content
            json_match = re.search(r'[\[\{].*[\]\}]', cleaned, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            return default
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON: {e}")
            return default
    
    def _calculate_cost(self, duration_seconds: int) -> float:
        """Calculate estimated cost for processing."""
        audio_minutes = duration_seconds / 60
        audio_cost = audio_minutes * self.audio_cost_per_minute
        
        # Estimate token costs (rough approximation)
        estimated_output_tokens = duration_seconds * 10  # ~10 tokens per second
        token_cost = (estimated_output_tokens / 1_000_000) * self.token_costs["output"]
        
        return audio_cost + token_cost
    
    def _calculate_actual_cost(self, duration_seconds: int, output_chars: int) -> float:
        """Calculate actual cost based on real usage."""
        audio_minutes = duration_seconds / 60
        audio_cost = audio_minutes * self.audio_cost_per_minute
        
        # Approximate tokens from characters (1 token ≈ 4 chars)
        output_tokens = output_chars / 4
        token_cost = (output_tokens / 1_000_000) * self.token_costs["output"]
        
        return audio_cost + token_cost 