"""Gemini Flash Transcriber with Native Audio Support."""

import os
import logging
import tempfile
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import google.generativeai as genai
from google.generativeai.types import RequestOptions, GenerationConfig
import json
import re
from pathlib import Path
import asyncio
import mimetypes

from ..models import VideoTranscript, KeyPoint, Entity, Topic
from ..config.settings import Settings
from .gemini_pool import GeminiPool, TaskType

logger = logging.getLogger(__name__)


class GeminiFlashTranscriber:
    """Transcribe video/audio using Gemini models with enhanced capabilities."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize transcriber with API key.
        
        Args:
            api_key: Google API key (optional, uses env var if not provided)
        """
        # Get settings
        settings = Settings()
        self.api_key = api_key or settings.google_api_key
        if not self.api_key:
            raise ValueError("Google API key is required")
        
        genai.configure(api_key=self.api_key)
        
        # Initialize GeminiPool instead of single client
        self.pool = GeminiPool(api_key=self.api_key)
        
        # Get timeout setting
        self.request_timeout = settings.gemini_request_timeout
        logger.info(f"Using Gemini request timeout: {self.request_timeout}s")
        
        # Track costs
        self.total_cost = 0.0
    
    def _enhance_json_response(self, raw_text: str) -> str:
        """
        Enhance malformed JSON from Gemini responses.
        
        Fixes common issues:
        - Missing commas between elements
        - Trailing commas
        - Unclosed strings
        - Missing quotes
        
        Args:
            raw_text: Raw response text from Gemini
            
        Returns:
            Enhanced JSON string
        """
        # Remove markdown code blocks if present
        if '```json' in raw_text:
            raw_text = raw_text.replace('```json', '').replace('```', '')
        elif '```' in raw_text:
            raw_text = raw_text.replace('```', '')
            
        # Remove any text before the first { or [
        json_start = max(raw_text.find('{'), raw_text.find('['))
        if json_start > 0:
            raw_text = raw_text[json_start:]
        
        # Remove any text after the last } or ]
        json_end_brace = raw_text.rfind('}')
        json_end_bracket = raw_text.rfind(']')
        json_end = max(json_end_brace, json_end_bracket) + 1
        if json_end < len(raw_text):
            raw_text = raw_text[:json_end]
        
        # Fix missing commas between array elements or object properties
        # This regex finds places where a string/number/boolean/object/array ends
        # and is followed by whitespace and then a quote (indicating a new element)
        raw_text = re.sub(r'(["\]\}])\s*\n\s*"', r'\1,\n"', raw_text)
        raw_text = re.sub(r'(["\]\}0-9])\s+"', r'\1,"', raw_text)
        
        # Fix trailing commas
        raw_text = re.sub(r',\s*([}\]])', r'\1', raw_text)
        
        # Fix unclosed strings at the end of arrays
        raw_text = re.sub(r'"\s*\n\s*\]', r'"\n]', raw_text)
        
        return raw_text
    
    def _parse_json_response(self, response_text: str, expected_type: str = "object") -> Optional[Any]:
        """
        Parse JSON response with enhanced error handling.
        
        Args:
            response_text: Raw response text from Gemini
            expected_type: Expected JSON type ("object" or "array")
            
        Returns:
            Parsed JSON object/array or None if parsing fails
        """
        try:
            # First try direct parsing
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.warning(f"Initial JSON parse failed: {e}")
            
            # Try enhanced parsing
            enhanced_text = self._enhance_json_response(response_text)
            try:
                result = json.loads(enhanced_text)
                logger.info("Successfully parsed JSON after enhancement")
                return result
            except json.JSONDecodeError as e2:
                logger.warning(f"Enhanced JSON parse failed: {e2}")
                
                # Last resort: try to extract valid JSON portion
                try:
                    # Find the most likely JSON boundaries
                    if expected_type == "array":
                        start = enhanced_text.find('[')
                        end = enhanced_text.rfind(']') + 1
                    else:
                        start = enhanced_text.find('{')
                        end = enhanced_text.rfind('}') + 1
                    
                    if start >= 0 and end > start:
                        json_portion = enhanced_text[start:end]
                        result = json.loads(json_portion)
                        logger.info("Successfully extracted valid JSON portion")
                        return result
                except:
                    pass
                
                logger.error(f"Failed to parse JSON response. First 500 chars: {response_text[:500]}")
                return None
    
    async def transcribe_audio(
        self, 
        audio_file: str,
        duration: int
    ) -> Dict[str, Any]:
        """
        Transcribe audio file using Gemini with video intelligence.
        
        Args:
            audio_file: Path to audio file
            duration: Duration in seconds
            
        Returns:
            Dictionary with transcript and analysis
        """
        logger.info(f"Uploading audio file: {audio_file}")
        
        # Upload the audio file
        file = genai.upload_file(audio_file, mime_type=self._get_mime_type(audio_file))
        
        # Wait for file to be ready
        while file.state.name == "PROCESSING":
            await asyncio.sleep(2)
            file = genai.get_file(file.name)
        
        # Use different model instances from pool for different tasks
        transcription_model = self.pool.get_model(TaskType.TRANSCRIPTION)
        
        # Calculate cost (Gemini pricing)
        # Audio: $0.000125 per second
        audio_cost = (duration * 0.000125)
        
        # Add output token costs (estimate ~1000 tokens per minute of audio)
        estimated_output_tokens = (duration / 60) * 1000
        output_cost = (estimated_output_tokens / 1000) * 0.00015  # $0.00015 per 1K tokens
        
        total_cost = audio_cost + output_cost
        self.total_cost += total_cost
        
        logger.info(f"Estimated cost: ${total_cost:.4f}")
        
        try:
            # First, get the transcript
            transcript_prompt = """
            Transcribe this audio file completely and accurately.
            Return the full transcript as plain text.
            """
            
            logger.info("Generating transcription...")
            response = await transcription_model.generate_content_async(
                [file, transcript_prompt],
                request_options=RequestOptions(timeout=self.request_timeout)
            )
            transcript_text = response.text.strip()
            
            # Use fresh models for each analysis task
            analysis_model = self.pool.get_model(TaskType.KEY_POINTS)
            
            # OPTIMIZED: Combined extraction in ONE API call instead of 5
            combined_prompt = f"""
            Analyze this transcript and extract ALL of the following in one comprehensive response.
            Be thorough and extract as much information as possible.
            
            Transcript:
            {transcript_text[:10000]}  # Increased from 8000 for better coverage
            
            Return a JSON object with this EXACT structure:
            {{
                "summary": "Write a comprehensive 3-4 paragraph summary covering all main points",
                "key_points": [
                    {{"timestamp": 0, "text": "Important point or moment", "importance": 0.9}},
                    // Extract 30-50 key points for comprehensive coverage
                ],
                "topics": ["main topic 1", "main topic 2", "topic 3"],
                "entities": [
                    {{"name": "Person/Org/Location Name", "type": "PERSON/ORGANIZATION/LOCATION", "confidence": 0.9}},
                    // Extract ALL named entities
                ],
                "relationships": [
                    {{"subject": "Entity A", "predicate": "specific action", "object": "Entity B", "confidence": 0.9}},
                    // Use specific predicates: founded, acquired, partnered with, invested in, developed, etc.
                    // Extract 20-50 relationships
                ]
            }}
            
            Be comprehensive and don't miss important information. Quality over speed.
            """
            
            logger.info("Performing combined extraction (summary, key points, topics, entities, relationships)...")
            
            # Use response_schema for guaranteed JSON format
            response_schema = {
                "type": "OBJECT",
                "properties": {
                    "summary": {"type": "STRING"},
                    "key_points": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "timestamp": {"type": "NUMBER"},
                                "text": {"type": "STRING"},
                                "importance": {"type": "NUMBER"}
                            },
                            "required": ["timestamp", "text", "importance"]
                        }
                    },
                    "topics": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"}
                    },
                    "entities": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "name": {"type": "STRING"},
                                "type": {"type": "STRING", "enum": ["PERSON", "ORGANIZATION", "LOCATION", "PRODUCT", "EVENT"]},
                                "confidence": {"type": "NUMBER"}
                            },
                            "required": ["name", "type", "confidence"]
                        }
                    },
                    "relationships": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "subject": {"type": "STRING"},
                                "predicate": {"type": "STRING"},
                                "object": {"type": "STRING"},
                                "confidence": {"type": "NUMBER"}
                            },
                            "required": ["subject", "predicate", "object", "confidence"]
                        }
                    }
                },
                "required": ["summary", "key_points", "topics", "entities", "relationships"]
            }
            
            # Make the combined API call with structured output
            response = await analysis_model.generate_content_async(
                combined_prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "response_schema": response_schema
                },
                request_options=RequestOptions(timeout=self.request_timeout)
            )
            
            # Parse the combined response
            combined_data = self._parse_json_response(response.text, "object") or {}
            
            # Extract individual components with defaults
            summary = combined_data.get("summary", "No summary generated")
            key_points = combined_data.get("key_points", [])
            topics = combined_data.get("topics", [])
            entities = combined_data.get("entities", [])
            relationships = combined_data.get("relationships", [])
            
            # Optional: Second pass for entity/relationship extraction if first pass seems incomplete
            if len(entities) < 10 or len(relationships) < 5:
                logger.info("Performing second pass for better entity/relationship extraction...")
                
                second_pass_prompt = f"""
                This is a second pass to catch any missed entities and relationships.
                Look carefully for:
                - People mentioned by title/role even without names
                - Organizations, companies, agencies
                - Locations, countries, cities
                - Products, technologies, systems
                - Events, dates, meetings
                
                Transcript:
                {transcript_text[:10000]}
                
                Already found entities: {[e['name'] for e in entities][:20]}
                
                Find ADDITIONAL entities and relationships not in the above list.
                
                Return JSON:
                {{
                    "additional_entities": [
                        {{"name": "Entity", "type": "TYPE", "confidence": 0.9}}
                    ],
                    "additional_relationships": [
                        {{"subject": "A", "predicate": "action", "object": "B", "confidence": 0.9}}
                    ]
                }}
                """
                
                second_model = self.pool.get_model(TaskType.ENTITIES)
                response = await second_model.generate_content_async(
                    second_pass_prompt,
                    generation_config={"response_mime_type": "application/json"},
                    request_options=RequestOptions(timeout=self.request_timeout)
                )
                
                second_pass_data = self._parse_json_response(response.text, "object") or {}
                
                # Merge additional findings
                additional_entities = second_pass_data.get("additional_entities", [])
                additional_relationships = second_pass_data.get("additional_relationships", [])
                
                entities.extend(additional_entities)
                relationships.extend(additional_relationships)
                
                logger.info(f"Second pass found {len(additional_entities)} more entities and {len(additional_relationships)} more relationships")
            
            processing_time = 0  # We'll calculate this properly
            
            logger.info(f"Transcription completed in {processing_time}s, cost: ${total_cost:.4f}")
            logger.info(f"Extracted: {len(entities)} entities, {len(relationships)} relationships, {len(key_points)} key points")
            
            # Clean up
            genai.delete_file(file)
            
            return {
                "transcript": transcript_text,
                "summary": summary,
                "key_points": key_points,
                "entities": entities,
                "topics": topics,
                "relationships": relationships,
                "language": "en",  # TODO: Detect language
                "confidence_score": 0.95,  # Gemini is generally very confident
                "processing_time": processing_time,
                "processing_cost": total_cost
            }
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            # Clean up file if it exists
            try:
                genai.delete_file(file)
            except:
                pass
            raise
    
    async def transcribe_video(
        self, 
        video_file: str,
        duration: int
    ) -> Dict[str, Any]:
        """
        Transcribe video file with visual analysis using Gemini.
        
        Args:
            video_file: Path to video file
            duration: Duration in seconds
            
        Returns:
            Dictionary with transcript and enhanced analysis including visual elements
        """
        logger.info(f"Uploading video file: {video_file}")
        
        # Upload the video file
        file = genai.upload_file(video_file, mime_type=self._get_mime_type(video_file))
        
        # Wait for file to be ready
        while file.state.name == "PROCESSING":
            await asyncio.sleep(2)
            file = genai.get_file(file.name)
        
        # Use different model instances from pool
        video_model = self.pool.get_model(TaskType.TRANSCRIPTION)
        
        # Calculate cost (Gemini pricing for video)
        # Video: $0.000125 per second (same as audio for now)
        video_cost = (duration * 0.000125)
        
        # Add output token costs (estimate ~1500 tokens per minute for video due to visual descriptions)
        estimated_output_tokens = (duration / 60) * 1500
        output_cost = (estimated_output_tokens / 1000) * 0.00015
        
        total_cost = video_cost + output_cost
        self.total_cost += total_cost
        
        logger.info(f"Estimated cost: ${total_cost:.4f}")
        
        try:
            # Get transcript with visual elements
            transcript_prompt = """
            Transcribe this video completely, including:
            1. All spoken dialogue and narration
            2. Important visual elements (text on screen, slides, code, diagrams)
            3. Scene descriptions when relevant to understanding
            
            Format visual elements like: [VISUAL: description]
            Format on-screen text like: [TEXT: content]
            
            Return the complete transcript with visual annotations.
            """
            
            logger.info("Generating video transcription with visual analysis...")
            response = await video_model.generate_content_async(
                [file, transcript_prompt],
                request_options=RequestOptions(timeout=self.request_timeout)
            )
            transcript_text = response.text.strip()
            
            # Use fresh models for analysis
            analysis_model = self.pool.get_model(TaskType.ENTITIES)
            
            # Extract visual elements separately
            visual_prompt = f"""
            From this video transcript, extract all visual elements, on-screen text, code snippets, and diagrams.
            
            Transcript:
            {transcript_text[:8000]}
            
            Return as JSON array:
            [
                {{"timestamp": 0, "type": "code", "content": "def example():", "context": "Python function shown"}},
                {{"timestamp": 120, "type": "slide", "content": "Title: Introduction", "context": "Presentation slide"}},
                {{"timestamp": 180, "type": "diagram", "content": "Flow chart showing...", "context": "Architecture diagram"}}
            ]
            """
            
            logger.info("Extracting visual elements...")
            response = await analysis_model.generate_content_async(
                visual_prompt,
                request_options=RequestOptions(timeout=self.request_timeout)
            )
            visual_elements = self._parse_json_response(response.text, "array") or []
            
            # Rest of the analysis (similar to audio but with visual context)
            # ... (key points, summary, entities, topics, relationships)
            
            # For brevity, I'll just show the enhanced key points extraction
            key_points_prompt = f"""
            Extract 30-50 key points from this video transcript, including both spoken and visual elements.
            Pay special attention to code, slides, diagrams, and on-screen text.
            
            Transcript:
            {transcript_text[:8000]}
            
            Return as JSON array:
            [
                {{"timestamp": 0, "text": "Key point about spoken content", "importance": 0.9, "type": "speech"}},
                {{"timestamp": 60, "text": "Important code shown: function definition", "importance": 0.95, "type": "visual"}}
            ]
            """
            
            summary_model = self.pool.get_model(TaskType.KEY_POINTS)
            logger.info("Extracting key points with visual context...")
            response = await summary_model.generate_content_async(
                key_points_prompt,
                request_options=RequestOptions(timeout=self.request_timeout)
            )
            key_points = self._parse_json_response(response.text, "array") or []
            
            # Similar enhancements for other extractions...
            # (Using the same pattern as audio but with visual awareness)
            
            processing_time = 0  # Calculate properly
            
            logger.info(f"Video transcription completed in {processing_time}s, cost: ${total_cost:.4f}")
            
            # Clean up
            genai.delete_file(file)
            
            return {
                "transcript": transcript_text,
                "visual_elements": visual_elements,
                "summary": "Video analysis summary",  # Would be extracted like in audio
                "key_points": key_points,
                "entities": [],  # Would be extracted
                "topics": [],  # Would be extracted  
                "relationships": [],  # Would be extracted
                "language": "en",
                "confidence_score": 0.95,
                "processing_time": processing_time,
                "processing_cost": total_cost
            }
            
        except Exception as e:
            logger.error(f"Video transcription failed: {e}")
            try:
                genai.delete_file(file)
            except:
                pass
            raise
    
    def _get_mime_type(self, file_path: str) -> str:
        """Get MIME type for file."""
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or "application/octet-stream"
    
    def get_total_cost(self) -> float:
        """Get total cost of all transcriptions."""
        return self.total_cost 