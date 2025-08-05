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
    
    def __init__(self, api_key: Optional[str] = None, performance_monitor: Optional[Any] = None, use_pro: bool = False):
        """
        Initialize transcriber with API key and enhanced temporal intelligence.
        
        Args:
            api_key: Google API key (optional, uses env var if not provided)
            performance_monitor: Performance monitoring instance
            use_pro: Use Gemini 2.5 Pro for highest quality (higher cost)
        """
        # Get settings
        self.settings = Settings()
        self.api_key = api_key or self.settings.google_api_key
        # Force Vertex AI off for reliability (prevents 400 errors)
        self.use_vertex_ai = False  # Disabled for production reliability
        
        # Choose model based on use_pro flag
        model_name = "gemini-2.5-pro" if use_pro else "gemini-2.5-flash"
        logger.info(f"Using model: {model_name} (use_pro={use_pro})")
        
        self.pool = GeminiPool(api_key=self.api_key, model_name=model_name)
        
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
        
        # Get timeout setting
        self.request_timeout = 3600
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
                    enhance_transcript=False, # Temporal intelligence removed
                    mode="audio"
                )
                # Convert to expected format
                return self._convert_vertex_result_to_dict(result)
            except Exception as e:
                logger.warning(f"Vertex AI transcription failed: {e}. Falling back to standard Gemini API.")
                # Fallback to standard Gemini API below
        
        logger.info(f"Using standard Gemini API to transcribe audio: {audio_file}")
        
        # Upload the audio file
        file = genai.upload_file(audio_file, mime_type=self._get_mime_type(audio_file))
        while file.state.name == "PROCESSING":
            await asyncio.sleep(2)
            file = genai.get_file(file.name)

        if file.state.name == "FAILED":
            raise ValueError(file.state.name)
        
        # Get the transcription model
        transcription_model = self.pool.get_model(TaskType.TRANSCRIPTION)
        
        # Calculate cost based on temporal intelligence level
        total_cost = self.settings.estimate_cost(duration, TemporalIntelligenceLevel.STANDARD) # Temporal intelligence removed
        self.total_cost += total_cost
        
        logger.info(f"Estimated cost with {TemporalIntelligenceLevel.STANDARD} temporal intelligence: ${total_cost:.4f}") # Temporal intelligence removed
        
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
            # temporal_intelligence = await self._extract_temporal_intelligence( # Temporal intelligence removed
            #     transcript_text, duration, is_video=False
            # )
            
            # Use fresh models for each analysis task
            analysis_model = self.pool.get_model(TaskType.KEY_POINTS)
            
            analysis_prompt = self._build_enhanced_analysis_prompt(transcript_text)
            response_schema = self._build_enhanced_response_schema()
            
            # Make the combined API call with structured output
            analysis_event = None
            if self.performance_monitor:
                analysis_event = self.performance_monitor.start_timer(
                    "gemini_combined_analysis",
                    model=analysis_model.model_name
                )

            response = await self._retry_generate_content(
                analysis_model,
                [analysis_prompt],
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
                - PEOPLE: Every person mentioned by name, title, role, background, or experience
                  * Named individuals: "John Smith", "General Miller", "Dr. Sarah Johnson"
                  * Government officials, business leaders, experts, sources
                  * Military backgrounds: "Former Special Forces operator", "Combat veteran", "Tier one instructor"
                  * Professional roles: "Senior analyst", "Selection cadre", "Training instructor"
                  * Functional roles: "The spokesperson", "A senior official", "The commander"
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
            # temporal_intelligence = {} # Temporal intelligence removed
            
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
            # result.update(temporal_intelligence) # Temporal intelligence removed
            
            return result
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            # Clean up file if it exists
            try:
                genai.delete_file(file)
            except:
                pass
            raise

    async def transcribe_video(self, video_file: str, duration: int) -> Dict[str, Any]:
        """
        Transcribes a video file using a robust two-step process to prevent timeouts.
        Step 1: Transcribe video to raw text.
        Step 2: Analyze raw text to extract intelligence.
        """
        logger.info(f"Starting two-step transcription for: {video_file}")
        
        file = await self._upload_file_with_retry(video_file)
        
        total_cost = self.settings.estimate_cost(duration, TemporalIntelligenceLevel.STANDARD) # Temporal intelligence removed
        self.total_cost += total_cost
        logger.info(f"Estimated cost for full processing: ${total_cost:.4f}")

        try:
            # --- STEP 1: Transcribe Video to Text ---
            transcript_prompt = "Transcribe this video's audio. Provide only the text of the transcript, without any other commentary."
            logger.info("Step 1: Requesting raw transcript from video...")
            transcription_model = self.pool.get_model(TaskType.TRANSCRIPTION)
            transcript_response = await self._retry_generate_content(
                transcription_model,
                [transcript_prompt, file],
                request_options=RequestOptions(timeout=self.request_timeout)
            )
            transcript_text = transcript_response.text
            logger.info(f"Step 1: Raw transcript received (length: {len(transcript_text)}).")

            # --- STEP 2: Analyze Text for Intelligence ---
            analysis_prompt = self._build_enhanced_analysis_prompt(transcript_text)
            response_schema = self._build_enhanced_response_schema()
            logger.info("Step 2: Requesting structured analysis from transcript...")
            analysis_model = self.pool.get_model(TaskType.ENTITIES)
            analysis_response = await self._retry_generate_content(
                analysis_model,
                [analysis_prompt],
                generation_config={"response_mime_type": "application/json", "response_schema": response_schema},
                request_options=RequestOptions(timeout=self.request_timeout)
            )
            
            combined_data = self._parse_json_response(analysis_response.text) or {}
            combined_data["transcript"] = transcript_text
            combined_data["processing_cost"] = total_cost
            logger.info("Step 2: Structured analysis complete.")
            
            return combined_data
        finally:
            logger.info(f"Deleting uploaded file from cloud: {file.name}")
            genai.delete_file(file.name)

    # async def _extract_temporal_intelligence( # Temporal intelligence removed
    #     self, 
    #     transcript_text: str, 
    #     duration: int, 
    #     is_video: bool = False,
    #     video_file: Optional[Any] = None
    # ) -> Dict[str, Any]:
    #     """Simplified temporal intelligence - complex timestamp extraction saved for roadmap with Whisper.""" # Temporal intelligence removed
    #     logger.info("Temporal intelligence simplified - complex timestamps saved for roadmap") # Temporal intelligence removed
        
    #     # Return empty temporal data - timestamps require Whisper for accuracy # Temporal intelligence removed
    #     # This functionality is saved for the roadmap as "nice to have eventually" # Temporal intelligence removed
    #     return { # Temporal intelligence removed
    #         "timeline_events": [], # Temporal intelligence removed
    #         "visual_temporal_cues": [], # Temporal intelligence removed
    #         "temporal_patterns": [], # Temporal intelligence removed
    #         "visual_dates": [] # Temporal intelligence removed
    #     } # Temporal intelligence removed

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
                # Add retry for 500 Internal Server Error
                if ("503" in str(e) or "500" in str(e)) and attempt < retries - 1:
                    logger.warning(f"Transient error ('{e}'): Retrying in {delay}s (attempt {attempt+1}/{retries})")
                    await asyncio.sleep(delay)
                    delay *= 2  # Exponential backoff
                    continue
                raise e

    async def _upload_file_with_retry(self, file_path: str, retries: int = 3, timeout: int = 300) -> Any:
        """Uploads a file with retries and a hard timeout, running sync code in a thread."""
        for attempt in range(retries):
            file = None
            try:
                logger.info(f"Attempt {attempt + 1}/{retries}: Uploading file {Path(file_path).name}...")

                # Run the synchronous upload_file in a separate thread
                upload_task = asyncio.to_thread(
                    genai.upload_file, file_path, mime_type=self._get_mime_type(file_path)
                )
                file = await asyncio.wait_for(upload_task, timeout=timeout)
                
                # Polling for "ACTIVE" state also needs to be handled carefully
                while file.state.name == "PROCESSING":
                    await asyncio.sleep(5)
                    get_file_task = asyncio.to_thread(genai.get_file, file.name)
                    file = await asyncio.wait_for(get_file_task, timeout=60)

                if file.state.name == "FAILED":
                    raise ValueError(f"File upload failed with state: {file.state.name}")
                
                logger.info(f"Successfully uploaded file: {file.name}")
                return file

            except asyncio.TimeoutError:
                logger.error(f"Upload for {file_path} timed out after {timeout} seconds.")
                if file:
                    try:
                        # Clean up timed-out file
                        delete_task = asyncio.to_thread(genai.delete_file, file.name)
                        await asyncio.wait_for(delete_task, timeout=60)
                        logger.info(f"Cleaned up timed-out file upload: {file.name}")
                    except Exception as e:
                        logger.warning(f"Failed to clean up timed-out file {file.name}: {e}")

                if attempt < retries - 1:
                    logger.warning("Retrying upload...")
                    await asyncio.sleep(2 ** attempt)
                else:
                    logger.critical(f"Upload for {file_path} failed after all retries due to timeout.")
                    raise
            except Exception as e:
                if attempt < retries - 1:
                    logger.warning(f"Upload attempt {attempt+1} failed: {e}. Retrying...")
                    await asyncio.sleep(2 ** attempt)
                else:
                    logger.critical(f"Upload for {file_path} failed after all retries.")
                    raise

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
        """Builds the comprehensive, professional-grade analysis prompt."""
        return f"""
        Analyze this transcript and extract COMPREHENSIVE intelligence. You are an expert analyst extracting actionable intelligence from video content.
        
        CRITICAL REQUIREMENTS:
        - Extract ALL meaningful entities and relationships comprehensively
        - Extract ALL meaningful entities (aim for 50+)
        - Extract ALL meaningful relationships (aim for 50+)  
        - Include ALL people, organizations, locations, events, technologies, products, concepts
        - Use SPECIFIC predicates for relationships (not generic "related to")
        - Calculate REALISTIC confidence scores (0.3-0.99, vary based on context clarity)
        
        Transcript:
        {transcript_text[:24000]}
        
        Return a JSON object with this EXACT structure:
        {{
            "summary": "Write a comprehensive 3-4 paragraph executive summary covering all main points, key players, and critical insights",
            "key_points": [
                {{"text": "Specific, actionable insight or key moment", "importance": 0.9}},
                // Extract 30-50 key points - every significant statement, fact, or claim
            ],
            "topics": ["primary topic", "secondary topic", "tertiary topic", "domain area", "theme"],
            "entities": [
                // PEOPLE: Extract ALL names, titles, roles, backgrounds, positions
                {{"name": "Donald Trump", "type": "PERSON", "confidence": 0.95}},
                {{"name": "President Biden", "type": "PERSON", "confidence": 0.93}},
                {{"name": "The CEO", "type": "PERSON", "confidence": 0.7}},  // Even unnamed roles
                {{"name": "Former Special Forces operator", "type": "PERSON", "confidence": 0.88}},  // Military backgrounds
                
                // ORGANIZATIONS: Companies, agencies, groups, institutions, military units and sub-units
                {{"name": "Department of Justice", "type": "ORGANIZATION", "confidence": 0.9}},
                {{"name": "Delta Force", "type": "ORGANIZATION", "confidence": 0.98}},
                
                // LOCATIONS: Countries, cities, regions, venues
                {{"name": "United States", "type": "LOCATION", "confidence": 0.98}},

                // EVENTS: Meetings, incidents, occurrences, selections, operations
                {{"name": "2024 Presidential Election", "type": "EVENT", "confidence": 0.93}},

                // PRODUCTS/TECH: Software, systems, technologies, equipment, weapons, tools
                {{"name": "Pegasus spyware", "type": "PRODUCT", "confidence": 0.91}},
                
                // Extract EVERYTHING - err on the side of too much rather than too little
            ],
            "relationships": [
                // Use SPECIFIC, MEANINGFUL predicates
                {{"subject": "Donald Trump", "predicate": "indicted_by", "object": "Department of Justice", "confidence": 0.92}},
                {{"subject": "Russia", "predicate": "invaded", "object": "Ukraine", "confidence": 0.98}},
                // Extract EVERY meaningful connection between entities
            ],
            "dates": [
                {{"original_text": "October 2018", "normalized_date": "2018-10-01", "precision": "month", "confidence": 0.95, "context": "when Pegasus was discovered"}},
                // Extract temporal references and calculate actual dates
            ]
        }}
        
        ENTITY CLASSIFICATION RULES:
        1. ORGANIZATIONS = Military units, companies, agencies, institutions, political groups, sports teams
        2. PRODUCTS = Technology, software, equipment, weapons, vehicles, tools, systems
        3. PEOPLE = Individuals, roles, titles, backgrounds, experience descriptors
        4. LOCATIONS = Geographic areas, buildings, facilities
        5. EVENTS = Incidents, meetings, operations, selections, exercises
        
        EXTRACTION RULES:
        1. Entity confidence: 0.95+ for explicitly named, 0.8-0.94 for clearly referenced, 0.6-0.79 for inferred, <0.6 for uncertain
        2. Relationship predicates must be SPECIFIC ACTIONS/STATES not generic terms
        3. BE AGGRESSIVE - I need rich, detailed intelligence extraction.
        """

    def _build_enhanced_response_schema(self) -> Dict[str, Any]:
        """Builds the comprehensive response schema to match the enhanced prompt."""
        return {
            "type": "OBJECT",
            "properties": {
                "summary": {"type": "STRING"},
                "key_points": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "text": {"type": "STRING"},
                            "importance": {"type": "NUMBER"}
                        },
                        "required": ["text", "importance"]
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
                            "type": {"type": "STRING"},
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
                            "precision": {"type": "STRING"},
                            "confidence": {"type": "NUMBER"},
                            "context": {"type": "STRING"}
                        },
                        "required": ["original_text", "normalized_date", "precision", "confidence"]
                    }
                }
            },
            "required": ["summary", "key_points", "topics", "entities", "relationships", "dates"]
        }

    def _build_temporal_intelligence_prompt( # Temporal intelligence removed
        self, 
        transcript_text: str, 
        is_video: bool, 
        duration: int
    ) -> str:
        """Build temporal intelligence extraction prompt.""" # Temporal intelligence removed
        base_prompt = f""" # Temporal intelligence removed
        Extract enhanced temporal intelligence from this content. # Temporal intelligence removed
        
        Content Type: {"Video with visual cues" if is_video else "Audio only"} # Temporal intelligence removed
        Duration: {duration} seconds # Temporal intelligence removed
        
        Extract: # Temporal intelligence removed
        1. TIMELINE EVENTS: Specific events with timestamps and temporal context # Temporal intelligence removed
        2. VISUAL TEMPORAL CUES: {"Charts, timelines, dates shown visually" if is_video else "Not applicable"} # Temporal intelligence removed
        3. VISUAL DATES: {"ALL dates shown on screen (chyrons, overlays, documents, graphics)" if is_video else "Not applicable"} # Temporal intelligence removed
        4. TEMPORAL PATTERNS: Sequences, cycles, progressions, causality chains # Temporal intelligence removed
        
        Content: # Temporal intelligence removed
        {transcript_text[:8000]} # Temporal intelligence removed
        
        CRITICAL for video content: Extract ALL visual dates including: # Temporal intelligence removed
        - News chyrons and lower thirds with dates # Temporal intelligence removed
        - Document headers showing dates # Temporal intelligence removed
        - Timeline graphics and charts # Temporal intelligence removed
        - Calendar displays # Temporal intelligence removed
        - Date overlays and watermarks # Temporal intelligence removed
        - Historical footage timestamps # Temporal intelligence removed
        
        Visual dates are often MORE ACCURATE than spoken dates. Prioritize them! # Temporal intelligence removed
        
        Focus on extracting temporal relationships, chronological sequences, and time-based patterns. # Temporal intelligence removed
        Include confidence scores based on clarity and specificity of temporal information. # Temporal intelligence removed
        """ # Temporal intelligence removed
        
        if is_video and self.settings.extract_visual_cues: # Temporal intelligence removed
            base_prompt += """ # Temporal intelligence removed
            
            ENHANCED VISUAL ANALYSIS: # Temporal intelligence removed
            - Extract dates, years, timelines from visual elements # Temporal intelligence removed
            - Identify temporal charts, graphs, calendars # Temporal intelligence removed
            - Note chronological sequences in presentations # Temporal intelligence removed
            - Capture time-based progressions and evolution # Temporal intelligence removed
            """ # Temporal intelligence removed
        
        return base_prompt # Temporal intelligence removed
    
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

    async def transcribe_large_video(self, video_file: str, duration: int) -> Dict[str, Any]:
        """
        Transcribes a large video using the "Smart Transcribe, Global Analyze" method.
        """
        from ..utils.video_splitter import split_video
        from ..utils.transcript_merger import TranscriptMerger

        logger.info(f"Large video detected. Splitting {video_file} into chunks with 30s overlap.")
        
        # Phase 1: Parallel Raw Transcription
        video_chunks = split_video(video_file, chunk_duration=600, overlap=30)
        
        if not video_chunks or len(video_chunks) <= 1:
            logger.info("Video not split, processing as a single file.")
            return await self.transcribe_video(video_file, duration)

        tasks = [self._transcribe_chunk_raw(chunk) for chunk in video_chunks]
        logger.info(f"Transcribing {len(video_chunks)} chunks in parallel...")
        chunk_transcripts = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out failed chunks
        successful_transcripts = [t for t in chunk_transcripts if isinstance(t, str)]
        if not successful_transcripts:
            return {"error": "All chunks failed to transcribe."}

        # Phase 2: Global Intelligence Analysis
        logger.info("Merging raw transcripts with overlap removal...")
        merger = TranscriptMerger()
        merged_transcript = merger.merge_transcripts(successful_transcripts)
        logger.info(f"Merged transcript length: {len(merged_transcript)}")

        # Perform one global analysis call
        logger.info("Performing global analysis on merged transcript...")
        analysis_prompt = self._build_enhanced_analysis_prompt(merged_transcript)
        response_schema = self._build_enhanced_response_schema()
        analysis_model = self.pool.get_model(TaskType.ENTITIES)
        
        analysis_response = await self._retry_generate_content(
            analysis_model,
            [analysis_prompt],
            generation_config={"response_mime_type": "application/json", "response_schema": response_schema},
            request_options=RequestOptions(timeout=self.request_timeout)
        )
        
        combined_data = self._parse_json_response(analysis_response.text) or {}
        combined_data["transcript"] = merged_transcript
        # Note: Cost calculation will need to be adjusted for this new method
        combined_data["processing_cost"] = self.settings.estimate_cost(duration, TemporalIntelligenceLevel.STANDARD)
        
        # Clean up chunk files
        for chunk_file in video_chunks:
            try:
                os.remove(chunk_file)
            except OSError as e:
                logger.warning(f"Could not remove chunk file {chunk_file}: {e}")

        return combined_data

    async def _transcribe_chunk_raw(self, chunk_file: str) -> str:
        """Helper to get only the raw transcript for a single video chunk."""
        try:
            file = await self._upload_file_with_retry(chunk_file)
            transcript_prompt = "Transcribe this video's audio. Provide only the text of the transcript."
            model = self.pool.get_model(TaskType.TRANSCRIPTION)
            response = await self._retry_generate_content(
                model,
                [transcript_prompt, file],
                request_options=RequestOptions(timeout=self.request_timeout)
            )
            return response.text
        finally:
            genai.delete_file(file.name)
 