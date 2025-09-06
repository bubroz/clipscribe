"""
Batch Extractor - Gemini removed, functionality moved to HybridProcessor.

This dramatically reduces API calls and token usage by doing everything at once 
"""

import json
import logging
from typing import Dict, Any
from datetime import datetime

import google.generativeai as genai
from google.generativeai.types import RequestOptions

logger = logging.getLogger(__name__)


class BatchExtractor:
    """
    Extract everything - Gemini removed, functionality deprecated.

    Instead of 6 separate API calls, we do it all in one shot!
    This saves tokens, time, and money
    """

    def __init__(self, model_name: str = "deprecated", timeout: int = 600):
        """Initialize the batch extractor."""
        self.model_name = model_name
        self.timeout = timeout

        # Gemini configuration removed
        genai.configure(api_key=None)  # Uses GOOGLE_API_KEY env var
        self.model = genai.GenerativeModel(model_name)

    async def extract_all_from_media(
        self, media_file, media_type: str = "audio", duration_seconds: int = 0
    ) -> Dict[str, Any]:
        """
        Extract transcript, key points, summary, entities, topics, and relationships in ONE call.

        This is 6x more efficient than separate calls!
        """
        prompt = self._build_mega_prompt(media_type)

        start_time = datetime.now()

        try:
            # One call to rule them all!
            response = await self.model.generate_content_async(
                [media_file, prompt],
                generation_config={"response_mime_type": "application/json"},
                request_options=RequestOptions(timeout=self.timeout),
            )

            # Parse the comprehensive response
            result = json.loads(response.text)

            # Add metadata
            processing_time = (datetime.now() - start_time).total_seconds()
            result["processing_time"] = processing_time
            result["processing_cost"] = self._calculate_cost(duration_seconds, len(response.text))

            logger.info(f"Batch extraction completed in {processing_time:.1f}s")
            return result

        except Exception as e:
            logger.error(f"Batch extraction failed: {e}")
            raise

    def _build_mega_prompt(self, media_type: str) -> str:
        """Build the comprehensive extraction prompt."""
        media_instructions = (
            """Analyze this video and provide:
1. A complete transcript of all spoken words
2. Descriptions of important visual elements (slides, code, diagrams)
3. Note any on-screen text or annotations"""
            if media_type == "video"
            else "Transcribe this audio completely and accurately."
        )

        return f"""
{media_instructions}

Then extract ALL of the following in a single JSON response:

{{
    "transcript": {{
        "full_text": "Complete verbatim transcription...",
        "segments": [
            {{"start": 0, "end": 30, "text": "Segment text..."}}
        ],
        "speaker_count": 1,
        "language": "en"
    }},
    
    "key_points": [
        {{
            "timestamp": 120,
            "text": "Key point text",
            "importance": 0.9,
            "context": "Additional context"
        }}
    ],
    
    "summary": {{
        "text": "Executive summary under 300 words",
        "main_topics": ["topic1", "topic2"],
        "key_takeaways": ["takeaway1", "takeaway2"]
    }},
    
    "entities": [
        {{
            "name": "Entity Name",
            "type": "PERSON|ORGANIZATION|LOCATION|EVENT|TECHNOLOGY|PRODUCT",
            "confidence": 0.95,
            "mentions": 3,
            "first_mention_timestamp": 45
        }}
    ],
    
    "topics": [
        {{
            "name": "Topic name",
            "relevance": 0.9,
            "keywords": ["keyword1", "keyword2"]
        }}
    ],
    
    "relationships": [
        {{
            "subject": "Entity1",
            "predicate": "specific action/relationship",
            "object": "Entity2",
            "timestamp": 120,
            "confidence": 0.95
        }}
    ],
    
    "sentiment": {{
        "overall": "positive|negative|neutral",
        "score": 0.8,
        "emotions": ["informative", "technical", "enthusiastic"]
    }},
    
    "quality_metrics": {{
        "audio_quality": "high|medium|low",
        "content_density": 0.8,
        "technical_level": "beginner|intermediate|advanced"
    }}
}}

IMPORTANT:
- Extract 30-50 key points for hour-long content
- Include ALL entities mentioned (people, companies, technologies)
- Focus on SPECIFIC relationship predicates (not generic like "mentioned")
- Be comprehensive - it's better to include too much than too little
"""

    def _calculate_cost(self, duration_seconds: int, output_chars: int) -> float:
        """Calculate the cost for batch processing."""
        # Audio processing cost
        audio_minutes = duration_seconds / 60
        audio_cost = audio_minutes * 0.002  # $0.002/min

        # Output token cost (1 token ≈ 4 chars)
        output_tokens = output_chars / 4
        token_cost = (output_tokens / 1_000_000) * 0.50  # $0.50/M output tokens

        return audio_cost + token_cost
