"""
Post-processing module for video transcripts using Gemini AI.

This module provides functionality to analyze and process video transcripts,
including sentiment analysis, topic detection, and clip extraction.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
import json
import os
from difflib import SequenceMatcher
import nltk
import numpy as np
from config import GEMINI_TEMPERATURE, GEMINI_TOP_P, GEMINI_TOP_K, GEMINI_MAX_TOKENS, GEMINI_STOP_SEQUENCES

import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from google.cloud import speech_v1 as speech
from config import GEMINI_MODEL, CLIP_PADDING, setup_logger
from moviepy.editor import VideoFileClip

# Download required NLTK data
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

# Configure logging using centralized configuration
logger = setup_logger("post_processing")

@dataclass
class ClipSuggestion:
    """Data class representing a suggested video clip segment."""
    text: str
    start_time: float
    end_time: float
    confidence: float
    explanation: str
    topic: str

@dataclass
class VideoSegment:
    """Data class representing a video segment with timing and confidence."""
    text: str
    start_time: float
    end_time: float
    confidence: float

class ProcessingError(Exception):
    """Custom exception for processing-related errors."""
    pass

class BasePostProcessor:
    """
    Abstract base class defining the interface for post-processing implementations.
    
    This class provides the foundation for transcript processing with standard
    confidence thresholds and required method signatures.
    """
    
    # Class-level confidence thresholds
    SEGMENT_CONFIDENCE_THRESHOLD = 0.85
    WORD_CONFIDENCE_THRESHOLD = 0.9
    TOPIC_CONFIDENCE_THRESHOLD = 0.95
    MIN_CONFIDENT_WORDS = 3

    def process_transcript(
        self, 
        transcript: Dict[str, Any], 
        description: str, 
        youtube_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a transcript with metadata and return analysis results.
        
        Args:
            transcript: Raw transcript data
            description: Video description
            youtube_metadata: Additional video metadata
            
        Returns:
            Dict containing processed transcript analysis
            
        Raises:
            ProcessingError: If processing fails
        """
        raise NotImplementedError

    def refine_transcript(self, transcript: str) -> str:
        """
        Refine and clean a transcript.
        
        Args:
            transcript: Raw transcript text
            
        Returns:
            Cleaned and formatted transcript
            
        Raises:
            ProcessingError: If refinement fails
        """
        raise NotImplementedError
    
class GeminiPostProcessor(BasePostProcessor):
    """
    Implements transcript post-processing using Google's Gemini AI model.
    
    This class provides methods for analyzing transcripts, generating summaries,
    and extracting insights using the Gemini language model.
    """

    # Constructor
    def __init__(self):
        """Initialize the post-processor."""
        try:
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            logger.info(f"Initializing Gemini model: {GEMINI_MODEL}")
            
            generation_config = GenerationConfig(
                temperature=GEMINI_TEMPERATURE,
                top_p=GEMINI_TOP_P,
                top_k=GEMINI_TOP_K,
                max_output_tokens=8192
            )
            
            self.gemini_model = genai.GenerativeModel(
                model_name=GEMINI_MODEL,
                generation_config=generation_config
            )
            logger.info("GeminiPostProcessor initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize GeminiPostProcessor: {str(e)}")
            raise

    # Core Public Methods
    def process_transcript(
        self, 
        transcript_data: Union[str, Dict[str, Any]], 
        description: str, 
        youtube_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a transcript and generate comprehensive analysis."""
        try:
            # Get output directory - handle both string paths and dict data
            if isinstance(transcript_data, str):
                output_dir = os.path.dirname(transcript_data)
            else:
                # Try different ways to get the output dir
                if "paths" in transcript_data:
                    output_dir = os.path.dirname(transcript_data["paths"]["processed"])
                elif "transcript_path" in transcript_data:
                    output_dir = os.path.dirname(transcript_data["transcript_path"])
                else:
                    # Fallback to current directory structure
                    video_title = youtube_metadata.get("title", "").replace(" ", "_")
                    output_dir = os.path.join("output", video_title)
                
            logger.debug(f"Using output directory: {output_dir}")
            
            # Create analysis file path
            video_name = os.path.basename(output_dir)
            analysis_path = os.path.join(output_dir, f"{video_name}_analysis.json")
            
            # Generate initial analysis
            analysis_data = {
                "metadata": youtube_metadata,
                "summary": self._generate_executive_summary(transcript_data, youtube_metadata),
                "segments": self.create_logical_segments(transcript_data),
                "transcript_analysis": {
                    "topics": self._analyze_topic_distribution(transcript_data, youtube_metadata),
                    "sentiment": self._analyze_sentiment_over_time(transcript_data, youtube_metadata),
                    "entities": self._perform_named_entity_recognition(transcript_data.get("transcript", "")),
                    "language_metrics": self._analyze_language(transcript_data.get("transcript", ""))
                },
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            # Save analysis file
            with open(analysis_path, 'w') as f:
                json.dump(analysis_data, f, indent=2)
            
            logger.info(f"Analysis saved to: {analysis_path}")
            
            return analysis_data

        except Exception as e:
            logger.error(f"Error in process_transcript: {str(e)}", exc_info=True)
            return {}

    def refine_transcript(self, transcript: str) -> str:
        """
        Clean and refine transcript text.

        Args:
            transcript: Raw transcript text

        Returns:
            Refined transcript text with improved formatting and clarity

        Raises:
            ProcessingError: If refinement fails
        """
        if not transcript or not isinstance(transcript, str):
            raise ValueError("Invalid transcript provided for refinement")
            
        try:
            prompt = """
            Please refine this transcript, improving clarity and readability:
            1. Correct grammar and spelling
            2. Add proper punctuation
            3. Remove filler words
            4. Preserve original meaning
            
            Transcript:
            {transcript}
            """
            
            return self._generate_content(prompt.format(transcript=transcript))
        except Exception as e:
            raise ProcessingError(f"Transcript refinement failed: {str(e)}")

    def create_clip(
        self, 
        video_path: str, 
        suggestion: ClipSuggestion, 
        padding_seconds: float = CLIP_PADDING
    ) -> str:
        """Create a video clip with verified timing."""
        try:
            video = VideoFileClip(video_path)
            
            # Get audio data for verification
            audio = video.audio
            if audio is None:
                logger.warning("Video has no audio track, using original timing")
                clip = video.subclip(suggestion.start_time, suggestion.end_time)
            else:
                # Properly reshape audio array
                try:
                    audio_array = np.array(audio.to_soundarray(), dtype=float)
                    if len(audio_array.shape) > 1:
                        audio_array = audio_array.mean(axis=1)  # Convert to mono
                    
                    # Calculate dynamic threshold
                    threshold = np.mean(audio_array) + np.std(audio_array)
                    speech_indices = np.where(np.abs(audio_array) > threshold)[0]
                    
                    if len(speech_indices) > 0:
                        # Adjust times based on actual speech
                        first_speech = speech_indices[0] / audio.fps
                        last_speech = speech_indices[-1] / audio.fps
                        
                        refined_start = suggestion.start_time + max(0, first_speech - padding_seconds)
                        refined_end = suggestion.start_time + min(
                            suggestion.end_time - suggestion.start_time, 
                            last_speech + padding_seconds
                        )
                        
                        clip = video.subclip(refined_start, refined_end)
                    else:
                        logger.warning("No speech detected, using original timing")
                        clip = video.subclip(suggestion.start_time, suggestion.end_time)
                    
                except Exception as audio_error:
                    logger.warning(f"Audio analysis failed, using original timing: {str(audio_error)}")
                    clip = video.subclip(suggestion.start_time, suggestion.end_time)
            
            # Generate output path and write clip
            base_path = os.path.splitext(video_path)[0]
            topic_slug = suggestion.topic.lower().replace(' ', '_')
            timestamp = f"{int(suggestion.start_time):03d}_{int(suggestion.end_time):03d}"
            output_path = f"{base_path}_{topic_slug}_{timestamp}_clip.mp4"
            
            clip.write_videofile(output_path, logger=None)
            
            # Cleanup
            clip.close()
            video.close()
            
            return output_path
            
        except Exception as e:
            if 'video' in locals():
                video.close()
            raise ProcessingError(f"Clip creation failed: {str(e)}")

    def find_and_create_clips(
        self, 
        video_path: str, 
        search_concept: str,
        transcript_data: Dict[str, Any], 
        min_confidence: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Find relevant segments and create video clips.

        Args:
            video_path: Path to source video file
            search_concept: Concept to search for
            transcript_data: Transcript data
            min_confidence: Minimum confidence threshold

        Returns:
            List of dictionaries containing clip information and paths

        Raises:
            ProcessingError: If clip finding/creation fails
        """
        try:
            # Get suggestions from Gemini
            suggestions = self.search_transcript_segments(search_concept, transcript_data)
            
            # Filter by confidence
            high_confidence_suggestions = [
                s for s in suggestions 
                if s.confidence >= min_confidence
            ]
            
            # Create clips for each suggestion
            clips = []
            for suggestion in high_confidence_suggestions:
                try:
                    clip_path = self.create_clip(video_path, suggestion)
                    clips.append({
                        "text": suggestion.text,
                        "explanation": suggestion.explanation,
                        "confidence": suggestion.confidence,
                        "topic": suggestion.topic,
                        "clip_path": clip_path,
                        "start_time": suggestion.start_time,
                        "end_time": suggestion.end_time
                    })
                except Exception as clip_error:
                    logger.error(f"Failed to create clip: {str(clip_error)}")
                    continue
                    
            return clips
            
        except Exception as e:
            raise ProcessingError(f"Clip finding/creation failed: {str(e)}")
        
    def _analyze_sentiment_over_time(self, transcript_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze sentiment with accurate timing."""
        try:
            segments = transcript_data.get("segments", [])
            sentiment_segments = []

            for segment in segments:
                text = segment["text"]
                start_time = segment["start_time"]
                end_time = segment["end_time"]
                confidence = segment["confidence"]

                # Get sentiment for this segment
                prompt = f"""
                Analyze the sentiment of this text segment. 
                Return only a float between -1.0 (very negative) and 1.0 (very positive):
                Text: {text}
                """

                sentiment = float(self._generate_content(prompt) or 0.0)

                sentiment_segments.append({
                    "text": text,
                    "start_time": start_time,
                    "end_time": end_time,
                    "sentiment_score": sentiment,
                    "confidence": confidence  # Use the actual confidence
                })

            return sentiment_segments
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {str(e)}")
            return []

    def _analyze_topic_distribution(
        self, 
        transcript: str, 
        youtube_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Analyze topic distribution across the transcript.

        Args:
            transcript: Transcript text
            youtube_metadata: Video metadata

        Returns:
            List of topics with percentages, each containing:
                - topic: Topic name
                - percentage: Coverage percentage
                - key_phrases: Related phrases
                - time_ranges: Topic occurrence times

        Raises:
            ProcessingError: If topic analysis fails
        """
        try:
            prompt = f"""
            Analyze the following transcript and identify the main topics discussed.
            For each topic segment, provide:
            - topic name
            - percentage of video coverage (0-100)
            - confidence score (0-1)
            
            Return the analysis as a JSON array of objects with these fields:
            topic, percentage, confidence
            
            Video Title: {youtube_metadata['title']}
            Channel: {youtube_metadata['author']}
            
            Transcript:
            {transcript}
            """

            topics = self._generate_content(prompt, response_type='json')
            
            if not isinstance(topics, list):
                raise ProcessingError("Invalid topic analysis response format")
                
            # Validate topic structure
            for topic in topics:
                required_fields = ['topic', 'percentage', 'confidence']
                if not all(field in topic for field in required_fields):
                    raise ProcessingError("Missing required fields in topic analysis")
            
            # Enhance topics with time ranges and key phrases
            for topic in topics:
                topic["time_ranges"] = self._get_topic_time_ranges(topic["topic"], transcript)
                topic["key_phrases"] = self._extract_key_phrases(topic["topic"], transcript)
            
            return topics
            
        except Exception as e:
            logger.error(f"Topic analysis error: {str(e)}")
            raise ProcessingError(f"Topic analysis failed: {str(e)}")

    def _analyze_language(
        self, 
        transcript: str,
        youtube_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform comprehensive language analysis.

        Args:
            transcript: Transcript text
            youtube_metadata: Video metadata

        Returns:
            Dict containing language metrics
        """
        try:
            if not transcript:
                return self._get_default_language_metrics()
            
            return {
                "formality_level": self._assess_formality(transcript),
                "tone": self._analyze_tone(transcript),
                "complexity": self._assess_complexity(transcript)
            }
            
        except Exception as e:
            raise ProcessingError(f"Language analysis failed: {str(e)}")

    def _analyze_arguments(
        self, 
        transcript: str,
        youtube_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Analyze arguments and claims in the transcript.

        Args:
            transcript: Transcript text
            youtube_metadata: Video metadata

        Returns:
            List of arguments with evidence
        """
        try:
            # Split transcript into sentences
            sentences = nltk.sent_tokenize(transcript)
            arguments = []
            current_argument = {"claim": "", "evidence": [], "time_range": []}
            
            for i, sentence in enumerate(sentences):
                # Estimate time based on position
                estimated_time = (i * len(sentence.split())) / 150 * 60
                
                if self._is_claim(sentence):
                    if current_argument["claim"]:
                        arguments.append(current_argument)
                    current_argument = {
                        "claim": sentence,
                        "evidence": [],
                        "time_range": [estimated_time],
                        "confidence": 0.8
                    }
                elif current_argument["claim"]:
                    current_argument["evidence"].append({
                        "text": sentence,
                        "time": estimated_time,
                        "confidence": 0.8
                    })

            # Add final argument if exists
            if current_argument["claim"]:
                arguments.append(current_argument)
                
            return arguments
            
        except Exception as e:
            raise ProcessingError(f"Argument analysis failed: {str(e)}")

    def _perform_named_entity_recognition(self, text: str) -> Dict[str, List[str]]:
        try:
            entities = self._generate_content(
                f"Extract named entities from this text and return as JSON:\n{text}",
                response_type='json'
            )
            
            # Handle both list and dict responses
            if isinstance(entities, list):
                return {"entities": entities}
            return entities
        except Exception as e:
            logger.error(f"Named entity recognition failed: {str(e)}")
            return {"entities": []}

    def _find_entity_mentions(self, entity: str, transcript: str) -> List[Dict[str, Any]]:
        """Find all mentions of an entity in the transcript with context."""
        try:
            sentences = nltk.sent_tokenize(transcript)
            mentions = []
            
            for i, sentence in enumerate(sentences):
                if entity.lower() in sentence.lower():
                    # Get surrounding context (previous and next sentences)
                    prev_sentence = sentences[i-1] if i > 0 else ""
                    next_sentence = sentences[i+1] if i < len(sentences)-1 else ""
                    
                    mentions.append({
                        "context": sentence,
                        "surrounding_context": {
                            "before": prev_sentence,
                            "after": next_sentence
                        },
                        "approximate_position": f"~{i/len(sentences)*100:.0f}% through transcript"
                    })
            
            return mentions
            
        except Exception as e:
            logger.error(f"Error finding entity mentions: {str(e)}")
            return []

    def _generate_executive_summary(
        self, 
        transcript: Dict[str, Any], 
        description: str, 
        youtube_metadata: Dict[str, Any]
    ) -> str:
        """
        Generate comprehensive summary of the video content.

        Args:
            transcript: Transcript data
            description: Video description
            youtube_metadata: Video metadata

        Returns:
            Executive summary text

        Raises:
            ProcessingError: If summary generation fails
        """
        try:
            text = self._extract_full_text(transcript)
            
            prompt = f"""
            Generate an executive summary for this YouTube video.
            
            Video Title: {youtube_metadata['title']}
            Channel: {youtube_metadata['author']}
            Upload Date: {youtube_metadata['publish_date']}
            Description: {description}

            Transcript: {text}

            Provide a concise summary that:
            1. Captures main points (max 350 words)
            2. Highlights key conclusions
            3. Mentions important stakeholders
            4. Includes critical data points
            5. Reflects overall tone
            """
            
            return self._generate_content(prompt)
            
        except Exception as e:
            raise ProcessingError(f"Executive summary generation failed: {str(e)}")
        
    # Content Generation Methods
    def _generate_content(
        self, 
        prompt: str, 
        response_type: str = 'text'
    ) -> Union[str, Dict[str, Any], List[Any]]:
        """Generate content using Gemini model."""
        try:
            logger.debug(f"Generating content with type: {response_type}")
            logger.debug(f"Prompt length: {len(prompt)} chars")
            logger.debug(f"Estimated tokens: {len(prompt.split())}")
            
            # Add response type instruction to prompt
            if response_type == 'json':
                prompt += "\nRespond ONLY with valid JSON. No other text."
            
            logger.debug(f"Sending prompt to Gemini: {prompt}")
            
            # Updated generation config based on Gemini 1.5 Pro best practices
            response = self.gemini_model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=GEMINI_TEMPERATURE,  # Use config value
                    candidate_count=1,
                    max_output_tokens=8192,  # Increased for 1.5 Pro
                    top_p=GEMINI_TOP_P,      # Use config value
                    top_k=GEMINI_TOP_K,      # Use config value
                    stop_sequences=GEMINI_STOP_SEQUENCES  # Use config value
                )
            )
            
            logger.debug(f"Content generated successfully")
            
            if not response or not response.text:
                logger.error("Empty response from Gemini")
                return {} if response_type == 'json' else ""
            
            if response_type == 'json':
                try:
                    text = response.text.strip()
                    # Clean JSON string
                    if '```' in text:
                        text = text.split('```')[1]
                        if text.startswith('json'):
                            text = text[4:]
                    text = text.strip()
                    
                    parsed = json.loads(text)
                    logger.debug(f"Parsed JSON response: {parsed}")
                    return parsed
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parse error: {str(e)}\nResponse text: {text}")
                    return {}
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Content generation error: {str(e)}", exc_info=True)
            return {} if response_type == 'json' else ""

    def _generate_metadata(self, transcript: str) -> Dict[str, Any]:
        """
        Generate metadata about the processed transcript.

        Args:
            transcript: Raw transcript text

        Returns:
            Dict containing:
                - duration_seconds: Estimated duration
                - average_confidence: Mean confidence score
                - language: Detected language
                - quality_metrics: Additional quality metrics

        Raises:
            ProcessingError: If metadata generation fails
        """
        try:
            # Estimate duration based on word count and average speaking rate
            words = len(transcript.split())
            estimated_duration = words / 150 * 60  # Assuming 150 words per minute
            
            # Detect language using NLTK (could be enhanced with langdetect)
            try:
                from nltk.tokenize import word_tokenize
                sample = ' '.join(word_tokenize(transcript)[:100])  # Take first 100 words
                language = "en"  # Default to English for now
            except Exception:
                language = "en"
            
            # Calculate quality metrics
            quality_metrics = self._calculate_quality_metrics(transcript)
            
            return {
                "duration_seconds": estimated_duration,
                "average_confidence": 0.9,  # Default confidence since we can't calculate from string
                "language": language,
                "quality_metrics": quality_metrics,
                "word_count": words,
                "processing_timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            raise ProcessingError(f"Metadata generation failed: {str(e)}")

    def _calculate_quality_metrics(self, transcript: str) -> Dict[str, float]:
        """
        Calculate quality-related metrics for the transcript.

        Args:
            transcript: Transcript text

        Returns:
            Dict containing quality metrics
        """
        try:
            # Split into sentences
            sentences = nltk.sent_tokenize(transcript)
            
            # Calculate average sentence length
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
            
            # Calculate vocabulary diversity
            unique_words = len(set(word.lower() for word in transcript.split()))
            total_words = len(transcript.split())
            vocabulary_diversity = unique_words / total_words if total_words > 0 else 0
            
            return {
                "average_sentence_length": avg_sentence_length,
                "vocabulary_diversity": vocabulary_diversity,
                "estimated_clarity": 0.85,  # Default value since we can't calculate from string
                "noise_level": 0.1  # Default value since we can't calculate from string
            }
        except Exception as e:
            logger.error(f"Error calculating quality metrics: {str(e)}")
            return {
                "average_sentence_length": 0,
                "vocabulary_diversity": 0,
                "estimated_clarity": 0,
                "noise_level": 0
            }

    # Text Processing Methods
    def _extract_full_text(self, transcript_data: Dict[str, Any]) -> str:
        """
        Extract complete text from transcript data.

        Args:
            transcript_data: Raw transcript data

        Returns:
            Complete transcript text

        Raises:
            ProcessingError: If text extraction fails
        """
        try:
            full_text = []
            
            # Handle both string and dict inputs
            if isinstance(transcript_data, str):
                return transcript_data
                
            # Extract from Google Speech API response structure
            results = transcript_data.get("results", {})
            if isinstance(results, dict):
                # Handle nested structure
                for file_result in results.values():
                    transcript_results = file_result.get("transcript", {}).get("results", [])
                    for result in transcript_results:
                        alternatives = result.get("alternatives", [])
                        if alternatives:
                            transcript = alternatives[0].get("transcript", "")
                            if transcript:
                                full_text.append(transcript)
            elif isinstance(results, list):
                # Handle flat structure
                for result in results:
                    alternatives = result.get("alternatives", [])
                    if alternatives:
                        transcript = alternatives[0].get("transcript", "")
                        if transcript:
                            full_text.append(transcript)
                            
            text = " ".join(full_text)
            logger.debug(f"Extracted text length: {len(text)}")
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
            raise ProcessingError(f"Text extraction failed: {str(e)}")

    def _get_high_confidence_segments(
        self, 
        transcript: Dict[str, Any], 
        threshold: float = None
    ) -> List[str]:
        """
        Extract transcript segments with high confidence scores.

        Args:
            transcript: Transcript data
            threshold: Optional confidence threshold (defaults to WORD_CONFIDENCE_THRESHOLD)

        Returns:
            List of high-confidence text segments

        Raises:
            ProcessingError: If segment extraction fails
        """
        try:
            threshold = threshold or self.WORD_CONFIDENCE_THRESHOLD
            high_confidence_text = []
            
            for segment in self._get_timed_segments(transcript):
                if segment.get("confidence", 0) > threshold:
                    high_confidence_text.append(segment.get("text", ""))
                    
            return high_confidence_text
            
        except Exception as e:
            raise ProcessingError(f"High confidence segment extraction failed: {str(e)}")

    def _get_timed_segments(self, transcript: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract segments with timing information.

        Args:
            transcript: Transcript data

        Returns:
            List of segments with text, timing, and confidence information

        Raises:
            ProcessingError: If segment extraction fails
        """
        try:
            segments = []
            results = transcript.get("results", {}).get("transcript", {}).get("results", [])
            
            for result in results:
                if not result.get("alternatives"):
                    continue
                
                alt = result["alternatives"][0]
                segments.append({
                    "text": alt.get("transcript", ""),
                    "time": float(result.get("resultEndOffset", "0").rstrip("s")),
                    "confidence": alt.get("confidence", 0.0)
                })
                
            return segments
            
        except Exception as e:
            raise ProcessingError(f"Timed segment extraction failed: {str(e)}")

    def _parse_sentiment_response(self, response: str) -> float:
        """
        Parse sentiment analysis response to float value.
        
        Args:
            response: Raw response from sentiment analysis
            
        Returns:
            Sentiment score between -1.0 and 1.0
            
        Raises:
            ProcessingError: If parsing fails
        """
        try:
            sentiment = float(response.strip())
            return max(min(sentiment, 1.0), -1.0)
        except (ValueError, AttributeError) as e:
            logger.error(f"Error parsing sentiment response: {str(e)}")
            return 0.0

    def _detect_topic(self, words: List[str]) -> str:
        """
        Detect primary topic from a list of words.
        
        Args:
            words: List of high-confidence words
            
        Returns:
            Detected topic string
            
        Raises:
            ProcessingError: If topic detection fails
        """
        try:
            if len(words) < self.MIN_CONFIDENT_WORDS:
                return ""
                
            prompt = f"""
            Extract the main topic from these words in 2-3 words.
            Return only the topic phrase.
            
            Words: {' '.join(words)}
            """
            
            return self._generate_content(prompt).strip()
        except Exception as e:
            logger.error(f"Error detecting topic: {str(e)}")
            return ""

    def _is_claim(self, text: str) -> bool:
        """
        Determine if text contains a significant claim or argument.

        Args:
            text: Text to analyze

        Returns:
            True if text contains a claim, False otherwise
        """
        try:
            prompt = f"""
            Determine if this text contains a significant claim or argument. Consider:
            1. Does it make a clear assertion?
            2. Is it supported by evidence or reasoning?
            3. Is it a central point rather than a minor statement?
            
            Text: {text}
            
            Return only 'true' or 'false'.
            """
            
            response = self._generate_content(prompt).strip().lower()
            return response == 'true'
        except Exception as e:
            logger.error(f"Error checking for claims: {str(e)}")
            return False
        
    def _calculate_confidence_metrics(self, transcript: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate confidence-related metrics for the transcript.

        Args:
            transcript: Transcript data

        Returns:
            Dict containing:
                - average_confidence: Mean confidence score
                - high_confidence_percentage: Percentage of high confidence words

        Raises:
            ProcessingError: If metric calculation fails
        """
        try:
            word_confidences = []
            results = transcript.get("results", {}).get("transcript", {}).get("results", [])
            
            for result in results:
                for alt in result.get("alternatives", []):
                    for word in alt.get("words", []):
                        if "confidence" in word:
                            word_confidences.append(float(word["confidence"]))
            
            if not word_confidences:
                return {
                    "average_confidence": 0.0,
                    "high_confidence_percentage": 0.0
                }
            
            avg_confidence = sum(word_confidences) / len(word_confidences)
            high_conf_words = len([c for c in word_confidences if c > 0.9])
            high_conf_percentage = (high_conf_words / len(word_confidences)) * 100
            
            return {
                "average_confidence": round(avg_confidence, 3),
                "high_confidence_percentage": round(high_conf_percentage, 2)
            }
            
        except Exception as e:
            raise ProcessingError(f"Confidence metric calculation failed: {str(e)}")

    def _calculate_speaker_clarity(self, transcript: Dict[str, Any]) -> float:
        """
        Calculate speaker clarity based on word confidence scores.

        Args:
            transcript: Transcript data

        Returns:
            Clarity score between 0.0 and 1.0

        Raises:
            ProcessingError: If clarity calculation fails
        """
        try:
            word_confidences = self._extract_word_confidences(transcript)
            if not word_confidences:
                return 0.0

            # Use exponential weighting to emphasize high confidence words
            weighted_sum = sum(conf ** 2 for conf in word_confidences)
            clarity = weighted_sum / len(word_confidences)
            return round(min(clarity, 1.0), 2)
            
        except Exception as e:
            raise ProcessingError(f"Speaker clarity calculation failed: {str(e)}")

    def _estimate_noise_level(self, transcript: Dict[str, Any]) -> float:
        """
        Estimate background noise level from confidence variations.

        Args:
            transcript: Transcript data

        Returns:
            Noise level score between 0.0 (noisy) and 1.0 (clear)

        Raises:
            ProcessingError: If noise estimation fails
        """
        try:
            word_confidences = self._extract_word_confidences(transcript)
            if not word_confidences:
                return 1.0

            mean_conf = sum(word_confidences) / len(word_confidences)
            variance = sum((c - mean_conf) ** 2 for c in word_confidences) / len(word_confidences)
            
            # Scale variance to 0-1 range, higher variance = more noise
            noise_level = min(variance * 10, 1.0)
            return round(1 - noise_level, 2)  # Invert so 1.0 = clear, 0.0 = noisy
            
        except Exception as e:
            raise ProcessingError(f"Noise level estimation failed: {str(e)}")

    def _calculate_topic_similarity(self, topic1: str, topic2: str) -> float:
        """
        Calculate semantic similarity between two topics.

        Args:
            topic1: First topic string
            topic2: Second topic string

        Returns:
            Similarity score between 0.0 and 1.0

        Raises:
            ProcessingError: If similarity calculation fails
        """
        try:
            prompt = f"""
            Rate the semantic similarity between these topics (0.0 to 1.0):
            Topic 1: {topic1}
            Topic 2: {topic2}
            Return only the float value.
            """
            
            similarity = float(self._generate_content(prompt).strip())
            return max(min(similarity, 1.0), 0.0)
            
        except Exception as e:
            raise ProcessingError(f"Topic similarity calculation failed: {str(e)}")

    def _extract_word_confidences(self, transcript: Dict[str, Any]) -> List[float]:
        """
        Extract word-level confidence scores from transcript.

        Args:
            transcript: Transcript data

        Returns:
            List of confidence scores

        Raises:
            ProcessingError: If confidence extraction fails
        """
        try:
            confidences = []
            results = transcript.get("results", {}).get("transcript", {}).get("results", [])
            
            for result in results:
                for alt in result.get("alternatives", []):
                    for word in alt.get("words", []):
                        if "confidence" in word:
                            confidences.append(float(word["confidence"]))
            
            return confidences
            
        except Exception as e:
            raise ProcessingError(f"Word confidence extraction failed: {str(e)}")

    def _validate_entity(self, entity: Dict[str, Any], category: str) -> bool:
        """
        Validate extracted named entity.

        Args:
            entity: Entity data
            category: Entity category

        Returns:
            True if entity is valid, False otherwise
        """
        try:
            required_fields = {"text", "confidence"}
            if not all(field in entity for field in required_fields):
                return False
                
            # Validate confidence score
            if not isinstance(entity["confidence"], (int, float)):
                return False
                
            if not (0 <= entity["confidence"] <= 1):
                return False
                
            # Validate text
            if not isinstance(entity["text"], str) or not entity["text"].strip():
                return False
                
            return True
            
        except Exception:
            return False

    def _get_default_language_metrics(self) -> Dict[str, Any]:
        """
        Get default language analysis metrics.

        Returns:
            Dict containing default language analysis values
        """
        return {
            "formality_level": 5,
            "tone": "neutral",
            "complexity": {
                "vocabulary_level": 5,
                "sentence_complexity": 5,
                "technical_density": 5,
                "readability_score": 5
            },
            "jargon": {},
            "rhetorical_devices": []
        }

    def _analyze_tone(self, text: List[str]) -> str:
        """
        Analyze tone of the text.

        Args:
            text: List of text segments

        Returns:
            Identified tone
        """
        try:
            combined_text = " ".join(text)
            prompt = f"""
            Analyze the tone of this text. Return a single word describing the dominant tone 
            (e.g., professional, casual, academic, enthusiastic, skeptical, neutral).
            
            Text: {combined_text}
            
            Return only the tone word, no other text.
            """
            
            return self._generate_content(prompt).strip().lower()
        except Exception as e:
            logger.error(f"Error analyzing tone: {str(e)}")
            return "neutral"

    def _assess_complexity(self, text: List[str]) -> Dict[str, int]:
        """
        Assess text complexity metrics.

        Args:
            text: List of text segments

        Returns:
            Dict containing complexity metrics
        """
        try:
            combined_text = " ".join(text)
            prompt = f"""
            Analyze the complexity of this text. Return a JSON object with these metrics:
            1. vocabulary_level (1-10)
            2. sentence_complexity (1-10)
            3. technical_density (1-10)
            4. readability_score (1-10)
            
            Text: {combined_text}
            """
            
            metrics = self._generate_content(prompt, response_type='json')
            return {
                k: min(max(int(v), 1), 10)
                for k, v in metrics.items()
            }
        except Exception as e:
            logger.error(f"Error assessing complexity: {str(e)}")
            return {
                "vocabulary_level": 5,
                "sentence_complexity": 5,
                "technical_density": 5,
                "readability_score": 5
            }
        
    def format_timestamp(self, seconds: int, nanos: int) -> str:
        """
        Convert time values to HH:MM:SS format.
        
        Args:
            seconds: Number of seconds
            nanos: Number of nanoseconds
            
        Returns:
            Formatted timestamp string
        """
        total_seconds = seconds + (nanos / 1e9)
        return str(timedelta(seconds=total_seconds)).split('.')[0]

    def format_transcript_with_timestamps(self, transcript_data: Dict[str, Any]) -> str:
        """
        Format transcript with timestamp markers.
        
        Args:
            transcript_data: Raw transcript data
            
        Returns:
            Formatted transcript with timestamps
            
        Raises:
            ProcessingError: If formatting fails
        """
        try:
            formatted_segments = []
            file_result = next(iter(transcript_data['results'].values()))
            results = file_result.get('transcript', {}).get('results', [])
            
            for result in results:
                if 'alternatives' in result and result['alternatives']:
                    text = result['alternatives'][0]['transcript']
                    end_time = float(result.get('resultEndOffset', '0s').rstrip('s'))
                    formatted_segments.append(f"[{end_time:.2f}s] {text}")
            
            return "\n".join(formatted_segments)
        except Exception as e:
            raise ProcessingError(f"Transcript formatting failed: {str(e)}")

    def _get_entity_contexts(self, entity: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get contextual information for entity mentions.

        Args:
            entity: Entity to find contexts for
            data: Transcript data

        Returns:
            List of context information for entity occurrences
        """
        try:
            contexts = []
            segments = data.get("sentiment_over_time", [])
            entity_lower = entity.lower()
            
            for i, segment in enumerate(segments):
                summary = segment.get("summary", "")
                if entity_lower in summary.lower():
                    context = {
                        "text": summary,
                        "time": segment.get("time", 0),
                        "confidence": segment.get("confidence", 0),
                        "sentiment": segment.get("sentiment_score", 0),
                        "surrounding_context": {
                            "before": segments[i-1].get("summary", "") if i > 0 else "",
                            "after": segments[i+1].get("summary", "") if i < len(segments)-1 else ""
                        }
                    }
                    contexts.append(context)
            
            return sorted(contexts, key=lambda x: x["confidence"], reverse=True)
        except Exception as e:
            logger.error(f"Error getting entity contexts: {str(e)}")
            return []

    def create_recognition_config(
        self, 
        audio_config: Dict[str, Any]
    ) -> speech.RecognitionConfig:
        """
        Create speech recognition configuration.

        Args:
            audio_config: Audio configuration parameters

        Returns:
            Speech recognition configuration object
        """
        return speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=audio_config["sample_rate"],
            language_code="en-US",
            enable_word_time_offsets=True,
            enable_automatic_punctuation=True,
            model="video"
        )

    def _get_topic_time_ranges(self, topic: str, data: Dict[str, Any]) -> List[Dict[str, float]]:
        """
        Get time ranges where a specific topic is discussed.

        Args:
            topic: Topic to find
            data: Transcript data

        Returns:
            List of time ranges where topic appears
        """
        try:
            segments = data.get("sentiment_over_time", [])
            if not segments:
                return []
            
            ranges = []
            current_range = None
            
            for segment in segments:
                if topic.lower() in segment.get("summary", "").lower():
                    if not current_range:
                        current_range = {"start": segment.get("time", 0)}
                    current_range["end"] = segment.get("time", 0)
                elif current_range:
                    ranges.append(current_range)
                    current_range = None
            
            if current_range:
                ranges.append(current_range)
            
            return ranges
        except Exception as e:
            logger.error(f"Error getting topic time ranges: {str(e)}")
            return []

    def _extract_key_phrases(self, topic: str, data: Dict[str, Any]) -> List[str]:
        """
        Extract key phrases related to a specific topic.

        Args:
            topic: Topic to find phrases for
            data: Transcript data

        Returns:
            List of key phrases related to the topic
        """
        try:
            segments = data.get("sentiment_over_time", [])
            if not segments:
                return []
            
            topic_segments = [
                s.get("summary", "") for s in segments 
                if topic.lower() in s.get("summary", "").lower()
            ]
            
            key_phrases = set()
            for segment in topic_segments:
                words = segment.split()
                for i in range(len(words)):
                    for j in range(i + 2, min(i + 5, len(words) + 1)):
                        phrase = " ".join(words[i:j])
                        if topic.lower() in phrase.lower():
                            key_phrases.add(phrase)
            
            return list(key_phrases)[:5]
        except Exception as e:
            logger.error(f"Error extracting key phrases: {str(e)}")
            return []

    def format_final_output(self, processed_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format the final processed content.
        
        Args:
            processed_content: Raw processed content
            
        Returns:
            Formatted output dictionary
        """
        try:
            return {
                "transcript_analysis": {
                    "executive_summary": processed_content.get("transcript_analysis", {}).get("executive_summary", ""),
                    "topics": processed_content.get("transcript_analysis", {}).get("topic_distribution", []),
                    "sentiment": processed_content.get("transcript_analysis", {}).get("sentiment_over_time", []),
                    "key_arguments": processed_content.get("transcript_analysis", {}).get("arguments", []),
                    "entities": processed_content.get("transcript_analysis", {}).get("named_entities", {}),
                    "language_metrics": processed_content.get("transcript_analysis", {}).get("language_analysis", {}),
                    "metadata": processed_content.get("transcript_analysis", {}).get("metadata", {})
                }
            }
        except Exception as e:
            logger.error(f"Error formatting output: {str(e)}")
            return {"error": str(e)}

    def create_logical_segments(self, processed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create meaningful segments based on content understanding."""
        try:
            # Load processed.json if we got a path instead of data
            if isinstance(processed_data, str):
                with open(processed_data, 'r') as f:
                    processed_data = json.load(f)
            
            # Get output directory
            base_dir = os.path.dirname(
                processed_data["paths"]["processed"] if isinstance(processed_data, dict) and "paths" in processed_data
                else processed_data
            )
            
            # Create analysis file path
            video_name = os.path.basename(base_dir)
            analysis_path = os.path.join(base_dir, f"{video_name}_analysis.json")
            
            # First, get Gemini to identify meaningful segments
            prompt = f"""
            You are a video content analyzer. Analyze this transcript and identify the most impactful segments.
            
            Requirements:
            1. Each segment must be a complete thought/concept (15-60 seconds)
            2. Must be highly quotable and meaningful
            3. Must use EXACT text from the transcript for timing matching
            4. Include context and impact score for each segment
            
            Return ONLY a JSON array in this exact format:
            [
                {{
                    "text": "exact transcript text...",
                    "topic": "what this segment is about",
                    "impact_score": 0.9,  # how meaningful/quotable (0.0-1.0)
                    "context": "why this segment matters"
                }}
            ]
            
            Transcript:
            {processed_data.get('transcript', '')}
            """

            logger.debug("Sending segment identification prompt to Gemini")
            segments = self._generate_content(prompt, response_type='json')
            if not segments:
                logger.error("No segments returned from Gemini")
                return []

            logger.debug(f"Got {len(segments)} segments from Gemini")

            # Match segments with word timings
            timed_segments = []
            words = processed_data.get("words", [])
            
            for segment in segments:
                text = segment["text"].strip()
                # Find first and last word in segment
                start_idx = None
                end_idx = None
                
                # Create a list of words from the segment text
                segment_words = text.lower().split()
                
                # Find the start index with better matching
                for i, word_info in enumerate(words):
                    if word_info["word"].lower() == segment_words[0]:
                        # Check if next few words match to ensure correct start
                        if all(words[i+j]["word"].lower() == segment_words[j] 
                              for j in range(min(3, len(segment_words))) 
                              if i+j < len(words)):
                            start_idx = i
                            break
                
                # Find the end index with better matching
                if start_idx is not None:
                    for i in range(len(words)-1, start_idx, -1):
                        if words[i]["word"].lower() == segment_words[-1]:
                            # Check if previous few words match to ensure correct end
                            if all(words[i-j]["word"].lower() == segment_words[-(j+1)]
                                  for j in range(min(3, len(segment_words)))
                                  if i-j >= 0):
                                end_idx = i
                                break
                
                if start_idx is not None and end_idx is not None:
                    segment_words = words[start_idx:end_idx + 1]
                    duration = float(segment_words[-1]["endOffset"].rstrip('s')) - float(segment_words[0]["startOffset"].rstrip('s'))
                    
                    # Only add segments within reasonable duration (15-60 seconds)
                    if 15 <= duration <= 60:
                        timed_segments.append({
                            "text": text,
                            "topic": segment["topic"],
                            "impact_score": segment["impact_score"],
                            "context": segment["context"],
                            "start_time": float(segment_words[0]["startOffset"].rstrip('s')),
                            "end_time": float(segment_words[-1]["endOffset"].rstrip('s')),
                            "duration": duration,
                            "words": segment_words,
                            "analysis": {
                                "sentiment": self._analyze_sentiment(text),
                                "entities": self._perform_named_entity_recognition(text),
                                "language_metrics": self._analyze_language(text)
                            }
                        })

            # Save analysis file with metadata and original analysis
            analysis_data = {
                "segments": timed_segments,
                "metadata": {
                    "title": video_name,
                    "analysis_timestamp": datetime.now().isoformat(),
                    "segment_count": len(timed_segments),
                    "total_duration": sum(s["duration"] for s in timed_segments)
                },
                "transcript_analysis": {
                    "topics": self._analyze_topic_distribution(processed_data, None),
                    "sentiment": self._analyze_sentiment_over_time(processed_data, None),
                    "entities": self._perform_named_entity_recognition(processed_data.get("transcript", "")),
                    "language_metrics": self._analyze_language(processed_data.get("transcript", ""))
                }
            }
            
            with open(analysis_path, 'w') as f:
                json.dump(analysis_data, f, indent=2)
            
            logger.info(f"Created {len(timed_segments)} logical segments")
            logger.info(f"Analysis saved to: {analysis_path}")

            return timed_segments

        except Exception as e:
            logger.error(f"Error creating logical segments: {str(e)}")
            return []

    def search_transcript_segments(
        self,
        search_concept: str,
        transcript_data: Dict[str, Any]
    ) -> List[ClipSuggestion]:
        """Search transcript for segments matching a concept."""
        try:
            # First create logical segments
            segments = self.create_logical_segments(transcript_data)
            
            # Then search through these segments
            prompt = f"""
            Find segments that discuss: "{search_concept}"
            
            For each relevant segment, provide:
            1. How well it matches the concept (0.0-1.0)
            2. Why it's relevant
            3. The specific aspect/subtopic it covers

            Return matches as JSON array:
            [{{
                "index": segment_number,
                "confidence": match_score,
                "explanation": "why relevant...",
                "topic": "specific aspect..."
            }}]

            Available segments:
            {json.dumps([{
                "index": i,
                "text": s["text"],
                "topic": s["topic"],
                "context": s["context"]
            } for i, s in enumerate(segments)])}
            """

            matches = self._generate_content(prompt, response_type='json')
            
            # Convert matches to clip suggestions
            suggestions = []
            for match in matches:
                segment = segments[match["index"]]
                suggestions.append(
                    ClipSuggestion(
                        text=segment["text"],
                        start_time=segment["start_time"],
                        end_time=segment["end_time"],
                        confidence=float(match["confidence"]),
                        explanation=match["explanation"],
                        topic=match["topic"]
                    )
                )

            return suggestions

        except Exception as e:
            logger.error(f"Error searching segments: {str(e)}")
            return []