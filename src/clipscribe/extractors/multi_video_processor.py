"""
Multi-Video Intelligence Processor for ClipScribe.

Handles cross-video entity resolution, relationship bridging, narrative flow analysis,
and unified knowledge graph generation with aggressive AI-powered entity merging.

Timeline features permanently discontinued - focuses on core intelligence extraction.
"""

import logging
from typing import List, Dict, Any, Optional
from collections import Counter
import time

from ..models import (
    VideoIntelligence,
    MultiVideoIntelligence,
    CrossVideoEntity,
    CrossVideoRelationship,
    VideoCollectionType,
    Entity,
    Topic,
    InformationFlowMap,
    ConceptNode,
    ConceptDependency,
    InformationFlow,
    ConceptEvolutionPath,
    ConceptCluster,
    ConceptMaturityLevel,
)
from .entity_normalizer import EntityNormalizer
from .series_detector import SeriesDetector
from ..config.settings import Settings

logger = logging.getLogger(__name__)


class MultiVideoProcessor:
    """
    Processes multiple videos to extract unified intelligence.

    Features:
    - Aggressive cross-video entity resolution
    - Relationship bridging across videos
    - Narrative flow analysis for series
    - Topic evolution tracking
    - Unified knowledge graph generation
    - Quality metrics and validation

    Note: Timeline features permanently discontinued per strategic pivot.
    """

    def __init__(self, use_ai_validation: bool = True):
        """
        Initialize multi-video processor for core intelligence extraction.

        Args:
            use_ai_validation: Whether to use AI for entity validation and merging
        """
        self.entity_normalizer = EntityNormalizer(similarity_threshold=0.85)  # Aggressive merging
        self.series_detector = SeriesDetector(similarity_threshold=0.7)
        self.use_ai_validation = use_ai_validation
        self.settings = Settings()

        # AI validation setup - using Pro for all multi-video intelligence
        if use_ai_validation:
            try:
                import google.generativeai as genai

                genai.configure(api_key=self.settings.google_api_key)
                self.ai_model = genai.GenerativeModel(
                    "gemini-2.5-pro"
                )  # 2.5 Pro for sophisticated analysis
            except Exception as e:
                logger.warning(f"AI validation unavailable: {e}")
                self.use_ai_validation = False

    # Knowledge panel methods removed - functionality moved to Chimera

    async def _synthesize_information_flow_map(
        self,
        videos: List[VideoIntelligence],
        unified_entities: List[CrossVideoEntity],
        cross_video_relationships: List[CrossVideoRelationship],
        collection_id: str,
        collection_title: str,
    ) -> InformationFlowMap:
        """
        Synthesizes comprehensive Information Flow Maps tracking concept evolution.

        Creates detailed analysis of how concepts, ideas, and information develop
        and flow across video collections, showing knowledge dependencies and evolution.

        Args:
            videos: List of processed videos
            unified_entities: Cross-video resolved entities
            cross_video_relationships: Cross-video relationships
            collection_id: ID of the collection
            collection_title: Title of the collection

        Returns:
            InformationFlowMap with comprehensive concept flow analysis
        """
        logger.info(f"Synthesizing Information Flow Map for {len(videos)} videos...")

        # Step 1: Extract concept nodes from all videos
        concept_nodes = await self._extract_concept_nodes(videos)

        # Step 2: Identify concept dependencies and information flows
        concept_dependencies = await self._identify_concept_dependencies(concept_nodes, videos)
        information_flows = await self._create_information_flows(concept_nodes)

        # Step 3: Analyze concept evolution paths
        evolution_paths = await self._analyze_concept_evolution_paths(concept_nodes, videos)

        # Step 4: Create concept clusters
        concept_clusters = await self._create_concept_clusters(concept_nodes, concept_dependencies)

        # Step 5: Analyze flow patterns and generate insights
        flow_analysis = await self._analyze_flow_patterns(
            concept_nodes, information_flows, concept_dependencies
        )

        # Step 6: Generate strategic insights
        if self.use_ai_validation:
            strategic_insights = await self._ai_generate_flow_insights(
                concept_nodes, information_flows, evolution_paths, collection_title
            )
        else:
            strategic_insights = self._template_generate_flow_insights(
                concept_nodes, information_flows
            )

        flow_map = InformationFlowMap(
            map_id=f"flow_map_{collection_id}",
            collection_id=collection_id,
            collection_title=collection_title,
            concept_nodes=concept_nodes,
            information_flows=information_flows,
            concept_dependencies=concept_dependencies,
            evolution_paths=evolution_paths,
            concept_clusters=concept_clusters,
            primary_information_pathways=flow_analysis.get("primary_pathways", []),
            knowledge_bottlenecks=flow_analysis.get("bottlenecks", []),
            information_gaps=flow_analysis.get("gaps", []),
            flow_summary=flow_analysis.get("summary", ""),
            learning_progression=flow_analysis.get("progression", ""),
            concept_complexity=flow_analysis.get("complexity", ""),
            strategic_insights=strategic_insights,
            overall_coherence=flow_analysis.get("coherence", 0.5),
            pedagogical_quality=flow_analysis.get("pedagogical", 0.5),
            information_density=flow_analysis.get("density", 0.5),
            total_concepts=len(concept_nodes),
            total_flows=len(information_flows),
            synthesis_quality="AI_ENHANCED" if self.use_ai_validation else "TEMPLATE",
        )

        logger.info(
            f"Successfully created Information Flow Map with {len(concept_nodes)} concepts and {len(information_flows)} flows"
        )
        return flow_map

    async def _extract_concept_nodes(self, videos: List[VideoIntelligence]) -> List[ConceptNode]:
        """Extract concept nodes from video content."""
        logger.info("Extracting concept nodes from video content...")

        concept_nodes = []

        for video_index, video in enumerate(videos):
            # Extract concepts from key points
            for kp_idx, kp in enumerate(video.key_points):
                # Filter for conceptual key points (not just factual statements)
                if self._is_conceptual_content(kp.text):
                    concept_name = await self._extract_main_concept(kp.text)
                    if concept_name:
                        maturity_level = self._assess_concept_maturity(kp.text)

                        node = ConceptNode(
                            node_id=f"concept_{video.metadata.video_id}_{kp_idx}_{len(concept_nodes)}",
                            concept_name=concept_name,
                            video_id=video.metadata.video_id,
                            video_title=video.metadata.title,
                            timestamp=0.0,  # Timestamps removed in v2.20.0 confidence-free architecture
                            maturity_level=maturity_level,
                            context=kp.text,
                            explanation_depth=self._assess_explanation_depth(kp.text),
                            key_points=[kp.text],
                            related_entities=self._extract_related_entities(
                                kp.text, video.entities
                            ),
                            sentiment=self._assess_concept_sentiment(kp.text),
                            confidence=kp.importance,
                            information_density=self._calculate_information_density(kp.text),
                            video_sequence_position=video_index,
                        )
                        concept_nodes.append(node)

            # Extract concepts from topics
            for topic in video.topics:
                if self._is_significant_topic(topic):
                    concept_name = topic.name

                    # Find context from summary or key points
                    context = self._find_topic_context(topic.name, video)

                    node = ConceptNode(
                        node_id=f"topic_{video.metadata.video_id}_{topic.name.replace(' ', '_')}",
                        concept_name=concept_name,
                        video_id=video.metadata.video_id,
                        video_title=video.metadata.title,
                        timestamp=0,  # Topics don't have specific timestamps
                        maturity_level=ConceptMaturityLevel.MENTIONED,  # Default for topics
                        context=context,
                        explanation_depth=topic.confidence,
                        related_entities=self._extract_related_entities(context, video.entities),
                        sentiment=0.0,
                        confidence=topic.confidence,
                        information_density=0.3,  # Topics are generally lower density
                        video_sequence_position=video_index,
                    )
                    concept_nodes.append(node)

        # Remove duplicate concepts
        concept_nodes = self._deduplicate_concepts(concept_nodes)

        logger.info(f"Extracted {len(concept_nodes)} concept nodes")
        return concept_nodes

    def _is_conceptual_content(self, text: str) -> bool:
        """Determine if text contains conceptual rather than purely factual content."""
        conceptual_indicators = [
            "concept",
            "idea",
            "theory",
            "principle",
            "approach",
            "strategy",
            "philosophy",
            "doctrine",
            "methodology",
            "framework",
            "model",
            "understanding",
            "perspective",
            "viewpoint",
            "analysis",
            "interpretation",
        ]

        text_lower = text.lower()
        return any(indicator in text_lower for indicator in conceptual_indicators)

    async def _extract_main_concept(self, text: str) -> Optional[str]:
        """Extract the main concept from text."""
        # Simple extraction - in production, could use NLP techniques
        # Look for noun phrases that represent concepts
        words = text.split()

        # Look for important concept keywords
        concept_patterns = [
            "nuclear program",
            "sanctions regime",
            "diplomatic relations",
            "security framework",
            "economic policy",
            "international law",
            "human rights",
            "climate change",
            "artificial intelligence",
        ]

        text_lower = text.lower()
        for pattern in concept_patterns:
            if pattern in text_lower:
                return pattern.title()

        # Fallback: extract first significant noun phrase
        significant_words = [w for w in words if len(w) > 4 and w.istitle()]
        if significant_words:
            return " ".join(significant_words[:2])

        return None

    def _assess_concept_maturity(self, text: str) -> ConceptMaturityLevel:
        """Assess the maturity level of a concept based on its context."""
        text_lower = text.lower()

        # Define maturity indicators
        maturity_indicators = {
            ConceptMaturityLevel.MENTIONED: ["mentions", "refers to", "talks about", "discusses"],
            ConceptMaturityLevel.DEFINED: [
                "defines",
                "explains",
                "describes",
                "clarifies",
                "outlines",
            ],
            ConceptMaturityLevel.EXPLORED: [
                "analyzes",
                "examines",
                "investigates",
                "explores",
                "studies",
            ],
            ConceptMaturityLevel.SYNTHESIZED: [
                "integrates",
                "combines",
                "synthesizes",
                "connects",
                "relates",
            ],
            ConceptMaturityLevel.CRITICIZED: [
                "criticizes",
                "challenges",
                "questions",
                "disputes",
                "argues against",
            ],
            ConceptMaturityLevel.EVOLVED: [
                "evolves",
                "develops",
                "progresses",
                "advances",
                "transforms",
            ],
        }

        # Check from highest to lowest maturity
        for level, indicators in reversed(list(maturity_indicators.items())):
            if any(indicator in text_lower for indicator in indicators):
                return level

        return ConceptMaturityLevel.MENTIONED  # Default

    def _assess_explanation_depth(self, text: str) -> float:
        """Assess how deeply a concept is explained."""
        # Simple heuristic based on text length and complexity
        base_score = min(len(text) / 200, 1.0)  # Longer text = more depth

        # Boost for analytical language
        analytical_terms = [
            "because",
            "therefore",
            "however",
            "furthermore",
            "analysis",
            "explains",
        ]
        analytical_boost = sum(1 for term in analytical_terms if term.lower() in text.lower()) * 0.1

        return min(base_score + analytical_boost, 1.0)

    def _extract_related_entities(self, text: str, entities: List[Entity]) -> List[str]:
        """Find entities mentioned in the concept text.

        Supports both legacy Entity (entity) and EnhancedEntity (name).
        """
        if not text:
            return []
        text_lower = text.lower()
        related: List[str] = []

        for ent in entities:
            name = getattr(ent, "entity", getattr(ent, "name", ""))
            if not name:
                continue
            if name.lower() in text_lower:
                related.append(name)

        # Deduplicate while preserving order
        seen = set()
        unique_related = []
        for n in related:
            if n not in seen:
                seen.add(n)
                unique_related.append(n)
        return unique_related[:5]  # Limit to top 5

    def _assess_concept_sentiment(self, text: str) -> float:
        """Assess sentiment toward the concept."""
        # Simple sentiment analysis
        positive_words = ["good", "excellent", "positive", "beneficial", "effective", "successful"]
        negative_words = ["bad", "poor", "negative", "harmful", "ineffective", "failed"]

        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        if positive_count + negative_count == 0:
            return 0.0  # Neutral

        return (positive_count - negative_count) / (positive_count + negative_count)

    def _calculate_information_density(self, text: str) -> float:
        """Calculate information density of the text."""
        # Simple heuristic: ratio of content words to total words
        words = text.split()

        # Define content words (not function words)
        function_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
        }
        content_words = [w for w in words if w.lower() not in function_words and len(w) > 2]

        if len(words) == 0:
            return 0.0

        return len(content_words) / len(words)

    def _is_significant_topic(self, topic: Topic) -> bool:
        """Determine if a topic is significant enough to track."""
        return topic.confidence > 0.7 and len(topic.name) > 3

    def _find_topic_context(self, topic_name: str, video: VideoIntelligence) -> str:
        """Find context for a topic from video content."""
        # Look in summary first
        if topic_name.lower() in video.summary.lower():
            sentences = video.summary.split(". ")
            for sentence in sentences:
                if topic_name.lower() in sentence.lower():
                    return sentence

        # Look in key points
        for kp in video.key_points:
            if topic_name.lower() in kp.text.lower():
                return kp.text

        return f"Topic '{topic_name}' discussed in video"

    def _deduplicate_concepts(self, concept_nodes: List[ConceptNode]) -> List[ConceptNode]:
        """Remove duplicate concept nodes."""
        maturity_values = {
            "mentioned": 1,
            "introduced": 2,
            "defined": 3,
            "explained": 4,
            "explored": 5,
            "analyzed": 6,
            "synthesized": 7,
            "evolved": 8,
            "criticized": 9,
        }
        seen_concepts = {}
        unique_nodes = []

        for node in concept_nodes:
            key = (node.concept_name.lower(), node.video_id)
            if key not in seen_concepts:
                seen_concepts[key] = node
                unique_nodes.append(node)
            else:
                # Merge with existing if this one has higher maturity
                existing = seen_concepts[key]
                if maturity_values.get(node.maturity_level, 0) > maturity_values.get(
                    existing.maturity_level, 0
                ):
                    seen_concepts[key] = node
                    unique_nodes = [n for n in unique_nodes if n.node_id != existing.node_id]
                    unique_nodes.append(node)

        return unique_nodes

    async def _identify_concept_dependencies(
        self, concept_nodes: List[ConceptNode], videos: List[VideoIntelligence]
    ) -> List[ConceptDependency]:
        """Identify dependencies between concepts."""
        logger.info("Identifying concept dependencies...")

        dependencies = []

        # Group concepts by name
        concept_groups = {}
        for node in concept_nodes:
            name = node.concept_name.lower()
            if name not in concept_groups:
                concept_groups[name] = []
            concept_groups[name].append(node)

        # Look for temporal dependencies (concepts that appear in sequence)
        sorted_nodes = sorted(concept_nodes, key=lambda n: (n.video_sequence_position, n.timestamp))

        for i in range(len(sorted_nodes) - 1):
            current = sorted_nodes[i]
            next_node = sorted_nodes[i + 1]

            # Check if concepts are related and next builds on current
            if (
                self._concepts_are_related(current, next_node)
                and current.video_sequence_position <= next_node.video_sequence_position
            ):
                dependency = ConceptDependency(
                    dependent_concept=next_node.concept_name,
                    prerequisite_concept=current.concept_name,
                    dependency_type="builds_on",
                    strength=self._calculate_dependency_strength(current, next_node),
                )
                dependencies.append(dependency)

        logger.info(f"Identified {len(dependencies)} concept dependencies")
        return dependencies

    def _concepts_are_related(self, concept1: ConceptNode, concept2: ConceptNode) -> bool:
        """Determine if two concepts are related."""
        # Check for overlapping entities
        entities1 = set(concept1.related_entities)
        entities2 = set(concept2.related_entities)
        entity_overlap = len(entities1.intersection(entities2)) / max(
            len(entities1.union(entities2)), 1
        )

        # Check for related concept names
        name_similarity = self._calculate_name_similarity(
            concept1.concept_name, concept2.concept_name
        )

        return entity_overlap > 0.3 or name_similarity > 0.5

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between concept names."""
        words1 = set(name1.lower().split())
        words2 = set(name2.lower().split())

        if len(words1.union(words2)) == 0:
            return 0.0

        return len(words1.intersection(words2)) / len(words1.union(words2))

    def _calculate_dependency_strength(
        self, prerequisite: ConceptNode, dependent: ConceptNode
    ) -> float:
        """Calculate the strength of dependency between concepts."""
        # Base strength on concept maturity levels
        maturity_levels = {
            ConceptMaturityLevel.MENTIONED: 1,
            ConceptMaturityLevel.DEFINED: 2,
            ConceptMaturityLevel.EXPLORED: 3,
            ConceptMaturityLevel.SYNTHESIZED: 4,
            ConceptMaturityLevel.CRITICIZED: 5,
            ConceptMaturityLevel.EVOLVED: 6,
        }

        prereq_level = maturity_levels.get(prerequisite.maturity_level, 1)
        dep_level = maturity_levels.get(dependent.maturity_level, 1)

        # Strong dependency if dependent concept is more mature
        if dep_level > prereq_level:
            return min(0.8, 0.5 + (dep_level - prereq_level) * 0.1)
        else:
            return 0.3

    async def _create_information_flows(
        self, concept_nodes: List[ConceptNode]
    ) -> List[InformationFlow]:
        """Create information flows between concept nodes."""
        logger.info("Creating information flows...")

        flows = []

        # Sort nodes by sequence and timestamp
        sorted_nodes = sorted(concept_nodes, key=lambda n: (n.video_sequence_position, n.timestamp))

        # Create flows between related concepts
        for i in range(len(sorted_nodes)):
            current = sorted_nodes[i]

            # Look for flows to later concepts
            for j in range(i + 1, min(i + 10, len(sorted_nodes))):  # Look ahead up to 10 concepts
                target = sorted_nodes[j]

                if self._should_create_flow(current, target):
                    flow = InformationFlow(
                        flow_id=f"flow_{current.node_id}_{target.node_id}",
                        source_node=current,
                        target_node=target,
                        flow_type=self._determine_flow_type(current, target),
                        information_transferred=self._describe_information_transfer(
                            current, target
                        ),
                        transformation_type=self._determine_transformation_type(current, target),
                        flow_quality=self._assess_flow_quality(current, target),
                        coherence_score=self._calculate_flow_coherence(current, target),
                        temporal_gap=self._calculate_temporal_gap(current, target),
                        bridge_entities=list(
                            set(current.related_entities).intersection(set(target.related_entities))
                        ),
                        supporting_evidence=[current.context, target.context],
                    )
                    flows.append(flow)

        logger.info(f"Created {len(flows)} information flows")
        return flows

    def _should_create_flow(self, source: ConceptNode, target: ConceptNode) -> bool:
        """Determine if an information flow should be created."""
        # Don't create flows within the same video unless there's clear progression
        if source.video_id == target.video_id:
            # Map maturity levels for comparison
            maturity_mapping = {
                "mentioned": 1,
                "defined": 2,
                "explored": 3,
                "synthesized": 4,
                "criticized": 5,
                "evolved": 6,
            }
            source_level = maturity_mapping.get(source.maturity_level, 1)
            target_level = maturity_mapping.get(target.maturity_level, 1)
            return target.timestamp > source.timestamp and target_level > source_level

        # Create flows between videos if concepts are related
        return self._concepts_are_related(source, target)

    def _determine_flow_type(self, source: ConceptNode, target: ConceptNode) -> str:
        """Determine the type of information flow."""
        if source.concept_name.lower() == target.concept_name.lower():
            return "development"  # Same concept being developed
        else:
            # Map maturity levels for comparison
            maturity_mapping = {
                "mentioned": 1,
                "defined": 2,
                "explored": 3,
                "synthesized": 4,
                "criticized": 5,
                "evolved": 6,
            }
            source_level = maturity_mapping.get(source.maturity_level, 1)
            target_level = maturity_mapping.get(target.maturity_level, 1)

            if target_level > source_level:
                return "elaboration"  # Concept being elaborated
            elif source.sentiment > 0 and target.sentiment < 0:
                return "contradiction"  # Contrasting viewpoints
            else:
                return "synthesis"  # Concepts being combined

    def _describe_information_transfer(self, source: ConceptNode, target: ConceptNode) -> str:
        """Describe what information flows between concepts."""
        if source.concept_name.lower() == target.concept_name.lower():
            return f"Enhanced understanding of {source.concept_name}"
        else:
            return f"Connecting {source.concept_name} to {target.concept_name}"

    def _determine_transformation_type(self, source: ConceptNode, target: ConceptNode) -> str:
        """Determine how information is transformed."""
        if target.explanation_depth > source.explanation_depth:
            return "deepening"
        elif len(target.related_entities) > len(source.related_entities):
            return "expansion"
        else:
            return "integration"

    def _assess_flow_quality(self, source: ConceptNode, target: ConceptNode) -> float:
        """Assess the quality of information flow."""
        # Base quality on confidence and coherence
        base_quality = (source.confidence + target.confidence) / 2

        # Map maturity levels for comparison
        maturity_mapping = {
            "mentioned": 1,
            "defined": 2,
            "explored": 3,
            "synthesized": 4,
            "criticized": 5,
            "evolved": 6,
        }
        source_level = maturity_mapping.get(source.maturity_level, 1)
        target_level = maturity_mapping.get(target.maturity_level, 1)

        # Boost for logical progression
        if target_level > source_level:
            base_quality += 0.2

        # Boost for temporal coherence
        if source.video_sequence_position < target.video_sequence_position:
            base_quality += 0.1

        return min(base_quality, 1.0)

    def _calculate_flow_coherence(self, source: ConceptNode, target: ConceptNode) -> float:
        """Calculate coherence of the flow."""
        # Based on entity overlap and concept similarity
        entity_overlap = len(
            set(source.related_entities).intersection(set(target.related_entities))
        )
        max_entities = max(len(source.related_entities), len(target.related_entities), 1)

        name_similarity = self._calculate_name_similarity(source.concept_name, target.concept_name)

        return (entity_overlap / max_entities + name_similarity) / 2

    def _calculate_temporal_gap(self, source: ConceptNode, target: ConceptNode) -> int:
        """Calculate temporal gap between concept appearances."""
        if source.video_id == target.video_id:
            return abs(target.timestamp - source.timestamp)
        else:
            # For different videos, use a large gap value
            return (
                target.video_sequence_position - source.video_sequence_position
            ) * 3600  # Assume 1 hour per video

    async def _analyze_concept_evolution_paths(
        self, concept_nodes: List[ConceptNode], videos: List[VideoIntelligence]
    ) -> List[ConceptEvolutionPath]:
        """Analyze how concepts evolve across videos."""
        logger.info("Analyzing concept evolution paths...")

        evolution_paths = []

        # Group nodes by concept name
        concept_groups = {}
        for node in concept_nodes:
            name = node.concept_name.lower()
            if name not in concept_groups:
                concept_groups[name] = []
            concept_groups[name].append(node)

        # Create evolution paths for concepts that appear multiple times
        for concept_name, nodes in concept_groups.items():
            if len(nodes) > 1:
                # Sort by video sequence and timestamp
                sorted_nodes = sorted(nodes, key=lambda n: (n.video_sequence_position, n.timestamp))

                evolution_path = ConceptEvolutionPath(
                    concept_name=concept_name.title(),
                    initial_maturity=(
                        sorted_nodes[0].maturity_level if sorted_nodes else "mentioned"
                    ),
                    final_maturity=sorted_nodes[-1].maturity_level if sorted_nodes else "mentioned",
                    progression_steps=[
                        {
                            "video_id": n.video_id,
                            "maturity_level": n.maturity_level,
                            "timestamp": n.timestamp,
                            "explanation_depth": n.explanation_depth,
                        }
                        for n in sorted_nodes
                    ],
                    key_dependencies=await self._identify_concept_dependencies(
                        sorted_nodes, videos
                    ),
                )
                evolution_paths.append(evolution_path)

        logger.info(f"Analyzed {len(evolution_paths)} concept evolution paths")
        return evolution_paths

    def _generate_evolution_summary(self, nodes: List[ConceptNode]) -> str:
        """Generate a summary of concept evolution."""
        if not nodes:
            return "No evolution path"

        start_maturity = nodes[0].maturity_level
        end_maturity = nodes[-1].maturity_level
        return f"Evolves from {start_maturity} to {end_maturity}"

    def _identify_key_transformations(self, nodes: List[ConceptNode]) -> List[str]:
        """Identify key transformation points in concept evolution."""
        transformations = []
        maturity_mapping = {
            "mentioned": 1,
            "introduced": 2,
            "defined": 3,
            "explained": 4,
            "explored": 5,
            "analyzed": 6,
            "synthesized": 7,
            "criticized": 8,
            "evolved": 9,
        }

        for i in range(len(nodes) - 1):
            current = nodes[i]
            next_node = nodes[i + 1]
            current_level = maturity_mapping.get(current.maturity_level, 0)
            next_level = maturity_mapping.get(next_node.maturity_level, 0)
            if next_level > current_level + 1:
                transformations.append(
                    f"Significant jump from {current.maturity_level} to {next_node.maturity_level} at video {next_node.video_sequence_position}"
                )
        return transformations

    def _identify_breakthrough_moments(self, nodes: List[ConceptNode]) -> List[Dict[str, Any]]:
        """Identify breakthrough moments in concept development."""
        breakthroughs = []
        maturity_mapping = {
            "mentioned": 1,
            "introduced": 2,
            "defined": 3,
            "explained": 4,
            "explored": 5,
            "analyzed": 6,
            "synthesized": 7,
            "criticized": 8,
            "evolved": 9,
        }
        for i in range(1, len(nodes)):
            current = nodes[i]
            previous = nodes[i - 1]
            current_level = maturity_mapping.get(current.maturity_level, 0)
            previous_level = maturity_mapping.get(previous.maturity_level, 0)
            if current_level >= previous_level + 2:
                breakthroughs.append(
                    {
                        "video_id": current.video_id,
                        "timestamp": current.timestamp,
                        "from_level": previous.maturity_level,
                        "to_level": current.maturity_level,
                        "concept": current.concept_name,
                        "description": f"Significant jump from {previous.maturity_level} to {current.maturity_level}",
                    }
                )
        return breakthroughs

    def _calculate_breakthrough_significance(
        self, node: ConceptNode, all_nodes: List[ConceptNode], index: int
    ) -> float:
        """Calculate the significance of a breakthrough moment."""
        significance = 0.0

        # Map maturity level to integer for calculation
        maturity_mapping = {
            "mentioned": 1,
            "defined": 2,
            "explored": 3,
            "synthesized": 4,
            "criticized": 5,
            "evolved": 6,
        }

        # Base significance on maturity level
        maturity_score = maturity_mapping.get(node.maturity_level, 1) / 6.0  # Normalize to 0-1
        significance += maturity_score * 0.2

        # Boost for explanation depth
        significance += node.explanation_depth * 0.3

        # Boost for confidence
        significance += node.confidence * 0.2

        # Boost for information density
        significance += node.information_density * 0.2

        # Boost for position in sequence (later developments may be more significant)
        sequence_position = index / len(all_nodes) if all_nodes else 0
        significance += sequence_position * 0.1

        return min(significance, 1.0)

    def _calculate_evolution_coherence(self, nodes: List[ConceptNode]) -> float:
        """Calculate how coherent the concept evolution is."""
        if len(nodes) < 2:
            return 1.0

        # Map maturity levels for comparison
        maturity_mapping = {
            "mentioned": 1,
            "defined": 2,
            "explored": 3,
            "synthesized": 4,
            "criticized": 5,
            "evolved": 6,
        }

        # Check for logical progression in maturity levels
        progression_score = 0.0
        for i in range(len(nodes) - 1):
            current_level = maturity_mapping.get(nodes[i].maturity_level, 1)
            next_level = maturity_mapping.get(nodes[i + 1].maturity_level, 1)
            if next_level >= current_level:
                progression_score += 1.0

        return progression_score / (len(nodes) - 1)

    def _calculate_completeness_score(self, nodes: List[ConceptNode]) -> float:
        """Calculate how complete the concept evolution is."""
        # Based on reaching higher maturity levels
        maturity_mapping = {
            "mentioned": 1,
            "defined": 2,
            "explored": 3,
            "synthesized": 4,
            "criticized": 5,
            "evolved": 6,
        }

        max_maturity = (
            max(maturity_mapping.get(node.maturity_level, 1) for node in nodes) if nodes else 1
        )
        max_possible = 6  # Maximum maturity level

        return max_maturity / max_possible

    async def _create_concept_clusters(
        self, concept_nodes: List[ConceptNode], concept_dependencies: List[ConceptDependency]
    ) -> List[ConceptCluster]:
        """Create clusters of related concepts."""
        logger.info("Creating concept clusters...")

        # Simple clustering based on shared entities and dependencies
        clusters = []
        clustered_concepts = set()

        for node in concept_nodes:
            if node.concept_name in clustered_concepts:
                continue

            # Find related concepts
            related_concepts = [node.concept_name]

            # Add concepts with shared entities
            for other_node in concept_nodes:
                if (
                    other_node.concept_name != node.concept_name
                    and other_node.concept_name not in clustered_concepts
                ):

                    # Check entity overlap
                    shared_entities = set(node.related_entities).intersection(
                        set(other_node.related_entities)
                    )
                    if len(shared_entities) > 0:
                        related_concepts.append(other_node.concept_name)

            # Add concepts with dependencies
            for dep in concept_dependencies:
                if dep.prerequisite_concept == node.concept_name:
                    if dep.dependent_concept not in related_concepts:
                        related_concepts.append(dep.dependent_concept)

            if len(related_concepts) > 1:  # Only create cluster if there are multiple concepts
                cluster = ConceptCluster(
                    cluster_id=f"cluster_{len(clusters)}",
                    cluster_name=f"{node.concept_name} cluster",
                    core_concepts=related_concepts,
                    cluster_evolution=f"Cluster of {len(related_concepts)} related concepts",
                    internal_relationships=concept_dependencies,
                    external_connections=[],  # Would need more analysis
                    coherence_score=0.7,  # Default
                    influence_score=0.5,  # Default
                    completeness=0.6,  # Default
                )
                clusters.append(cluster)
                clustered_concepts.update(related_concepts)

        logger.info(f"Created {len(clusters)} concept clusters")
        return clusters

    async def _analyze_flow_patterns(
        self,
        concept_nodes: List[ConceptNode],
        information_flows: List[InformationFlow],
        concept_dependencies: List[ConceptDependency],
    ) -> Dict[str, Any]:
        """Analyze information flow patterns."""
        logger.info("Analyzing flow patterns...")

        # Identify primary pathways (most frequent flow types)
        flow_types = {}
        for flow in information_flows:
            flow_types[flow.flow_type] = flow_types.get(flow.flow_type, 0) + 1

        primary_pathways = [
            f"{ftype}: {count} flows"
            for ftype, count in sorted(flow_types.items(), key=lambda x: x[1], reverse=True)
        ]

        # Identify bottlenecks (concepts with many dependencies)
        concept_dep_count = {}
        for dep in concept_dependencies:
            concept_dep_count[dep.prerequisite_concept] = (
                concept_dep_count.get(dep.prerequisite_concept, 0) + 1
            )

        bottlenecks = [concept for concept, count in concept_dep_count.items() if count > 2]

        # Identify information gaps (concepts without flows)
        concepts_in_flows = set()
        for flow in information_flows:
            concepts_in_flows.add(flow.source_node.concept_name)
            concepts_in_flows.add(flow.target_node.concept_name)

        all_concepts = {node.concept_name for node in concept_nodes}
        information_gaps = list(all_concepts - concepts_in_flows)

        # Calculate overall metrics
        avg_coherence = (
            sum(flow.coherence_score for flow in information_flows) / len(information_flows)
            if information_flows
            else 0.5
        )
        avg_quality = (
            sum(flow.flow_quality for flow in information_flows) / len(information_flows)
            if information_flows
            else 0.5
        )

        return {
            "primary_pathways": primary_pathways,
            "bottlenecks": bottlenecks,
            "gaps": information_gaps,
            "summary": f"Information flows through {len(primary_pathways)} main pathways with {len(bottlenecks)} bottlenecks",
            "progression": "Concepts develop through systematic information flow patterns",
            "complexity": f"Medium complexity with {len(information_flows)} total flows",
            "coherence": avg_coherence,
            "pedagogical": avg_quality,
            "density": len(information_flows) / len(concept_nodes) if concept_nodes else 0.0,
        }

    async def _ai_generate_flow_insights(
        self,
        concept_nodes: List[ConceptNode],
        information_flows: List[InformationFlow],
        evolution_paths: List[ConceptEvolutionPath],
        collection_title: str,
    ) -> List[str]:
        """Generate AI-powered insights about information flow."""
        try:
            # Prepare analysis data
            top_concepts = sorted(concept_nodes, key=lambda n: n.explanation_depth, reverse=True)[
                :10
            ]
            key_flows = sorted(information_flows, key=lambda f: f.flow_quality, reverse=True)[:10]

            prompt = f"""
            Analyze the information flow and concept evolution in this video collection: "{collection_title}"
            
            CONCEPT ANALYSIS:
            Total concepts tracked: {len(concept_nodes)}
            Information flows: {len(information_flows)}
            Evolution paths: {len(evolution_paths)}
            
            TOP CONCEPTS BY DEPTH:
            {chr(10).join(c.concept_name for c in top_concepts)}
            
            KEY INFORMATION FLOWS:
            {chr(10).join(f"{f.source_node.concept_name} → {f.target_node.concept_name} ({f.flow_type})" for f in key_flows)}
            
            EVOLUTION PATTERNS:
            {chr(10).join(p.evolution_summary for p in evolution_paths[:5] if p.evolution_summary)}
            
            Generate insights about:
            1. How information flows through the collection
            2. Which concepts are most critical to understanding
            3. How knowledge builds and evolves
            4. Pedagogical strengths and weaknesses
            5. Information architecture effectiveness
            6. Strategic implications for learning/understanding
            
            Format as bullet points, each 1-2 sentences.
            """

            response = await self.ai_model.generate_content_async(
                prompt, request_options={"timeout": 120 if len(concept_nodes) <= 5 else 300}
            )

            # Parse insights
            insights = []
            for line in response.text.strip().split("\n"):
                line = line.strip()
                if line and (line.startswith("-") or line.startswith("•")):
                    insights.append(line.lstrip("-•").strip())

            return insights[:7]  # Limit to 7 insights

        except Exception as e:
            logger.warning(f"AI flow insights generation failed: {e}")
            return self._template_generate_flow_insights(concept_nodes, information_flows)

    def _template_generate_flow_insights(
        self, concept_nodes: List[ConceptNode], information_flows: List[InformationFlow]
    ) -> List[str]:
        """Generate template-based flow insights."""
        insights = []

        if concept_nodes:
            # Map maturity levels to integers for comparison
            maturity_mapping = {
                "mentioned": 1,
                "defined": 2,
                "explored": 3,
                "synthesized": 4,
                "criticized": 5,
                "evolved": 6,
            }

            avg_maturity = sum(
                maturity_mapping.get(n.maturity_level, 1) for n in concept_nodes
            ) / len(concept_nodes)
            insights.append(
                f"Concept maturity averages {avg_maturity:.1f} across {len(concept_nodes)} concepts"
            )

        if information_flows:
            avg_quality = sum(f.flow_quality for f in information_flows) / len(information_flows)
            insights.append(
                f"Information flow quality averages {avg_quality:.2f} across {len(information_flows)} flows"
            )

        insights.append("Information flow shows systematic development across video collection")
        insights.append("Information architecture enables progressive understanding development")

        return insights

    # All knowledge panel methods have been removed - functionality moved to Chimera

    async def process_video_collection(
        self,
        videos: List[VideoIntelligence],
        collection_type: "VideoCollectionType",
        collection_title: str,
        user_confirmed_series: bool = False,
        core_only: bool = False,
    ) -> "MultiVideoIntelligence":
        """
        Process a collection of videos to extract unified intelligence.

        Args:
            videos: List of processed VideoIntelligence objects
            collection_type: Type of video collection
            collection_title: Title of the collection
            user_confirmed_series: Whether user confirmed this is a series
            core_only: If True, unify only entities that appear in more than one video.

        Returns:
            MultiVideoIntelligence object with unified analysis
        """
        logger.info(f"Processing video collection: {len(videos)} videos")

        # Generate collection ID
        collection_id = f"collection_{int(time.time())}_{len(videos)}"

        # Step 1: Extract and unify entities across videos
        unified_entities = await self._unify_entities_across_videos(videos, core_only=core_only)

        # Step 2: Extract cross-video relationships
        cross_video_relationships = await self._extract_cross_video_relationships(
            videos, unified_entities
        )

        # Step 3: Generate unified knowledge graph
        unified_knowledge_graph = await self._generate_unified_knowledge_graph(
            videos, unified_entities, cross_video_relationships
        )

        # Step 4: Synthesize information flow map
        information_flow_map = await self._synthesize_information_flow_map(
            videos, unified_entities, cross_video_relationships, collection_id, collection_title
        )
        # Ensure pydantic-friendly mapping for tests that patch with Mock
        if not isinstance(information_flow_map, dict):
            try:
                dumped = information_flow_map.model_dump()  # type: ignore[attr-defined]
                if isinstance(dumped, dict):
                    information_flow_map = dumped
                else:
                    raise TypeError("model_dump did not return dict")
            except Exception:
                information_flow_map = {
                    "map_id": collection_id,
                    "collection_id": collection_id,
                    "collection_title": collection_title,
                    "concept_nodes": [],
                    "information_flows": [],
                    "concept_dependencies": [],
                    "evolution_paths": [],
                    "concept_clusters": [],
                    "primary_information_pathways": [],
                    "knowledge_bottlenecks": [],
                    "information_gaps": [],
                    "flow_summary": "",
                    "learning_progression": "",
                    "concept_complexity": "",
                    "strategic_insights": [],
                    "overall_coherence": 0.0,
                    "pedagogical_quality": 0.0,
                    "information_density": 0.0,
                    "total_concepts": 0,
                    "total_flows": 0,
                    "synthesis_quality": "",
                }

        # Step 5: Generate key insights
        key_insights = await self._generate_collection_insights(
            videos, unified_entities, cross_video_relationships
        )

        # Step 6: Calculate quality metrics
        entity_resolution_quality = self._calculate_entity_resolution_quality(unified_entities)
        narrative_coherence = self._calculate_narrative_coherence(videos, cross_video_relationships)

        # Step 7: Calculate total processing cost
        total_processing_cost = sum(getattr(v, "processing_cost", 0.0) for v in videos)

        # Create MultiVideoIntelligence object
        from clipscribe.models import MultiVideoIntelligence

        multi_video_result = MultiVideoIntelligence(
            collection_id=collection_id,
            collection_title=collection_title,
            collection_type=collection_type,
            collection_summary=f"Automated summary of {len(videos)} {collection_type.value} videos",  # Include count
            video_ids=[v.metadata.video_id for v in videos],
            video_titles=[v.metadata.title for v in videos],
            videos=videos,  # Include the actual video objects
            unified_entities=unified_entities,
            cross_video_relationships=cross_video_relationships,
            unified_knowledge_graph=unified_knowledge_graph,
            information_flow_map=information_flow_map,
            key_insights=key_insights,
            entity_resolution_quality=entity_resolution_quality,
            narrative_coherence=narrative_coherence,
            total_processing_cost=total_processing_cost,
            consolidated_timeline=None,
            processing_stats={
                "videos_processed": len(videos),
                "entities_unified": len(unified_entities),
                "relationships_cross_video": len(cross_video_relationships),
                "concepts_tracked": (lambda seq: len(seq) if isinstance(seq, list) else 0)(
                    information_flow_map.get("concept_nodes", [])
                    if isinstance(information_flow_map, dict)
                    else getattr(information_flow_map, "concept_nodes", [])
                ),
                "information_flows": (lambda seq: len(seq) if isinstance(seq, list) else 0)(
                    information_flow_map.get("information_flows", [])
                    if isinstance(information_flow_map, dict)
                    else getattr(information_flow_map, "information_flows", [])
                ),
            },
        )

        logger.info(
            f"Successfully processed video collection with {len(videos)} videos, {len(unified_entities)} unified entities and {len(cross_video_relationships)} cross-video relationships"
        )
        logger.info(
            f"Collection summary set to: {multi_video_result.collection_summary}"
        )  # Debug log
        return multi_video_result

    async def _unify_entities_across_videos(
        self, videos: List[VideoIntelligence], core_only: bool = False
    ) -> List["CrossVideoEntity"]:
        """
        Unify entities across multiple videos.
        - Default (core_only=False): Comprehensive Union strategy. Retains all unique entities.
        - Core Theme (core_only=True): Intersection strategy. Retains only entities that appear in more than one video.
        """
        if core_only:
            logger.info("Unifying entities using Core Theme Analysis (Intersection)...")
        else:
            logger.info("Unifying entities using Comprehensive Union...")

        all_entities_with_source = []
        for video in videos:
            for entity in video.entities:
                all_entities_with_source.append(
                    {
                        "entity": entity,
                        "video_id": video.metadata.video_id,
                        "video_title": video.metadata.title,
                    }
                )

        # Normalize to simple structures with names and types to handle EnhancedEntity vs Entity
        all_raw_entities = [item["entity"] for item in all_entities_with_source]
        entity_groups = self.entity_normalizer._group_similar_entities(all_raw_entities)

        unified_entities = []
        for group in entity_groups:
            if not group:
                continue

            video_ids_in_group = set()
            for entity_obj in group:
                for source_item in all_entities_with_source:
                    if source_item["entity"] == entity_obj:
                        video_ids_in_group.add(source_item["video_id"])

            # This is the new logic based on the core_only flag
            if core_only and len(video_ids_in_group) <= 1:
                continue

            # Support both .entity (Entity) and .name (EnhancedEntity)
            def _ename(e):
                return getattr(e, "entity", getattr(e, "name", ""))

            def _etype(e):
                return getattr(e, "type", "unknown")

            def _mentions(e):
                return getattr(e, "mention_count", 1)

            canonical_name = Counter(_ename(e) for e in group).most_common(1)[0][0]
            canonical_entity = next((e for e in group if _ename(e) == canonical_name), group[0])
            aliases = list(set(_ename(e) for e in group if _ename(e) != canonical_name))
            total_mentions = sum(_mentions(e) for e in group)

            from clipscribe.models import CrossVideoEntity

            cross_video_entity = CrossVideoEntity(
                name=canonical_name,
                type=_etype(canonical_entity),
                canonical_name=canonical_name,
                aliases=aliases,
                video_appearances=list(video_ids_in_group),
                mention_count=total_mentions,
            )
            unified_entities.append(cross_video_entity)

        logger.info(
            f"Unified to {len(unified_entities)} unique entities across {len(videos)} videos"
        )
        return unified_entities

    async def _extract_cross_video_relationships(
        self, videos: List[VideoIntelligence], unified_entities: List["CrossVideoEntity"]
    ) -> List["CrossVideoRelationship"]:
        """Extract relationships that span across multiple videos."""
        logger.info("Extracting cross-video relationships...")

        cross_video_relationships = []

        # For now, create simple cross-video relationships based on shared entities
        # In a full implementation, this would use more sophisticated analysis

        for i, entity1 in enumerate(unified_entities):
            for entity2 in unified_entities[i + 1 :]:
                # Check if these entities appear together in any video
                shared_videos = set(entity1.video_appearances).intersection(
                    set(entity2.video_appearances)
                )

                if (
                    len(shared_videos) > 1
                ):  # Only create relationship if entities appear together in multiple videos
                    from clipscribe.models import CrossVideoRelationship

                    relationship = CrossVideoRelationship(
                        subject=entity1.name,
                        predicate="co_occurs_with",
                        object=entity2.name,
                        mention_count=len(shared_videos),
                        video_sources=list(shared_videos),
                    )
                    cross_video_relationships.append(relationship)

        logger.info(f"Extracted {len(cross_video_relationships)} cross-video relationships")
        return cross_video_relationships

    async def _generate_unified_knowledge_graph(
        self,
        videos: List[VideoIntelligence],
        unified_entities: List["CrossVideoEntity"],
        cross_video_relationships: List["CrossVideoRelationship"],
    ) -> Dict[str, Any]:
        """Generate a unified knowledge graph from all videos."""
        logger.info("Generating unified knowledge graph...")

        # Create nodes from unified entities
        nodes = []
        for entity in unified_entities:
            nodes.append(
                {
                    "id": entity.name,
                    "label": entity.name,
                    "type": entity.type,
                    "mention_count": entity.mention_count,
                    "occurrences": len(entity.video_appearances),
                }
            )

        # Create edges from cross-video relationships
        edges = []
        for rel in cross_video_relationships:
            edges.append(
                {
                    "source": rel.subject,
                    "target": rel.object,
                    "label": rel.predicate,
                    "mention_count": rel.mention_count,
                    "type": "cross_video_relationship",
                }
            )

        # Add edges from individual video relationships
        for video in videos:
            for rel in getattr(video, "relationships", []):
                edges.append(
                    {
                        "source": rel.subject,
                        "target": rel.object,
                        "label": rel.predicate,
                        "confidence": getattr(rel, "confidence", 0.5),
                        "type": "intra_video",
                        "video_id": video.metadata.video_id,
                    }
                )

        unified_graph = {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "graph_type": "unified_multi_video",
            "collection_stats": {
                "videos": len(videos),
                "unified_entities": len(unified_entities),
                "cross_video_relationships": len(cross_video_relationships),
            },
        }

        logger.info(
            f"Generated unified knowledge graph with {len(nodes)} nodes and {len(edges)} edges"
        )
        return unified_graph

    async def _generate_collection_insights(
        self,
        videos: List[VideoIntelligence],
        unified_entities: List["CrossVideoEntity"],
        cross_video_relationships: List["CrossVideoRelationship"],
    ) -> List[str]:
        """Generate key insights about the video collection."""
        logger.info("Generating collection insights...")

        insights = []

        # Entity insights
        if unified_entities:
            top_entities = sorted(unified_entities, key=lambda e: e.mention_count, reverse=True)[:5]
            insights.append(
                f"Most frequently mentioned entities: {', '.join(e.name for e in top_entities)}"
            )

        # Relationship insights
        if cross_video_relationships:
            insights.append(f"Found {len(cross_video_relationships)} cross-video relationships")

        # Content insights
        total_key_points = sum(len(v.key_points) for v in videos)
        insights.append(
            f"Collection contains {total_key_points} key insights across {len(videos)} videos"
        )

        # Cost insights
        total_cost = sum(getattr(v, "processing_cost", 0.0) for v in videos)
        insights.append(f"Total processing cost: ${total_cost:.4f}")

        return insights

    def _calculate_entity_resolution_quality(
        self, unified_entities: List["CrossVideoEntity"]
    ) -> float:
        """Calculate the quality of entity resolution across videos."""
        if not unified_entities:
            return 0.0

        # Calculate average mention frequency across videos (confidence-free architecture)
        avg_mention_freq = sum(e.mention_count for e in unified_entities) / len(unified_entities)
        # Normalize to 0-1 range (assuming max ~20 mentions per entity across videos)
        normalized_freq = min(1.0, avg_mention_freq / 20.0)

        # Bonus for entities that appear in multiple videos
        multi_video_bonus = sum(1 for e in unified_entities if len(e.video_appearances) > 1) / len(
            unified_entities
        )

        return min(1.0, normalized_freq + multi_video_bonus * 0.2)

    def _calculate_narrative_coherence(
        self,
        videos: List[VideoIntelligence],
        cross_video_relationships: List["CrossVideoRelationship"],
    ) -> float:
        """Calculate the narrative coherence of the video collection."""
        if len(videos) < 2:
            return 1.0

        # Simple coherence based on cross-video relationships
        relationship_density = len(cross_video_relationships) / (
            len(videos) * (len(videos) - 1) / 2
        )

        # Normalize to 0-1 range
        return min(1.0, relationship_density * 10)
