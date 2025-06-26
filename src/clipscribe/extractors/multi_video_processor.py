"""
Multi-Video Intelligence Processor for ClipScribe.

Handles cross-video entity resolution, relationship bridging, narrative flow analysis,
and unified knowledge graph generation with aggressive AI-powered entity merging.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
from collections import defaultdict, Counter
import json

from ..models import (
    VideoIntelligence, MultiVideoIntelligence, CrossVideoEntity, 
    CrossVideoRelationship, NarrativeSegment, TopicEvolution,
    VideoCollectionType, SeriesMetadata, Entity, Relationship, Topic
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
    """
    
    def __init__(self, use_ai_validation: bool = True):
        """
        Initialize multi-video processor.
        
        Args:
            use_ai_validation: Whether to use AI for entity validation and merging
        """
        self.entity_normalizer = EntityNormalizer(similarity_threshold=0.85)  # Aggressive merging
        self.series_detector = SeriesDetector(similarity_threshold=0.7)
        self.use_ai_validation = use_ai_validation
        self.settings = Settings()
        
        # AI validation setup
        if use_ai_validation:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.settings.google_api_key)
                self.ai_model = genai.GenerativeModel('gemini-1.5-flash')
            except Exception as e:
                logger.warning(f"AI validation unavailable: {e}")
                self.use_ai_validation = False
    
    async def process_video_collection(
        self, 
        videos: List[VideoIntelligence],
        collection_type: VideoCollectionType = VideoCollectionType.CUSTOM_COLLECTION,
        collection_title: Optional[str] = None,
        user_confirmed_series: bool = False
    ) -> MultiVideoIntelligence:
        """
        Process a collection of videos to extract unified intelligence.
        
        Args:
            videos: List of VideoIntelligence objects
            collection_type: Type of collection for processing strategy
            collection_title: Optional custom title
            user_confirmed_series: Whether user confirmed this is a series
            
        Returns:
            MultiVideoIntelligence with unified analysis
        """
        if not videos:
            raise ValueError("Cannot process empty video collection")
        
        logger.info(f"Processing collection of {len(videos)} videos (type: {collection_type})")
        
        # Step 1: Series detection (if not user-confirmed)
        series_metadata = None
        if collection_type == VideoCollectionType.SERIES or user_confirmed_series:
            if not user_confirmed_series:
                detection_result = await self.series_detector.detect_series(videos)
                if detection_result.is_series:
                    series_metadata = self.series_detector.create_series_metadata(videos, detection_result)
            else:
                # Create series metadata for user-confirmed series
                series_metadata = SeriesMetadata(
                    series_id=f"user_series_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    series_title=collection_title or f"{videos[0].metadata.channel} Series",
                    total_parts=len(videos),
                    confidence=1.0
                )
        
        # Step 2: Cross-video entity resolution
        unified_entities = await self._resolve_cross_video_entities(videos)
        
        # Step 3: Cross-video relationship extraction
        cross_video_relationships = await self._extract_cross_video_relationships(videos, unified_entities)
        
        # Step 4: Topic evolution analysis
        topic_evolution = self._analyze_topic_evolution(videos)
        
        # Step 5: Unified topic extraction
        unified_topics = self._extract_unified_topics(videos, topic_evolution)
        
        # Step 6: Narrative flow analysis (for series)
        narrative_flow = []
        if series_metadata:
            narrative_flow = await self._analyze_narrative_flow(videos, unified_entities)
        
        # Step 7: Generate collection summary
        collection_summary = await self._generate_collection_summary(videos, unified_entities, cross_video_relationships)
        
        # Step 8: Extract key insights
        key_insights = await self._extract_key_insights(videos, unified_entities, cross_video_relationships, topic_evolution)
        
        # Step 9: Generate unified knowledge graph
        unified_knowledge_graph = self._generate_unified_knowledge_graph(unified_entities, cross_video_relationships)
        
        # Step 10: Calculate quality metrics
        quality_metrics = self._calculate_quality_metrics(videos, unified_entities, cross_video_relationships)
        
        # Create collection ID and title
        collection_id = f"collection_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(videos)}"
        if not collection_title:
            if series_metadata:
                collection_title = series_metadata.series_title
            else:
                collection_title = f"{videos[0].metadata.channel} - {len(videos)} Videos"
        
        # Calculate processing stats
        total_cost = sum(video.processing_cost for video in videos)
        total_time = sum(video.processing_time for video in videos)
        
        return MultiVideoIntelligence(
            collection_id=collection_id,
            collection_type=collection_type,
            collection_title=collection_title,
            video_ids=[video.metadata.video_id for video in videos],
            videos=videos,
            series_metadata=series_metadata,
            narrative_flow=narrative_flow,
            unified_entities=unified_entities,
            cross_video_relationships=cross_video_relationships,
            unified_topics=unified_topics,
            topic_evolution=topic_evolution,
            collection_summary=collection_summary,
            key_insights=key_insights,
            unified_knowledge_graph=unified_knowledge_graph,
            total_processing_cost=total_cost,
            total_processing_time=total_time,
            **quality_metrics
        )
    
    async def _resolve_cross_video_entities(self, videos: List[VideoIntelligence]) -> List[CrossVideoEntity]:
        """Resolve entities across videos with aggressive AI-powered merging."""
        logger.info("Resolving entities across videos...")
        
        # Collect all entities from all videos
        all_entities = []
        entity_video_map = {}  # entity -> video info
        
        for video in videos:
            for entity in video.entities:
                # Add video context to entity
                entity_with_context = Entity(
                    name=entity.name,
                    type=entity.type,
                    confidence=entity.confidence,
                    properties={
                        **entity.properties,
                        'source_video_id': video.metadata.video_id,
                        'source_video_title': video.metadata.title,
                        'source_video_published': video.metadata.published_at.isoformat()
                    },
                    timestamp=entity.timestamp
                )
                all_entities.append(entity_with_context)
                
                # Track which video this entity came from
                if entity.name not in entity_video_map:
                    entity_video_map[entity.name] = []
                entity_video_map[entity.name].append({
                    'video_id': video.metadata.video_id,
                    'video_title': video.metadata.title,
                    'confidence': entity.confidence,
                    'timestamp': entity.timestamp
                })
        
        # Use aggressive entity normalization
        normalized_entities = self.entity_normalizer.normalize_entities(all_entities)
        
        # Convert to CrossVideoEntity objects
        cross_video_entities = []
        entity_aliases = self.entity_normalizer.get_entity_aliases(normalized_entities)
        
        for entity in normalized_entities:
            # Find all videos where this entity (or its aliases) appears
            video_appearances = set()
            source_videos = []
            all_names = [entity.name] + entity_aliases.get(entity.name, [])
            
            for name in all_names:
                if name in entity_video_map:
                    for video_info in entity_video_map[name]:
                        video_appearances.add(video_info['video_id'])
                        source_videos.append(video_info)
            
            # Calculate aggregated confidence and temporal info
            confidences = [info['confidence'] for info in source_videos]
            avg_confidence = sum(confidences) / len(confidences) if confidences else entity.confidence
            
            # Find first and last mentions
            video_dates = []
            for video in videos:
                if video.metadata.video_id in video_appearances:
                    video_dates.append(video.metadata.published_at)
            
            first_mentioned = min(video_dates) if video_dates else None
            last_mentioned = max(video_dates) if video_dates else None
            
            cross_video_entity = CrossVideoEntity(
                name=entity.name,
                type=entity.type,
                canonical_name=entity.name,
                aliases=entity_aliases.get(entity.name, []),
                video_appearances=list(video_appearances),
                aggregated_confidence=avg_confidence,
                first_mentioned=first_mentioned,
                last_mentioned=last_mentioned,
                mention_count=len(source_videos),
                properties=entity.properties,
                source_videos=source_videos
            )
            cross_video_entities.append(cross_video_entity)
        
        # AI validation of entity merging (if enabled)
        if self.use_ai_validation and len(cross_video_entities) > 10:
            cross_video_entities = await self._ai_validate_entity_merging(cross_video_entities, videos)
        
        logger.info(f"Resolved {len(all_entities)} entities to {len(cross_video_entities)} cross-video entities")
        return cross_video_entities
    
    async def _extract_cross_video_relationships(
        self, 
        videos: List[VideoIntelligence], 
        unified_entities: List[CrossVideoEntity]
    ) -> List[CrossVideoRelationship]:
        """Extract relationships that span or are confirmed across multiple videos."""
        logger.info("Extracting cross-video relationships...")
        
        # Create entity lookup for normalization
        entity_lookup = {}
        for entity in unified_entities:
            entity_lookup[entity.canonical_name.lower()] = entity.canonical_name
            for alias in entity.aliases:
                entity_lookup[alias.lower()] = entity.canonical_name
        
        # Collect all relationships from all videos
        all_relationships = []
        relationship_video_map = defaultdict(list)
        
        for video in videos:
            if hasattr(video, 'relationships') and video.relationships:
                for rel in video.relationships:
                    # Normalize entity names using cross-video entities
                    subject = entity_lookup.get(rel.subject.lower(), rel.subject)
                    object_name = entity_lookup.get(rel.object.lower(), rel.object)
                    
                    # Create normalized relationship
                    normalized_rel = Relationship(
                        subject=subject,
                        predicate=rel.predicate,
                        object=object_name,
                        confidence=rel.confidence,
                        context=rel.context
                    )
                    
                    # Create relationship key for deduplication
                    rel_key = (subject.lower(), rel.predicate.lower(), object_name.lower())
                    
                    relationship_video_map[rel_key].append({
                        'video_id': video.metadata.video_id,
                        'video_title': video.metadata.title,
                        'relationship': normalized_rel,
                        'published_at': video.metadata.published_at,
                        'context': rel.context
                    })
        
        # Create cross-video relationships
        cross_video_relationships = []
        
        for rel_key, video_instances in relationship_video_map.items():
            subject, predicate, object_name = rel_key
            
            # Calculate aggregated confidence
            confidences = [instance['relationship'].confidence for instance in video_instances]
            avg_confidence = sum(confidences) / len(confidences)
            
            # Boost confidence if relationship appears in multiple videos
            if len(video_instances) > 1:
                avg_confidence = min(1.0, avg_confidence * (1 + 0.1 * (len(video_instances) - 1)))
            
            # Get temporal info
            dates = [instance['published_at'] for instance in video_instances]
            first_mentioned = min(dates) if dates else None
            
            # Collect context examples
            context_examples = [
                instance['context'] for instance in video_instances 
                if instance['context']
            ][:3]  # Keep top 3 examples
            
            cross_video_rel = CrossVideoRelationship(
                subject=video_instances[0]['relationship'].subject,
                predicate=video_instances[0]['relationship'].predicate,
                object=video_instances[0]['relationship'].object,
                confidence=avg_confidence,
                video_sources=[instance['video_id'] for instance in video_instances],
                first_mentioned=first_mentioned,
                mention_count=len(video_instances),
                context_examples=context_examples,
                properties={
                    'cross_video_validated': len(video_instances) > 1,
                    'source_count': len(video_instances)
                }
            )
            cross_video_relationships.append(cross_video_rel)
        
        logger.info(f"Extracted {len(cross_video_relationships)} cross-video relationships")
        return cross_video_relationships
    
    def _analyze_topic_evolution(self, videos: List[VideoIntelligence]) -> List[TopicEvolution]:
        """Analyze how topics evolve across videos."""
        logger.info("Analyzing topic evolution...")
        
        # Sort videos by publication date
        sorted_videos = sorted(videos, key=lambda v: v.metadata.published_at)
        
        # Collect all topics across videos
        topic_video_map = defaultdict(list)
        
        for video in sorted_videos:
            for topic in video.topics:
                topic_video_map[topic.name.lower()].append({
                    'video_id': video.metadata.video_id,
                    'video_title': video.metadata.title,
                    'confidence': topic.confidence,
                    'published_at': video.metadata.published_at,
                    'video_index': sorted_videos.index(video)
                })
        
        # Create topic evolution objects
        topic_evolutions = []
        
        for topic_name, appearances in topic_video_map.items():
            if len(appearances) > 1:  # Only topics that appear in multiple videos
                # Sort by video order
                appearances.sort(key=lambda x: x['video_index'])
                
                # Generate evolution summary
                evolution_summary = f"Topic '{topic_name}' evolves across {len(appearances)} videos"
                
                # Track sentiment evolution (placeholder - would need sentiment analysis)
                sentiment_evolution = [0.5] * len(appearances)  # Neutral for now
                
                # Track key milestones
                key_milestones = [
                    {
                        'video_index': appearance['video_index'],
                        'video_title': appearance['video_title'],
                        'milestone': f"Topic discussed with {appearance['confidence']:.2f} confidence",
                        'date': appearance['published_at'].isoformat()
                    }
                    for appearance in appearances
                ]
                
                topic_evolution = TopicEvolution(
                    topic_name=topic_name,
                    video_sequence=[app['video_id'] for app in appearances],
                    evolution_summary=evolution_summary,
                    key_milestones=key_milestones,
                    sentiment_evolution=sentiment_evolution,
                    entity_changes={}  # Would need more sophisticated analysis
                )
                topic_evolutions.append(topic_evolution)
        
        logger.info(f"Analyzed evolution of {len(topic_evolutions)} topics")
        return topic_evolutions
    
    def _extract_unified_topics(self, videos: List[VideoIntelligence], topic_evolution: List[TopicEvolution]) -> List[Topic]:
        """Extract unified topics across all videos."""
        # Collect all topics and their confidences
        topic_confidences = defaultdict(list)
        
        for video in videos:
            for topic in video.topics:
                topic_confidences[topic.name.lower()].append(topic.confidence)
        
        # Create unified topics with aggregated confidence
        unified_topics = []
        for topic_name, confidences in topic_confidences.items():
            avg_confidence = sum(confidences) / len(confidences)
            
            # Boost confidence for topics that appear in multiple videos
            if len(confidences) > 1:
                avg_confidence = min(1.0, avg_confidence * (1 + 0.05 * (len(confidences) - 1)))
            
            unified_topic = Topic(
                name=topic_name,
                confidence=avg_confidence
            )
            unified_topics.append(unified_topic)
        
        # Sort by confidence
        unified_topics.sort(key=lambda t: t.confidence, reverse=True)
        
        return unified_topics
    
    async def _analyze_narrative_flow(
        self, 
        videos: List[VideoIntelligence], 
        unified_entities: List[CrossVideoEntity]
    ) -> List[NarrativeSegment]:
        """Analyze narrative flow across videos in a series."""
        logger.info("Analyzing narrative flow...")
        
        # Sort videos by publication date or detected order
        sorted_videos = sorted(videos, key=lambda v: v.metadata.published_at)
        
        narrative_segments = []
        
        for i, video in enumerate(sorted_videos):
            # Create narrative segments from key points
            for j, key_point in enumerate(video.key_points[:5]):  # Top 5 key points per video
                segment_id = f"segment_{video.metadata.video_id}_{j}"
                
                # Find entities mentioned in this key point
                key_entities = []
                for entity in unified_entities:
                    if any(video.metadata.video_id in entity.video_appearances for video in videos):
                        # Simple check if entity name appears in key point text
                        if entity.canonical_name.lower() in key_point.text.lower():
                            key_entities.append(entity.canonical_name)
                
                # Determine connections to other segments (simplified)
                connects_to = []
                if i > 0:  # Connect to previous video's segments
                    connects_to.append(f"segment_{sorted_videos[i-1].metadata.video_id}_0")
                
                narrative_segment = NarrativeSegment(
                    segment_id=segment_id,
                    title=f"Part {i+1}: {key_point.text[:50]}...",
                    video_id=video.metadata.video_id,
                    start_time=key_point.timestamp,
                    end_time=key_point.timestamp + 30,  # Assume 30-second segments
                    summary=key_point.text,
                    key_entities=key_entities,
                    narrative_importance=key_point.importance,
                    connects_to=connects_to
                )
                narrative_segments.append(narrative_segment)
        
        return narrative_segments
    
    async def _generate_collection_summary(
        self, 
        videos: List[VideoIntelligence], 
        unified_entities: List[CrossVideoEntity], 
        cross_video_relationships: List[CrossVideoRelationship]
    ) -> str:
        """Generate a comprehensive summary of the video collection."""
        if self.use_ai_validation:
            return await self._ai_generate_collection_summary(videos, unified_entities, cross_video_relationships)
        else:
            return self._template_generate_collection_summary(videos, unified_entities, cross_video_relationships)
    
    async def _ai_generate_collection_summary(
        self, 
        videos: List[VideoIntelligence], 
        unified_entities: List[CrossVideoEntity], 
        cross_video_relationships: List[CrossVideoRelationship]
    ) -> str:
        """Use AI to generate a comprehensive collection summary."""
        try:
            # Prepare context for AI
            video_summaries = [f"Video {i+1}: {video.summary}" for i, video in enumerate(videos)]
            key_entities = [f"{entity.canonical_name} ({entity.type})" for entity in unified_entities[:10]]
            key_relationships = [f"{rel.subject} {rel.predicate} {rel.object}" for rel in cross_video_relationships[:10]]
            
            prompt = f"""
            Analyze this collection of {len(videos)} videos and provide a comprehensive summary.
            
            Video Summaries:
            {chr(10).join(video_summaries)}
            
            Key Entities:
            {', '.join(key_entities)}
            
            Key Relationships:
            {chr(10).join(key_relationships)}
            
            Provide a 2-3 paragraph summary that:
            1. Explains the overall theme and purpose of this video collection
            2. Highlights the main entities and their roles
            3. Describes key relationships and developments across videos
            4. Notes any narrative progression or evolution of topics
            """
            
            response = await self.ai_model.generate_content_async(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.warning(f"AI summary generation failed: {e}")
            return self._template_generate_collection_summary(videos, unified_entities, cross_video_relationships)
    
    def _template_generate_collection_summary(
        self, 
        videos: List[VideoIntelligence], 
        unified_entities: List[CrossVideoEntity], 
        cross_video_relationships: List[CrossVideoRelationship]
    ) -> str:
        """Generate a template-based collection summary."""
        # Basic template summary
        total_duration = sum(video.metadata.duration for video in videos)
        avg_duration = total_duration / len(videos)
        
        top_entities = sorted(unified_entities, key=lambda e: e.mention_count, reverse=True)[:5]
        entity_names = [entity.canonical_name for entity in top_entities]
        
        summary = f"""
        This collection contains {len(videos)} videos with a total duration of {total_duration/3600:.1f} hours 
        (average {avg_duration/60:.1f} minutes per video). 
        
        The videos feature {len(unified_entities)} unique entities, with the most prominent being: 
        {', '.join(entity_names)}. 
        
        Across all videos, {len(cross_video_relationships)} relationships were identified, 
        indicating strong thematic connections and narrative continuity.
        """.strip()
        
        return summary
    
    async def _extract_key_insights(
        self, 
        videos: List[VideoIntelligence], 
        unified_entities: List[CrossVideoEntity], 
        cross_video_relationships: List[CrossVideoRelationship],
        topic_evolution: List[TopicEvolution]
    ) -> List[str]:
        """Extract key insights from cross-video analysis."""
        insights = []
        
        # Entity insights
        multi_video_entities = [e for e in unified_entities if len(e.video_appearances) > 1]
        if multi_video_entities:
            insights.append(f"{len(multi_video_entities)} entities appear across multiple videos, indicating strong thematic connections")
        
        # Relationship insights
        cross_validated_rels = [r for r in cross_video_relationships if len(r.video_sources) > 1]
        if cross_validated_rels:
            insights.append(f"{len(cross_validated_rels)} relationships are validated across multiple videos")
        
        # Topic evolution insights
        evolving_topics = [t for t in topic_evolution if len(t.video_sequence) > 2]
        if evolving_topics:
            insights.append(f"{len(evolving_topics)} topics show clear evolution across the video series")
        
        # Temporal insights
        if len(videos) > 1:
            time_span = (videos[-1].metadata.published_at - videos[0].metadata.published_at).days
            insights.append(f"Videos span {time_span} days, showing temporal development of content")
        
        # Quality insights
        avg_entity_confidence = sum(e.aggregated_confidence for e in unified_entities) / len(unified_entities)
        if avg_entity_confidence > 0.8:
            insights.append("High-confidence entity extraction indicates reliable content analysis")
        
        return insights
    
    def _generate_unified_knowledge_graph(
        self, 
        unified_entities: List[CrossVideoEntity], 
        cross_video_relationships: List[CrossVideoRelationship]
    ) -> Dict[str, Any]:
        """Generate unified knowledge graph from cross-video intelligence."""
        # Create nodes from entities
        nodes = []
        for entity in unified_entities:
            node = {
                'id': entity.canonical_name,
                'label': entity.canonical_name,
                'type': entity.type,
                'confidence': entity.aggregated_confidence,
                'video_appearances': entity.video_appearances,
                'mention_count': entity.mention_count,
                'aliases': entity.aliases
            }
            nodes.append(node)
        
        # Create edges from relationships
        edges = []
        for rel in cross_video_relationships:
            edge = {
                'source': rel.subject,
                'target': rel.object,
                'predicate': rel.predicate,
                'confidence': rel.confidence,
                'video_sources': rel.video_sources,
                'mention_count': rel.mention_count
            }
            edges.append(edge)
        
        # Calculate graph metrics
        node_count = len(nodes)
        edge_count = len(edges)
        density = (2 * edge_count) / (node_count * (node_count - 1)) if node_count > 1 else 0
        
        return {
            'nodes': nodes,
            'edges': edges,
            'metrics': {
                'node_count': node_count,
                'edge_count': edge_count,
                'density': density,
                'cross_video_entities': len([e for e in unified_entities if len(e.video_appearances) > 1]),
                'cross_video_relationships': len([r for r in cross_video_relationships if len(r.video_sources) > 1])
            }
        }
    
    def _calculate_quality_metrics(
        self, 
        videos: List[VideoIntelligence], 
        unified_entities: List[CrossVideoEntity], 
        cross_video_relationships: List[CrossVideoRelationship]
    ) -> Dict[str, float]:
        """Calculate quality metrics for multi-video analysis."""
        # Entity resolution quality
        total_original_entities = sum(len(video.entities) for video in videos)
        compression_ratio = len(unified_entities) / total_original_entities if total_original_entities > 0 else 0
        entity_resolution_quality = 1.0 - compression_ratio  # Higher compression = better resolution
        
        # Narrative coherence (based on cross-video connections)
        cross_video_entity_ratio = len([e for e in unified_entities if len(e.video_appearances) > 1]) / len(unified_entities)
        narrative_coherence = cross_video_entity_ratio
        
        # Information completeness (based on relationship density)
        if len(unified_entities) > 1:
            max_possible_relationships = len(unified_entities) * (len(unified_entities) - 1)
            relationship_density = len(cross_video_relationships) / max_possible_relationships
            information_completeness = min(1.0, relationship_density * 10)  # Scale appropriately
        else:
            information_completeness = 0.0
        
        return {
            'entity_resolution_quality': entity_resolution_quality,
            'narrative_coherence': narrative_coherence,
            'information_completeness': information_completeness
        }
    
    async def _ai_validate_entity_merging(
        self, 
        entities: List[CrossVideoEntity], 
        videos: List[VideoIntelligence]
    ) -> List[CrossVideoEntity]:
        """Use AI to validate and improve entity merging."""
        try:
            # Focus on entities that appear in multiple videos
            multi_video_entities = [e for e in entities if len(e.video_appearances) > 1]
            
            if not multi_video_entities:
                return entities
            
            # Prepare validation prompt
            entity_descriptions = []
            for entity in multi_video_entities[:20]:  # Limit to avoid token limits
                videos_info = f"Videos: {', '.join(entity.video_appearances)}"
                aliases_info = f"Aliases: {', '.join(entity.aliases)}" if entity.aliases else "No aliases"
                entity_descriptions.append(f"{entity.canonical_name} ({entity.type}) - {videos_info}, {aliases_info}")
            
            prompt = f"""
            Review these entities that appear across multiple videos and validate the merging:
            
            {chr(10).join(entity_descriptions)}
            
            For each entity, determine if:
            1. The entity merging is correct (same real-world entity)
            2. Any entities should be split (different real-world entities incorrectly merged)
            3. Any additional aliases should be noted
            
            Respond with "VALIDATED" if all merging looks correct, or suggest specific corrections.
            """
            
            response = await self.ai_model.generate_content_async(prompt)
            
            # For now, just log the AI response (full implementation would parse and apply corrections)
            logger.info(f"AI entity validation: {response.text[:200]}...")
            
            return entities
            
        except Exception as e:
            logger.warning(f"AI entity validation failed: {e}")
            return entities 