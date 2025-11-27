"""Hybrid entity extractor combining SpaCy (free) with LLM validation (selective)."""

import json
import logging
from typing import Dict, List, Tuple

from ..config.settings import Settings
from ..models import Entity
from .spacy_extractor import SpacyEntityExtractor

logger = logging.getLogger(__name__)


class HybridEntityExtractor:
    """
    Cost-optimized entity extraction using SpaCy + selective LLM validation.

    Based on Chimera's approach:
    - 98.6% cost reduction
    - 20x speed improvement
    - Maintains high accuracy
    """

    def __init__(
        self,
        confidence_threshold: float = 0.8,
        batch_size: int = 20,
        enable_cost_tracking: bool = True,
    ):
        """
        Initialize hybrid extractor.

        Args:
            confidence_threshold: Entities below this confidence go to LLM
            batch_size: Number of entities to validate in one LLM call
            enable_cost_tracking: Track costs in real-time
        """
        self.spacy_extractor = SpacyEntityExtractor()
        # Move import here to avoid circular import
        # Gemini removed - using Voxtral-Grok pipeline
        self.llm_validator = None  # Validator removed
        self.confidence_threshold = confidence_threshold
        self.batch_size = batch_size

        # Get timeout from settings
        Settings()
        # self.request_timeout = settings.gemini_request_timeout  # Gemini removed

        # Cost tracking
        self.enable_cost_tracking = enable_cost_tracking
        self.total_cost = 0.0
        self.entities_processed = 0
        self.llm_validations = 0

        logger.info(f"Initialized hybrid extractor with threshold={confidence_threshold}")

    async def extract_entities(self, text: str, force_llm_validation: bool = False) -> List[Entity]:
        """
        Extract entities using hybrid approach.

        1. Use SpaCy for initial extraction (free)
        2. Filter high-confidence entities
        3. Batch low-confidence entities for LLM validation
        4. Merge results

        Args:
            text: Text to extract entities from
            force_llm_validation: Force LLM validation for all entities

        Returns:
            List of validated entities
        """
        # Step 1: SpaCy extraction (zero cost)
        logger.info("Starting SpaCy entity extraction...")
        spacy_entities = self.spacy_extractor.extract_entities(text)
        self.entities_processed += len(spacy_entities)

        if not spacy_entities:
            logger.warning("No entities found by SpaCy, falling back to LLM")
            return await self._llm_only_extraction(text)

        # Step 2: Separate by confidence
        high_confidence = []
        low_confidence = []

        for entity, confidence in spacy_entities:
            if confidence >= self.confidence_threshold and not force_llm_validation:
                high_confidence.append(entity)
            else:
                low_confidence.append((entity, confidence))

        logger.info(
            f"Entities: {len(high_confidence)} high confidence, {len(low_confidence)} need validation"
        )

        # Step 3: Validate low confidence entities with LLM
        validated_entities = []
        if low_confidence:
            validated = await self._validate_with_llm(low_confidence, text)
            validated_entities.extend(validated)

        # Step 4: Merge results
        all_entities = high_confidence + validated_entities

        # Deduplicate
        seen = set()
        final_entities = []
        for entity in all_entities:
            key = (entity.entity.lower(), entity.type)
            if key not in seen:
                seen.add(key)
                final_entities.append(entity)

        logger.info(f"Extracted {len(final_entities)} total entities")

        if self.enable_cost_tracking:
            self._log_cost_metrics()

        return final_entities

    async def _validate_with_llm(
        self, entities: List[Tuple[Entity, float]], full_text: str
    ) -> List[Entity]:
        """
        Validate low-confidence entities using LLM.

        Batches multiple entities in one request for efficiency.
        """
        validated = []

        # Process in batches
        for i in range(0, len(entities), self.batch_size):
            batch = entities[i : i + self.batch_size]

            # LLM validation removed - using Voxtral-Grok pipeline
            # Fall back to including all entities with adjusted confidence
            for entity, conf in batch:
                entity.confidence = conf * 0.8  # Reduce confidence
                validated.append(entity)

        return validated

    def _create_validation_prompt(self, entities: List[Tuple[Entity, float]], context: str) -> str:
        """Create prompt for entity validation."""
        # Take a snippet of context around first mention
        context_snippet = context[:1000] + "..." if len(context) > 1000 else context

        entities_json = [
            {
                "name": ent.entity,
                "type": ent.type,
                "confidence": conf,
                "context": self._get_entity_context(ent.entity, context),
            }
            for ent, conf in entities
        ]

        prompt = f"""Validate these entities extracted from the text. For each entity:
1. Confirm if it's correctly identified
2. Correct the type if wrong
3. Merge duplicates (e.g., "Trump" and "Donald Trump")
4. Add any missing important entities nearby

Context: {context_snippet}

Entities to validate:
{json.dumps(entities_json, indent=2)}

Return a JSON array with validated entities:
[
    {{
        "name": "Full Entity Name",
        "type": "PERSON|ORGANIZATION|LOCATION|EVENT|TECHNOLOGY|CONCEPT|PRODUCT",
        "confidence": 0.95,
        "correct": true,
        "merged_with": []
    }}
]
"""
        return prompt

    def _get_entity_context(self, entity_name: str, text: str, window: int = 100) -> str:
        """Get context around entity mention."""
        idx = text.lower().find(entity_name.lower())
        if idx == -1:
            return ""

        start = max(0, idx - window)
        end = min(len(text), idx + len(entity_name) + window)

        context = text[start:end]
        # Highlight the entity
        context = context.replace(entity_name, f"**{entity_name}**")

        return context

    def _parse_validation_response(
        self, response: str, original_entities: List[Tuple[Entity, float]]
    ) -> List[Entity]:
        """Parse LLM validation response."""
        try:
            # Extract JSON from response
            import re

            json_match = re.search(r"\[.*\]", response, re.DOTALL)
            if not json_match:
                logger.warning("No JSON found in validation response")
                return [ent for ent, _ in original_entities]

            validated_data = json.loads(json_match.group())

            validated_entities = []
            for item in validated_data:
                if item.get("correct", True):
                    entity = Entity(
                        entity=item["name"],
                        type=item["type"],
                        properties={"validated": True},
                    )
                    validated_entities.append(entity)

            return validated_entities

        except Exception as e:
            logger.error(f"Failed to parse validation response: {e}")
            # Return original entities with reduced confidence
            return [ent for ent, _ in original_entities]

    async def _llm_only_extraction(self, text: str) -> List[Entity]:
        """Fallback to LLM-only extraction when SpaCy finds nothing."""

        try:
            # LLM validation removed - using Voxtral-Grok pipeline
            # Returning original batch without validation
            if False:  # Disabled - using Voxtral-Grok pipeline instead

                json_match = None
            if json_match:
                entities_data = json.loads(json_match.group())
                return [
                    Entity(
                        entity=e["name"],
                        type=e["type"],
                        properties={"source": "llm"},
                    )
                    for e in entities_data
                ]
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")

        return []

    def _log_cost_metrics(self):
        """Log cost metrics for monitoring."""
        if self.entities_processed > 0:
            validation_rate = (self.llm_validations / self.entities_processed) * 100
            avg_cost_per_entity = self.total_cost / max(1, self.entities_processed)

            logger.info(
                f"""
Cost Metrics:
- Total entities: {self.entities_processed}
- LLM validations: {self.llm_validations} ({validation_rate:.1f}%)
- Total cost: ${self.total_cost:.4f}
- Cost per entity: ${avg_cost_per_entity:.6f}
- Estimated monthly cost (1M docs): ${avg_cost_per_entity * 1_000_000 * 30:.2f}
"""
            )

    def get_total_cost(self) -> float:
        """Get total cost incurred."""
        return self.total_cost

    def get_statistics(self) -> Dict[str, any]:
        """Get extraction statistics."""
        return {
            "entities_processed": self.entities_processed,
            "llm_validations": self.llm_validations,
            "validation_rate": (self.llm_validations / max(1, self.entities_processed)) * 100,
            "total_cost": self.total_cost,
            "avg_cost_per_entity": self.total_cost / max(1, self.entities_processed),
            "confidence_threshold": self.confidence_threshold,
        }
