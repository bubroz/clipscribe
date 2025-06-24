"""SpaCy-based entity extractor for zero-cost NER."""

import logging
from typing import List, Dict, Optional, Tuple
import spacy
from spacy.tokens import Doc
import re

from ..models import Entity

logger = logging.getLogger(__name__)


class SpacyEntityExtractor:
    """Extract entities using SpaCy NLP - zero cost, high speed."""
    
    # Entity type mapping from SpaCy to our types
    ENTITY_TYPE_MAP = {
        "PERSON": "PERSON",
        "ORG": "ORGANIZATION",
        "GPE": "LOCATION",      # Geopolitical entities
        "LOC": "LOCATION",      # Locations
        "FAC": "LOCATION",      # Facilities
        "EVENT": "EVENT",
        "PRODUCT": "PRODUCT",
        "WORK_OF_ART": "PRODUCT",
        "LAW": "CONCEPT",
        "LANGUAGE": "CONCEPT",
        "DATE": None,           # Skip dates
        "TIME": None,           # Skip times
        "PERCENT": None,        # Skip percentages
        "MONEY": None,          # Skip money amounts
        "QUANTITY": None,       # Skip quantities
        "ORDINAL": None,        # Skip ordinals
        "CARDINAL": None        # Skip cardinals
    }
    
    def __init__(self, model_name: str = "en_core_web_sm"):
        """
        Initialize SpaCy extractor.
        
        Args:
            model_name: SpaCy model to use (en_core_web_sm is lightweight)
        """
        try:
            self.nlp = spacy.load(model_name)
            logger.info(f"Loaded SpaCy model: {model_name}")
        except OSError:
            logger.warning(f"SpaCy model {model_name} not found. Installing...")
            import subprocess
            subprocess.check_call(["python", "-m", "spacy", "download", model_name])
            self.nlp = spacy.load(model_name)
            
        # Add custom patterns for news entities
        self._add_custom_patterns()
    
    def _add_custom_patterns(self):
        """Add custom entity patterns for news content."""
        # Add ruler for common news patterns
        ruler = self.nlp.add_pipe("entity_ruler", before="ner")
        
        patterns = [
            # Military/Government patterns
            {"label": "ORGANIZATION", "pattern": [{"LOWER": {"IN": ["pentagon", "nato", "un", "iaea"]}}]},
            {"label": "ORGANIZATION", "pattern": [{"TEXT": {"REGEX": "^[A-Z]{2,5}$"}}]},  # Acronyms
            
            # Technology patterns
            {"label": "TECHNOLOGY", "pattern": [{"LOWER": {"IN": ["ai", "llm", "gpt", "gemini"]}}]},
            {"label": "TECHNOLOGY", "pattern": [{"TEXT": {"REGEX": "GPT-\\d+"}}]},
            
            # Military operations
            {"label": "EVENT", "pattern": [{"LOWER": "operation"}, {"IS_TITLE": True}]},
        ]
        
        ruler.add_patterns(patterns)
    
    def extract_entities(
        self, 
        text: str,
        min_confidence: float = 0.0
    ) -> List[Tuple[Entity, float]]:
        """
        Extract entities from text with confidence scores.
        
        Args:
            text: Text to extract entities from
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of (Entity, confidence) tuples
        """
        doc = self.nlp(text)
        entities_with_conf = []
        seen_entities = set()
        
        for ent in doc.ents:
            # Skip if entity type should be ignored
            entity_type = self.ENTITY_TYPE_MAP.get(ent.label_)
            if entity_type is None:
                continue
                
            # Deduplicate
            entity_key = (ent.text.lower(), entity_type)
            if entity_key in seen_entities:
                continue
            seen_entities.add(entity_key)
            
            # Calculate confidence based on various factors
            confidence = self._calculate_confidence(ent, doc)
            
            if confidence >= min_confidence:
                entity = Entity(
                    name=ent.text,
                    type=entity_type,
                    confidence=confidence,
                    properties={
                        "spacy_label": ent.label_,
                        "start_char": ent.start_char,
                        "end_char": ent.end_char
                    }
                )
                entities_with_conf.append((entity, confidence))
        
        # Sort by confidence
        entities_with_conf.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"SpaCy extracted {len(entities_with_conf)} entities from {len(text)} chars")
        return entities_with_conf
    
    def _calculate_confidence(self, ent, doc: Doc) -> float:
        """
        Calculate confidence score for an entity.
        
        Factors:
        - Entity length (longer = more confident)
        - Capitalization (proper nouns)
        - Frequency in document
        - Context words
        """
        confidence = 0.7  # Base confidence for SpaCy
        
        # Length factor (longer entities are often more specific)
        if len(ent.text) > 10:
            confidence += 0.1
        elif len(ent.text) < 3:
            confidence -= 0.1
            
        # Proper noun check
        if ent.text[0].isupper():
            confidence += 0.05
            
        # Frequency factor (mentioned multiple times = more important)
        frequency = doc.text.lower().count(ent.text.lower())
        if frequency > 3:
            confidence += 0.1
        elif frequency == 1:
            confidence -= 0.05
            
        # Known entity types get higher confidence
        if ent.label_ in ["PERSON", "ORG", "GPE"]:
            confidence += 0.05
            
        # Clamp confidence between 0 and 1
        return max(0.0, min(1.0, confidence))
    
    def extract_with_context(
        self,
        text: str,
        context_window: int = 50
    ) -> List[Dict[str, any]]:
        """
        Extract entities with surrounding context.
        
        Useful for validation and disambiguation.
        """
        doc = self.nlp(text)
        entities_with_context = []
        
        for ent in doc.ents:
            entity_type = self.ENTITY_TYPE_MAP.get(ent.label_)
            if entity_type is None:
                continue
                
            # Get context
            start = max(0, ent.start_char - context_window)
            end = min(len(text), ent.end_char + context_window)
            context = text[start:end]
            
            # Highlight entity in context
            entity_start = ent.start_char - start
            entity_end = ent.end_char - start
            context_highlighted = (
                context[:entity_start] + 
                f"**{context[entity_start:entity_end]}**" + 
                context[entity_end:]
            )
            
            entities_with_context.append({
                "entity": ent.text,
                "type": entity_type,
                "context": context_highlighted,
                "confidence": self._calculate_confidence(ent, doc)
            })
            
        return entities_with_context
    
    def get_entity_statistics(self, text: str) -> Dict[str, any]:
        """Get statistics about entities in the text."""
        doc = self.nlp(text)
        
        stats = {
            "total_entities": len(doc.ents),
            "by_type": {},
            "unique_entities": set(),
            "most_frequent": {}
        }
        
        entity_counts = {}
        
        for ent in doc.ents:
            entity_type = self.ENTITY_TYPE_MAP.get(ent.label_)
            if entity_type is None:
                continue
                
            # Count by type
            if entity_type not in stats["by_type"]:
                stats["by_type"][entity_type] = 0
            stats["by_type"][entity_type] += 1
            
            # Track unique entities
            stats["unique_entities"].add(ent.text)
            
            # Count frequency
            if ent.text not in entity_counts:
                entity_counts[ent.text] = 0
            entity_counts[ent.text] += 1
        
        # Get most frequent entities
        sorted_entities = sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)
        stats["most_frequent"] = sorted_entities[:10]
        stats["unique_entities"] = len(stats["unique_entities"])
        
        return stats 