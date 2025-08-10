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

from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

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
        self.settings = Settings()
        self.api_key = api_key or self.settings.google_api_key
        self.use_vertex_ai = False
        
        model_name = "gemini-2.5-pro" if use_pro else "gemini-2.5-flash"
        logger.info(f"Using model: {model_name} (use_pro={use_pro})")
        
        self.pool = GeminiPool(api_key=self.api_key, model_name=model_name)
        
        if self.use_vertex_ai:
            logger.info("Using Vertex AI for video processing")
            self.vertex_transcriber = VertexAITranscriber()
        else:
            if not self.api_key:
                raise ValueError("Google API key is required")
            genai.configure(api_key=self.api_key)
            self.vertex_transcriber = None
            
        self.performance_monitor = performance_monitor
        # Use configured timeout from settings for consistency
        self.request_timeout = self.settings.gemini_request_timeout
        logger.info(f"Using Gemini request timeout: {self.request_timeout}s")
        self.total_cost = 0.0
    
    def _enhance_json_response(self, raw_text: str) -> str:
        """Enhance malformed JSON from Gemini responses."""
        if '```json' in raw_text:
            raw_text = raw_text.replace('```json', '').replace('```', '')
        elif '```' in raw_text:
            raw_text = raw_text.replace('```', '')
            
        json_start = max(raw_text.find('{'), raw_text.find('['))
        if json_start > 0:
            raw_text = raw_text[json_start:]
        
        json_end_brace = raw_text.rfind('}')
        json_end_bracket = raw_text.rfind(']')
        json_end = max(json_end_brace, json_end_bracket) + 1
        if json_end < len(raw_text):
            raw_text = raw_text[:json_end]
        
        raw_text = re.sub(r'(["\]\}])\s*\n\s*"', r'\1,\n"', raw_text)
        raw_text = re.sub(r'(["\]\}0-9])\s+"', r'\1,"', raw_text)
        raw_text = re.sub(r',\s*([}\]])', r'\1', raw_text)
        raw_text = re.sub(r'"\s*\n\s*\]', r'"\n]', raw_text)
        
        return raw_text
    
    def _parse_json_response(self, response_text: str, expected_type: str = "object") -> Optional[Any]:
        """Parse JSON response with enhanced error handling."""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.warning(f"Initial JSON parse failed: {e}")
            enhanced_text = self._enhance_json_response(response_text)
            try:
                result = json.loads(enhanced_text)
                logger.info("Successfully parsed JSON after enhancement")
                return result
            except json.JSONDecodeError as e2:
                logger.warning(f"Enhanced JSON parse failed: {e2}")
                try:
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
        """Transcribe audio file with enhanced temporal intelligence."""
        if self.use_vertex_ai and self.vertex_transcriber:
            logger.info(f"Attempting to transcribe audio with Vertex AI: {audio_file}")
            try:
                result = await self.vertex_transcriber.transcribe_with_vertex(Path(audio_file), enhance_transcript=False, mode="audio")
                return self._convert_vertex_result_to_dict(result)
            except Exception as e:
                logger.warning(f"Vertex AI transcription failed: {e}. Falling back to standard Gemini API.")
        
        logger.info(f"Using standard Gemini API to transcribe audio: {audio_file}")
        
        file = genai.upload_file(audio_file, mime_type=self._get_mime_type(audio_file))
        while file.state.name == "PROCESSING":
            await asyncio.sleep(2)
            file = genai.get_file(file.name)

        if file.state.name == "FAILED":
            raise ValueError(file.state.name)
        
        transcription_model = self.pool.get_model(TaskType.TRANSCRIPTION)
        total_cost = self.settings.estimate_cost(duration, TemporalIntelligenceLevel.STANDARD)
        self.total_cost += total_cost
        logger.info(f"Estimated cost with {TemporalIntelligenceLevel.STANDARD} temporal intelligence: ${total_cost:.4f}")
        
        try:
            transcript_prompt = "Transcribe this audio file completely and accurately. Return the full transcript as plain text."
            logger.info("Generating transcription...")
            
            transcription_event = None
            if self.performance_monitor:
                transcription_event = self.performance_monitor.start_timer("gemini_transcription", model=transcription_model.model_name)

            response = await self._retry_generate_content(
                transcription_model, [file, transcript_prompt],
                request_options=RequestOptions(timeout=self.request_timeout)
            )

            if self.performance_monitor:
                self.performance_monitor.stop_timer(transcription_event)

            transcript_text = response.text.strip()
            
            analysis_model = self.pool.get_model(TaskType.KEY_POINTS)
            analysis_prompt = self._build_enhanced_analysis_prompt(transcript_text)
            response_schema = self._build_enhanced_response_schema()
            
            analysis_event = None
            if self.performance_monitor:
                analysis_event = self.performance_monitor.start_timer("gemini_combined_analysis", model=analysis_model.model_name)

            response = await self._retry_generate_content(
                analysis_model, [analysis_prompt],
                generation_config={"response_mime_type": "application/json", "response_schema": response_schema},
                request_options=RequestOptions(timeout=self.request_timeout)
            )

            if self.performance_monitor:
                self.performance_monitor.stop_timer(analysis_event)
            
            combined_data = self._parse_json_response(response.text, "object") or {}
            
            summary = combined_data.get("summary", "No summary generated")
            key_points = combined_data.get("key_points", [])
            topics = combined_data.get("topics", [])
            entities = combined_data.get("entities", [])
            relationships = combined_data.get("relationships", [])
            dates = combined_data.get("dates", [])
            
            if len(entities) < 15 or len(relationships) < 10:
                logger.info("Performing second pass for enhanced entity/relationship extraction...")
                
                second_pass_prompt = f"""
                SECOND PASS - Extract additional meaningful entities and relationships.
                
                You are an expert intelligence analyst. The first pass found {len(entities)} entities and {len(relationships)} relationships.
                Extract ALL additional meaningful entities and relationships comprehensively.
                
                Look for:
                - PEOPLE: Every person mentioned by name, title, role, background, or experience
                - ORGANIZATIONS: Every company, agency, group, institution
                - LOCATIONS: Every geographic reference
                - EVENTS: Every incident, meeting, occurrence
                - CONCEPTS/PRODUCTS: Technologies, systems, policies, laws
                
                Transcript:
                {transcript_text[:12000]}
                
                Already found entities: {[e['name'] for e in entities][:30]}
                
                Find ALL ADDITIONAL entities and relationships not in the above list.
                
                Return JSON:
                {{
                    "additional_entities": [
                        {{"name": "Entity Name", "type": "PERSON/ORGANIZATION/LOCATION/EVENT/PRODUCT", "confidence": 0.85}}
                    ],
                    "additional_relationships": [
                        {{"subject": "Entity A", "predicate": "specific_action_verb", "object": "Entity B", "confidence": 0.85}}
                    ]
                }}
                
                BE EXHAUSTIVE - Every sentence likely contains multiple entities and at least one relationship.
                """
                
                second_model = self.pool.get_model(TaskType.ENTITIES)
                
                second_pass_event = None
                if self.performance_monitor:
                    second_pass_event = self.performance_monitor.start_timer("gemini_second_pass_analysis", model=second_model.model_name)

                response = await self._retry_generate_content(
                    second_model, second_pass_prompt,
                    generation_config={"response_mime_type": "application/json"},
                    request_options=RequestOptions(timeout=self.request_timeout)
                )

                if self.performance_monitor:
                    self.performance_monitor.stop_timer(second_pass_event)
                
                second_pass_data = self._parse_json_response(response.text, "object") or {}
                
                additional_entities = second_pass_data.get("additional_entities", [])
                additional_relationships = second_pass_data.get("additional_relationships", [])
                
                entities.extend(additional_entities)
                relationships.extend(additional_relationships)
                
                logger.info(f"Second pass found {len(additional_entities)} more entities and {len(additional_relationships)} more relationships")
            
            processing_time = 0
            
            logger.info(f"Transcription completed in {processing_time}s, cost: ${total_cost:.4f}")
            logger.info(f"Extracted: {len(entities)} entities, {len(relationships)} relationships, {len(key_points)} key points")
            logger.info(f"Extracted dates: {len(dates)} dates from content")
            
            genai.delete_file(file)
            
            result = {
                "transcript": transcript_text, "summary": summary, "key_points": key_points,
                "entities": entities, "topics": topics, "relationships": relationships, "dates": dates,
                "language": "en", "confidence_score": 0.95, "processing_time": processing_time,
                "processing_cost": total_cost
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            try:
                genai.delete_file(file)
            except:
                pass
            raise

    async def transcribe_video(self, video_file: str, duration: int) -> Dict[str, Any]:
        """Transcribes a video file using a robust two-step process to prevent timeouts."""
        logger.info(f"Starting two-step transcription for: {video_file}")
        
        file = await self._upload_file_with_retry(video_file)
        
        total_cost = self.settings.estimate_cost(duration, TemporalIntelligenceLevel.STANDARD)
        self.total_cost += total_cost
        logger.info(f"Estimated cost for full processing: ${total_cost:.4f}")

        try:
            transcript_prompt = "Transcribe this video's audio. Provide only the text of the transcript, without any other commentary."
            logger.info("Step 1: Requesting raw transcript from video...")
            transcription_model = self.pool.get_model(TaskType.TRANSCRIPTION)
            transcript_response = await self._retry_generate_content(
                transcription_model, [transcript_prompt, file],
                request_options=RequestOptions(timeout=self.request_timeout)
            )
            transcript_text = transcript_response.text
            logger.info(f"Step 1: Raw transcript received (length: {len(transcript_text)}).")

            analysis_prompt = self._build_enhanced_analysis_prompt(transcript_text)
            response_schema = self._build_enhanced_response_schema()
            logger.info("Step 2: Requesting structured analysis from transcript...")
            analysis_model = self.pool.get_model(TaskType.ENTITIES)
            analysis_response = await self._retry_generate_content(
                analysis_model, [analysis_prompt],
                generation_config={"response_mime_type": "application/json", "response_schema": response_schema},
                request_options=RequestOptions(timeout=self.request_timeout)
            )
            
            combined_data = self._parse_json_response(analysis_response.text) or {}
            # If parser returned a string blob, wrap appropriately; otherwise prefer explicit key
            if isinstance(combined_data, dict):
                combined_data["transcript"] = transcript_text
            else:
                combined_data = {"transcript": transcript_text}
            combined_data["processing_cost"] = total_cost
            logger.info("Step 2: Structured analysis complete.")
            
            return combined_data
        finally:
            logger.info(f"Deleting uploaded file from cloud: {getattr(file, 'name', '<unknown>')}")
            try:
                delete_task = asyncio.to_thread(genai.delete_file, file.name)
                await asyncio.wait_for(delete_task, timeout=60)
            except Exception:
                pass

    async def _retry_generate_content(self, model, contents, generation_config=None, request_options=None, retries=3, initial_delay=5):
        delay = initial_delay
        for attempt in range(retries):
            try:
                return await model.generate_content_async(
                    contents, generation_config=generation_config, request_options=request_options
                )
            except Exception as e:
                if ("503" in str(e) or "500" in str(e)) and attempt < retries - 1:
                    logger.warning(f"Transient error ('{e}'): Retrying in {delay}s (attempt {attempt+1}/{retries})")
                    await asyncio.sleep(delay)
                    delay *= 2
                    continue
                raise e

    async def _upload_file_with_retry(self, file_path: str, retries: int = 3, timeout: int = 300) -> Any:
        """Uploads a file with retries and a hard timeout, running sync code in a thread."""
        for attempt in range(retries):
            file = None
            try:
                logger.info(f"Attempt {attempt + 1}/{retries}: Uploading file {Path(file_path).name}...")
                upload_task = asyncio.to_thread(genai.upload_file, file_path, mime_type=self._get_mime_type(file_path))
                file = await asyncio.wait_for(upload_task, timeout=timeout)
                # Some tests may patch upload to return awaitable; handle gracefully
                if asyncio.iscoroutine(file):
                    file = await file
                
                while file.state.name == "PROCESSING":
                    await asyncio.sleep(5)
                    get_file_task = asyncio.to_thread(genai.get_file, file.name)
                    file = await asyncio.wait_for(get_file_task, timeout=60)
                    if asyncio.iscoroutine(file):
                        file = await file

                if file.state.name == "FAILED":
                    raise ValueError(f"File upload failed with state: {file.state.name}")
                
                logger.debug(f"Successfully uploaded file: {file.name}")
                return file

            except asyncio.TimeoutError:
                logger.error(f"Upload for {file_path} timed out after {timeout} seconds.")
                if file:
                    try:
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
        return "Transcribe this video with enhanced temporal intelligence extraction..."

    def _build_enhanced_analysis_prompt(self, transcript_text: str) -> str:
        """
        Builds a robust prompt for comprehensive intelligence extraction, with specific instructions
        to prevent data validation errors.
        """
        prompt = f"""
        **ROLE: Expert Intelligence Analyst**
        **TASK: Analyze the following transcript to extract a comprehensive intelligence package.**
        **OUTPUT FORMAT: JSON ONLY, strictly adhering to the provided schema.**

        **CRITICAL INSTRUCTIONS:**
        1.  **key_points.importance**: This MUST be a float between 0.0 (least important) and 1.0 (most important). If you would rate something an 8 out of 10, the value MUST be `0.8`.
        2.  **entities.confidence**: This MUST be a float between 0.0 and 1.0.
        3.  **relationships.confidence**: This MUST be a float between 0.0 and 1.0.
        4.  **dates.confidence**: This MUST be a float between 0.0 and 1.0.
        5.  **Extraction Scope**: Extract ALL relevant entities, topics, relationships, and key points. Be exhaustive.
        6.  **Date Normalization**: All dates MUST be normalized to `YYYY-MM-DD` format where possible.
        7.  **Summary**: Provide a concise, executive-level summary of the content.

        **Transcript for Analysis (first 24,000 characters):**
        ```
        {transcript_text[:24000]}
        ```
        """
        return prompt

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

    def _get_mime_type(self, file_path: str) -> str:
        mime_type, _ = mimetypes.guess_type(file_path)
        if file_path.endswith('.mp3'):
            return 'audio/mpeg'
        return mime_type or 'application/octet-stream'
    
    def get_total_cost(self) -> float:
        return self.total_cost 

    def _convert_vertex_result_to_dict(self, vertex_result) -> Dict[str, Any]:
        if isinstance(vertex_result, dict):
            return {"transcript": vertex_result.get("transcript", {}).get("full_text", "")}
        return {"transcript": vertex_result.transcript_text}

    async def transcribe_large_video(self, video_file: str, duration: int) -> Dict[str, Any]:
        """
        Transcribes a large video using the "Smart Transcribe, Global Analyze" method with concurrency limiting.
        This is a professional-grade implementation that respects API rate limits and handles transient errors gracefully.
        """
        from ..utils.video_splitter import split_video
        from ..utils.transcript_merger import TranscriptMerger

        logger.info(f"Large video detected. Splitting {video_file} into chunks with 30s overlap.")
        
        # Phase 1: Parallel Raw Transcription with Concurrency Limiting
        # This is the core of our rate-limiting solution. The semaphore ensures that we never
        # exceed the configured number of concurrent requests to the Gemini API.
        # Use configurable chunk size to improve reliability of uploads
        video_chunks = split_video(
            video_file,
            chunk_duration=self.settings.chunk_size,
            overlap=10,
        )
        
        if not video_chunks or len(video_chunks) <= 1:
            logger.info("Video not split, processing as a single file.")
            return await self.transcribe_video(video_file, duration)

        semaphore = asyncio.Semaphore(self.settings.gemini_concurrent_requests)
        tasks = [self._transcribe_chunk_raw(chunk, semaphore) for chunk in video_chunks]
        logger.info(f"Transcribing {len(video_chunks)} chunks with a concurrency limit of {self.settings.gemini_concurrent_requests}...")
        chunk_transcripts = await asyncio.gather(*tasks, return_exceptions=True)

        successful_transcripts = [t for t in chunk_transcripts if isinstance(t, str)]
        if not successful_transcripts:
            return {"error": "All chunks failed to transcribe."}

        # Phase 2: Global Intelligence Analysis
        # By merging the transcripts first, we can perform a single, high-quality analysis
        # on the full text, which produces a more coherent and comprehensive result.
        logger.info("Merging raw transcripts with overlap removal...")
        merger = TranscriptMerger()
        merged_transcript = merger.merge_transcripts(successful_transcripts)
        logger.info(f"Merged transcript length: {len(merged_transcript)}")

        logger.info("Performing global analysis on merged transcript...")
        analysis_prompt = self._build_enhanced_analysis_prompt(merged_transcript)
        response_schema = self._build_enhanced_response_schema()
        analysis_model = self.pool.get_model(TaskType.ENTITIES)
        
        analysis_response = await self._retry_generate_content(
            analysis_model, [analysis_prompt],
            generation_config={"response_mime_type": "application/json", "response_schema": response_schema},
            request_options=RequestOptions(timeout=self.request_timeout)
        )
        
        combined_data = self._parse_json_response(analysis_response.text) or {}
        combined_data["transcript"] = merged_transcript
        combined_data["processing_cost"] = self.settings.estimate_cost(duration, TemporalIntelligenceLevel.STANDARD)
        
        for chunk_file in video_chunks:
            try:
                os.remove(chunk_file)
            except OSError as e:
                logger.warning(f"Could not remove chunk file {chunk_file}: {e}")

        return combined_data

    @retry(
        stop=stop_after_attempt(3), 
        wait=wait_exponential(multiplier=2, min=5, max=60),
        retry=retry_if_exception_type(Exception),
        before_sleep=lambda retry_state: logger.warning(f"Chunk transcription attempt {retry_state.attempt_number} failed, retrying...")
    )
    async def _transcribe_chunk_raw(self, chunk_file: str, semaphore: asyncio.Semaphore) -> str:
        """
        Helper to get only the raw transcript for a single video chunk.
        This method is wrapped in a semaphore to limit concurrency and a retry decorator for resilience.
        """
        async with semaphore:
            file = None
            temp_audio_path: Optional[str] = None
            try:
                # Convert video chunk to audio to reduce upload size and avoid ECONNRESET
                temp_audio_path = await self._extract_audio_for_upload(chunk_file)
                file = await self._upload_file_with_retry(temp_audio_path)
                transcript_prompt = "Transcribe this audio. Provide only the text of the transcript."
                model = self.pool.get_model(TaskType.TRANSCRIPTION)
                response = await self._retry_generate_content(
                    model, [transcript_prompt, file],
                    request_options=RequestOptions(timeout=self.request_timeout)
                )
                return response.text
            finally:
                if file:
                    genai.delete_file(file.name)
                try:
                    if temp_audio_path and os.path.exists(temp_audio_path):
                        os.remove(temp_audio_path)
                except Exception as e:
                    logger.warning(f"Failed to remove temp audio file {temp_audio_path}: {e}")

    async def _extract_audio_for_upload(self, video_chunk_path: str) -> str:
        """Extract audio from a video chunk to a temporary MP3 file for smaller, reliable uploads."""
        import subprocess
        base = Path(video_chunk_path).with_suffix("").name
        temp_dir = Path(tempfile.gettempdir())
        out_path = str(temp_dir / f"{base}.mp3")
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            video_chunk_path,
            "-vn",
            "-acodec",
            "mp3",
            "-ar",
            "44100",
            "-b:a",
            "192k",
            out_path,
        ]
        try:
            logger.debug(f"Extracting audio for upload: {' '.join(cmd)}")
            await asyncio.to_thread(subprocess.run, cmd, check=True, capture_output=True)
            return out_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Audio extraction failed: {e.stderr.decode('utf-8', errors='ignore') if hasattr(e, 'stderr') else e}")
            # Fallback to original video if audio extraction fails
            return video_chunk_path
