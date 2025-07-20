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
from typing import List, Dict, Any, Optional, Tuple, Set
import asyncio
from collections import defaultdict
import os
import re

import networkx as nx
import google.generativeai as genai
from google.generativeai.types import RequestOptions

from ..models import VideoIntelligence, Entity, Relationship, VideoTranscript, EnhancedEntity
from .spacy_extractor import SpacyEntityExtractor
from .rebel_extractor import REBELExtractor
from .gliner_extractor import GLiNERExtractor
from .entity_normalizer import EntityNormalizer
from .entity_quality_filter import EntityQualityFilter
from .enhanced_entity_extractor import EnhancedEntityExtractor
from .relationship_evidence_extractor import RelationshipEvidenceExtractor
from .temporal_reference_resolver import TemporalReferenceResolver
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
        llm_model: str = "gemini-2.5-flash",
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
        
        # Initialize extractors - they will use cached models from model_manager
        self.spacy_extractor = SpacyEntityExtractor()
        
        if use_gliner:
            self.gliner_extractor = GLiNERExtractor(device=device)
        else:
            self.gliner_extractor = None
            
        if use_rebel:
            self.rebel_extractor = REBELExtractor(device=device)
        else:
            self.rebel_extractor = None
            
        # Initialize entity normalizer for cross-method deduplication
        self.entity_normalizer = EntityNormalizer()
        
        # Initialize entity quality filter for enhanced quality
        self.quality_filter = EntityQualityFilter(
            min_confidence_threshold=confidence_threshold,
            enable_llm_validation=use_llm
        )
            
        # Initialize GeminiPool for LLM validation
        if api_key:
            genai.configure(api_key=api_key)
            self.pool = GeminiPool(api_key=api_key)
            self.llm_enabled = True
        else:
            self.llm_enabled = False
            logger.warning("No API key provided, LLM validation disabled")
        
        # Domain-specific enhancement patterns
        self.domain_patterns = self._initialize_domain_patterns()
        
        self.enhanced_extractor = EnhancedEntityExtractor()
        
        # Phase 2: Initialize relationship evidence extractor
        self.relationship_evidence_extractor = RelationshipEvidenceExtractor()
        self.temporal_reference_resolver = TemporalReferenceResolver()
        
        logger.info(f"Advanced hybrid extractor initialized with GLiNER={use_gliner}, REBEL={use_rebel}, LLM={use_llm} :-)")
        
    async def extract_all(
        self,
        video_intel: VideoIntelligence,
        domain: Optional[str] = None
    ) -> VideoIntelligence:
        """
        Run the full advanced intelligence extraction pipeline.
        
        Args:
            video_intel: VideoIntelligence object with transcript.
            domain: Optional domain for specialized extraction.
            
        Returns:
            Updated VideoIntelligence object with all extractions.
        """
        if not video_intel.transcript or not video_intel.transcript.full_text:
            logger.warning("Cannot extract intelligence, transcript is missing or empty.")
            return video_intel

        stats = defaultdict(int)

        # Step 1: Extract entities from all sources
        spacy_entities = self._extract_spacy_entities(video_intel.transcript.full_text, stats)
        gliner_entities = self._extract_gliner_entities(video_intel.transcript.full_text, domain, stats)

        # Step 2: Normalize entities and extract relationships
        all_raw_entities = spacy_entities + gliner_entities
        normalized_entities = self.entity_normalizer.normalize_entities(all_raw_entities)
        
        # Step 2.5: Apply quality filtering and enhancement
        quality_filtered_entities, quality_metrics = await self.quality_filter.filter_and_enhance_entities(
            normalized_entities, video_intel
        )
        
        # Step 2.6: Enhance entities with metadata (Phase 1 implementation)
        enhanced_entities = self.enhanced_extractor.enhance_entities(
            quality_filtered_entities,
            transcript_segments=video_intel.transcript.segments if hasattr(video_intel.transcript, 'segments') else None,
            visual_data=None  # TODO: Add visual data when available
        )
        
        video_intel.entities = enhanced_entities
        
        # Log quality improvements
        logger.info(f"Quality enhancement: {quality_metrics.total_input_entities} → {quality_metrics.filtered_entities} entities")
        logger.info(f"Removed {quality_metrics.false_positives_removed} false positives, {quality_metrics.language_filtered} non-English")
        logger.info(f"Quality score: {quality_metrics.final_quality_score:.3f}, Language purity: {quality_metrics.language_purity_score:.3f}")
        logger.info(f"Enhanced {len(enhanced_entities)} entities with metadata")
        
        # Add quality metrics to processing stats
        stats.update({
            'quality_false_positives_removed': quality_metrics.false_positives_removed,
            'quality_language_filtered': quality_metrics.language_filtered,
            'quality_confidence_improved': quality_metrics.confidence_improved,
            'quality_score': quality_metrics.final_quality_score,
            'language_purity': quality_metrics.language_purity_score,
            'enhanced_entities': len(enhanced_entities)
        })
        
        entity_lookup = self.entity_normalizer.create_entity_lookup(video_intel.entities)
        video_intel = self._extract_relationships_with_entity_awareness(video_intel, entity_lookup, stats)
        
        # Phase 2: Extract evidence chains for relationships
        if video_intel.relationships:
            logger.info("Extracting evidence chains for relationships...")
            enhanced_relationships = self.relationship_evidence_extractor.extract_evidence_chains(
                video_intel.relationships,
                video_intel,
                enhanced_entities
            )
            video_intel.relationships = enhanced_relationships
            
            # Update stats with evidence metrics
            total_evidence = sum(len(r.evidence_chain) for r in enhanced_relationships)
            relationships_with_evidence = sum(1 for r in enhanced_relationships if r.evidence_chain)
            stats["relationship_evidence_total"] = total_evidence
            stats["relationships_with_evidence"] = relationships_with_evidence
            logger.info(f"Enhanced {len(enhanced_relationships)} relationships with {total_evidence} pieces of evidence")

        # Phase 3: Resolve temporal references
        temporal_references = self.temporal_reference_resolver.resolve_temporal_references(video_intel)
        video_intel.temporal_references = temporal_references
        stats["temporal_references"] = len(temporal_references)
        logger.info(f"Resolved {len(temporal_references)} temporal references")

        # Step 3: Optional LLM validation and knowledge graph construction
        if self.use_llm:
            video_intel = await self._validate_with_llm(video_intel)
            stats["llm_validated"] = sum(1 for e in video_intel.entities if e.confidence > self.confidence_threshold)

        video_intel = self._build_knowledge_graph(video_intel, stats)
        
        # Step 4: Extract final facts and update stats
        video_intel = self._extract_key_facts(video_intel)
        video_intel.processing_stats.update(stats)
        
        logger.info(f"Advanced extraction complete with quality enhancement: {dict(stats)} :-)")
        return video_intel

    def _extract_spacy_entities(self, text: str, stats: Dict[str, int]) -> List[Entity]:
        """Extract entities using SpaCy."""
        logger.info("Extracting entities with SpaCy...")
        spacy_entities_with_conf = self.spacy_extractor.extract_entities(text)
        stats["spacy_entities"] = len(spacy_entities_with_conf)
        return [entity for entity, conf in spacy_entities_with_conf]

    def _extract_gliner_entities(self, text: str, domain: Optional[str], stats: Dict[str, int]) -> List[Entity]:
        """Extract entities using GLiNER."""
        if not self.use_gliner or not self.gliner_extractor:
            return []
            
        logger.info(f"Extracting custom entities with GLiNER (domain={domain})...")
        if domain:
            custom_entities = self.gliner_extractor.extract_domain_specific(text, domain)
        else:
            custom_entities = self.gliner_extractor.extract_entities(text)
        
        gliner_entities = [
            Entity(entity=e.text, type=e.label, confidence=e.confidence, source="GLiNER")
            for e in custom_entities
        ]
        stats["gliner_entities"] = len(gliner_entities)
        return gliner_entities

    def _extract_relationships_with_entity_awareness(
        self, 
        video_intel: VideoIntelligence, 
        entity_lookup: Dict[str, str],
        stats: Dict[str, int]
    ) -> VideoIntelligence:
        """Extract relationships using REBEL with awareness of normalized entities."""
        if not self.use_rebel or not self.rebel_extractor or not video_intel.transcript:
            return video_intel
            
        logger.info("Extracting relationships with REBEL...")
        triplets = self.rebel_extractor.extract_triplets(video_intel.transcript.full_text)
        
        relationships = []
        entity_names = {e.entity.lower() for e in video_intel.entities}

        for triplet in triplets:
            subject = triplet['subject']
            object_name = triplet['object']
            
            canonical_subject = entity_lookup.get(subject.lower(), subject)
            canonical_object = entity_lookup.get(object_name.lower(), object_name)
            
            if canonical_subject.lower() in entity_names or canonical_object.lower() in entity_names:
                relationships.append(Relationship(
                    subject=canonical_subject,
                    predicate=triplet['predicate'],
                    object=canonical_object,
                    confidence=0.85,
                    properties={"source": "REBEL", "original_subject": subject, "original_object": object_name}
                ))
                
        unique_relationships = self._deduplicate_relationships(relationships)
        video_intel.relationships.extend(unique_relationships)
        
        stats["relationships"] = len(unique_relationships)
        logger.info(f"Added {len(unique_relationships)} normalized relationships")
        return video_intel

    def _build_knowledge_graph(self, video_intel: VideoIntelligence, stats: Dict[str, int]) -> VideoIntelligence:
        """Build a knowledge graph from entities and relationships."""
        logger.info("Building knowledge graph...")
        G = nx.DiGraph()
        
        # Debug logging
        logger.debug(f"Building graph with {len(video_intel.entities)} entities and {len(video_intel.relationships)} relationships")
        
        for entity in video_intel.entities:
            G.add_node(entity.entity, type=entity.type, confidence=entity.confidence)
            
        for rel in video_intel.relationships:
            G.add_edge(rel.subject, rel.object, predicate=rel.predicate, confidence=rel.confidence)
            
        knowledge_graph = {
            "nodes": [{"id": node, **data} for node, data in G.nodes(data=True)],
            "edges": [{"source": u, "target": v, **data} for u, v, data in G.edges(data=True)],
            "node_count": G.number_of_nodes(),
            "edge_count": G.number_of_edges(),
            "connected_components": nx.number_weakly_connected_components(G) if G.nodes else 0,
            "density": nx.density(G)
        }
        
        # Debug logging
        logger.debug(f"Created knowledge graph: {knowledge_graph['node_count']} nodes, {knowledge_graph['edge_count']} edges")
        
        video_intel.knowledge_graph = knowledge_graph
        stats["graph_nodes"] = knowledge_graph["node_count"]
        stats["graph_edges"] = knowledge_graph["edge_count"]
        
        # Verify assignment
        logger.debug(f"Knowledge graph assigned: {video_intel.knowledge_graph is not None}")
        
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
        
    def _build_entity_validation_prompt(self, entities: List[Entity], transcript: str) -> str:
        """Build prompt for entity validation."""
        entity_list = "\n".join([f"- {e.entity} ({e.type})" for e in entities])
        
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
            if entity.entity.lower() in response_lower:
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

    def _initialize_domain_patterns(self) -> Dict[str, Dict]:
        """Initialize domain-specific patterns for entity enhancement."""
        return {
            'military': {
                'keywords': {
                    'general', 'admiral', 'colonel', 'major', 'captain', 'lieutenant', 'sergeant',
                    'battalion', 'brigade', 'regiment', 'squadron', 'platoon', 'division',
                    'pentagon', 'nato', 'dod', 'usmc', 'navy', 'army', 'air force', 'marines',
                    'deployment', 'operation', 'mission', 'exercise', 'combat', 'warfare',
                    'f-35', 'f-16', 'apache', 'blackhawk', 'patriot', 'javelin', 'abrams'
                },
                'patterns': {
                    r'\b(general|admiral|colonel|major|captain|lieutenant)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b': 'COMMISSIONED_OFFICER',
                    r'\b(sergeant|corporal)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b': 'NON_COMMISSIONED_OFFICER',
                    r'\b(\d+(?:st|nd|rd|th)\s+(?:infantry|armored|airborne|marine)\s+(?:division|brigade|battalion))\b': 'MILITARY_UNIT',
                    r'\b(operation\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b': 'MILITARY_OPERATION'
                },
                'boost_factor': 0.3
            },
            
            'intelligence': {
                'keywords': {
                    'cia', 'nsa', 'fbi', 'dia', 'dni', 'mossad', 'mi6', 'svr', 'mss', 'gru',
                    'classified', 'top secret', 'secret', 'confidential', 'intelligence',
                    'operative', 'agent', 'analyst', 'handler', 'asset', 'source',
                    'surveillance', 'reconnaissance', 'humint', 'sigint', 'osint', 'geoint'
                },
                'patterns': {
                    r'\b(cia|nsa|fbi|dia)\s+(officer|agent|analyst)\b': 'INTELLIGENCE_OFFICER',
                    r'\b(operation|project)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b': 'INTELLIGENCE_OPERATION',
                    r'\b(apt|advanced\s+persistent\s+threat)\s*(\d+|[a-z]+)\b': 'APT_GROUP'
                },
                'boost_factor': 0.3
            },
            
            'political': {
                'keywords': {
                    'president', 'prime minister', 'senator', 'congressman', 'governor', 'mayor',
                    'parliament', 'congress', 'senate', 'house', 'cabinet', 'ministry',
                    'election', 'campaign', 'vote', 'ballot', 'democracy', 'republican', 'democrat',
                    'scandal', 'corruption', 'bribery', 'lobbying', 'policy', 'legislation'
                },
                'patterns': {
                    r'\b(president|prime\s+minister|senator|congressman|governor|mayor)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b': 'POLITICAL_FIGURE',
                    r'\b(secretary\s+of\s+(?:state|defense|treasury|homeland\s+security))\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b': 'GOVERNMENT_OFFICIAL',
                    r'\b(operation|scandal|affair)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b': 'POLITICAL_SCANDAL'
                },
                'boost_factor': 0.3
            },
            
            'criminal': {
                'keywords': {
                    'cartel', 'mafia', 'gang', 'crime family', 'syndicate', 'trafficking',
                    'smuggling', 'laundering', 'extortion', 'kidnapping', 'assassination',
                    'murder', 'robbery', 'fraud', 'embezzlement', 'bribery', 'corruption',
                    'suspect', 'defendant', 'convict', 'arrest', 'indictment', 'trial'
                },
                'patterns': {
                    r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(cartel|mafia|crime\s+family)\b': 'CRIMINAL_ORGANIZATION',
                    r'\b(drug|arms|human)\s+trafficking\b': 'CRIMINAL_ACTIVITY',
                    r'\b(money\s+laundering|embezzlement|fraud|bribery)\b': 'FINANCIAL_CRIME'
                },
                'boost_factor': 0.3
            },
            
            'terrorism': {
                'keywords': {
                    'terrorist', 'terrorism', 'extremist', 'jihadist', 'militant', 'insurgent',
                    'al-qaeda', 'isis', 'hezbollah', 'hamas', 'taliban', 'boko haram',
                    'bombing', 'attack', 'suicide bomber', 'ied', 'cell', 'recruitment',
                    'radicalization', 'ideology', 'martyrdom', 'jihad'
                },
                'patterns': {
                    r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(terrorist\s+(?:group|organization)|terror\s+group)\b': 'TERRORIST_ORGANIZATION',
                    r'\b(suicide\s+bombing|car\s+bombing|ied\s+attack)\b': 'TERRORIST_ATTACK',
                    r'\b(terror\s+cell|terrorist\s+cell)\b': 'TERRORIST_CELL'
                },
                'boost_factor': 0.3
            },
            
            'business': {
                'keywords': {
                    'ceo', 'cfo', 'cto', 'chairman', 'board', 'executive', 'corporation',
                    'company', 'firm', 'enterprise', 'startup', 'ipo', 'merger', 'acquisition',
                    'stock', 'shares', 'market', 'nasdaq', 'nyse', 'wall street',
                    'revenue', 'profit', 'loss', 'earnings', 'quarterly', 'annual'
                },
                'patterns': {
                    r'\b(ceo|cfo|cto|chairman)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b': 'BUSINESS_EXECUTIVE',
                    r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(corporation|company|inc\.?|corp\.?)\b': 'CORPORATION',
                    r'\b(merger|acquisition|ipo|bankruptcy)\b': 'BUSINESS_EVENT'
                },
                'boost_factor': 0.2
            },
            
            'energy': {
                'keywords': {
                    'oil', 'gas', 'petroleum', 'refinery', 'pipeline', 'drilling', 'fracking',
                    'solar', 'wind', 'nuclear', 'coal', 'renewable', 'power plant',
                    'grid', 'electricity', 'energy', 'fuel', 'opec', 'exxon', 'chevron',
                    'bp', 'shell', 'total', 'gazprom', 'rosneft'
                },
                'patterns': {
                    r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(oil|gas|energy)\s+(company|corporation)\b': 'ENERGY_COMPANY',
                    r'\b(power\s+plant|refinery|pipeline|drilling\s+site)\b': 'ENERGY_FACILITY',
                    r'\b(oil\s+spill|gas\s+leak|pipeline\s+explosion)\b': 'ENERGY_INCIDENT'
                },
                'boost_factor': 0.2
            },
            
            'technology': {
                'keywords': {
                    'ai', 'artificial intelligence', 'machine learning', 'neural network',
                    'quantum', 'blockchain', 'cryptocurrency', 'bitcoin', 'cyber',
                    'software', 'hardware', 'semiconductor', 'chip', 'processor',
                    'google', 'apple', 'microsoft', 'amazon', 'facebook', 'meta',
                    'tesla', 'nvidia', 'intel', 'amd', 'tsmc'
                },
                'patterns': {
                    r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(ai|artificial\s+intelligence)\b': 'AI_SYSTEM',
                    r'\b(quantum\s+(?:computer|computing|encryption))\b': 'QUANTUM_TECHNOLOGY',
                    r'\b(cyber\s+(?:attack|warfare|espionage))\b': 'CYBER_OPERATION'
                },
                'boost_factor': 0.2
            },
            
            'geopolitical': {
                'keywords': {
                    'nato', 'eu', 'un', 'g7', 'g20', 'brics', 'asean', 'quad',
                    'alliance', 'treaty', 'sanctions', 'embargo', 'diplomacy',
                    'summit', 'negotiation', 'agreement', 'accord', 'pact',
                    'sphere of influence', 'balance of power', 'containment'
                },
                'patterns': {
                    r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(treaty|agreement|accord|pact)\b': 'INTERNATIONAL_AGREEMENT',
                    r'\b(nato|eu|un|brics|asean)\s+(summit|meeting|conference)\b': 'DIPLOMATIC_EVENT',
                    r'\b(economic\s+sanctions|trade\s+embargo)\b': 'ECONOMIC_PRESSURE'
                },
                'boost_factor': 0.2
            }
        }
        
    def extract_entities_and_relationships(self, text: str) -> Tuple[List[Entity], List[Relationship]]:
        """
        Extract entities and relationships using advanced hybrid approach.
        
        Args:
            text: Input text for extraction
            
        Returns:
            Tuple of (enhanced entities, relationships)
        """
        logger.info("Starting advanced hybrid extraction...")
        
        # Step 1: Extract entities from all models
        all_entities = []
        
        # SpaCy extraction
        spacy_entities = self.spacy_extractor.extract_entities(text)
        for entity in spacy_entities:
            entity.properties = entity.properties or {}
            entity.properties['source'] = 'SpaCy'
        all_entities.extend(spacy_entities)
        
        # GLiNER extraction
        gliner_entities = self.gliner_extractor.extract_entities(text)
        for entity in gliner_entities:
            entity.properties = entity.properties or {}
            entity.properties['source'] = 'GLiNER'
        all_entities.extend(gliner_entities)
        
        # Step 2: Enhance entities with domain-specific classification
        enhanced_entities = self._enhance_entities_with_domain_knowledge(text, all_entities)
        
        # Step 3: Normalize and deduplicate entities
        normalized_entities = self.entity_normalizer.normalize_entities(enhanced_entities)
        
        # Step 4: Create entity lookup for REBEL
        entity_lookup = self.entity_normalizer.create_entity_lookup(normalized_entities)
        
        # Step 5: Extract relationships using REBEL with entity awareness
        relationships = self.rebel_extractor.extract_relationships(text, entity_lookup)
        
        # Step 6: Enhance relationships with domain context
        enhanced_relationships = self._enhance_relationships_with_context(relationships, normalized_entities, text)
        
        logger.info(f"Advanced extraction complete: {len(normalized_entities)} entities, {len(enhanced_relationships)} relationships")
        
        return normalized_entities, enhanced_relationships
        
    def _enhance_entities_with_domain_knowledge(self, text: str, entities: List[Entity]) -> List[Entity]:
        """Enhance entities using domain-specific knowledge and patterns."""
        enhanced_entities = []
        text_lower = text.lower()
        
        # Detect active domains based on keyword density
        active_domains = self._detect_active_domains(text_lower)
        
        for entity in entities:
            enhanced_entity = self._enhance_single_entity(entity, text, text_lower, active_domains)
            enhanced_entities.append(enhanced_entity)
            
        # Add entities discovered through pattern matching
        pattern_entities = self._extract_pattern_entities(text, active_domains)
        enhanced_entities.extend(pattern_entities)
        
        return enhanced_entities
        
    def _detect_active_domains(self, text_lower: str) -> Set[str]:
        """Detect which domains are active in the text based on keyword density."""
        active_domains = set()
        
        for domain, config in self.domain_patterns.items():
            keyword_count = sum(1 for keyword in config['keywords'] if keyword in text_lower)
            keyword_density = keyword_count / len(config['keywords'])
            
            # Domain is active if it has significant keyword presence
            if keyword_density > 0.05:  # 5% of domain keywords present
                active_domains.add(domain)
                logger.debug(f"Domain '{domain}' active (density: {keyword_density:.2f})")
                
        return active_domains
        
    def _enhance_single_entity(self, entity: Entity, text: str, text_lower: str, active_domains: Set[str]) -> Entity:
        """Enhance a single entity with domain-specific classification."""
        enhanced_entity = Entity(
                            entity=entity.entity,
            type=entity.type,
            confidence=entity.confidence,
            properties=entity.properties or {}
        )
        
        # Check for domain-specific enhancements
        for domain in active_domains:
            if domain not in self.domain_patterns:
                continue
                
            config = self.domain_patterns[domain]
            entity_name_lower = entity.entity.lower()
            
            # Check if entity name contains domain keywords
            for keyword in config['keywords']:
                if keyword in entity_name_lower or keyword in text_lower:
                    # Apply domain-specific type enhancement
                    enhanced_type = self._get_enhanced_type(entity, domain, text)
                    if enhanced_type:
                        enhanced_entity.type = enhanced_type
                        enhanced_entity.confidence = min(1.0, enhanced_entity.confidence + config['boost_factor'])
                        enhanced_entity.properties['domain'] = domain
                        enhanced_entity.properties['enhancement'] = 'domain_keyword'
                        break
                        
        return enhanced_entity
        
    def _get_enhanced_type(self, entity: Entity, domain: str, text: str) -> Optional[str]:
        """Get enhanced entity type based on domain and context."""
        entity_name = entity.entity.lower()
        
        # Domain-specific type mappings
        if domain == 'military':
            if any(rank in entity_name for rank in ['general', 'admiral', 'colonel', 'major', 'captain', 'lieutenant']):
                return 'COMMISSIONED_OFFICER'
            elif any(rank in entity_name for rank in ['sergeant', 'corporal']):
                return 'NON_COMMISSIONED_OFFICER'
            elif any(unit in entity_name for unit in ['battalion', 'brigade', 'regiment', 'squadron']):
                return 'MILITARY_UNIT'
                
        elif domain == 'political':
            if any(title in entity_name for title in ['president', 'prime minister', 'senator', 'congressman']):
                return 'POLITICAL_FIGURE'
            elif any(title in entity_name for title in ['secretary', 'minister', 'ambassador']):
                return 'GOVERNMENT_OFFICIAL'
                
        elif domain == 'criminal':
            if any(org in entity_name for org in ['cartel', 'mafia', 'gang']):
                return 'CRIMINAL_ORGANIZATION'
            elif any(crime in entity_name for crime in ['trafficking', 'laundering', 'fraud']):
                return 'CRIMINAL_ACTIVITY'
                
        elif domain == 'terrorism':
            if any(term in entity_name for term in ['terrorist', 'terror', 'militant']):
                return 'TERRORIST_ORGANIZATION'
            elif any(attack in entity_name for attack in ['bombing', 'attack', 'strike']):
                return 'TERRORIST_ATTACK'
                
        elif domain == 'business':
            if any(title in entity_name for title in ['ceo', 'cfo', 'cto', 'chairman']):
                return 'BUSINESS_EXECUTIVE'
            elif any(org in entity_name for org in ['corporation', 'company', 'inc', 'corp']):
                return 'CORPORATION'
                
        elif domain == 'energy':
            if any(facility in entity_name for facility in ['plant', 'refinery', 'pipeline']):
                return 'ENERGY_FACILITY'
            elif any(company in entity_name for company in ['oil', 'gas', 'energy']):
                return 'ENERGY_COMPANY'
                
        elif domain == 'technology':
            if any(tech in entity_name for tech in ['ai', 'artificial intelligence']):
                return 'AI_SYSTEM'
            elif 'quantum' in entity_name:
                return 'QUANTUM_TECHNOLOGY'
            elif 'cyber' in entity_name:
                return 'CYBER_TECHNOLOGY'
                
        return None
        
    def _extract_pattern_entities(self, text: str, active_domains: Set[str]) -> List[Entity]:
        """Extract additional entities using domain-specific patterns."""
        pattern_entities = []
        
        for domain in active_domains:
            if domain not in self.domain_patterns:
                continue
                
            config = self.domain_patterns[domain]
            
            for pattern, entity_type in config['patterns'].items():
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    # Extract the main entity name (usually the second group)
                    entity_name = match.group(2) if match.lastindex >= 2 else match.group(1)
                    
                    if len(entity_name) > 2:  # Avoid very short matches
                        entity = Entity(
                            name=entity_name,
                            type=entity_type,
                            confidence=0.7 + config['boost_factor'],
                            properties={
                                'source': 'Pattern',
                                'domain': domain,
                                'pattern': pattern[:50] + '...' if len(pattern) > 50 else pattern
                            }
                        )
                        pattern_entities.append(entity)
                        
        return pattern_entities
        
    def _enhance_relationships_with_context(self, relationships: List[Relationship], 
                                          entities: List[Entity], text: str) -> List[Relationship]:
        """Enhance relationships with domain-specific context."""
        enhanced_relationships = []
        
        # Create entity type mapping for context
        entity_types = {entity.entity.lower(): entity.type for entity in entities}
        
        for relationship in relationships:
            enhanced_rel = Relationship(
                subject=relationship.subject,
                predicate=relationship.predicate,
                object=relationship.object,
                confidence=relationship.confidence,
                properties=relationship.properties or {}
            )
            
            # Enhance relationship based on entity types
            subject_type = entity_types.get(relationship.subject.lower())
            object_type = entity_types.get(relationship.object.lower())
            
            if subject_type and object_type:
                enhanced_rel.properties['subject_type'] = subject_type
                enhanced_rel.properties['object_type'] = object_type
                
                # Add domain-specific relationship context
                context = self._get_relationship_context(subject_type, object_type, relationship.predicate)
                if context:
                    enhanced_rel.properties['context'] = context
                    enhanced_rel.confidence = min(1.0, enhanced_rel.confidence + 0.1)
                    
            enhanced_relationships.append(enhanced_rel)
            
        return enhanced_relationships
        
    def _get_relationship_context(self, subject_type: str, object_type: str, predicate: str) -> Optional[str]:
        """Get contextual information for relationships based on entity types."""
        
        # Military relationships
        if 'OFFICER' in subject_type or 'MILITARY' in subject_type:
            if 'commands' in predicate.lower() or 'leads' in predicate.lower():
                return 'military_command'
            elif 'serves' in predicate.lower():
                return 'military_service'
                
        # Political relationships  
        elif 'POLITICAL' in subject_type or 'GOVERNMENT' in subject_type:
            if 'appointed' in predicate.lower() or 'nominated' in predicate.lower():
                return 'political_appointment'
            elif 'meets' in predicate.lower() or 'negotiates' in predicate.lower():
                return 'diplomatic_engagement'
                
        # Criminal relationships
        elif 'CRIMINAL' in subject_type or 'TERRORIST' in subject_type:
            if 'leads' in predicate.lower() or 'controls' in predicate.lower():
                return 'criminal_leadership'
            elif 'funds' in predicate.lower() or 'supports' in predicate.lower():
                return 'criminal_financing'
                
        # Business relationships
        elif 'BUSINESS' in subject_type or 'CORPORATION' in object_type:
            if 'ceo' in predicate.lower() or 'founded' in predicate.lower():
                return 'business_leadership'
            elif 'invests' in predicate.lower() or 'acquires' in predicate.lower():
                return 'business_transaction'
                
        return None 

    def _deduplicate_relationships(self, relationships: List[Relationship]) -> List[Relationship]:
        """
        Remove duplicate relationships based on subject, predicate, and object.
        
        Args:
            relationships: List of relationships to deduplicate
            
        Returns:
            List of unique relationships
        """
        seen = set()
        unique = []
        
        for rel in relationships:
            # Create a unique key based on subject, predicate, object (all lowercase)
            key = (rel.subject.lower(), rel.predicate.lower(), rel.object.lower())
            
            if key not in seen:
                seen.add(key)
                unique.append(rel)
            else:
                # If we've seen this relationship before, update confidence if higher
                for existing in unique:
                    if (existing.subject.lower() == rel.subject.lower() and
                        existing.predicate.lower() == rel.predicate.lower() and
                        existing.object.lower() == rel.object.lower()):
                        if rel.confidence > existing.confidence:
                            existing.confidence = rel.confidence
                        break
                        
        return unique 

    def _extract_key_facts(self, video_intel: VideoIntelligence) -> VideoIntelligence:
        """
        Extract key facts from the video intelligence.
        
        This is a placeholder method that returns the video intelligence unchanged
        since key facts are already extracted during the initial Gemini processing.
        
        Args:
            video_intel: VideoIntelligence object
            
        Returns:
            Unchanged VideoIntelligence object
        """
        # Key facts are already extracted by Gemini during initial processing
        # This method exists for compatibility but doesn't need to do anything
        return video_intel 

    async def extract(
        self, transcript: VideoTranscript, video_title: str
    ) -> Tuple[List[dict], List[dict]]:
        # ... existing code ...
        logger.info(f"Extracted {len(spacy_entities)} entities from SpaCy.")

        # Step 2: Extract entities with GLiNER
        gliner_entities = self.gliner_extractor.extract(
            transcript.full_text, {"Person": "person", "Organization": "organization"}
        )
        logger.info(f"Extracted {len(gliner_entities)} entities from GLiNER.")

        # Step 3: Extract relationships with REBEL
        relationships = self.rebel_extractor.extract(transcript.full_text)
        logger.info(f"Extracted {len(relationships)} relationships from REBEL.")
        rebel_entities = self._get_entities_from_relationships(relationships)
        logger.info(
            f"Inferred {len(rebel_entities)} entities from REBEL relationships."
        )

        # Combine all entities
        all_entities = spacy_entities + gliner_entities + rebel_entities
        logger.info(f"Total entities before deduplication: {len(all_entities)}")

        # Step 4: Enhance entities
        enhanced_entities = self.enhanced_extractor.enhance_entities(
            entities=all_entities,
            transcript_segments=transcript.segments
        )
        logger.info(f"Enhanced {len(enhanced_entities)} unique entities.")

        # Step 5: Filter entities for quality
        quality_entities, quality_report = self.quality_filter.filter_entities(
            enhanced_entities
        )
        logger.info(
            f"Filtered entities, retaining {len(quality_entities)} high-quality entities."
        )
        logger.debug(f"Quality report: {quality_report}")

        # Step 6: Optional LLM validation
        if self.use_llm_validation and self.llm_validator:
            # ... existing LLM validation logic ...
            # This part may need to be adapted for EnhancedEntity objects
            pass

        # Convert EnhancedEntity objects to dicts for output
        final_entities = [entity.model_dump() for entity in quality_entities]
        final_relationships = [rel.model_dump() for rel in relationships]

        return final_entities, final_relationships

    def _get_entities_from_relationships(self, relationships: List[Relationship]) -> List[Entity]:
        # ... existing code ...
        return list(entities.values())

    def _deduplicate_and_normalize_entities(
        self, entities: List[Entity]
    ) -> List[Entity]:
        """
        This method is now handled by the EnhancedEntityExtractor.
        It can be deprecated or removed.
        """
        logger.warning(
            "_deduplicate_and_normalize_entities is deprecated. "
            "Functionality is now in EnhancedEntityExtractor."
        )
        # For backward compatibility, we can still do a simple normalization
        # Or just return the entities as is.
        return entities 