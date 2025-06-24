"""
Advanced Hybrid Extractor combining multiple extraction methods.

This extractor uses:
1. SpaCy for basic NER (free)
2. GLiNER for custom entities
3. REBEL for relationships
4. Selective LLM validation for low-confidence items

This provides comprehensive intelligence extraction while maintaining cost efficiency :-)
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import asyncio
from collections import defaultdict

import networkx as nx
import google.generativeai as genai

from ..models import VideoIntelligence, Entity, Relationship
from .spacy_extractor import SpacyEntityExtractor
from .rebel_extractor import REBELExtractor
from .gliner_extractor import GLiNERExtractor

logger = logging.getLogger(__name__)


class AdvancedHybridExtractor:
    """
    Advanced hybrid extraction combining multiple methods.
    
    Features:
    - Entities from SpaCy + GLiNER + selective LLM
    - Relationships from REBEL
    - Knowledge graph generation
    - Domain-specific extraction
    - Cost optimization
    """
    
    def __init__(
        self,
        use_gliner: bool = True,
        use_rebel: bool = True,
        use_llm: bool = True,
        confidence_threshold: float = 0.7,
        llm_model: str = "gemini-1.5-flash",
        device: str = "auto"
    ):
        """
        Initialize advanced hybrid extractor.
        
        Args:
            use_gliner: Whether to use GLiNER for custom entities
            use_rebel: Whether to use REBEL for relationships
            use_llm: Whether to use LLM for validation
            confidence_threshold: Min confidence before LLM validation
            llm_model: Gemini model for validation
            device: Device for ML models ("auto", "cpu", "cuda", "mps")
        """
        self.use_gliner = use_gliner
        self.use_rebel = use_rebel
        self.use_llm = use_llm
        self.confidence_threshold = confidence_threshold
        self.llm_model = llm_model
        self.device = device
        
        # Initialize extractors
        self.spacy_extractor = SpacyEntityExtractor()
        
        if use_gliner:
            self.gliner_extractor = GLiNERExtractor(device=device)
        else:
            self.gliner_extractor = None
            
        if use_rebel:
            self.rebel_extractor = REBELExtractor(device=device)
        else:
            self.rebel_extractor = None
            
        logger.info(f"Advanced hybrid extractor initialized with GLiNER={use_gliner}, REBEL={use_rebel}, LLM={use_llm} :-)")
        
    async def extract_all(
        self,
        video_intel: VideoIntelligence,
        domain: Optional[str] = None
    ) -> VideoIntelligence:
        """
        Extract all intelligence from video.
        
        Args:
            video_intel: VideoIntelligence with transcript
            domain: Optional domain for specialized extraction
            
        Returns:
            Updated VideoIntelligence with all extractions
        """
        if not video_intel.transcript:
            logger.warning("No transcript found")
            return video_intel
            
        # Track processing stats
        stats = {
            "spacy_entities": 0,
            "gliner_entities": 0,
            "llm_validated": 0,
            "relationships": 0,
            "graph_nodes": 0,
            "graph_edges": 0
        }
        
        # 1. Extract basic entities with SpaCy
        logger.info("Extracting entities with SpaCy...")
        spacy_entities_with_conf = self.spacy_extractor.extract_entities(
            video_intel.transcript.full_text
        )
        # Convert to Entity objects without confidence tuples
        video_intel.entities = [entity for entity, conf in spacy_entities_with_conf]
        stats["spacy_entities"] = len(video_intel.entities)
        
        # 2. Extract custom entities with GLiNER
        if self.use_gliner and self.gliner_extractor:
            logger.info(f"Extracting custom entities with GLiNER (domain={domain})...")
            video_intel = self.gliner_extractor.extract_from_video_intelligence(video_intel, domain)
            stats["gliner_entities"] = len(video_intel.entities) - stats["spacy_entities"]
            
        # 3. Extract relationships with REBEL
        if self.use_rebel and self.rebel_extractor:
            logger.info("Extracting relationships with REBEL...")
            video_intel = self.rebel_extractor.extract_from_video_intelligence(video_intel)
            stats["relationships"] = len(video_intel.relationships)
            
        # 4. Validate low-confidence items with LLM
        if self.use_llm:
            logger.info("Validating low-confidence items with LLM...")
            video_intel = await self._validate_with_llm(video_intel)
            stats["llm_validated"] = sum(1 for e in video_intel.entities if e.confidence > self.confidence_threshold)
            
        # 5. Build knowledge graph
        logger.info("Building knowledge graph...")
        video_intel = self._build_knowledge_graph(video_intel)
        if video_intel.knowledge_graph:
            stats["graph_nodes"] = video_intel.knowledge_graph.get("node_count", 0)
            stats["graph_edges"] = video_intel.knowledge_graph.get("edge_count", 0)
            
        # 6. Extract key facts
        video_intel = self._extract_key_facts(video_intel)
        
        # Update processing stats
        video_intel.processing_stats.update(stats)
        
        logger.info(f"Advanced extraction complete: {stats} :-)")
        return video_intel
        
    async def _validate_with_llm(self, video_intel: VideoIntelligence) -> VideoIntelligence:
        """Validate low-confidence entities and relationships with LLM."""
        # Collect items needing validation
        entities_to_validate = [
            e for e in video_intel.entities 
            if e.confidence < self.confidence_threshold
        ]
        
        relationships_to_validate = [
            r for r in video_intel.relationships
            if r.confidence < self.confidence_threshold
        ]
        
        if not entities_to_validate and not relationships_to_validate:
            return video_intel
            
        try:
            # Configure Gemini
            genai.configure(api_key=None)  # Uses GOOGLE_API_KEY env var
            model = genai.GenerativeModel(self.llm_model)
            
            # Validate entities
            if entities_to_validate:
                prompt = self._build_entity_validation_prompt(entities_to_validate, video_intel.transcript)
                response = await model.generate_content_async(prompt)
                validated = self._parse_entity_validation(response.text, entities_to_validate)
                
                # Update entities
                video_intel.entities = [
                    e for e in video_intel.entities 
                    if e not in entities_to_validate or e in validated
                ]
                
            # Validate relationships  
            if relationships_to_validate:
                prompt = self._build_relationship_validation_prompt(relationships_to_validate, video_intel.transcript)
                response = await model.generate_content_async(prompt)
                validated = self._parse_relationship_validation(response.text, relationships_to_validate)
                
                # Update relationships
                video_intel.relationships = [
                    r for r in video_intel.relationships
                    if r not in relationships_to_validate or r in validated
                ]
                
        except Exception as e:
            logger.error(f"LLM validation failed: {e}")
            
        return video_intel
        
    def _build_knowledge_graph(self, video_intel: VideoIntelligence) -> VideoIntelligence:
        """Build a knowledge graph from entities and relationships."""
        G = nx.DiGraph()
        
        # Add entities as nodes
        for entity in video_intel.entities:
            G.add_node(
                entity.name,
                type=entity.type,
                confidence=entity.confidence
            )
            
        # Add relationships as edges
        for rel in video_intel.relationships:
            G.add_edge(
                rel.subject,
                rel.object,
                predicate=rel.predicate,
                confidence=rel.confidence
            )
            
        # Convert to serializable format
        video_intel.knowledge_graph = {
            "nodes": [
                {
                    "id": node,
                    "type": data.get("type", "unknown"),
                    "confidence": data.get("confidence", 0.9)
                }
                for node, data in G.nodes(data=True)
            ],
            "edges": [
                {
                    "source": u,
                    "target": v,
                    "predicate": data.get("predicate", "related_to"),
                    "confidence": data.get("confidence", 0.9)
                }
                for u, v, data in G.edges(data=True)
            ],
            "node_count": G.number_of_nodes(),
            "edge_count": G.number_of_edges(),
            "connected_components": nx.number_weakly_connected_components(G),
            "density": nx.density(G)
        }
        
        return video_intel
        
    def _extract_key_facts(self, video_intel: VideoIntelligence) -> VideoIntelligence:
        """Extract key facts from relationships."""
        facts = []
        
        for rel in video_intel.relationships:
            # Format as human-readable fact
            fact = f"{rel.subject} {rel.predicate} {rel.object}"
            facts.append({
                "fact": fact,
                "confidence": rel.confidence,
                "subject": rel.subject,
                "predicate": rel.predicate,
                "object": rel.object
            })
            
        # Sort by confidence
        facts.sort(key=lambda x: x["confidence"], reverse=True)
        
        # Store top facts as key moments
        video_intel.key_moments = facts[:20]  # Top 20 facts
        
        return video_intel
        
    def _build_entity_validation_prompt(self, entities: List[Entity], transcript: str) -> str:
        """Build prompt for entity validation."""
        entity_list = "\n".join([f"- {e.name} ({e.type})" for e in entities])
        
        return f"""
Please validate these entities extracted from the video transcript.
Return ONLY the entities that are correctly identified.

Transcript excerpt: {transcript[:1000]}...

Entities to validate:
{entity_list}

For each entity, verify:
1. It actually appears in the transcript
2. The type is correct
3. It's a meaningful entity (not noise)

Return a simple list of validated entities in format: "name (type)"
"""
        
    def _build_relationship_validation_prompt(self, relationships: List[Relationship], transcript: str) -> str:
        """Build prompt for relationship validation."""
        rel_list = "\n".join([f"- {r.subject} | {r.predicate} | {r.object}" for r in relationships])
        
        return f"""
Please validate these relationships extracted from the video transcript.
Return ONLY the relationships that are factually correct based on the transcript.

Transcript excerpt: {transcript[:1000]}...

Relationships to validate:
{rel_list}

For each relationship, verify it's actually stated or strongly implied in the transcript.

Return validated relationships in format: "subject | predicate | object"
"""
        
    def _parse_entity_validation(self, response: str, original: List[Entity]) -> List[Entity]:
        """Parse LLM validation response for entities."""
        validated = []
        response_lower = response.lower()
        
        for entity in original:
            # Check if entity appears in response
            if entity.name.lower() in response_lower:
                entity.confidence = 0.95  # Boost confidence after validation
                validated.append(entity)
                
        return validated
        
    def _parse_relationship_validation(self, response: str, original: List[Relationship]) -> List[Relationship]:
        """Parse LLM validation response for relationships."""
        validated = []
        response_lower = response.lower()
        
        for rel in original:
            # Check if relationship components appear in response
            if (rel.subject.lower() in response_lower and 
                rel.object.lower() in response_lower):
                rel.confidence = 0.95  # Boost confidence after validation
                validated.append(rel)
                
        return validated 