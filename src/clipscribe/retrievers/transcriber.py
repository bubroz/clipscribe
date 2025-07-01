"""Gemini Flash Transcriber with Enhanced Temporal Intelligence."""

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

from ..models import VideoTranscript, KeyPoint, Entity, Topic, TimelineEvent
from ..config.settings import Settings, TemporalIntelligenceLevel
from .gemini_pool import GeminiPool, TaskType

logger = logging.getLogger(__name__)


class GeminiFlashTranscriber:
    """Transcribe video/audio using Gemini models with enhanced temporal intelligence capabilities."""
    
    def __init__(self, api_key: Optional[str] = None, performance_monitor: Optional[Any] = None):
        """
        Initialize transcriber with API key and enhanced temporal intelligence.
        
        Args:
            api_key: Google API key (optional, uses env var if not provided)
            performance_monitor: Performance monitoring instance
        """
        # Get settings
        self.settings = Settings()
        self.api_key = api_key or self.settings.google_api_key
        if not self.api_key:
            raise ValueError("Google API key is required")
        
        genai.configure(api_key=self.api_key)
        
        # Initialize GeminiPool instead of single client
        self.pool = GeminiPool(api_key=self.api_key)
        self.performance_monitor = performance_monitor
        
        # Get temporal intelligence configuration
        self.temporal_config = self.settings.get_temporal_intelligence_config()
        logger.info(f"Temporal intelligence level: {self.temporal_config['level']}")
        
        # Get timeout setting
        self.request_timeout = self.settings.gemini_request_timeout
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
        Transcribe audio file using Gemini with enhanced temporal intelligence.
        
        Args:
            audio_file: Path to audio file
            duration: Duration in seconds
            
        Returns:
            Dictionary with transcript and temporal intelligence analysis
        """
        logger.info(f"Uploading audio file: {audio_file}")
        logger.info(f"Temporal intelligence level: {self.temporal_config['level']}")
        
        # Upload the audio file
        file = genai.upload_file(audio_file, mime_type=self._get_mime_type(audio_file))
        
        # Wait for file to be ready
        while file.state.name == "PROCESSING":
            await asyncio.sleep(2)
            file = genai.get_file(file.name)
        
        # Use different model instances from pool for different tasks
        transcription_model = self.pool.get_model(TaskType.TRANSCRIPTION)
        
        # Calculate cost based on temporal intelligence level
        total_cost = self.settings.estimate_cost(duration, self.temporal_config['level'])
        self.total_cost += total_cost
        
        logger.info(f"Estimated cost with {self.temporal_config['level']} temporal intelligence: ${total_cost:.4f}")
        
        try:
            # First, get the transcript
            transcript_prompt = """
            Transcribe this audio file completely and accurately.
            Return the full transcript as plain text.
            """
            
            logger.info("Generating transcription...")
            
            # Performance monitoring
            transcription_event = None
            if self.performance_monitor:
                transcription_event = self.performance_monitor.start_timer(
                    "gemini_transcription",
                    model=transcription_model.model_name
                )

            response = await transcription_model.generate_content_async(
                [file, transcript_prompt],
                request_options=RequestOptions(timeout=self.request_timeout)
            )

            if self.performance_monitor:
                self.performance_monitor.stop_timer(transcription_event)

            transcript_text = response.text.strip()
            
            # Enhanced temporal intelligence extraction
            temporal_intelligence = await self._extract_temporal_intelligence(
                transcript_text, duration, is_video=False
            )
            
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
            analysis_event = None
            if self.performance_monitor:
                analysis_event = self.performance_monitor.start_timer(
                    "gemini_combined_analysis",
                    model=analysis_model.model_name
                )

            response = await analysis_model.generate_content_async(
                combined_prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "response_schema": response_schema
                },
                request_options=RequestOptions(timeout=self.request_timeout)
            )

            if self.performance_monitor:
                self.performance_monitor.stop_timer(analysis_event)
            
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
                
                second_pass_event = None
                if self.performance_monitor:
                    second_pass_event = self.performance_monitor.start_timer(
                        "gemini_second_pass_analysis",
                        model=second_model.model_name
                    )

                response = await second_model.generate_content_async(
                    second_pass_prompt,
                    generation_config={"response_mime_type": "application/json"},
                    request_options=RequestOptions(timeout=self.request_timeout)
                )

                if self.performance_monitor:
                    self.performance_monitor.stop_timer(second_pass_event)
                
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
            logger.info(f"Temporal intelligence: {len(temporal_intelligence.get('timeline_events', []))} timeline events")
            
            # Clean up
            genai.delete_file(file)
            
            # Merge temporal intelligence with results
            result = {
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
            
            # Add temporal intelligence data
            result.update(temporal_intelligence)
            
            return result
            
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
        Transcribe video file with enhanced temporal intelligence and visual analysis.
        
        Args:
            video_file: Path to video file
            duration: Duration in seconds
            
        Returns:
            Dictionary with transcript and enhanced analysis including visual temporal elements
        """
        logger.info(f"Uploading video file: {video_file}")
        logger.info(f"Enhanced temporal intelligence level: {self.temporal_config['level']}")
        
        # Upload the video file
        file = genai.upload_file(video_file, mime_type=self._get_mime_type(video_file))
        
        # Wait for file to be ready
        while file.state.name == "PROCESSING":
            await asyncio.sleep(2)
            file = genai.get_file(file.name)
        
        # Use different model instances from pool
        video_model = self.pool.get_model(TaskType.TRANSCRIPTION)
        
        # Calculate cost with enhanced temporal intelligence multiplier
        total_cost = self.settings.estimate_cost(duration, self.temporal_config['level'])
        self.total_cost += total_cost
        
        logger.info(f"Estimated cost with enhanced temporal intelligence: ${total_cost:.4f}")
        
        try:
            # Enhanced prompt for temporal intelligence with visual cues
            transcript_prompt = self._build_enhanced_transcript_prompt()
            
            logger.info("Generating video transcription with enhanced temporal intelligence...")
            
            # Performance monitoring
            video_transcription_event = None
            if self.performance_monitor:
                video_transcription_event = self.performance_monitor.start_timer(
                    "gemini_enhanced_video_transcription",
                    model=video_model.model_name
                )

            response = await video_model.generate_content_async(
                [file, transcript_prompt],
                request_options=RequestOptions(timeout=self.request_timeout)
            )

            if self.performance_monitor:
                self.performance_monitor.stop_timer(video_transcription_event)

            transcript_text = response.text.strip()
            
            # Extract enhanced temporal intelligence with visual cues
            temporal_intelligence = await self._extract_temporal_intelligence(
                transcript_text, duration, is_video=True, video_file=file
            )
            
            # Use fresh models for analysis
            analysis_model = self.pool.get_model(TaskType.ENTITIES)
            
            # Enhanced analysis with visual temporal elements
            combined_prompt = self._build_enhanced_analysis_prompt(transcript_text)
            
            # Extended response schema for enhanced temporal intelligence
            response_schema = self._build_enhanced_response_schema()
            
            logger.info("Performing enhanced combined extraction with visual temporal intelligence...")
            
            # Make the enhanced API call
            analysis_event = None
            if self.performance_monitor:
                analysis_event = self.performance_monitor.start_timer(
                    "gemini_enhanced_analysis",
                    model=analysis_model.model_name
                )

            response = await analysis_model.generate_content_async(
                combined_prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "response_schema": response_schema
                },
                request_options=RequestOptions(timeout=self.request_timeout)
            )

            if self.performance_monitor:
                self.performance_monitor.stop_timer(analysis_event)
            
            # Parse the enhanced response
            combined_data = self._parse_json_response(response.text, "object") or {}
            
            # Extract components
            summary = combined_data.get("summary", "No summary generated")
            key_points = combined_data.get("key_points", [])
            topics = combined_data.get("topics", [])
            entities = combined_data.get("entities", [])
            relationships = combined_data.get("relationships", [])
            
            processing_time = 0
            
            logger.info(f"Enhanced video transcription completed in {processing_time}s, cost: ${total_cost:.4f}")
            logger.info(f"Extracted: {len(entities)} entities, {len(relationships)} relationships, {len(key_points)} key points")
            logger.info(f"Enhanced temporal intelligence: {len(temporal_intelligence.get('timeline_events', []))} timeline events")
            logger.info(f"Visual temporal cues: {len(temporal_intelligence.get('visual_temporal_cues', []))} cues")
            
            # Clean up
            genai.delete_file(file)
            
            # Merge enhanced results
            result = {
                "transcript": transcript_text,
                "summary": summary,
                "key_points": key_points,
                "entities": entities,
                "topics": topics,
                "relationships": relationships,
                "language": "en",
                "confidence_score": 0.95,
                "processing_time": processing_time,
                "processing_cost": total_cost
            }
            
            # Add enhanced temporal intelligence data
            result.update(temporal_intelligence)
            
            return result
            
        except Exception as e:
            logger.error(f"Enhanced video transcription failed: {e}")
            try:
                genai.delete_file(file)
            except:
                pass
            raise

    async def _extract_temporal_intelligence(
        self, 
        transcript_text: str, 
        duration: int, 
        is_video: bool = False,
        video_file: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Extract enhanced temporal intelligence from content."""
        logger.info("Extracting enhanced temporal intelligence...")
        
        # Skip if temporal intelligence is disabled
        if self.temporal_config['level'] == TemporalIntelligenceLevel.STANDARD:
            return {"timeline_events": [], "visual_temporal_cues": [], "temporal_patterns": []}
        
        temporal_model = self.pool.get_model(TaskType.TEMPORAL_INTELLIGENCE)
        
        # Build temporal intelligence prompt based on configuration
        temporal_prompt = self._build_temporal_intelligence_prompt(
            transcript_text, is_video, duration
        )
        
        # Define temporal intelligence schema
        temporal_schema = {
            "type": "OBJECT",
            "properties": {
                "timeline_events": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "timestamp": {"type": "NUMBER"},
                            "event_description": {"type": "STRING"},
                            "event_type": {"type": "STRING"},
                            "confidence": {"type": "NUMBER"},
                            "involved_entities": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"}
                            }
                        },
                        "required": ["timestamp", "event_description", "event_type", "confidence"]
                    }
                },
                "visual_temporal_cues": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "timestamp": {"type": "NUMBER"},
                            "cue_type": {"type": "STRING"},
                            "description": {"type": "STRING"},
                            "temporal_significance": {"type": "STRING"}
                        },
                        "required": ["timestamp", "cue_type", "description"]
                    }
                },
                "temporal_patterns": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "pattern_type": {"type": "STRING"},
                            "description": {"type": "STRING"},
                            "timespan": {"type": "STRING"},
                            "significance": {"type": "STRING"}
                        }
                    }
                }
            },
            "required": ["timeline_events", "visual_temporal_cues", "temporal_patterns"]
        }
        
        temporal_event = None
        if self.performance_monitor:
            temporal_event = self.performance_monitor.start_timer(
                "gemini_temporal_intelligence",
                model=temporal_model.model_name
            )

        # Make the temporal intelligence call
        if is_video and video_file and self.temporal_config['extract_visual_cues']:
            # Video mode with visual cues
            response = await temporal_model.generate_content_async(
                [video_file, temporal_prompt],
                generation_config={
                    "response_mime_type": "application/json",
                    "response_schema": temporal_schema
                },
                request_options=RequestOptions(timeout=self.request_timeout)
            )
        else:
            # Audio mode or visual cues disabled
            response = await temporal_model.generate_content_async(
                temporal_prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "response_schema": temporal_schema
                },
                request_options=RequestOptions(timeout=self.request_timeout)
            )

        if self.performance_monitor:
            self.performance_monitor.stop_timer(temporal_event)
        
        temporal_data = self._parse_json_response(response.text, "object") or {}
        
        return {
            "timeline_events": temporal_data.get("timeline_events", []),
            "visual_temporal_cues": temporal_data.get("visual_temporal_cues", []),
            "temporal_patterns": temporal_data.get("temporal_patterns", [])
        }

    def _build_enhanced_transcript_prompt(self) -> str:
        """Build enhanced transcript prompt for temporal intelligence."""
        return """
        Transcribe this video with enhanced temporal intelligence extraction:
        
        1. COMPLETE TRANSCRIPTION: All spoken dialogue and narration
        2. VISUAL TEMPORAL CUES: Extract temporal information from visual elements:
           - Timelines, charts, graphs with temporal data
           - Dates, years, time periods shown on screen
           - Chronological sequences in slides or presentations
           - Progress indicators, calendars, schedules
        3. TEMPORAL CONTEXT: Note temporal relationships and sequences
        4. VISUAL ANNOTATIONS: Format visual elements as [VISUAL: description]
        
        Focus on extracting 300% more temporal intelligence through combined audio-visual analysis.
        """

    def _build_enhanced_analysis_prompt(self, transcript_text: str) -> str:
        """Build enhanced analysis prompt with temporal intelligence."""
        return f"""
        Analyze this transcript with enhanced temporal intelligence extraction.
        Extract comprehensive information including temporal patterns and relationships.
        
        Transcript with Visual Annotations:
        {transcript_text[:12000]}  # Increased for visual content
        
        Return a JSON object with this EXACT structure:
        {{
            "summary": "Comprehensive 3-4 paragraph summary including temporal context",
            "key_points": [
                {{"timestamp": 0, "text": "Important point with temporal context", "importance": 0.9}},
                // Extract 40-60 key points including temporal significance
            ],
            "topics": ["main topic 1", "temporal theme", "chronological topic"],
            "entities": [
                {{"name": "Entity Name", "type": "PERSON/ORGANIZATION/LOCATION/EVENT", "confidence": 0.9}},
                // Include temporal entities (events, dates, periods)
            ],
            "relationships": [
                {{"subject": "Entity A", "predicate": "temporal_action", "object": "Entity B", "confidence": 0.9}},
                // Include temporal relationships: before, after, during, caused, led_to
            ]
        }}
        
        Focus on temporal intelligence: sequences, causality, chronology, evolution.
        """

    def _build_enhanced_response_schema(self) -> Dict[str, Any]:
        """Build enhanced response schema for temporal intelligence."""
        return {
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
                            "importance": {"type": "NUMBER"},
                            "temporal_significance": {"type": "STRING"}
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
                            "type": {"type": "STRING", "enum": ["PERSON", "ORGANIZATION", "LOCATION", "PRODUCT", "EVENT", "DATE", "PERIOD"]},
                            "confidence": {"type": "NUMBER"},
                            "temporal_context": {"type": "STRING"}
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
                            "confidence": {"type": "NUMBER"},
                            "temporal_nature": {"type": "STRING"}
                        },
                        "required": ["subject", "predicate", "object", "confidence"]
                    }
                }
            },
            "required": ["summary", "key_points", "topics", "entities", "relationships"]
        }

    def _build_temporal_intelligence_prompt(
        self, 
        transcript_text: str, 
        is_video: bool, 
        duration: int
    ) -> str:
        """Build temporal intelligence extraction prompt."""
        base_prompt = f"""
        Extract enhanced temporal intelligence from this content.
        
        Content Type: {"Video with visual cues" if is_video else "Audio only"}
        Duration: {duration} seconds
        
        Extract:
        1. TIMELINE EVENTS: Specific events with timestamps and temporal context
        2. VISUAL TEMPORAL CUES: {"Charts, timelines, dates shown visually" if is_video else "Not applicable"}
        3. TEMPORAL PATTERNS: Sequences, cycles, progressions, causality chains
        
        Content:
        {transcript_text[:8000]}
        
        Focus on extracting temporal relationships, chronological sequences, and time-based patterns.
        Include confidence scores based on clarity and specificity of temporal information.
        """
        
        if is_video and self.temporal_config['extract_visual_cues']:
            base_prompt += """
            
            ENHANCED VISUAL ANALYSIS:
            - Extract dates, years, timelines from visual elements
            - Identify temporal charts, graphs, calendars
            - Note chronological sequences in presentations
            - Capture time-based progressions and evolution
            """
        
        return base_prompt
    
    def _get_mime_type(self, file_path: str) -> str:
        """Get MIME type for file."""
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or 'application/octet-stream'
    
    def get_total_cost(self) -> float:
        """Get total cost of all operations."""
        return self.total_cost 