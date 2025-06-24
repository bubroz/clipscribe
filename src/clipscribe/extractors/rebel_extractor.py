"""
REBEL (Relation Extraction By End-to-end Language generation) extractor.

Extracts entity relationships from text using the REBEL model from Babelscape.
This enables building knowledge graphs from video transcripts :-)
"""

import logging
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass

import torch
from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer

from ..models import VideoIntelligence

logger = logging.getLogger(__name__)


@dataclass
class Relationship:
    """Represents a relationship between entities."""
    subject: str
    predicate: str
    object: str
    confidence: float = 0.9
    context: Optional[str] = None


class REBELExtractor:
    """
    Extract entity relationships using REBEL model.
    
    REBEL extracts structured knowledge in the form of (subject, predicate, object)
    triples from natural language text. Perfect for building knowledge graphs :-)
    """
    
    def __init__(self, model_name: str = "Babelscape/rebel-large", device: str = "auto"):
        """
        Initialize REBEL extractor.
        
        Args:
            model_name: HuggingFace model name (default: Babelscape/rebel-large)
            device: Device to run on ("auto", "cpu", "cuda", "mps")
        """
        self.model_name = model_name
        self.device = self._get_device(device)
        self.pipeline = None
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
        """Load the REBEL model."""
        try:
            logger.info(f"Loading REBEL model {self.model_name} on {self.device}...")
            
            # Load model and tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
            
            # Move to device
            if self.device != "cpu":
                self.model = self.model.to(self.device)
                
            # Create pipeline
            self.pipeline = pipeline(
                "text2text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1
            )
            
            logger.info("REBEL model loaded successfully :-)") 
            
        except Exception as e:
            logger.error(f"Failed to load REBEL model: {e}")
            raise
            
    def extract_relations(self, text: str, max_length: int = 512) -> List[Relationship]:
        """
        Extract relationships from text.
        
        Args:
            text: Input text to extract relationships from
            max_length: Maximum length for model input
            
        Returns:
            List of extracted relationships
        """
        if not self.pipeline:
            raise RuntimeError("Model not loaded")
            
        relationships = []
        
        try:
            # Split text into chunks if too long
            chunks = self._split_text(text, max_length)
            
            for chunk in chunks:
                # Generate relations
                outputs = self.pipeline(
                    chunk,
                    max_length=256,
                    num_beams=3,
                    num_return_sequences=3
                )
                
                # Debug logging
                logger.debug(f"Processing chunk ({len(chunk)} chars): {chunk[:50]}...")
                logger.debug(f"REBEL outputs: {outputs}")
                
                # Parse outputs
                for output in outputs:
                    relations = self._parse_rebel_output(output['generated_text'])
                    logger.debug(f"Parsed {len(relations)} relations from: {output['generated_text']}")
                    for rel in relations:
                        # Fix malformed relations first
                        fixed_rel = self._fix_malformed_relation(rel)
                        if fixed_rel and self._is_valid_relation(fixed_rel):
                            relationships.append(Relationship(
                                subject=fixed_rel[0],
                                predicate=fixed_rel[1],
                                object=fixed_rel[2],
                                confidence=0.9,  # REBEL doesn't provide confidence
                                context=chunk[:100]  # First 100 chars as context
                            ))
                            
        except Exception as e:
            logger.error(f"Error extracting relations: {e}")
            
        # Remove duplicates
        unique_relations = self._deduplicate_relations(relationships)
        
        logger.info(f"Extracted {len(unique_relations)} unique relationships :-)") 
        return unique_relations
        
    def _split_text(self, text: str, max_length: int) -> List[str]:
        """Split text into chunks for processing."""
        # Simple sentence-based splitting
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < max_length:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
                
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks
        
    def _parse_rebel_output(self, output: str) -> List[Tuple[str, str, str]]:
        """
        Parse REBEL output format.
        
        REBEL can output relations in different formats:
        1. With tags: <triplet> subject | predicate | object <triplet>
        2. Without tags: subject predicate object (space-separated)
        """
        relations = []
        
        # First try to extract with triplet tags
        if '<triplet>' in output:
            # Extract all triplets
            triplets = output.split('<triplet>')
            
            for triplet in triplets:
                if '|' in triplet:
                    parts = triplet.strip().split('|')
                    if len(parts) == 3:
                        subject = parts[0].strip()
                        predicate = parts[1].strip()
                        obj = parts[2].strip()
                        relations.append((subject, predicate, obj))
        else:
            # Try space-separated format
            # REBEL often outputs multiple triples in a single string
            # Look for common patterns
            
            # Clean the output
            output = output.strip()
            
            # Common entity-relation patterns
            # Try to identify entities (usually proper nouns or multi-word phrases)
            import re
            
            # Split by multiple spaces (REBEL often uses 2+ spaces as delimiter)
            parts = re.split(r'\s{2,}', output)
            
            if len(parts) >= 3:
                # Try to form triples from the parts
                i = 0
                while i + 2 < len(parts):
                    subject = parts[i].strip()
                    predicate = parts[i + 1].strip()
                    obj = parts[i + 2].strip()
                    
                    # Basic validation
                    if subject and predicate and obj:
                        # Check if this looks like a valid triple
                        if len(subject) > 1 and len(predicate) > 1 and len(obj) > 1:
                            relations.append((subject, predicate, obj))
                    
                    # Move to next potential triple
                    i += 3
                    
            # If no triples found with double-space splitting, try another approach
            if not relations:
                # Look for known relation patterns
                relation_patterns = [
                    (r'(\w+(?:\s+\w+)*)\s+(is|was|are|were|has|have|had)\s+(\w+(?:\s+\w+)*)', None),
                    (r'(\w+(?:\s+\w+)*)\s+(located in|president of|capital of|part of|member of)\s+(\w+(?:\s+\w+)*)', None),
                    (r'(\w+(?:\s+\w+)*)\s+(position held|officeholder|instance of|occupation)\s*(\w+(?:\s+\w+)*)?', None),
                ]
                
                for pattern, _ in relation_patterns:
                    matches = re.finditer(pattern, output, re.IGNORECASE)
                    for match in matches:
                        if match.group(3):  # Ensure we have all three parts
                            relations.append((match.group(1), match.group(2), match.group(3)))
                            
        return relations
        
    def _is_valid_relation(self, relation: Tuple[str, str, str]) -> bool:
        """Check if a relation is valid."""
        subject, predicate, obj = relation
        
        # Basic validation
        if not all([subject, predicate, obj]):
            return False
            
        # Filter out too short or too long
        if any(len(x) < 2 or len(x) > 100 for x in [subject, predicate, obj]):
            return False
            
        # Filter out relations with special characters
        special_chars = ['<', '>', '[', ']', '{', '}']
        if any(char in text for text in [subject, predicate, obj] for char in special_chars):
            return False
        
        # Filter out relations where subject is a predicate-like word
        predicate_words = ['part of', 'contains', 'has', 'is', 'was', 'are', 'were', 'member of', 
                          'located in', 'president of', 'capital of', 'instance of', 'occupation',
                          'office held by', 'diplomatic relation', 'affiliated with', 'subsidiary of']
        if subject.lower() in predicate_words:
            return False
            
        return True
        
    def _fix_malformed_relation(self, relation: Tuple[str, str, str]) -> Optional[Tuple[str, str, str]]:
        """Fix common malformations in relationships."""
        subject, predicate, obj = relation
        
        # Common predicates that should not be subjects or objects
        known_predicates = {
            'part of', 'contains', 'has', 'is', 'was', 'are', 'were', 'member of',
            'located in', 'president of', 'capital of', 'instance of', 'occupation',
            'office held by', 'diplomatic relation', 'affiliated with', 'subsidiary of',
            'founded by', 'owned by', 'created by', 'born in', 'died in', 'works for',
            'married to', 'parent of', 'child of', 'sibling of', 'influenced by',
            'succeeded by', 'preceded by', 'contains administrative territorial entity',
            'office held by head of government', 'has part', 'related to'
        }
        
        # Check if predicate and object are swapped (common REBEL error)
        if obj.lower() in known_predicates and predicate.lower() not in known_predicates:
            # Swap predicate and object
            logger.debug(f"Fixing swapped relation: {subject} | {predicate} | {obj} -> {subject} | {obj} | {predicate}")
            return (subject, obj, predicate)
        
        # Check if subject is actually a predicate (another common error)
        if subject.lower() in known_predicates:
            logger.debug(f"Skipping relation with predicate as subject: {subject} | {predicate} | {obj}")
            return None
            
        return relation
        
    def _deduplicate_relations(self, relations: List[Relationship]) -> List[Relationship]:
        """Remove duplicate relationships."""
        seen = set()
        unique = []
        
        for rel in relations:
            key = (rel.subject.lower(), rel.predicate.lower(), rel.object.lower())
            if key not in seen:
                seen.add(key)
                unique.append(rel)
                
        return unique
        
    def extract_from_video_intelligence(self, video_intel: VideoIntelligence) -> VideoIntelligence:
        """
        Extract relationships from a VideoIntelligence object.
        
        Args:
            video_intel: VideoIntelligence object with transcript
            
        Returns:
            Updated VideoIntelligence with relationships
        """
        if not video_intel.transcript:
            logger.warning("No transcript found in VideoIntelligence")
            return video_intel
            
        # Extract relationships
        transcript_text = video_intel.transcript.full_text
        relationships = self.extract_relations(transcript_text)
        
        # Convert to model format
        from ..models import Relationship as ModelRelationship
        video_intel.relationships = [
            ModelRelationship(
                subject=rel.subject,
                predicate=rel.predicate,
                object=rel.object,
                confidence=rel.confidence,
                context=rel.context
            )
            for rel in relationships
        ]
        
        logger.info(f"Added {len(relationships)} relationships to VideoIntelligence :-)") 
        return video_intel 