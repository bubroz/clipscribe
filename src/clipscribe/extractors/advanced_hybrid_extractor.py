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
import os

import networkx as nx
import google.generativeai as genai
from google.generativeai.types import RequestOptions

from ..models import VideoIntelligence, Entity, Relationship
from .spacy_extractor import SpacyEntityExtractor
from .rebel_extractor import REBELExtractor
from .gliner_extractor import GLiNERExtractor
from ..config.settings import Settings
from ..retrievers.gemini_pool import GeminiPool, TaskType

try:
    import torch
    from gliner import GLiNER
    from transformers import pipeline
    ADVANCED_EXTRACTORS_AVAILABLE = True
except ImportError:
    ADVANCED_EXTRACTORS_AVAILABLE = False

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
        device: str = "auto",
        api_key: Optional[str] = None
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
            api_key: Google API key for LLM validation
        """
        self.use_gliner = use_gliner
        self.use_rebel = use_rebel
        self.use_llm = use_llm
        self.confidence_threshold = confidence_threshold
        self.llm_model = llm_model
        self.device = device
        
        # Get settings for timeout
        self.settings = Settings()
        self.request_timeout = self.settings.gemini_request_timeout
        
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
            
        # Initialize GeminiPool for LLM validation
        if api_key:
            genai.configure(api_key=api_key)
            self.pool = GeminiPool(api_key=api_key)
            self.llm_enabled = True
        else:
            self.llm_enabled = False
            logger.warning("No API key provided, LLM validation disabled")
        
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
            # Get a validation model from the pool
            validation_model = self.pool.get_model(TaskType.VALIDATION)
            
            # Validate entities
            if entities_to_validate:
                prompt = self._build_entity_validation_prompt(entities_to_validate, video_intel.transcript.full_text)
                response = await validation_model.generate_content_async(
                    prompt,
                    request_options=RequestOptions(timeout=self.request_timeout)
                )
                validated = self._parse_entity_validation(response.text, entities_to_validate)
                
                # Update entities
                video_intel.entities = [
                    e for e in video_intel.entities 
                    if e not in entities_to_validate or e in validated
                ]
                
            # Validate relationships  
            if relationships_to_validate:
                prompt = self._build_relationship_validation_prompt(relationships_to_validate, video_intel.transcript.full_text)
                response = await validation_model.generate_content_async(
                    prompt,
                    request_options=RequestOptions(timeout=self.request_timeout)
                )
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
        """Extract key facts from relationships and key points."""
        facts = []
        
        # Extract facts from relationships
        for rel in video_intel.relationships:
            # Format as human-readable fact
            fact = f"{rel.subject} {rel.predicate} {rel.object}"
            facts.append({
                "fact": fact,
                "confidence": rel.confidence,
                "subject": rel.subject,
                "predicate": rel.predicate,
                "object": rel.object,
                "source": "Relationship"
            })
        
        # Extract facts from key points
        if hasattr(video_intel, 'key_points') and video_intel.key_points:
            for kp in video_intel.key_points:
                facts.append({
                    "fact": kp.text,
                    "confidence": 0.9,  # Key points are typically high quality
                    "timestamp": kp.timestamp,
                    "source": "Key Point"
                })
        
        # Extract facts from entities with high confidence
        high_conf_entities = [e for e in video_intel.entities if e.confidence > 0.85]
        for entity in high_conf_entities[:20]:  # Top 20 high confidence entities
            if entity.properties:
                for prop, value in entity.properties.items():
                    fact = f"{entity.name} has {prop}: {value}"
                    facts.append({
                        "fact": fact,
                        "confidence": entity.confidence,
                        "subject": entity.name,
                        "source": "Entity Property"
                    })
        
        # Sort by confidence and diversity
        # First, group by type to ensure diversity
        facts_by_type = {}
        for fact in facts:
            fact_type = fact.get('source', 'unknown')
            if fact_type not in facts_by_type:
                facts_by_type[fact_type] = []
            facts_by_type[fact_type].append(fact)
        
        # Sort each type by confidence
        for fact_type in facts_by_type:
            facts_by_type[fact_type].sort(key=lambda x: x['confidence'], reverse=True)
        
        # Interleave facts from different types for diversity
        final_facts = []
        max_per_type = max(len(facts) for facts in facts_by_type.values()) if facts_by_type else 0
        
        for i in range(max_per_type):
            for fact_type in ['Relationship', 'Key Point', 'Entity Property']:
                if fact_type in facts_by_type and i < len(facts_by_type[fact_type]):
                    final_facts.append(facts_by_type[fact_type][i])
        
        # Store more facts (was 20, now up to 100)
        video_intel.key_moments = final_facts[:100]
        
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
Please validate and IMPROVE these relationships extracted from the video transcript.
For each relationship, either:
1. Keep it if it's meaningful and specific
2. Replace generic predicates with more specific ones
3. Remove it if it's too vague or not supported by the transcript

Transcript excerpt: {transcript[:2000]}...

Relationships to validate:
{rel_list}

AVOID generic predicates like: mentioned, referenced, discussed, talked about
PREFER specific predicates like: signed, announced, vetoed, partnered with, acquired, defeated, funded, criticized, supported

For example:
- BAD: "Biden | mentioned | Ukraine" 
- GOOD: "Biden | signed security pact with | Ukraine"

Return validated relationships in format: "subject | predicate | object"
Include ONLY meaningful, specific relationships that convey real information.
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

    def get_total_cost(self) -> float:
        """Get total cost of LLM operations."""
        # Include costs from all components
        total = 0.0
        
        if self.use_gliner and self.gliner_extractor:
            total += self.gliner_extractor.get_total_cost()
            
        if self.use_rebel and self.rebel_extractor:
            total += self.rebel_extractor.get_total_cost()
            
        return total 