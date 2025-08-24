"""SpaCy-based entity extractor for basic NER functionality."""

import logging
from typing import List, Tuple, Any
from ..models import Entity
from ..utils.optional_deps import optional_deps
from .model_manager import ModelManager

logger = logging.getLogger(__name__)


class SpacyEntityExtractor:
    """Simple SpaCy-based entity extractor."""

    def __init__(self, model_name: str = "en_core_web_sm"):
        """Initialize the SpaCy extractor."""
        self.model_name = model_name
        self.model_manager = ModelManager()
        self.spacy_model = None

    def extract_entities(self, text: str) -> List[Tuple[Entity, float]]:
        """
        Extract entities from text using SpaCy.

        Args:
            text: Text to extract entities from

        Returns:
            List of tuples (entity, confidence_score)
        """
        try:
            # Lazy load SpaCy model
            if self.spacy_model is None:
                self.spacy_model = self.model_manager.get_spacy_model(self.model_name)

            # Process text with SpaCy
            doc = self.spacy_model(text)

            entities = []
            for ent in doc.ents:
                # Convert SpaCy entity to our Entity model
                entity = Entity(
                    entity=ent.text,
                    type=ent.label_.upper(),
                    properties={"source": "spacy", "spacy_label": ent.label_}
                )
                entities.append((entity, 0.8))

            return entities

        except Exception as e:
            logger.warning(f"SpaCy extraction failed: {e}. Returning empty list.")
            return []
