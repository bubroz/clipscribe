"""
REBEL (Relation Extraction By End-to-end Language generation) extractor.

Extracts relationships between entities using the REBEL model.
This enables finding connections like "person works at organization" :-)
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import re
import warnings

import torch
from transformers import pipeline

from ..models import VideoIntelligence, Relationship
from .model_manager import model_manager

logger = logging.getLogger(__name__)


class REBELExtractor:
    """
    Extract relationships between entities using REBEL model.
    
    REBEL can detect relationships like:
    - person -> works_at -> organization
    - company -> headquartered_in -> location
    - person -> founded -> company
    - etc.
    """
    
    def __init__(self, model_name: str = "Babelscape/rebel-large", device: str = "auto"):
        """
        Initialize REBEL extractor.
        
        Args:
            model_name: HuggingFace model name
            device: Device to run on ("auto", "cpu", "cuda", "mps")
        """
        self.model_name = model_name
        self.device = device
        self.triplet_extractor = None
        self._load_model()
        
    def _load_model(self):
        """Load the REBEL model using the model manager."""
        try:
            # Suppress warnings during loading
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self.triplet_extractor = model_manager.get_rebel_model(self.model_name, self.device)
                
        except Exception as e:
            logger.error(f"Failed to load REBEL model: {e}")
            raise
            
    def extract_triplets(self, text: str) -> List[Dict[str, str]]:
        """
        Extract relationship triplets from text.
        
        Args:
            text: Input text
            
        Returns:
            List of triplets with subject, predicate, object
        """
        if not self.triplet_extractor:
            raise RuntimeError("Model not loaded")
            
        # REBEL has a token limit, so chunk the text
        chunks = self._chunk_text(text, max_length=512)
        logger.debug(f"Processing {len(chunks)} text chunks for REBEL extraction")
        
        all_triplets = []
        
        for i, chunk in enumerate(chunks):
            try:
                # Suppress warnings during extraction
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    # Extract triplets from chunk
                    extracted = self.triplet_extractor(chunk)
                    
                    # Parse the output
                    if extracted and len(extracted) > 0:
                        triplets_text = extracted[0]['generated_text']
                        logger.debug(f"Chunk {i}: REBEL output: {triplets_text[:200]}...")
                        triplets = self._parse_triplets(triplets_text)
                        logger.debug(f"Chunk {i}: Parsed {len(triplets)} triplets")
                        all_triplets.extend(triplets)
                    else:
                        logger.debug(f"Chunk {i}: No output from REBEL")
                        
            except Exception as e:
                logger.warning(f"REBEL extraction warning (non-critical) in chunk {i}: {e}")
                continue
                
        # Deduplicate triplets
        unique_triplets = self._deduplicate_triplets(all_triplets)
        
        logger.info(f"Extracted {len(unique_triplets)} unique relationships from {len(all_triplets)} total")
        return unique_triplets
        
    def _parse_triplets(self, text: str) -> List[Dict[str, str]]:
        """Parse REBEL output into structured triplets."""
        triplets = []
        
        # REBEL output format can vary. Try multiple parsing strategies
        
        # Strategy 1: Look for <triplet> tags
        triplet_pattern = r'<triplet>(.*?)</triplet>'
        matches = re.findall(triplet_pattern, text)
        
        if matches:
            logger.debug(f"Found {len(matches)} triplet matches using <triplet> tags")
            for match in matches:
                parts = match.split(' | ')
                if len(parts) == 3:
                    subject, predicate, object_ = parts
                    # Clean up the values
                    subject = subject.strip()
                    predicate = predicate.strip().replace('_', ' ')
                    object_ = object_.strip()
                    
                    # Skip if any part is empty
                    if subject and predicate and object_:
                        triplets.append({
                            'subject': subject,
                            'predicate': predicate,
                            'object': object_
                        })
                        logger.debug(f"Parsed triplet: {subject} | {predicate} | {object_}")
                    else:
                        logger.debug(f"Skipped empty triplet parts: '{subject}' | '{predicate}' | '{object_}'")
                else:
                    logger.debug(f"Skipped malformed triplet with {len(parts)} parts: {match}")
        else:
            # Strategy 2: Parse space-separated format
            # REBEL sometimes outputs: "subject  object  predicate" with double spaces
            logger.debug("No <triplet> tags found, trying space-separated format")
            
            # Split by double space and group into triplets
            parts = [p.strip() for p in text.split('  ') if p.strip()]
            logger.debug(f"Found {len(parts)} parts in space-separated format: {parts[:10]}")
            
            # Try to form triplets from consecutive parts
            i = 0
            while i + 2 < len(parts):
                subject = parts[i]
                middle = parts[i + 1]
                last = parts[i + 2]
                
                # Try both orderings: subject-predicate-object and subject-object-predicate
                # Check if middle part looks like a predicate (usually lowercase or contains 'of', 'in', etc.)
                if any(word in middle.lower() for word in ['of', 'in', 'at', 'by', 'for', 'with', 'to', 'from', 'held', 'born', 'educated']) or middle.islower():
                    # Likely subject-predicate-object
                    predicate = middle
                    object_ = last
                else:
                    # Likely subject-object-predicate
                    object_ = middle
                    predicate = last
                
                # Clean up predicate
                predicate = predicate.replace('_', ' ')
                
                if subject and predicate and object_:
                    triplets.append({
                        'subject': subject,
                        'predicate': predicate,
                        'object': object_
                    })
                    logger.debug(f"Parsed triplet: {subject} | {predicate} | {object_}")
                
                # Move to next potential triplet
                i += 3
                    
        return triplets
        
    def _chunk_text(self, text: str, max_length: int = 512) -> List[str]:
        """Split text into chunks suitable for REBEL."""
        # Simple sentence-based chunking
        sentences = text.split('. ')
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence.split())
            if current_length + sentence_length > max_length and current_chunk:
                chunks.append('. '.join(current_chunk) + '.')
                current_chunk = [sentence]
                current_length = sentence_length
            else:
                current_chunk.append(sentence)
                current_length += sentence_length
                
        if current_chunk:
            chunks.append('. '.join(current_chunk) + '.')
            
        return chunks
        
    def _deduplicate_triplets(self, triplets: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Remove duplicate triplets."""
        seen = set()
        unique = []
        
        for triplet in triplets:
            key = (triplet['subject'].lower(), 
                   triplet['predicate'].lower(), 
                   triplet['object'].lower())
            if key not in seen:
                seen.add(key)
                unique.append(triplet)
                
        return unique
        
    def extract_from_video_intelligence(
        self, 
        video_intel: VideoIntelligence
    ) -> VideoIntelligence:
        """
        Extract relationships from VideoIntelligence object.
        
        Args:
            video_intel: VideoIntelligence with transcript
            
        Returns:
            Updated VideoIntelligence with relationships
        """
        if not video_intel.transcript:
            logger.warning("No transcript found")
            return video_intel
            
        # Extract triplets
        triplets = self.extract_triplets(video_intel.transcript.full_text)
        
        # Get entity names for validation
        entity_names = {e.name.lower() for e in video_intel.entities}
        
        # Convert to Relationship objects
        relationships = []
        for triplet in triplets:
            # Only include if at least one entity is recognized
            if (triplet['subject'].lower() in entity_names or 
                triplet['object'].lower() in entity_names):
                
                rel = Relationship(
                    subject=triplet['subject'],
                    predicate=triplet['predicate'],
                    object=triplet['object'],
                    confidence=0.85,  # REBEL doesn't provide confidence
                    properties={"source": "REBEL"}  # Track source
                )
                relationships.append(rel)
                
        # Add to video intelligence
        if not hasattr(video_intel, 'relationships'):
            video_intel.relationships = []
        video_intel.relationships.extend(relationships)
        
        logger.info(f"Added {len(relationships)} relationships to VideoIntelligence")
        return video_intel
        
    def analyze_relationship_types(
        self, 
        relationships: List[Relationship]
    ) -> Dict[str, int]:
        """Analyze distribution of relationship types."""
        distribution = {}
        for rel in relationships:
            predicate = rel.predicate
            distribution[predicate] = distribution.get(predicate, 0) + 1
        return dict(sorted(distribution.items(), key=lambda x: x[1], reverse=True))
        
    def get_entity_connections(
        self, 
        relationships: List[Relationship], 
        entity_name: str
    ) -> List[Relationship]:
        """Get all relationships involving a specific entity."""
        connections = []
        entity_lower = entity_name.lower()
        
        for rel in relationships:
            if (rel.subject.lower() == entity_lower or 
                rel.object.lower() == entity_lower):
                connections.append(rel)
                
        return connections
    
    def get_total_cost(self) -> float:
        """Get total cost of REBEL operations (always 0 since it's local)."""
        return 0.0 
    
    def extract_relationships(self, text: str, entity_lookup: Dict[str, str]) -> List[Relationship]:
        """
        Extract relationships from text with entity awareness.
        
        This method is called by AdvancedHybridExtractor and uses the entity_lookup
        to ensure relationships are only created between recognized entities.
        
        Args:
            text: Input text to extract relationships from
            entity_lookup: Dictionary mapping entity names (lowercase) to their canonical forms
            
        Returns:
            List of Relationship objects
        """
        # Extract raw triplets
        triplets = self.extract_triplets(text)
        
        # Convert to Relationship objects with entity validation
        relationships = []
        for triplet in triplets:
            # Check if subject and object are in our entity lookup
            subject_lower = triplet['subject'].lower()
            object_lower = triplet['object'].lower()
            
            # Get canonical forms from entity lookup
            canonical_subject = entity_lookup.get(subject_lower, triplet['subject'])
            canonical_object = entity_lookup.get(object_lower, triplet['object'])
            
            # Only create relationship if at least one entity is recognized
            if subject_lower in entity_lookup or object_lower in entity_lookup:
                rel = Relationship(
                    subject=canonical_subject,
                    predicate=triplet['predicate'],
                    object=canonical_object,
                    confidence=0.85,  # REBEL doesn't provide confidence
                    properties={
                        "source": "REBEL",
                        "original_subject": triplet['subject'],
                        "original_object": triplet['object']
                    }
                )
                relationships.append(rel)
                
        logger.info(f"Extracted {len(relationships)} entity-aware relationships from {len(triplets)} triplets")
        return relationships 