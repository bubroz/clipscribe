"""
Web Research Integration for Timeline Building Pipeline.

Provides event context validation and enrichment capabilities for ARGOS v2.17.0.
Integrates with timeline synthesis to validate events against external sources.
"""

import logging
import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

try:
    import google.generativeai as genai
    from google.generativeai.types import RequestOptions

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class ResearchResult:
    """Result from web research validation."""

    event_description: str
    validation_status: str  # "validated", "conflicting", "unverified", "enhanced"
    confidence: float
    external_context: str
    sources_cited: List[str]
    timeline_adjustments: Optional[Dict[str, Any]] = None
    enrichment_data: Optional[Dict[str, Any]] = None


class WebResearchIntegrator:
    """
    Integrates web research capabilities for timeline event validation and enrichment.

    Features:
    - Event context validation against external sources
    - Timeline event enrichment with additional context
    - Cross-reference verification for improved accuracy
    - Smart research query generation from timeline events
    """

    def __init__(self, api_key: Optional[str] = None, enable_research: bool = True):
        """
        Initialize web research integrator.

        Args:
            api_key: Google API key for Gemini research
            enable_research: Whether to enable web research (can disable for testing)
        """
        self.enable_research = enable_research and GEMINI_AVAILABLE
        self.api_key = api_key
        self.research_model = None

        if self.enable_research and api_key:
            try:
                genai.configure(api_key=api_key)
                self.research_model = genai.GenerativeModel("gemini-2.5-flash")
                logger.info("Web research integration enabled with Gemini 2.5 Flash")
            except Exception as e:
                logger.warning(f"Failed to initialize research model: {e}")
                self.enable_research = False
        else:
            logger.info(
                "Web research integration disabled - timeline synthesis will use local validation only"
            )

    async def validate_timeline_events(
        self, timeline_events: List[Dict[str, Any]], collection_context: str
    ) -> List[ResearchResult]:
        """
        Validate timeline events against external sources.

        Args:
            timeline_events: List of timeline events to validate
            collection_context: Context about the video collection

        Returns:
            List of research results with validation status
        """
        if not self.enable_research:
            return self._create_local_validation_results(timeline_events)

        logger.info(f"Validating {len(timeline_events)} timeline events with web research...")
        research_results = []

        # Process events in batches to avoid overwhelming the API
        batch_size = 5
        for i in range(0, len(timeline_events), batch_size):
            batch = timeline_events[i : i + batch_size]
            batch_results = await self._validate_event_batch(batch, collection_context)
            research_results.extend(batch_results)

            # Rate limiting
            await asyncio.sleep(2)

        logger.info(f"Completed validation for {len(research_results)} events")
        return research_results

    async def _validate_event_batch(
        self, events: List[Dict[str, Any]], collection_context: str
    ) -> List[ResearchResult]:
        """Validate a batch of events."""
        if not self.research_model:
            return self._create_local_validation_results(events)

        # Create research query from events
        event_descriptions = [event.get("description", "") for event in events]
        research_query = self._create_research_query(event_descriptions, collection_context)

        try:
            # Use Gemini to research and validate events
            prompt = self._build_validation_prompt(events, collection_context, research_query)

            response = await self.research_model.generate_content_async(
                prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.1,
                    "max_output_tokens": 4096,
                },
                request_options=RequestOptions(timeout=60),
            )

            return self._parse_validation_response(response.text, events)

        except Exception as e:
            logger.error(f"Research validation failed: {e}")
            return self._create_local_validation_results(events)

    def _create_research_query(self, event_descriptions: List[str], context: str) -> str:
        """Create a focused research query from timeline events."""
        # Extract key entities and topics for research
        key_terms = []

        for description in event_descriptions:
            # Simple extraction of proper nouns and important terms
            words = description.split()
            for word in words:
                if word[0].isupper() and len(word) > 3:
                    key_terms.append(word)

        # Remove duplicates and limit to top terms
        unique_terms = list(set(key_terms))[:10]
        query = " ".join(unique_terms)

        return f"{context} {query}"

    def _build_validation_prompt(
        self, events: List[Dict[str, Any]], collection_context: str, research_query: str
    ) -> str:
        """Build prompt for event validation research."""
        events_json = json.dumps(
            [
                {
                    "event_id": event.get("event_id", f"event_{i}"),
                    "timestamp": (
                        event.get("timestamp", "").isoformat()
                        if isinstance(event.get("timestamp"), datetime)
                        else str(event.get("timestamp", ""))
                    ),
                    "description": event.get("description", ""),
                    "involved_entities": event.get("involved_entities", []),
                }
                for i, event in enumerate(events)
            ],
            indent=2,
        )

        return f"""
You are a research analyst validating timeline events from video content analysis.

CONTEXT: {collection_context}
RESEARCH FOCUS: {research_query}

EVENTS TO VALIDATE:
{events_json}

TASK: For each event, determine:

1. VALIDATION STATUS:
   - "validated": Event confirmed by external knowledge
   - "conflicting": Event contradicts known information  
   - "unverified": Cannot confirm or deny with available knowledge
   - "enhanced": Event confirmed and can be enriched with additional context

2. CONFIDENCE (0.0-1.0): How certain you are about the validation

3. EXTERNAL CONTEXT: Additional relevant information about the event

4. TIMELINE ADJUSTMENTS: Any corrections to timing or details

Return JSON:
{{
  "results": [
    {{
      "event_description": "original description",
      "validation_status": "validated|conflicting|unverified|enhanced",
      "confidence": 0.85,
      "external_context": "Additional context from external knowledge",
      "sources_cited": ["general knowledge", "historical records"],
      "timeline_adjustments": {{"corrected_date": "2023-12-15"}},
      "enrichment_data": {{"additional_details": "relevant extra information"}}
    }}
  ]
}}

Focus on factual accuracy and providing valuable context enhancement.
"""

    def _parse_validation_response(
        self, response_text: str, original_events: List[Dict[str, Any]]
    ) -> List[ResearchResult]:
        """Parse research validation response."""
        try:
            response_data = json.loads(response_text)
            results = response_data.get("results", [])

            research_results = []
            for i, result in enumerate(results):
                if i < len(original_events):
                    research_result = ResearchResult(
                        event_description=result.get("event_description", ""),
                        validation_status=result.get("validation_status", "unverified"),
                        confidence=result.get("confidence", 0.5),
                        external_context=result.get("external_context", ""),
                        sources_cited=result.get("sources_cited", []),
                        timeline_adjustments=result.get("timeline_adjustments"),
                        enrichment_data=result.get("enrichment_data"),
                    )
                    research_results.append(research_result)

            return research_results

        except Exception as e:
            logger.error(f"Failed to parse validation response: {e}")
            return self._create_local_validation_results(original_events)

    def _create_local_validation_results(
        self, events: List[Dict[str, Any]]
    ) -> List[ResearchResult]:
        """Create local validation results when web research is disabled."""
        results = []
        for event in events:
            result = ResearchResult(
                event_description=event.get("description", ""),
                validation_status="unverified",  # No external validation available
                confidence=0.6,  # Lower confidence without external validation
                external_context="No external validation performed (web research disabled)",
                sources_cited=["local_extraction"],
                timeline_adjustments=None,
                enrichment_data=None,
            )
            results.append(result)

        return results
