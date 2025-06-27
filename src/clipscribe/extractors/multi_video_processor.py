"""
Multi-Video Intelligence Processor for ClipScribe.

Handles cross-video entity resolution, relationship bridging, narrative flow analysis,
and unified knowledge graph generation with aggressive AI-powered entity merging.
"""

import logging
import asyncio
import json
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict, Counter

from ..models import (
    VideoIntelligence, MultiVideoIntelligence, CrossVideoEntity, 
    CrossVideoRelationship, NarrativeSegment, TopicEvolution,
    VideoCollectionType, SeriesMetadata, Entity, Relationship, Topic,
    ConsolidatedTimeline, TimelineEvent, ExtractedDate
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
        
        # AI validation setup - using Pro for all multi-video intelligence
        if use_ai_validation:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.settings.google_api_key)
                self.ai_model = genai.GenerativeModel('gemini-2.5-pro')  # 2.5 Pro for sophisticated analysis
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
        
        # Create collection ID and title early
        collection_id = f"collection_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(videos)}"
        if not collection_title:
            if collection_type == VideoCollectionType.SERIES:
                collection_title = f"{videos[0].metadata.channel} Series"
            else:
                collection_title = f"{videos[0].metadata.channel} - {len(videos)} Videos"
        
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
        
        # Step 2b: (Optional) AI-powered validation of entity merging
        if self.use_ai_validation:
            unified_entities = await self._ai_validate_entity_merging(unified_entities, videos)
        
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
        
        # Step 9: Synthesize event timeline
        consolidated_timeline = await self._synthesize_event_timeline(videos, unified_entities, collection_id)
        
        # Step 10: Generate unified knowledge graph
        unified_knowledge_graph = self._generate_unified_knowledge_graph(unified_entities, cross_video_relationships)
        
        # Step 11: Calculate quality metrics
        quality_metrics = self._calculate_quality_metrics(videos, unified_entities, cross_video_relationships)
        
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
            consolidated_timeline=consolidated_timeline,
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
        
        logger.info(f"Resolved {len(all_entities)} entities to {len(cross_video_entities)} cross-video entities")
        return cross_video_entities
    
    async def _extract_cross_video_relationships(
        self, 
        videos: List[VideoIntelligence], 
        unified_entities: List[CrossVideoEntity]
    ) -> List[CrossVideoRelationship]:
        """Extract relationships that span or are confirmed across multiple videos."""
        logger.info("Extracting cross-video relationships...")
        
        # Debug logging to track what we receive
        for idx, video in enumerate(videos):
            rel_count = len(getattr(video, 'relationships', []))
            logger.info(f"Multi-video processor - Video {idx+1}: {rel_count} relationships, has attr: {hasattr(video, 'relationships')}")
        
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
                logger.info(f"Processing {len(video.relationships)} relationships from video: {video.metadata.title}")
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
            else:
                logger.warning(f"Video {video.metadata.title} has no relationships attribute or empty relationships")
        
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
        
        logger.info(f"Extracted {len(cross_video_relationships)} cross-video relationships from {len(relationship_video_map)} unique relationships")
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
        """Analyze narrative flow across videos using Gemini 2.5 Pro for sophisticated story analysis."""
        logger.info("Analyzing narrative flow with AI assistance...")
        
        if self.use_ai_validation and len(videos) > 1:
            return await self._ai_analyze_narrative_flow(videos, unified_entities)
        else:
            return self._template_analyze_narrative_flow(videos, unified_entities)
    
    async def _ai_analyze_narrative_flow(
        self, 
        videos: List[VideoIntelligence], 
        unified_entities: List[CrossVideoEntity]
    ) -> List[NarrativeSegment]:
        """Use Gemini 2.5 Pro to analyze sophisticated narrative flow patterns."""
        try:
            # Sort videos by publication date
            sorted_videos = sorted(videos, key=lambda v: v.metadata.published_at)
            
            # Prepare context for AI narrative analysis
            video_summaries = []
            for i, video in enumerate(sorted_videos):
                key_points_text = '; '.join([kp.text for kp in video.key_points[:3]])
                video_summaries.append(f"""
                Video {i+1}: "{video.metadata.title}"
                Duration: {video.metadata.duration/60:.1f} minutes
                Summary: {video.summary}
                Key Points: {key_points_text}
                """)
            
            # Key entities context
            entity_context = [f"{e.canonical_name} ({e.type})" for e in unified_entities if len(e.video_appearances) > 1]
            
            prompt = f"""
            As an expert narrative analyst, analyze the story flow across this video series using sophisticated reasoning.
            
            VIDEO SEQUENCE:
            {chr(10).join(video_summaries)}
            
            KEY CROSS-VIDEO ENTITIES:
            {', '.join(entity_context)}
            
            NARRATIVE ANALYSIS REQUIREMENTS:
            Identify 3-5 major narrative segments that span across videos, focusing on:
            
            1. STORY PROGRESSION: How does the narrative develop from video to video?
            2. THEMATIC ARCS: What major themes or storylines connect the videos?
            3. ENTITY JOURNEYS: How do key entities (people, organizations, concepts) evolve?
            4. INFORMATION DEPENDENCIES: Which segments build upon previous information?
            5. NARRATIVE TURNING POINTS: Where do significant developments or revelations occur?
            
            For each narrative segment, provide:
            - Segment title (descriptive, not generic)
            - Which video(s) it spans
            - Key entities involved
            - Narrative importance (0.0-1.0)
            - How it connects to other segments
            - Brief summary of its role in the overall story
            
            FORMAT: Return as structured analysis focusing on meaningful narrative elements, not just chronological summaries.
            """
            
            response = await self.ai_model.generate_content_async(prompt)
            
            # For now, create template segments and enhance with AI insights
            # (Full implementation would parse AI response into NarrativeSegment objects)
            template_segments = self._template_analyze_narrative_flow(videos, unified_entities)
            
            # Log AI insights for future enhancement
            logger.info(f"AI narrative analysis: {response.text[:300]}...")
            
            return template_segments
            
        except Exception as e:
            logger.warning(f"AI narrative analysis failed: {e}")
            return self._template_analyze_narrative_flow(videos, unified_entities)
    
    def _template_analyze_narrative_flow(
        self, 
        videos: List[VideoIntelligence], 
        unified_entities: List[CrossVideoEntity]
    ) -> List[NarrativeSegment]:
        """Generate template-based narrative flow analysis."""
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
        """Use Gemini Pro to generate a comprehensive, sophisticated collection summary."""
        try:
            # Prepare detailed context for Pro's advanced analysis
            video_details = []
            for i, video in enumerate(videos):
                video_info = f"""
                Video {i+1}: "{video.metadata.title}"
                Channel: {video.metadata.channel}
                Published: {video.metadata.published_at.strftime('%Y-%m-%d')}
                Duration: {video.metadata.duration/60:.1f} minutes
                Summary: {video.summary}
                Key Topics: {', '.join([topic.name for topic in video.topics[:5]])}
                Entity Count: {len(video.entities)}
                """
                video_details.append(video_info)
            
            # Detailed entity analysis
            entity_analysis = []
            for entity in unified_entities[:15]:  # More entities for Pro
                appearances = f"Appears in {len(entity.video_appearances)} videos"
                aliases = f"Aliases: {', '.join(entity.aliases)}" if entity.aliases else "No aliases"
                entity_analysis.append(f"• {entity.canonical_name} ({entity.type}) - {appearances}, {aliases}")
            
            # Relationship patterns
            relationship_patterns = []
            for rel in cross_video_relationships[:15]:  # More relationships for Pro
                sources = f"Validated across {len(rel.video_sources)} videos" if len(rel.video_sources) > 1 else "Single video"
                relationship_patterns.append(f"• {rel.subject} → {rel.predicate} → {rel.object} ({sources})")
            
            # Temporal analysis
            time_span = (videos[-1].metadata.published_at - videos[0].metadata.published_at).days
            temporal_context = f"Videos span {time_span} days from {videos[0].metadata.published_at.strftime('%Y-%m-%d')} to {videos[-1].metadata.published_at.strftime('%Y-%m-%d')}"
            
            prompt = f"""
            As an expert intelligence analyst, provide a comprehensive analysis of this video collection using your advanced reasoning capabilities.
            
            COLLECTION OVERVIEW:
            {chr(10).join(video_details)}
            
            TEMPORAL CONTEXT:
            {temporal_context}
            
            UNIFIED ENTITY ANALYSIS:
            {chr(10).join(entity_analysis)}
            
            CROSS-VIDEO RELATIONSHIP PATTERNS:
            {chr(10).join(relationship_patterns)}
            
            ANALYSIS REQUIREMENTS:
            Provide a sophisticated 4-5 paragraph analysis that demonstrates deep understanding:
            
            1. NARRATIVE COHERENCE: Analyze how the videos work together as a cohesive information unit. Identify the overarching narrative thread and how each video contributes to the complete picture.
            
            2. ENTITY EVOLUTION: Examine how key entities (people, organizations, concepts) are portrayed and develop across the video sequence. Note any changes in characterization, role, or significance.
            
            3. INFORMATION ARCHITECTURE: Assess the logical flow of information. How do the videos build upon each other? Are there information dependencies, contradictions, or gaps?
            
            4. THEMATIC ANALYSIS: Identify the core themes and how they're explored across different videos. Note any thematic evolution or deepening complexity.
            
            5. INTELLIGENCE VALUE: Evaluate the collection's value for understanding the subject matter. What unique insights emerge from analyzing these videos together rather than individually?
            
            Use sophisticated analytical language appropriate for intelligence briefings. Focus on patterns, implications, and strategic insights rather than simple summaries.
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
        """Extract sophisticated key insights using Gemini 2.5 Pro analysis."""
        if self.use_ai_validation:
            return await self._ai_extract_key_insights(videos, unified_entities, cross_video_relationships, topic_evolution)
        else:
            return self._template_extract_key_insights(videos, unified_entities, cross_video_relationships, topic_evolution)
    
    async def _ai_extract_key_insights(
        self, 
        videos: List[VideoIntelligence], 
        unified_entities: List[CrossVideoEntity], 
        cross_video_relationships: List[CrossVideoRelationship],
        topic_evolution: List[TopicEvolution]
    ) -> List[str]:
        """Use Gemini 2.5 Pro to extract sophisticated strategic insights."""
        try:
            # Prepare comprehensive context for Pro analysis
            video_context = f"{len(videos)} videos spanning {(videos[-1].metadata.published_at - videos[0].metadata.published_at).days} days"
            
            # Entity analysis
            multi_video_entities = [e for e in unified_entities if len(e.video_appearances) > 1]
            entity_patterns = [f"{e.canonical_name} ({e.type}) - {len(e.video_appearances)} videos" for e in multi_video_entities[:10]]
            
            # Relationship analysis
            cross_validated_rels = [r for r in cross_video_relationships if len(r.video_sources) > 1]
            relationship_patterns = [f"{r.subject} → {r.predicate} → {r.object} (validated across {len(r.video_sources)} videos)" for r in cross_validated_rels[:10]]
            
            # Topic evolution analysis
            evolving_topics = [f"{t.topic_name} - evolves across {len(t.video_sequence)} videos" for t in topic_evolution if len(t.video_sequence) > 1]
            
            # Quality metrics
            avg_entity_confidence = sum(e.aggregated_confidence for e in unified_entities) / len(unified_entities)
            entity_compression = len(unified_entities) / sum(len(v.entities) for v in videos)
            
            prompt = f"""
            As an expert intelligence analyst, extract strategic insights from this cross-video analysis using advanced reasoning.
            
            COLLECTION OVERVIEW:
            {video_context}
            Total entities resolved: {len(unified_entities)} (compression ratio: {entity_compression:.2f})
            Cross-video relationships: {len(cross_video_relationships)}
            Average entity confidence: {avg_entity_confidence:.2f}
            
            CROSS-VIDEO ENTITY PATTERNS:
            {chr(10).join(entity_patterns) if entity_patterns else "No significant cross-video entities"}
            
            VALIDATED RELATIONSHIP PATTERNS:
            {chr(10).join(relationship_patterns) if relationship_patterns else "No cross-validated relationships"}
            
            TOPIC EVOLUTION PATTERNS:
            {chr(10).join(evolving_topics) if evolving_topics else "No clear topic evolution"}
            
            ANALYSIS REQUIREMENTS:
            Extract 5-7 strategic insights that demonstrate sophisticated understanding:
            
            1. INFORMATION ARCHITECTURE: How is information structured across videos? What does this reveal about the content strategy or narrative approach?
            
            2. ENTITY SIGNIFICANCE: Which entities are most strategically important based on cross-video presence? What does their treatment reveal?
            
            3. RELATIONSHIP DYNAMICS: What relationship patterns emerge? Are there power structures, influence networks, or causal chains?
            
            4. TEMPORAL INTELLIGENCE: How does the temporal sequence affect information value? Are there dependencies or evolutionary patterns?
            
            5. ANALYTICAL QUALITY: What does the entity resolution and relationship validation tell us about information reliability?
            
            6. STRATEGIC IMPLICATIONS: What broader implications emerge from analyzing these videos as a unified intelligence source?
            
            7. INFORMATION GAPS: What critical information or perspectives might be missing from this collection?
            
            FORMAT: Return exactly 5-7 insights as bullet points, each 1-2 sentences, focusing on strategic intelligence value rather than descriptive statistics.
            """
            
            response = await self.ai_model.generate_content_async(prompt)
            
            # Parse the response into individual insights
            insights_text = response.text.strip()
            insights = []
            
            # Split by bullet points or numbered items
            for line in insights_text.split('\n'):
                line = line.strip()
                if line and (line.startswith('•') or line.startswith('-') or line.startswith('*') or 
                           any(line.startswith(f"{i}.") for i in range(1, 10))):
                    # Clean up the bullet point
                    clean_insight = line.lstrip('•-*0123456789. ').strip()
                    if clean_insight:
                        insights.append(clean_insight)
            
            # Fallback if parsing fails
            if not insights:
                insights = [insights_text]
            
            return insights[:7]  # Limit to 7 insights
            
        except Exception as e:
            logger.warning(f"AI insight extraction failed: {e}")
            return self._template_extract_key_insights(videos, unified_entities, cross_video_relationships, topic_evolution)
    
    def _template_extract_key_insights(
        self, 
        videos: List[VideoIntelligence], 
        unified_entities: List[CrossVideoEntity], 
        cross_video_relationships: List[CrossVideoRelationship],
        topic_evolution: List[TopicEvolution]
    ) -> List[str]:
        """Generate template-based insights as fallback."""
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
            You are an expert intelligence analyst reviewing entity resolution across multiple video sources. 
            Apply sophisticated reasoning to validate entity merging decisions.
            
            ENTITIES TO VALIDATE:
            {chr(10).join(entity_descriptions)}
            
            VALIDATION CRITERIA:
            For each entity, perform deep analysis:
            
            1. IDENTITY VERIFICATION: Are these truly the same real-world entity across videos?
               - Consider temporal context (roles may change over time)
               - Analyze contextual references and descriptions
               - Account for formal vs informal naming conventions
            
            2. DISAMBIGUATION ANALYSIS: Should any entities be split?
               - Different people with similar names
               - Organizations vs sub-organizations
               - Concepts vs specific implementations
            
            3. ALIAS ENHANCEMENT: Identify missing aliases or name variations
               - Official titles vs common references
               - Acronyms and abbreviations
               - Cultural or linguistic variations
            
            4. CONFIDENCE ASSESSMENT: Rate the merging confidence (0.0-1.0)
               - High confidence: Clear same entity across all videos
               - Medium confidence: Likely same but some ambiguity
               - Low confidence: Uncertain, may need splitting
            
            RESPONSE FORMAT:
            For each entity, provide:
            - VALIDATED/SPLIT/ENHANCE decision
            - Confidence score
            - Reasoning for decision
            - Suggested corrections if needed
            
            Focus on intelligence-grade accuracy for reliable cross-video analysis.
            """
            
            response = await self.ai_model.generate_content_async(prompt)
            
            # For now, just log the AI response (full implementation would parse and apply corrections)
            logger.info(f"AI entity validation: {response.text[:200]}...")
            
            return entities
            
        except Exception as e:
            logger.warning(f"AI entity validation failed: {e}")
            return entities

    async def _extract_date_from_text(self, text: str, source_type: str) -> Optional[ExtractedDate]:
        """
        Uses an LLM to extract a specific date from a string of text.

        Args:
            text: The text to analyze (e.g., video title, key point).
            source_type: A string indicating the source ('title', 'description', 'content').

        Returns:
            An ExtractedDate object if a date is found, otherwise None.
        """
        if not self.use_ai_validation:
            return None

        prompt = f"""
        Analyze the following text and extract the single most specific date mentioned.
        The current year is {datetime.now().year}.

        Text: "{text}"

        If you find a date, respond with a JSON object in the following format:
        {{
            "parsed_date": "YYYY-MM-DDTHH:MM:SS",
            "original_text": "the exact text of the date you found",
            "confidence": "your confidence from 0.0 to 1.0"
        }}

        - "parsed_date" must be a full ISO 8601 timestamp.
        - If only a year is mentioned (e.g., "in 1995"), use January 1st of that year.
        - If a relative date is mentioned (e.g., "last Tuesday"), calculate the actual date.
        - If no specific date is found, respond with the single word: "None".
        """
        try:
            response = await self.ai_model.generate_content_async(prompt)
            response_text = response.text.strip()

            if response_text.lower() == "none":
                return None

            # Clean the response text to ensure it's valid JSON
            clean_json_text = response_text.strip().replace('`', '')
            if clean_json_text.startswith('json'):
                clean_json_text = clean_json_text[4:]
            
            data = json.loads(clean_json_text)

            return ExtractedDate(
                parsed_date=datetime.fromisoformat(data["parsed_date"]),
                original_text=data["original_text"],
                confidence=float(data["confidence"]),
                source=source_type
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Could not parse date from LLM response: {e}. Response was: '{response.text[:100]}'")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during date extraction: {e}")
            return None

    async def _synthesize_event_timeline(
        self, 
        videos: List[VideoIntelligence], 
        unified_entities: List[CrossVideoEntity],
        collection_id: str
    ) -> ConsolidatedTimeline:
        """
        Synthesizes a consolidated, chronological event timeline from a collection of videos.
        
        This method uses LLM-based date extraction for higher accuracy and falls back to
        publication dates if no specific date is found.
        
        Args:
            videos: The list of processed VideoIntelligence objects.
            unified_entities: The list of cross-video resolved entities.
            collection_id: The ID of the current video collection.
            
        Returns:
            A ConsolidatedTimeline object containing the sorted list of events.
        """
        logger.info("Synthesizing consolidated event timeline with temporal extraction...")
        all_events: List[TimelineEvent] = []
        
        entity_lookup = {entity.canonical_name.lower(): entity for entity in unified_entities}
        for alias_entity in unified_entities:
            for alias in alias_entity.aliases:
                entity_lookup[alias.lower()] = alias_entity

        for video in videos:
            if not video.metadata.published_at:
                logger.warning(f"Skipping video {video.metadata.video_id} for timeline synthesis due to missing publication date.")
                continue

            # Attempt to get a more accurate base date from the video title first
            base_date_from_title = await self._extract_date_from_text(video.metadata.title, 'video_title')
            
            for key_point in video.key_points:
                event_timestamp = None
                extracted_date_obj = None
                date_source = "video_published_date"

                # 1. Try to extract date from the key point itself
                date_from_content = await self._extract_date_from_text(key_point.text, 'key_point_content')
                
                if date_from_content:
                    event_timestamp = date_from_content.parsed_date
                    extracted_date_obj = date_from_content
                    date_source = "key_point_content"
                # 2. Fallback to date from video title
                elif base_date_from_title:
                    event_timestamp = base_date_from_title.parsed_date
                    extracted_date_obj = base_date_from_title
                    date_source = "video_title"
                # 3. Fallback to video publication date
                else:
                    event_timestamp = video.metadata.published_at + timedelta(seconds=key_point.timestamp)

                # Identify involved entities mentioned in the key point text
                involved_entities = {
                    entity_lookup[name.lower()].canonical_name
                    for name in entity_lookup
                    if name in key_point.text.lower()
                }

                event = TimelineEvent(
                    event_id=f"evt_{video.metadata.video_id}_{key_point.timestamp}",
                    timestamp=event_timestamp,
                    description=key_point.text,
                    source_video_id=video.metadata.video_id,
                    source_video_title=video.metadata.title,
                    video_timestamp_seconds=key_point.timestamp,
                    involved_entities=sorted(list(involved_entities)),
                    confidence=key_point.importance,
                    extracted_date=extracted_date_obj,
                    date_source=date_source
                )
                all_events.append(event)

        # Sort all events chronologically
        all_events.sort(key=lambda e: e.timestamp)

        timeline = ConsolidatedTimeline(
            timeline_id=f"timeline_{collection_id}",
            collection_id=collection_id,
            events=all_events,
            summary=f"Generated a timeline with {len(all_events)} events from {len(videos)} videos."
        )
        
        logger.info(f"Successfully synthesized timeline with {len(all_events)} events.")
        return timeline 