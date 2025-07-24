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

from ..config.settings import Settings, TemporalIntelligenceLevel
from .gemini_pool import GeminiPool, TaskType
from .vertex_ai_transcriber import VertexAITranscriber

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
        # Force Vertex AI off for reliability (prevents 400 errors)
        self.use_vertex_ai = False  # Disabled for production reliability
        self.pool = GeminiPool(api_key=self.api_key) # ALWAYS initialize the pool
        
        # Initialize appropriate backend
        if self.use_vertex_ai:
            logger.info("Using Vertex AI for video processing")
            # Lazy import to avoid dependency if not using Vertex AI
            self.vertex_transcriber = VertexAITranscriber()
        else:
            if not self.api_key:
                raise ValueError("Google API key is required")
            
            genai.configure(api_key=self.api_key)
            
            # Initialize GeminiPool instead of single client
            # self.pool = GeminiPool(api_key=self.api_key) # This line is now redundant as pool is initialized above
            self.vertex_transcriber = None
            
        self.performance_monitor = performance_monitor
        
        # Get temporal intelligence configuration
        self.temporal_config = self.settings.get_temporal_intelligence_config()
        logger.info(f"Temporal intelligence level: {self.temporal_config['level']}")
        
        # Get timeout setting
        self.request_timeout = 600
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

    async def transcribe_audio(self, audio_file: str, duration: int) -> Dict[str, Any]:
        """Transcribe audio file with enhanced temporal intelligence.
        
        Args:
            audio_file: Path to the audio file
            duration: Duration in seconds
            
        Returns:
            Dictionary with transcript and enhanced analysis
        """
        # Use Vertex AI if configured
        if self.use_vertex_ai and self.vertex_transcriber:
            logger.info(f"Attempting to transcribe audio with Vertex AI: {audio_file}")
            try:
                result = await self.vertex_transcriber.transcribe_with_vertex(
                    Path(audio_file),
                    enhance_transcript=self.temporal_config['level'] != TemporalIntelligenceLevel.STANDARD,
                    mode="audio"
                )
                # Convert to expected format
                return self._convert_vertex_result_to_dict(result)
            except Exception as e:
                logger.warning(f"Vertex AI transcription failed: {e}. Falling back to standard Gemini API.")
                # Fallback to standard Gemini API below
        
        logger.info(f"Using standard Gemini API to transcribe audio: {audio_file}")
        logger.info(f"Enhanced temporal intelligence level: {self.temporal_config['level']}")
        
        # Upload the audio file
        file = genai.upload_file(audio_file, mime_type=self._get_mime_type(audio_file))
        
        # Wait for file to be ready
        while file.state.name == "PROCESSING":
            await asyncio.sleep(2)
            file = genai.get_file(file.name)
        
        # Get the transcription model
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

            response = await self._retry_generate_content(
                transcription_model,
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
            Analyze this transcript and extract COMPREHENSIVE intelligence. You are an expert analyst extracting actionable intelligence from video content.
            
            CRITICAL REQUIREMENTS:
            - Extract ALL meaningful entities and relationships comprehensively
            - Extract ALL meaningful entities (aim for 50+)
            - Extract ALL meaningful relationships (aim for 50+)  
            - Include ALL people, organizations, locations, events, technologies, products, concepts
            - Use SPECIFIC predicates for relationships (not generic "related to")
            - Calculate REALISTIC confidence scores (0.3-0.99, vary based on context clarity)
            
            Transcript:
            {transcript_text[:12000]}  # Increased for better coverage
            
            Return a JSON object with this EXACT structure:
            {{
                "summary": "Write a comprehensive 3-4 paragraph executive summary covering all main points, key players, and critical insights",
                "key_points": [
                    {{"timestamp": 0, "text": "Specific, actionable insight or key moment", "importance": 0.9}},
                    // Extract 30-50 key points - every significant statement, fact, or claim
                ],
                "topics": ["primary topic", "secondary topic", "tertiary topic", "domain area", "theme"],
                "entities": [
                    // PEOPLE: Extract ALL names, titles, roles
                    {{"name": "Donald Trump", "type": "PERSON", "confidence": 0.95}},
                    {{"name": "President Biden", "type": "PERSON", "confidence": 0.93}},
                    {{"name": "The CEO", "type": "PERSON", "confidence": 0.7}},  // Even unnamed roles
                    
                    // ORGANIZATIONS: Companies, agencies, groups, institutions
                    {{"name": "Department of Justice", "type": "ORGANIZATION", "confidence": 0.9}},
                    {{"name": "Wall Street Journal", "type": "ORGANIZATION", "confidence": 0.95}},  // NOT location!
                    {{"name": "Republican Party", "type": "ORGANIZATION", "confidence": 0.92}},
                    
                    // LOCATIONS: Countries, cities, regions, venues
                    {{"name": "United States", "type": "LOCATION", "confidence": 0.98}},
                    {{"name": "Ukraine", "type": "LOCATION", "confidence": 0.95}},
                    {{"name": "Washington DC", "type": "LOCATION", "confidence": 0.9}},
                    
                    // EVENTS: Meetings, incidents, occurrences
                    {{"name": "2024 Presidential Election", "type": "EVENT", "confidence": 0.93}},
                    {{"name": "January 6 Capitol Attack", "type": "EVENT", "confidence": 0.96}},
                    
                    // PRODUCTS/TECH: Software, systems, technologies
                    {{"name": "Pegasus spyware", "type": "PRODUCT", "confidence": 0.91}},
                    {{"name": "ChatGPT", "type": "PRODUCT", "confidence": 0.94}},
                    
                    // Extract EVERYTHING - err on the side of too much rather than too little
                ],
                "relationships": [
                    // Use SPECIFIC, MEANINGFUL predicates
                    {{"subject": "Donald Trump", "predicate": "indicted_by", "object": "Department of Justice", "confidence": 0.92}},
                    {{"subject": "Russia", "predicate": "invaded", "object": "Ukraine", "confidence": 0.98}},
                    {{"subject": "Elon Musk", "predicate": "acquired", "object": "Twitter", "confidence": 0.97}},
                    {{"subject": "Federal Reserve", "predicate": "raised_interest_rates_to", "object": "5.5%", "confidence": 0.89}},
                    {{"subject": "China", "predicate": "banned_export_of", "object": "rare earth minerals", "confidence": 0.85}},
                    {{"subject": "OpenAI", "predicate": "developed", "object": "GPT-4", "confidence": 0.96}},
                    {{"subject": "Congress", "predicate": "passed", "object": "Infrastructure Bill", "confidence": 0.91}},
                    {{"subject": "Apple", "predicate": "announced", "object": "Vision Pro", "confidence": 0.94}},
                    
                    // Include causal relationships, temporal sequences, hierarchies
                    {{"subject": "Inflation", "predicate": "caused_by", "object": "supply chain disruption", "confidence": 0.78}},
                    {{"subject": "Bank failures", "predicate": "triggered", "object": "regulatory response", "confidence": 0.83}},
                    
                    // Extract EVERY meaningful connection between entities
                ],
                "dates": [
                    {{"original_text": "October 2018", "normalized_date": "2018-10-01", "precision": "month", "confidence": 0.95, "source": "transcript", "context": "when Pegasus was discovered", "timestamp": 120.5}},
                    {{"original_text": "last Tuesday", "normalized_date": "2025-07-15", "precision": "day", "confidence": 0.8, "source": "transcript", "context": "meeting date", "timestamp": 45.2}},
                    {{"original_text": "three years ago", "normalized_date": "2022-07-01", "precision": "month", "confidence": 0.7, "source": "transcript", "context": "project start", "timestamp": 200.1}},
                    // Extract ALL temporal references and calculate actual dates
                ]
            }}
            
            EXTRACTION RULES:
            1. Entity confidence: 0.95+ for explicitly named, 0.8-0.94 for clearly referenced, 0.6-0.79 for inferred, <0.6 for uncertain
            2. Relationship predicates must be SPECIFIC ACTIONS/STATES not generic terms
            3. Include entities mentioned only once - they might be crucial
            4. Extract implied relationships from context
            5. For unnamed entities (e.g., "the CEO"), still extract with lower confidence
            6. Every fact should generate at least one relationship
            7. Quality over quantity, but aim for COMPREHENSIVE extraction
            
            BE AGGRESSIVE - I need rich, detailed intelligence extraction. Missing information is worse than including uncertain information with low confidence.
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
                    },
                    "dates": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "original_text": {"type": "STRING"},
                                "normalized_date": {"type": "STRING"},
                                "precision": {"type": "STRING", "enum": ["exact", "day", "month", "year", "approximate"]},
                                "confidence": {"type": "NUMBER"},
                                "context": {"type": "STRING"},
                                "source": {"type": "STRING", "enum": ["transcript", "visual", "both"]},
                                "visual_description": {"type": "STRING"},
                                "timestamp": {"type": "NUMBER"}
                            },
                            "required": ["original_text", "normalized_date", "precision", "confidence", "source"]
                        }
                    }
                },
                "required": ["summary", "key_points", "topics", "entities", "relationships", "dates"]
            }
            
            # Make the combined API call with structured output
            analysis_event = None
            if self.performance_monitor:
                analysis_event = self.performance_monitor.start_timer(
                    "gemini_combined_analysis",
                    model=analysis_model.model_name
                )

            response = await self._retry_generate_content(
                analysis_model,
                combined_prompt,
                generation_config={"response_mime_type": "application/json", "response_schema": response_schema},
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
            dates = combined_data.get("dates", [])
            
            # Optional: Second pass for entity/relationship extraction if first pass seems incomplete
            if len(entities) < 15 or len(relationships) < 10:  # More realistic thresholds
                logger.info("Performing second pass for enhanced entity/relationship extraction...")
                
                second_pass_prompt = f"""
                SECOND PASS - Extract additional meaningful entities and relationships.
                
                You are an expert intelligence analyst. The first pass found {len(entities)} entities and {len(relationships)} relationships.
                
                Extract ALL additional meaningful entities and relationships comprehensively.
                
                Look for:
                - PEOPLE: Every person mentioned by name, title, role, or reference
                  * Government officials, business leaders, experts, sources
                  * "The spokesperson", "a senior official", "analysts" - extract these too
                - ORGANIZATIONS: Every company, agency, group, institution
                  * Government bodies, companies, NGOs, trade groups, media outlets
                  * Departments, divisions, committees, teams
                - LOCATIONS: Every geographic reference
                  * Countries, states, cities, regions, buildings, venues
                  * "The Middle East", "Silicon Valley", "Wall Street" - these count
                - EVENTS: Every incident, meeting, occurrence
                  * Elections, attacks, announcements, releases, crises
                  * "The 2008 financial crisis", "last week's summit"
                - CONCEPTS/PRODUCTS: Technologies, systems, policies, laws
                  * Software, hardware, financial instruments, regulations
                  * Abstract concepts if they're central to the discussion
                
                Transcript:
                {transcript_text[:12000]}
                
                Already found entities: {[e['name'] for e in entities][:30]}
                
                Find ALL ADDITIONAL entities and relationships not in the above list.
                
                Return JSON:
                {{
                    "additional_entities": [
                        {{"name": "Entity Name", "type": "PERSON/ORGANIZATION/LOCATION/EVENT/PRODUCT", "confidence": 0.85}},
                        // Find ALL additional meaningful entities
                    ],
                    "additional_relationships": [
                        {{"subject": "Entity A", "predicate": "specific_action_verb", "object": "Entity B", "confidence": 0.85}},
                        // Find ALL additional meaningful relationships
                        // Examples of good predicates:
                        // - announced, acquired, partnered_with, invested_in, sued, regulated
                        // - increased_by, decreased_to, exceeded, fell_below
                        // - caused, triggered, prevented, enabled, blocked
                        // - located_in, headquartered_in, operates_in, expanded_to
                        // - competed_with, allied_with, opposed, supported
                    ]
                }}
                
                BE EXHAUSTIVE - Every sentence likely contains multiple entities and at least one relationship.
                """
                
                second_model = self.pool.get_model(TaskType.ENTITIES)
                
                second_pass_event = None
                if self.performance_monitor:
                    second_pass_event = self.performance_monitor.start_timer(
                        "gemini_second_pass_analysis",
                        model=second_model.model_name
                    )

                response = await self._retry_generate_content(
                    second_model,
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
            logger.info(f"Extracted dates: {len(dates)} dates from content")
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
                "dates": dates,
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
        """Transcribe video file with full temporal and visual analysis.
        
        Args:
            video_file: Path to the video file
            duration: Duration in seconds
            
        Returns:
            Dictionary with transcript and comprehensive intelligence
        """
        # Use Vertex AI if configured
        if self.use_vertex_ai and self.vertex_transcriber:
            logger.info(f"Attempting to transcribe video with Vertex AI: {video_file}")
            try:
                result = await self.vertex_transcriber.transcribe_with_vertex(
                    Path(video_file),
                    enhance_transcript=self.temporal_config['level'] != TemporalIntelligenceLevel.STANDARD,
                    mode="video"
                )
                # Convert to expected format
                return self._convert_vertex_result_to_dict(result)
            except Exception as e:
                logger.warning(f"Vertex AI transcription failed: {e}. Falling back to standard Gemini API.")
                # Fallback to standard Gemini API below

        logger.info(f"Using standard Gemini API to transcribe video: {video_file}")
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

            response = await self._retry_generate_content(
                video_model,
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

            response = await self._retry_generate_content(
                analysis_model,
                combined_prompt,
                generation_config={"response_mime_type": "application/json", "response_schema": response_schema},
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
            dates = combined_data.get("dates", [])
            
            processing_time = 0
            
            logger.info(f"Enhanced video transcription completed in {processing_time}s, cost: ${total_cost:.4f}")
            logger.info(f"Extracted: {len(entities)} entities, {len(relationships)} relationships, {len(key_points)} key points")
            logger.info(f"Extracted dates: {len(dates)} dates (transcript + visual)")
            logger.info(f"Enhanced temporal intelligence: {len(temporal_intelligence.get('timeline_events', []))} timeline events")
            logger.info(f"Visual temporal cues: {len(temporal_intelligence.get('visual_temporal_cues', []))} cues")
            logger.info(f"Visual dates: {len(temporal_intelligence.get('visual_dates', []))} visual dates")
            
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
                "dates": dates,
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
                "visual_dates": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "timestamp": {"type": "NUMBER"},
                            "date_text": {"type": "STRING"},
                            "normalized_date": {"type": "STRING"},
                            "screen_location": {"type": "STRING"},
                            "confidence": {"type": "NUMBER"}
                        },
                        "required": ["timestamp", "date_text", "confidence"]
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
            "required": ["timeline_events", "visual_temporal_cues", "visual_dates", "temporal_patterns"]
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
            response = await self._retry_generate_content(
                temporal_model,
                [video_file, temporal_prompt],
                generation_config={
                    "response_mime_type": "application/json",
                    "response_schema": temporal_schema
                },
                request_options=RequestOptions(timeout=self.request_timeout)
            )
        else:
            # Audio mode or visual cues disabled
            response = await self._retry_generate_content(
                temporal_model,
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
            "visual_dates": temporal_data.get("visual_dates", []),
            "temporal_patterns": temporal_data.get("temporal_patterns", [])
        }

    async def _retry_generate_content(self, model, contents, generation_config=None, request_options=None, retries=3, initial_delay=5):
        delay = initial_delay
        for attempt in range(retries):
            try:
                return await model.generate_content_async(
                    contents,
                    generation_config=generation_config,
                    request_options=request_options
                )
            except Exception as e:
                if "503" in str(e) and attempt < retries - 1:
                    logger.warning(f"Transient error (503): Retrying in {delay}s (attempt {attempt+1}/{retries})")
                    await asyncio.sleep(delay)
                    delay *= 2
                    continue
                raise e

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
        3. VISUAL DATE EXTRACTION: Capture ALL dates shown visually:
           - News chyrons/lower thirds: [VISUAL DATE: October 2018 - lower third]
           - Document dates: [VISUAL DATE: Letter dated June 15, 2023]
           - Timeline graphics: [VISUAL DATE: Timeline shows 2019-2021]
           - On-screen text: [VISUAL DATE: "Since 1995" overlay]
        4. TEMPORAL CONTEXT: Note temporal relationships and sequences
        5. VISUAL ANNOTATIONS: Format visual elements as [VISUAL: description]
        
        CRITICAL: Extract ALL visual dates from on-screen text, chyrons, documents, timelines
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
            ],
            "dates": [
                {{"original_text": "October 2018", "normalized_date": "2018-10-01", "precision": "month", "confidence": 0.9, "source": "both", "context": "Pegasus discovery", "visual_description": "date shown on screen", "timestamp": 120.5}},
                // Extract ALL dates from both transcript AND visual elements:
                // - Dates shown in chyrons, overlays, documents
                // - Dates mentioned in speech
                // - Timeline graphics and temporal visualizations
                // Visual dates are often more accurate than spoken dates
            ]
        }}
        
        Focus on temporal intelligence: sequences, causality, chronology, evolution. Pay special attention to visual dates as they're often more accurate than spoken dates.
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
                },
                "dates": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "original_text": {"type": "STRING"},
                            "normalized_date": {"type": "STRING"},
                            "precision": {"type": "STRING", "enum": ["exact", "day", "month", "year", "approximate"]},
                            "confidence": {"type": "NUMBER"},
                            "context": {"type": "STRING"},
                            "source": {"type": "STRING", "enum": ["transcript", "visual", "both"]},
                            "visual_description": {"type": "STRING"},
                            "timestamp": {"type": "NUMBER"}
                        },
                        "required": ["original_text", "normalized_date", "precision", "confidence", "source"]
                    }
                }
            },
            "required": ["summary", "key_points", "topics", "entities", "relationships", "dates"]
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
        3. VISUAL DATES: {"ALL dates shown on screen (chyrons, overlays, documents, graphics)" if is_video else "Not applicable"}
        4. TEMPORAL PATTERNS: Sequences, cycles, progressions, causality chains
        
        Content:
        {transcript_text[:8000]}
        
        CRITICAL for video content: Extract ALL visual dates including:
        - News chyrons and lower thirds with dates
        - Document headers showing dates
        - Timeline graphics and charts
        - Calendar displays
        - Date overlays and watermarks
        - Historical footage timestamps
        
        Visual dates are often MORE ACCURATE than spoken dates. Prioritize them!
        
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
        if file_path.endswith('.mp3'):
            return 'audio/mpeg'
        return mime_type or 'application/octet-stream'
    
    def get_total_cost(self) -> float:
        """Get total cost of all operations."""
        return self.total_cost 

    def _convert_vertex_result_to_dict(self, vertex_result) -> Dict[str, Any]:
        """Convert Vertex AI VideoIntelligence result to dictionary format."""
        # Handle dictionary response from Vertex AI
        if isinstance(vertex_result, dict):
            # The vertex AI already returns a well-structured dict
            # Just need to convert it to our expected format
            
            # Extract transcript text
            transcript_text = ""
            segments = []
            
            if "transcript" in vertex_result:
                transcript_data = vertex_result["transcript"]
                transcript_text = transcript_data.get("full_text", "")
                
                # Convert segments if they exist
                if "segments" in transcript_data and isinstance(transcript_data["segments"], list):
                    # Handle TranscriptSegment objects or dicts
                    for seg in transcript_data["segments"]:
                        if hasattr(seg, '__dict__'):  # It's an object
                            segments.append({
                                "text": seg.text,
                                "start_time": seg.start_time,
                                "end_time": seg.end_time,
                                "speaker": getattr(seg, 'speaker', None)
                            })
                        else:  # It's already a dict
                            segments.append({
                                "text": seg.get("text", ""),
                                "start_time": seg.get("start_time", 0.0),
                                "end_time": seg.get("end_time", 0.0),
                                "speaker": seg.get("speaker")
                            })
            
            # Extract entities
            entities = []
            for e in vertex_result.get("entities", []):
                if hasattr(e, '__dict__'):  # Entity object
                    entities.append({
                        "entity": getattr(e, 'name', getattr(e, 'entity', '')),
                        "type": e.type,

                        "context": getattr(e, 'description', getattr(e, 'context', ''))
                    })
                else:  # Dict
                    entities.append({
                        "entity": e.get('name', e.get('entity', '')),
                        "type": e.get('type', ''),

                        "context": e.get('description', e.get('context', ''))
                    })
            
            # Extract relationships
            relationships = []
            for r in vertex_result.get("relationships", []):
                if hasattr(r, '__dict__'):  # Relationship object
                    relationships.append({
                        "source_entity": r.source,
                        "relationship_type": r.type,
                        "target_entity": r.target,

                        "context": getattr(r, 'description', getattr(r, 'context', ''))
                    })
                else:  # Dict
                    relationships.append({
                        "source_entity": r.get('source', r.get('source_entity', '')),
                        "relationship_type": r.get('type', r.get('relationship_type', '')),
                        "target_entity": r.get('target', r.get('target_entity', '')),

                        "context": r.get('description', r.get('context', ''))
                    })
            
            return {
                "transcript": transcript_text,
                "segments": segments,
                "entities": entities,
                "relationships": relationships,
                "key_insights": vertex_result.get("key_insights", []),
                "temporal_intelligence": vertex_result.get("temporal_intelligence", {}),
                "processing_cost": vertex_result.get("processing_cost", 0.0)
            }
        
        # Original logic for object-based response (backward compatibility)
        return {
            "transcript": vertex_result.transcript_text,
            "segments": [
                {
                    "text": seg.text,
                    "start_time": seg.start_time,
                    "end_time": seg.end_time,
                    "speaker": seg.speaker
                }
                for seg in vertex_result.transcript_segments
            ],
            "entities": [
                {
                    "entity": e.entity,
                    "type": e.type,
                    "confidence": e.confidence,
                    "context": e.context
                }
                for e in vertex_result.entities
            ],
            "relationships": [
                {
                    "source_entity": r.source_entity,
                    "relationship_type": r.relationship_type,
                    "target_entity": r.target_entity,
                    "confidence": r.confidence,
                    "context": r.context
                }
                for r in vertex_result.relationships
            ],
            "key_insights": vertex_result.key_insights,
            "temporal_intelligence": vertex_result.temporal_intelligence.dict() if vertex_result.temporal_intelligence else {},
            "processing_cost": 0.0  # Vertex AI costs are handled differently
        } 