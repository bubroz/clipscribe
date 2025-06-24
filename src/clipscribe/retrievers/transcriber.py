"""Gemini Flash Transcriber with Native Audio Support."""

import os
import logging
import tempfile
from typing import Dict, List, Optional, Any
from datetime import datetime
import google.generativeai as genai
from google.generativeai.types import RequestOptions
import json
import re
from pathlib import Path

from ..models import VideoTranscript, KeyPoint, Entity
from ..config.settings import Settings

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
        
        # Get settings
        self.settings = Settings()
        self.request_timeout = self.settings.gemini_request_timeout
        logger.info(f"Using Gemini request timeout: {self.request_timeout}s")
        
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
Extract ALL significant key points from this audio with timestamps. Be comprehensive - for a 60-minute video, 
we expect 30-50 key points. For each key point provide:
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

Include ALL of the following:
- Major announcements, decisions, or revelations
- Important statistics, numbers, or data points
- Key arguments, positions, or conclusions
- Significant quotes or statements
- Technical specifications or important details
- Policy changes or new initiatives
- Breaking news or updates
- Expert opinions or analysis
- Controversial statements or debates
- Action items or next steps mentioned

For news programs, include:
- Each major story or segment
- Key facts from each story
- Important quotes from officials
- Statistical data mentioned
- Policy implications discussed

Be thorough - it's better to include too many key points than too few.
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
""",
            
            "relationships": """
Extract meaningful relationships between entities from this audio. Focus on SPECIFIC, ACTIONABLE relationships.

Return as JSON:
[
    {
        "subject": "Entity name",
        "predicate": "specific action/relationship",
        "object": "Entity name",
        "timestamp": 120,
        "confidence": 0.95
    }
]

Examples of GOOD predicates:
- signed agreement with, vetoed bill from, acquired company
- defeated candidate, funded project, criticized policy
- announced partnership with, launched product, published research
- testified before, sanctioned country, awarded contract to

AVOID vague predicates like: mentioned, discussed, talked about, referenced

Focus on relationships that represent:
- Actions taken (signed, vetoed, launched)
- Formal relationships (partnered with, acquired, funded)
- Positions/stances (opposed, supported, criticized)
- Events/outcomes (defeated, won, achieved)
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
            transcript_response = await self.model.generate_content_async(
                [media_file, transcribe_prompt],
                request_options=RequestOptions(timeout=self.request_timeout)
            )
            results["transcript"] = transcript_response.text.strip()
            
            # 2. Key points extraction
            logger.info("Extracting key points...")
            keypoints_response = await self.model.generate_content_async(
                [media_file, self.prompts["key_points"]],
                request_options=RequestOptions(timeout=self.request_timeout)
            )
            results["key_points"] = self._parse_json_response(
                keypoints_response.text,
                default=[]
            )
            
            # 3. Summary generation
            logger.info("Generating summary...")
            summary_response = await self.model.generate_content_async(
                [media_file, self.prompts["summary"]],
                request_options=RequestOptions(timeout=self.request_timeout)
            )
            results["summary"] = summary_response.text.strip()
            
            # 4. Entity extraction
            logger.info("Extracting entities...")
            entities_response = await self.model.generate_content_async(
                [media_file, self.prompts["entities"]],
                request_options=RequestOptions(timeout=self.request_timeout)
            )
            results["entities"] = self._parse_json_response(
                entities_response.text,
                default=[]
            )
            
            # 5. Topic extraction
            logger.info("Extracting topics...")
            topics_response = await self.model.generate_content_async(
                [media_file, self.prompts["topics"]],
                request_options=RequestOptions(timeout=self.request_timeout)
            )
            results["topics"] = self._parse_json_response(
                topics_response.text,
                default=[]
            )
            
            # 6. Relationship extraction
            logger.info("Extracting relationships...")
            relationships_response = await self.model.generate_content_async(
                [media_file, self.prompts["relationships"]],
                request_options=RequestOptions(timeout=self.request_timeout)
            )
            results["relationships"] = self._parse_json_response(
                relationships_response.text,
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
                json_str = json_match.group()
                
                # Try to parse as-is first
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    # Common fixes for malformed JSON
                    # 1. Add missing commas between array/object items
                    json_str = re.sub(r'}\s*{', '},{', json_str)
                    json_str = re.sub(r']\s*\[', '],[', json_str)
                    json_str = re.sub(r'}\s*\[', '},[', json_str)
                    json_str = re.sub(r']\s*{', '],{', json_str)
                    
                    # 2. Fix missing commas after string values
                    json_str = re.sub(r'"\s*\n\s*"', '",\n"', json_str)
                    
                    # 3. Remove trailing commas
                    json_str = re.sub(r',\s*}', '}', json_str)
                    json_str = re.sub(r',\s*]', ']', json_str)
                    
                    # 4. Fix unclosed strings (basic attempt)
                    # Count quotes and add one if odd
                    quote_count = json_str.count('"') - json_str.count('\\"')
                    if quote_count % 2 == 1:
                        json_str += '"'
                    
                    # Try parsing again
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse JSON after fixes: {e}")
                        # Log more details to help debug
                        logger.debug(f"JSON length: {len(json_str)}")
                        logger.debug(f"Error position: {e.pos if hasattr(e, 'pos') else 'unknown'}")
                        logger.debug(f"JSON around error: {json_str[max(0, e.pos-100):e.pos+100] if hasattr(e, 'pos') else json_str[:200]}")
                        
                        # Last resort: try to extract valid portions
                        # For arrays, extract individual valid objects
                        if json_str.strip().startswith('['):
                            valid_items = []
                            # Extract individual objects
                            for match in re.finditer(r'{[^{}]*}', json_str):
                                try:
                                    valid_items.append(json.loads(match.group()))
                                except:
                                    pass
                            if valid_items:
                                return valid_items
                        
                        return default
            
            return default
            
        except Exception as e:
            logger.warning(f"Unexpected error parsing JSON: {e}")
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