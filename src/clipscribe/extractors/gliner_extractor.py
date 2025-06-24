"""
GLiNER (Generalist and Lightweight Model for Named Entity Recognition) extractor.

Extracts custom entity types from text using GLiNER model.
This enables detecting domain-specific entities like military hardware, operations, etc :-)
"""

import logging
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass

import torch
from gliner import GLiNER

from ..models import VideoIntelligence, Entity

logger = logging.getLogger(__name__)


@dataclass  
class CustomEntity:
    """Represents a custom entity detected by GLiNER."""
    text: str
    label: str
    start: int
    end: int
    confidence: float


class GLiNERExtractor:
    """
    Extract custom entity types using GLiNER model.
    
    GLiNER can detect ANY entity type you specify, not just standard NER labels.
    Perfect for domain-specific entity extraction :-)
    """
    
    # Default entity labels for video intelligence
    DEFAULT_LABELS = [
        # Standard entities
        "person", "organization", "location", "date", "time", 
        "money", "percentage", "product", "event",
        
        # Military/Defense
        "weapon", "military_unit", "operation", "military_hardware",
        "military_rank", "military_base", "conflict",
        
        # Technology
        "software", "hardware", "technology", "algorithm", "model",
        "framework", "programming_language", "api", "protocol",
        
        # Business/Finance
        "company", "stock_symbol", "financial_metric", "market",
        "investment", "currency", "economic_indicator",
        
        # Media/Content
        "movie", "book", "song", "game", "show", "character",
        "genre", "platform", "channel",
        
        # Science/Medical
        "disease", "symptom", "treatment", "drug", "medical_procedure",
        "chemical", "biological_entity", "scientific_concept"
    ]
    
    def __init__(self, model_name: str = "urchade/gliner_multi-v2.1", device: str = "auto"):
        """
        Initialize GLiNER extractor.
        
        Args:
            model_name: HuggingFace model name (default: urchade/gliner_multi-v2.1)
            device: Device to run on ("auto", "cpu", "cuda", "mps") 
        """
        self.model_name = model_name
        self.device = self._get_device(device)
        self.model = None
        self._load_model()
        
    def _get_device(self, device: str) -> str:
        """Determine the best device to use."""
        if device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif torch.backends.mps.is_available():
                return "mps"  # Apple Silicon
            else:
                return "cpu"
        return device
        
    def _load_model(self):
        """Load the GLiNER model."""
        try:
            logger.info(f"Loading GLiNER model {self.model_name} on {self.device}...")
            
            # Load model
            self.model = GLiNER.from_pretrained(self.model_name)
            
            # Move to device
            if self.device != "cpu":
                self.model = self.model.to(self.device)
                
            logger.info("GLiNER model loaded successfully :-)")
            
        except Exception as e:
            logger.error(f"Failed to load GLiNER model: {e}")
            raise
            
    def extract_entities(
        self, 
        text: str, 
        labels: Optional[List[str]] = None,
        threshold: float = 0.5,
        flat_ner: bool = True
    ) -> List[CustomEntity]:
        """
        Extract custom entities from text.
        
        Args:
            text: Input text to extract entities from
            labels: Entity types to detect (uses defaults if None)
            threshold: Confidence threshold for entity detection
            flat_ner: Whether to use flat NER (no nested entities)
            
        Returns:
            List of detected entities
        """
        if not self.model:
            raise RuntimeError("Model not loaded")
            
        if labels is None:
            labels = self.DEFAULT_LABELS
            
        entities = []
        
        # Chunk long text to avoid truncation
        chunks = self._chunk_text(text, max_length=2000)  # Conservative chunk size
        
        for chunk_idx, (chunk_text, chunk_offset) in enumerate(chunks):
            try:
                # GLiNER expects a single string, not a list
                # Predict entities directly from the text chunk
                predictions = self.model.predict_entities(
                    chunk_text,
                    labels,
                    threshold=threshold,
                    flat_ner=flat_ner
                )
                
                # Parse results - predictions is a list of entity dicts
                for entity in predictions:
                    if isinstance(entity, dict) and all(key in entity for key in ["text", "label"]):
                        entities.append(CustomEntity(
                            text=entity["text"],
                            label=entity["label"],
                            start=entity.get("start", 0) + chunk_offset,
                            end=entity.get("end", 0) + chunk_offset,
                            confidence=entity.get("score", 0.9)
                        ))
                        
            except Exception as e:
                logger.warning(f"GLiNER extraction warning in chunk {chunk_idx} (non-critical): {e}")
                # Continue with next chunk instead of failing
                continue
            
        # Remove duplicates and filter
        unique_entities = self._deduplicate_entities(entities)
        
        logger.info(f"Extracted {len(unique_entities)} custom entities from {len(chunks)} chunks :-)")
        return unique_entities
        
    def extract_domain_specific(
        self,
        text: str,
        domain: str = "general"
    ) -> List[CustomEntity]:
        """
        Extract domain-specific entities.
        
        Args:
            text: Input text
            domain: Domain type (military, tech, finance, medical, etc.)
            
        Returns:
            List of domain-specific entities
        """
        # Define domain-specific labels
        domain_labels = {
            "military": [
                "weapon", "military_unit", "operation", "military_hardware",
                "military_rank", "military_base", "conflict", "defense_contractor",
                "missile_system", "aircraft", "naval_vessel", "military_exercise"
            ],
            "tech": [
                "software", "hardware", "algorithm", "framework", "api",
                "programming_language", "cloud_service", "database", "protocol",
                "vulnerability", "cyber_attack", "tech_company", "startup"
            ],
            "finance": [
                "stock_symbol", "financial_metric", "investment", "market",
                "cryptocurrency", "exchange", "financial_instrument", "rating_agency",
                "economic_indicator", "central_bank", "fund", "index"
            ],
            "medical": [
                "disease", "symptom", "treatment", "drug", "medical_procedure",
                "medical_device", "vaccine", "clinical_trial", "hospital",
                "medical_condition", "diagnostic_test", "therapeutic_method"
            ]
        }
        
        # Get labels for domain
        labels = domain_labels.get(domain, self.DEFAULT_LABELS)
        
        # Add general labels too
        general_labels = ["person", "organization", "location", "date", "time"]
        labels = list(set(labels + general_labels))
        
        return self.extract_entities(text, labels)
        
    def _chunk_text(self, text: str, max_length: int = 2000) -> List[tuple[str, int]]:
        """
        Split text into chunks at sentence boundaries.
        
        Returns list of (chunk_text, offset) tuples.
        """
        import re
        
        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        current_offset = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            # If adding this sentence would exceed max_length, save current chunk
            if current_length + sentence_length > max_length and current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunks.append((chunk_text, current_offset))
                
                # Start new chunk
                current_offset += current_length + 1  # +1 for space
                current_chunk = [sentence]
                current_length = sentence_length
            else:
                current_chunk.append(sentence)
                current_length += sentence_length + 1  # +1 for space
        
        # Add final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append((chunk_text, current_offset))
        
        return chunks
    
    def _deduplicate_entities(self, entities: List[CustomEntity]) -> List[CustomEntity]:
        """Remove duplicate and overlapping entities."""
        # Sort by start position
        sorted_entities = sorted(entities, key=lambda x: (x.start, -x.confidence))
        
        # Remove overlaps, keeping higher confidence
        kept = []
        for entity in sorted_entities:
            # Check if overlaps with any kept entity
            overlap = False
            for kept_entity in kept:
                if (entity.start >= kept_entity.start and entity.start < kept_entity.end) or \
                   (entity.end > kept_entity.start and entity.end <= kept_entity.end):
                    overlap = True
                    break
                    
            if not overlap:
                kept.append(entity)
                
        return kept
        
    def extract_from_video_intelligence(
        self,
        video_intel: VideoIntelligence,
        domain: Optional[str] = None
    ) -> VideoIntelligence:
        """
        Extract custom entities from a VideoIntelligence object.
        
        Args:
            video_intel: VideoIntelligence object with transcript
            domain: Optional domain for specialized extraction
            
        Returns:
            Updated VideoIntelligence with custom entities
        """
        if not video_intel.transcript:
            logger.warning("No transcript found in VideoIntelligence")
            return video_intel
            
        # Extract entities based on domain
        transcript_text = video_intel.transcript.full_text
        if domain:
            entities = self.extract_domain_specific(transcript_text, domain)
        else:
            entities = self.extract_entities(transcript_text)
            
        # Merge with existing entities
        existing_entities = {(e.name.lower(), e.type.lower()) for e in video_intel.entities}
        
        for entity in entities:
            key = (entity.text.lower(), entity.label.lower())
            if key not in existing_entities:
                video_intel.entities.append(Entity(
                    name=entity.text,
                    type=entity.label,
                    confidence=entity.confidence
                ))
                existing_entities.add(key)
                
        logger.info(f"Added {len(entities)} custom entities to VideoIntelligence :-)")
        return video_intel
        
    def analyze_entity_distribution(self, entities: List[CustomEntity]) -> Dict[str, int]:
        """Analyze the distribution of entity types."""
        distribution = {}
        for entity in entities:
            distribution[entity.label] = distribution.get(entity.label, 0) + 1
        return dict(sorted(distribution.items(), key=lambda x: x[1], reverse=True)) 