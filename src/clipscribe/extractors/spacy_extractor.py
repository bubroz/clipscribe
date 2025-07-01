"""
SpaCy-based entity extractor for ClipScribe.

Uses SpaCy's pre-trained models for basic entity extraction.
This is fast and free but limited to standard entity types :-)
"""

import logging
from typing import List, Tuple, Optional

import spacy
from spacy.language import Language

from ..models import Entity
from .model_manager import model_manager

logger = logging.getLogger(__name__)


class SpacyEntityExtractor:
    """
    Extract entities using SpaCy NLP models.
    
    Fast and efficient for basic entity types:
    - PERSON, ORG, GPE (locations)
    - DATE, TIME, MONEY, PERCENT
    - PRODUCT, EVENT, FAC (facilities)
    """
    
    def __init__(self, model_name: str = "en_core_web_sm"):
        """
        Initialize SpaCy extractor.
        
        Args:
            model_name: SpaCy model to use (default: en_core_web_sm)
        """
        self.model_name = model_name
        self.nlp = None
        self._load_model()
        
    def _load_model(self):
        """Load SpaCy model using the model manager."""
        try:
            self.nlp = model_manager.get_spacy_model(self.model_name)
            logger.info(f"Using SpaCy model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load SpaCy model: {e}")
            logger.info("Installing model...")
            import subprocess
            subprocess.run([
                "python", "-m", "spacy", "download", self.model_name
            ])
            # Try loading again
            self.nlp = model_manager.get_spacy_model(self.model_name)
            
    def extract_entities(self, text: str) -> List[Tuple[Entity, float]]:
        """
        Extract entities from text.
        
        Args:
            text: Input text to extract entities from
            
        Returns:
            List of (Entity, confidence) tuples
        """
        if not self.nlp:
            raise RuntimeError("SpaCy model not loaded")
            
        # Process text
        doc = self.nlp(text)
        
        # Extract entities
        entities = []
        seen_entities = set()  # Track unique entities
        
        for ent in doc.ents:
            # Create unique key
            entity_key = (ent.text.lower(), ent.label_)
            
            if entity_key not in seen_entities:
                seen_entities.add(entity_key)
                
                # Map SpaCy labels to our schema
                entity_type = self._map_entity_type(ent.label_)
                
                # Calculate dynamic confidence based on entity characteristics
                dynamic_confidence = self._calculate_spacy_confidence(ent, doc)
                
                # Create Entity object
                entity = Entity(
                    name=ent.text,
                    type=entity_type,
                    confidence=dynamic_confidence,
                    properties={"source": "SpaCy"}
                )
                
                entities.append((entity, dynamic_confidence))
                
        logger.info(f"Extracted {len(entities)} entities with SpaCy (dynamic confidence)")
        return entities
    
    def _calculate_spacy_confidence(self, ent, doc) -> float:
        """Calculate dynamic confidence for SpaCy entities."""
        base_confidence = 0.75  # Start lower than hardcoded 0.85
        
        # Entity length scoring
        if len(ent.text) >= 3:
            base_confidence += 0.1
        
        # Label confidence (some SpaCy labels are more reliable)
        reliable_labels = {'PERSON', 'ORG', 'GPE', 'DATE', 'MONEY', 'PERCENT'}
        if ent.label_ in reliable_labels:
            base_confidence += 0.1
        
        # Capitalization bonus for proper nouns
        if ent.text.istitle():
            base_confidence += 0.05
        
        # Context scoring - entities appearing multiple times are more likely correct
        entity_count = doc.text.lower().count(ent.text.lower())
        if entity_count > 1:
            base_confidence += min(0.1, entity_count * 0.02)
        
        return min(1.0, base_confidence)
        
    def _map_entity_type(self, spacy_label: str) -> str:
        """Map SpaCy entity labels to our schema."""
        mapping = {
            "PERSON": "person",
            "ORG": "organization", 
            "GPE": "location",  # Geopolitical entity
            "LOC": "location",
            "DATE": "date",
            "TIME": "time",
            "MONEY": "money",
            "PERCENT": "percentage",
            "PRODUCT": "product",
            "EVENT": "event",
            "FAC": "facility",
            "NORP": "group",  # Nationality/religious/political group
            "WORK_OF_ART": "work_of_art",
            "LAW": "law",
            "LANGUAGE": "language",
            "QUANTITY": "quantity",
            "ORDINAL": "ordinal",
            "CARDINAL": "cardinal"
        }
        
        return mapping.get(spacy_label, spacy_label.lower())
        
    def extract_with_context(
        self, 
        text: str, 
        window_size: int = 50
    ) -> List[Tuple[Entity, str]]:
        """
        Extract entities with surrounding context.
        
        Args:
            text: Input text
            window_size: Characters of context on each side
            
        Returns:
            List of (Entity, context) tuples
        """
        if not self.nlp:
            raise RuntimeError("SpaCy model not loaded")
            
        doc = self.nlp(text)
        entities_with_context = []
        
        for ent in doc.ents:
            # Get context window
            start = max(0, ent.start_char - window_size)
            end = min(len(text), ent.end_char + window_size)
            context = text[start:end]
            
            # Create entity
            entity = Entity(
                name=ent.text,
                type=self._map_entity_type(ent.label_),
                confidence=0.85
            )
            
            entities_with_context.append((entity, context))
            
        return entities_with_context
        
    def analyze_entity_distribution(self, text: str) -> dict:
        """
        Analyze the distribution of entity types in text.
        
        Returns:
            Dictionary of entity_type -> count
        """
        entities = self.extract_entities(text)
        
        distribution = {}
        for entity, _ in entities:
            entity_type = entity.type
            distribution[entity_type] = distribution.get(entity_type, 0) + 1
            
        return distribution 