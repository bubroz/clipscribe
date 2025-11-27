#!/usr/bin/env python3
"""
ClipScribe Multi-Video Collection Demo (v2.13.0)

This example demonstrates the new multi-video intelligence capabilities:
- Automatic series detection
- Cross-video entity resolution
- Unified knowledge graph generation
- Narrative flow analysis
- Topic evolution tracking

Best for: Documentary series, educational content, news coverage analysis
"""

import asyncio
import json
from pathlib import Path
from typing import List

from clipscribe.retrievers import VideoIntelligenceRetriever
from clipscribe.extractors.series_detector import SeriesDetector
from clipscribe.extractors.multi_video_processor import MultiVideoProcessor
from clipscribe.models import VideoCollectionType, VideoIntelligence


async def demo_multi_video_collection():
    """Demonstrate comprehensive multi-video collection processing."""
    
    print(" ClipScribe Multi-Video Collection Demo (v2.13.0)")
    print("=" * 60)
    
    # Example: PBS NewsHour series on climate change
    # These are actual PBS videos that work well for demonstration
    video_urls = [
        "https://www.youtube.com/watch?v=6ZVj1_SE4Mo",  # Part 1
        "https://www.youtube.com/watch?v=xYMWTXIkANM",  # Part 2
        # Add more URLs as needed
    ]
    
    collection_title = "PBS NewsHour Climate Coverage"
    output_dir = Path("output/demo_collection")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f" Output directory: {output_dir}")
    print(f" Processing {len(video_urls)} videos...")
    print()
    
    # Step 1: Process individual videos
    print(" Step 1: Processing individual videos...")
    video_intelligences: List[VideoIntelligence] = []
    
    retriever = VideoIntelligenceRetriever(
        use_cache=True,
        mode='audio',
        output_dir=output_dir / "individual_videos"
    )
    
    for i, url in enumerate(video_urls, 1):
        print(f"  Processing video {i}/{len(video_urls)}: {url}")
        
        try:
            video_result = await retriever.process_url(url)
            if video_result:
                # Save individual outputs
                individual_dir = output_dir / "individual_videos" / f"video_{i}"
                individual_dir.mkdir(parents=True, exist_ok=True)
                retriever.save_all_formats(video_result, str(individual_dir))
                video_intelligences.append(video_result)
                print(f"     Success: {video_result.metadata.title[:50]}...")
            else:
                print(f"     Failed to process video {i}")
        except Exception as e:
            print(f"     Error: {e}")
    
    if not video_intelligences:
        print(" No videos were successfully processed. Exiting.")
        return
    
    print(f" Successfully processed {len(video_intelligences)} videos")
    print()
    
    # Step 2: Series detection
    print(" Step 2: Automatic series detection...")
    series_detector = SeriesDetector()
    detection_result = await series_detector.detect_series(video_intelligences)
    
    print(f"  Series detected: {detection_result.is_series}")
    print(f"  Confidence: {detection_result.confidence:.2f}")
    print(f"  Detection method: {detection_result.detection_method}")
    print(f"  User confirmation needed: {detection_result.user_confirmation_needed}")
    
    if detection_result.suggested_grouping:
        print(f"  Suggested groupings: {len(detection_result.suggested_grouping)} groups")
    print()
    
    # Step 3: Multi-video intelligence processing
    print(" Step 3: Multi-video intelligence analysis...")
    multi_processor = MultiVideoProcessor(use_ai_validation=True)
    
    # Determine collection type
    collection_type = VideoCollectionType.SERIES if detection_result.is_series else VideoCollectionType.TOPIC_RESEARCH
    
    try:
        multi_video_result = await multi_processor.process_video_collection(
            videos=video_intelligences,
            collection_type=collection_type,
            collection_title=collection_title,
            user_confirmed_series=detection_result.is_series
        )
        
        print(f"   Collection processing complete!")
        print(f"  Collection ID: {multi_video_result.collection_id}")
        print(f"  Unified entities: {len(multi_video_result.unified_entities)}")
        print(f"  Cross-video relationships: {len(multi_video_result.cross_video_relationships)}")
        print(f"  Key insights: {len(multi_video_result.key_insights)}")
        print()
        
        # Step 4: Save unified outputs
        print(" Step 4: Saving unified collection outputs...")
        
        collection_output_dir = output_dir / "unified_collection"
        collection_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save main collection intelligence
        with open(collection_output_dir / "multi_video_intelligence.json", "w", encoding="utf-8") as f:
            json.dump(multi_video_result.dict(), f, indent=2, ensure_ascii=False, default=str)
        print("   Saved: multi_video_intelligence.json")
        
        # Save unified knowledge graph
        if multi_video_result.unified_knowledge_graph:
            with open(collection_output_dir / "unified_knowledge_graph.json", "w", encoding="utf-8") as f:
                json.dump(multi_video_result.unified_knowledge_graph, f, indent=2, ensure_ascii=False)
            print("   Saved: unified_knowledge_graph.json")
        
        # Save collection summary as markdown
        with open(collection_output_dir / "collection_summary.md", "w", encoding="utf-8") as f:
            f.write(f"# {multi_video_result.collection_title}\n\n")
            f.write(f"**Collection Type:** {multi_video_result.collection_type.value}\n")
            f.write(f"**Videos:** {len(multi_video_result.video_ids)}\n")
            f.write(f"**Created:** {multi_video_result.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write(f"## Executive Summary\n\n{multi_video_result.collection_summary}\n\n")
            
            if multi_video_result.key_insights:
                f.write("## Key Strategic Insights\n\n")
                for insight in multi_video_result.key_insights:
                    f.write(f"- {insight}\n")
                f.write("\n")
            
            # Quality metrics
            f.write(f"## Quality Metrics\n\n")
            f.write(f"- **Entity Resolution Quality:** {multi_video_result.entity_resolution_quality:.2f}/1.0\n")
            f.write(f"- **Narrative Coherence:** {multi_video_result.narrative_coherence:.2f}/1.0\n")
            f.write(f"- **Cross-Video Relationship Strength:** {multi_video_result.cross_video_relationship_strength:.2f}/1.0\n\n")
            
            # Statistics
            f.write(f"## Collection Statistics\n\n")
            f.write(f"- **Unified Entities:** {len(multi_video_result.unified_entities)}\n")
            f.write(f"- **Cross-Video Relationships:** {len(multi_video_result.cross_video_relationships)}\n")
            f.write(f"- **Processing Cost:** ${multi_video_result.total_processing_cost:.4f}\n")
            f.write(f"- **Processing Time:** {multi_video_result.total_processing_time:.1f} seconds\n")
            
            # Topic evolution
            if multi_video_result.topic_evolution:
                f.write(f"\n## Topic Evolution\n\n")
                for topic in multi_video_result.topic_evolution:
                    f.write(f"### {topic.topic_name}\n")
                    f.write(f"- **Evolution:** {topic.evolution_description}\n")
                    f.write(f"- **Milestones:** {len(topic.milestones)}\n")
                    f.write(f"- **Coherence Score:** {topic.coherence_score:.2f}\n\n")
            
            # Narrative segments
            if multi_video_result.narrative_segments:
                f.write(f"## Narrative Flow\n\n")
                for segment in multi_video_result.narrative_segments:
                    f.write(f"### {segment.segment_title}\n")
                    f.write(f"- **Videos:** {', '.join(segment.video_ids)}\n")
                    f.write(f"- **Progression:** {segment.progression_description}\n")
                    f.write(f"- **Coherence:** {segment.coherence_score:.2f}\n\n")
        
        print("   Saved: collection_summary.md")
        print()
        
        # Step 5: Display results summary
        print(" Step 5: Results Summary")
        print("=" * 40)
        print(f"Collection Title: {multi_video_result.collection_title}")
        print(f"Collection Type: {multi_video_result.collection_type.value}")
        print(f"Videos Processed: {len(multi_video_result.video_ids)}")
        print(f"Unified Entities: {len(multi_video_result.unified_entities)}")
        print(f"Cross-Video Relationships: {len(multi_video_result.cross_video_relationships)}")
        print(f"Key Insights: {len(multi_video_result.key_insights)}")
        print(f"Total Cost: ${multi_video_result.total_processing_cost:.4f}")
        print()
        
        # Quality scores
        print(" Quality Metrics:")
        print(f"  Entity Resolution Quality: {multi_video_result.entity_resolution_quality:.2f}/1.0")
        print(f"  Narrative Coherence: {multi_video_result.narrative_coherence:.2f}/1.0")
        print(f"  Cross-Video Relationship Strength: {multi_video_result.cross_video_relationship_strength:.2f}/1.0")
        print()
        
        # Sample insights
        if multi_video_result.key_insights:
            print(" Sample Key Insights:")
            for i, insight in enumerate(multi_video_result.key_insights[:3], 1):
                print(f"  {i}. {insight}")
            if len(multi_video_result.key_insights) > 3:
                print(f"  ... and {len(multi_video_result.key_insights) - 3} more insights")
        print()
        
        print(f" All outputs saved to: {collection_output_dir}")
        print()
        print(" Multi-video collection processing complete!")
        print()
        print("Next steps:")
        print("- Review the collection_summary.md for comprehensive analysis")
        print("- Explore the unified_knowledge_graph.json for cross-video relationships")
        print("- Check individual video outputs for detailed per-video analysis")
        
    except Exception as e:
        print(f" Multi-video processing failed: {e}")
        import traceback
        traceback.print_exc()


async def demo_series_comparison():
    """Demonstrate different collection types for comparison."""
    
    print("\n" + "=" * 60)
    print(" Collection Type Comparison Demo")
    print("=" * 60)
    
    # This would show how different collection types affect processing
    # For brevity, we'll just show the concept
    
    collection_types = [
        (VideoCollectionType.SERIES, "Sequential narrative analysis"),
        (VideoCollectionType.TOPIC_RESEARCH, "Cross-source topic comparison"),
        (VideoCollectionType.CHANNEL_ANALYSIS, "Channel content patterns"),
        (VideoCollectionType.CROSS_SOURCE_TOPIC, "Multi-source bias analysis")
    ]
    
    print(" Available Collection Types:")
    for collection_type, description in collection_types:
        print(f"  • {collection_type.value}: {description}")
    
    print("\n Pro Tip: Use the CLI commands for different collection types:")
    print("  clipscribe process-collection URLs --collection-type series")
    print("  clipscribe process-collection URLs --collection-type topic_research")
    print("  clipscribe process-series URLs  # Optimized for series")


def main():
    """Run the multi-video collection demo."""
    print("Starting ClipScribe Multi-Video Collection Demo...")
    print("This demo showcases the new v2.13.0 multi-video intelligence features.")
    print()
    
    # Check for API key
    import os
    if not os.getenv("GOOGLE_API_KEY"):
        print(" Error: GOOGLE_API_KEY environment variable not set")
        print("Please set your API key:")
        print('echo "GOOGLE_API_KEY=your_key_here" > .env')
        return
    
    # Run the demo
    asyncio.run(demo_multi_video_collection())
    asyncio.run(demo_series_comparison())


if __name__ == "__main__":
    main() 