"""
Collections Management Page - Enhanced with Timeline Building Pipeline (v2.17.0)
Browse, view, and manage multi-video collections with timeline intelligence
"""

import streamlit as st
import json
import sys
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime

# Add the src directory to the path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from clipscribe.models import MultiVideoIntelligence

def load_collection_data(collection_path: Path):
    """Load collection intelligence data"""
    try:
        # Load collection intelligence (corrected filename)
        collection_file = collection_path / "collection_intelligence.json"
        if collection_file.exists():
            with open(collection_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data  # Return raw data for now since it may not match MultiVideoIntelligence model
        else:
            # Fallback to old filename for backward compatibility
            multi_video_file = collection_path / "multi_video_intelligence.json"
            if multi_video_file.exists():
                with open(multi_video_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data
    except Exception as e:
        st.error(f"Error loading collection data: {e}")
    return None

def show_collection_overview(collection_path: Path, intelligence):
    """Show overview of a collection with v2.17.0 Timeline Building Pipeline integration"""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        videos = intelligence.get('videos', [])
        st.metric("Videos", len(videos))
    
    with col2:
        unified_entities = intelligence.get('unified_entities', [])
        st.metric("Unified Entities", len(unified_entities))
    
    with col3:
        cross_video_relationships = intelligence.get('cross_video_relationships', [])
        st.metric("Cross-Video Relationships", len(cross_video_relationships))
    
    with col4:
        # Calculate total duration
        total_duration = 0
        for video in videos:
            if isinstance(video, dict) and 'metadata' in video:
                total_duration += video['metadata'].get('duration', 0)
        hours = int(total_duration // 3600)
        minutes = int((total_duration % 3600) // 60)
        st.metric("Total Duration", f"{hours}h {minutes}m")
    
    # Collection summary
    collection_summary = intelligence.get('collection_summary')
    if collection_summary:
        st.subheader("📝 Collection Summary")
        with st.expander("View Summary", expanded=True):
            if isinstance(collection_summary, str):
                st.write(collection_summary)
            elif isinstance(collection_summary, dict):
                st.write(collection_summary.get('summary', 'No summary available'))
                
                key_insights = collection_summary.get('key_insights', [])
                if key_insights:
                    st.markdown("**Key Insights:**")
                    for insight in key_insights:
                        st.markdown(f"• {insight}")
            else:
                st.write(str(collection_summary))
    
    # Show key insights if they exist at top level
    key_insights = intelligence.get('key_insights', [])
    if key_insights:
        st.subheader("💡 Key Insights")
        for insight in key_insights:
            st.markdown(f"• {insight}")

def show_videos_list(intelligence):
    """Show list of videos in collection"""
    st.subheader("📹 Videos in Collection")
    
    videos = intelligence.get('videos', [])
    for i, video in enumerate(videos):
        if isinstance(video, dict):
            metadata = video.get('metadata', {})
            title = metadata.get('title', f'Video {i+1}')
            
            with st.expander(f"Video {i+1}: {title}", expanded=False):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**URL:** {video.get('url', 'Unknown')}")
                    st.write(f"**Duration:** {metadata.get('duration', 0)} seconds")
                    st.write(f"**Channel:** {metadata.get('channel', 'Unknown')}")
                    
                    summary = video.get('summary', '')
                    if summary:
                        st.write(f"**Summary:** {summary}")
                
                with col2:
                    entities = video.get('entities', [])
                    key_points = video.get('key_points', [])
                    relationships = video.get('relationships', [])
                    
                    st.write(f"**Entities:** {len(entities)}")
                    st.write(f"**Key Points:** {len(key_points)}")
                    st.write(f"**Relationships:** {len(relationships)}")

def show_cross_video_entities(intelligence):
    """Show unified entities analysis"""
    st.subheader("👥 Unified Entities") 
    
    unified_entities = intelligence.get('unified_entities', [])
    if not unified_entities:
        st.info("No unified entities found.")
        return
    
    # Sort entities by confidence score
    sorted_entities = sorted(
        unified_entities, 
        key=lambda x: x.get('aggregated_confidence', 0), 
        reverse=True
    )
    
    videos = intelligence.get('videos', [])
    
    st.write(f"Found {len(sorted_entities)} unified entities across all videos")
    
    for entity in sorted_entities[:20]:  # Show top 20
        if isinstance(entity, dict):
            name = entity.get('canonical_name', entity.get('name', 'Unknown'))
            entity_type = entity.get('type', 'Unknown')
            confidence = entity.get('aggregated_confidence', 0)
            
            with st.expander(f"{name} ({entity_type}) - {confidence:.3f} confidence"):
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.write(f"**Type:** {entity_type}")
                    st.write(f"**Confidence:** {confidence:.3f}")
                    
                    properties = entity.get('properties', {})
                    if properties:
                        sources = properties.get('sources', [])
                        if sources:
                            st.write(f"**Sources:** {', '.join(sources)}")
                        
                        source = properties.get('source', '')
                        if source:
                            st.write(f"**Extraction Method:** {source}")
                
                with col2:
                    # For unified entities, we don't have video_appearances
                    # but we can show which videos contain this entity
                    st.write("**Entity Context:**")
                    timestamp = entity.get('timestamp')
                    if timestamp:
                        st.write(f"• Timestamp: {timestamp}")
                    else:
                        st.write("• Appears across video collection")
                        
                    # Show if this entity appears in individual video entities
                    entity_found_in_videos = []
                    for video in videos:
                        if isinstance(video, dict):
                            video_entities = video.get('entities', [])
                            for ve in video_entities:
                                if isinstance(ve, dict):
                                    ve_name = ve.get('canonical_name', ve.get('name', ''))
                                    if ve_name.lower() == name.lower():
                                        title = video.get('metadata', {}).get('title', 'Unknown')
                                        entity_found_in_videos.append(title)
                                        break
                    
                    if entity_found_in_videos:
                        st.write("**Found in videos:**")
                        for title in entity_found_in_videos:
                            st.write(f"• {title}")

def show_knowledge_synthesis(collection_path: Path, intelligence):
    """Show knowledge synthesis features with Timeline Building Pipeline integration"""
    
    # Legacy timeline support
    consolidated_timeline = intelligence.get('consolidated_timeline')
    if consolidated_timeline:
        st.subheader("⏰ Legacy Timeline Synthesis")
        
        events = consolidated_timeline.get('events', [])
        time_range_start = consolidated_timeline.get('time_range_start', 'Unknown')
        time_range_end = consolidated_timeline.get('time_range_end', 'Unknown')
        
        st.write(f"**Events:** {len(events)}")
        st.write(f"**Time Range:** {time_range_start} to {time_range_end}")
        
        st.info("💡 Upgrade to Timeline Building Pipeline by reprocessing with `--enhanced-temporal`")
    
    # Information Flow Maps
    collection_id = intelligence.get('collection_id', 'unknown')
    flow_map_file = collection_path / "information_flow_map.json"
    if flow_map_file.exists():
        st.subheader("🔄 Information Flow Maps Available")
        st.success("✅ Information Flow Maps generated for this collection")
        
        if st.button("View Information Flows", key=f"if_{collection_id}_{abs(hash(str(collection_path)))}"):
            st.switch_page("pages/Information_Flows.py")

def main():
    """Main collections page with Timeline Building Pipeline integration"""
    st.title("📹 Collections Management")
    st.markdown("**Enhanced with Timeline Building Pipeline (v2.17.0)**")
    
    # Look for collections (check both backup and standard locations)
    collections_paths = [
        Path("../backup_output/collections"),  # Real data location
        Path("../output/collections"),         # Standard location
        Path("output/collections")             # Relative location
    ]
    
    collections_path = None
    for path in collections_paths:
        if path.exists():
            collections_path = path
            break
    
    if not collections_path:
        st.warning("No collections directory found. Process some multi-video collections first!")
        
        st.subheader("🚀 Getting Started with Timeline Intelligence")
        st.markdown("""
        To create collections with enhanced temporal intelligence:
        
        ```bash
        # Process with Timeline Building Pipeline (v2.17.0)
        poetry run clipscribe process-collection "topic or series name" \\
            "url1" "url2" "url3" \\
            --enhanced-temporal \\
            --collection-type research
        
        # Process a detected series with timeline intelligence
        poetry run clipscribe process-series "series name" \\
            "url1" "url2" "url3" \\
            --enhanced-temporal
        ```
        
        **Timeline Building Pipeline Features:**
        - ✅ **300% More Intelligence** for only 12-20% cost increase
        - ✅ **Enhanced Temporal Event Extraction** from video content
        - ✅ **Cross-Video Timeline Correlation** with intelligent synthesis
        - ✅ **Web Research Integration** for external validation (optional)
        - ✅ **Interactive Timeline Visualizations** in Mission Control
        - ✅ **Timeline Export** to external tools and formats
        """)
        return
    
    # Get all collections (filter out special directories)
    skip_dirs = {"individual_videos", "video_archive", ".DS_Store"}
    collection_dirs = [d for d in collections_path.iterdir() 
                      if d.is_dir() and d.name not in skip_dirs]
    
    if not collection_dirs:
        st.info("No collections found. Process some multi-video collections first!")
        return
    
    st.write(f"Found {len(collection_dirs)} collections")
    
    # Collection selector with human-readable names
    collection_options = {}
    for d in collection_dirs:
        # Try to load the collection title for display
        try:
            collection_file = d / "collection_intelligence.json"
            if collection_file.exists():
                with open(collection_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    title = data.get('collection_title', 'Untitled Collection')
                    
                    # Extract date for better readability
                    folder_name = d.name
                    if 'collection_' in folder_name:
                        # Extract date from folder name: collection_20250629_163934_2
                        parts = folder_name.split('_')
                        if len(parts) >= 3:
                            date_str = parts[1]  # 20250629
                            time_str = parts[2]  # 163934
                            try:
                                from datetime import datetime
                                date_obj = datetime.strptime(date_str, '%Y%m%d')
                                time_obj = datetime.strptime(time_str, '%H%M%S')
                                readable_date = date_obj.strftime('%b %d, %Y')
                                readable_time = time_obj.strftime('%I:%M %p')
                                display_name = f"{title} - {readable_date} at {readable_time}"
                            except:
                                display_name = f"{title} ({folder_name})"
                        else:
                            display_name = f"{title} ({folder_name})"
                    else:
                        display_name = f"{title} ({folder_name})"
                    
                    collection_options[display_name] = d.name
            else:
                # Fallback: make folder name more readable
                folder_name = d.name
                if 'collection_' in folder_name:
                    parts = folder_name.split('_')
                    if len(parts) >= 3:
                        date_str = parts[1]
                        try:
                            from datetime import datetime
                            date_obj = datetime.strptime(date_str, '%Y%m%d')
                            readable_date = date_obj.strftime('%b %d, %Y')
                            display_name = f"Collection - {readable_date}"
                        except:
                            display_name = folder_name
                    else:
                        display_name = folder_name
                else:
                    display_name = folder_name
                collection_options[display_name] = d.name
        except Exception as e:
            # Final fallback
            collection_options[d.name] = d.name
    
    selected_display_name = st.selectbox(
        "Select a collection to view:",
        list(collection_options.keys()),
        key="collection_selector"
    )
    
    selected_collection = collection_options.get(selected_display_name, selected_display_name)
    
    if selected_collection:
        collection_path = collections_path / selected_collection
        
        # Load collection data
        with st.spinner("Loading collection data..."):
            intelligence = load_collection_data(collection_path)
        
        if intelligence:
            # Show collection details
            collection_id = intelligence.get('collection_id', selected_collection)
            st.success(f"✅ Loaded collection: {collection_id}")
            
            # Enhanced Tabs with Timeline Building Pipeline
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "📊 Overview", 
                "📹 Videos", 
                "👥 Entities", 
                "🧠 Knowledge Synthesis"
            ])
            
            with tab1:
                show_collection_overview(collection_path, intelligence)
            
            with tab2:
                show_videos_list(intelligence)
            
            with tab3:
                show_cross_video_entities(intelligence)
            
            with tab4:
                show_knowledge_synthesis(collection_path, intelligence)
        
        else:
            st.error("Could not load collection data. Check the collection format.")

if __name__ == "__main__":
    main() 