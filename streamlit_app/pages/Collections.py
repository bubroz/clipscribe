"""
Collections Management Page
Browse, view, and manage multi-video collections
"""

import streamlit as st
import json
import sys
from pathlib import Path
from datetime import datetime

# Add the src directory to the path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from clipscribe.models import MultiVideoIntelligence

def load_collection_data(collection_path: Path):
    """Load collection intelligence data"""
    try:
        # Load multi-video intelligence
        multi_video_file = collection_path / "multi_video_intelligence.json"
        if multi_video_file.exists():
            with open(multi_video_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return MultiVideoIntelligence.model_validate(data)
    except Exception as e:
        st.error(f"Error loading collection data: {e}")
    return None

def show_collection_overview(collection_path: Path, intelligence: MultiVideoIntelligence):
    """Show overview of a collection"""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Videos", len(intelligence.videos))
    
    with col2:
        st.metric("Cross-Video Entities", len(intelligence.cross_video_entities))
    
    with col3:
        st.metric("Cross-Video Relationships", len(intelligence.cross_video_relationships))
    
    with col4:
        # Calculate total duration
        total_duration = sum([video.metadata.duration for video in intelligence.videos])
        hours = int(total_duration // 3600)
        minutes = int((total_duration % 3600) // 60)
        st.metric("Total Duration", f"{hours}h {minutes}m")
    
    # Collection summary
    if intelligence.collection_summary:
        st.subheader("📝 Collection Summary")
        with st.expander("View Summary", expanded=True):
            st.write(intelligence.collection_summary.summary)
            
            if intelligence.collection_summary.key_insights:
                st.markdown("**Key Insights:**")
                for insight in intelligence.collection_summary.key_insights:
                    st.markdown(f"• {insight}")

def show_videos_list(intelligence: MultiVideoIntelligence):
    """Show list of videos in collection"""
    st.subheader("📹 Videos in Collection")
    
    for i, video in enumerate(intelligence.videos):
        with st.expander(f"Video {i+1}: {video.metadata.title}", expanded=False):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**URL:** {video.url}")
                st.write(f"**Duration:** {video.metadata.duration} seconds")
                st.write(f"**Channel:** {video.metadata.channel}")
                
                if video.summary:
                    st.write(f"**Summary:** {video.summary}")
            
            with col2:
                st.write(f"**Entities:** {len(video.entities)}")
                st.write(f"**Key Points:** {len(video.key_points)}")
                if hasattr(video, 'relationships'):
                    st.write(f"**Relationships:** {len(video.relationships)}")

def show_cross_video_entities(intelligence: MultiVideoIntelligence):
    """Show cross-video entities analysis"""
    st.subheader("👥 Cross-Video Entities")
    
    if not intelligence.cross_video_entities:
        st.info("No cross-video entities found.")
        return
    
    # Sort entities by video count (most videos first)
    sorted_entities = sorted(
        intelligence.cross_video_entities, 
        key=lambda x: len(x.video_appearances), 
        reverse=True
    )
    
    for entity in sorted_entities[:20]:  # Show top 20
        with st.expander(f"{entity.name} ({entity.type}) - {len(entity.video_appearances)} videos"):
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.write(f"**Type:** {entity.type}")
                st.write(f"**Confidence:** {entity.confidence:.2f}")
                
                if entity.aliases:
                    st.write(f"**Aliases:** {', '.join(entity.aliases)}")
            
            with col2:
                st.write("**Appears in videos:**")
                for video_ref in entity.video_appearances:
                    video = next((v for v in intelligence.videos if v.url == video_ref.video_url), None)
                    if video:
                        st.write(f"• {video.metadata.title}")

def show_knowledge_synthesis(intelligence: MultiVideoIntelligence):
    """Show knowledge synthesis features"""
    
    # Timeline synthesis
    if hasattr(intelligence, 'consolidated_timeline') and intelligence.consolidated_timeline:
        st.subheader("⏰ Timeline Synthesis")
        timeline = intelligence.consolidated_timeline
        
        st.write(f"**Events:** {len(timeline.events)}")
        st.write(f"**Time Range:** {timeline.time_range_start} to {timeline.time_range_end}")
        
        # Show recent events
        with st.expander("Recent Timeline Events", expanded=False):
            for event in sorted(timeline.events, key=lambda x: x.timestamp, reverse=True)[:10]:
                st.write(f"**{event.timestamp}:** {event.description}")
                if event.key_entities:
                    st.write(f"   Entities: {', '.join(event.key_entities)}")
    
    # Knowledge Panels
    knowledge_panels_file = Path("output") / "collections" / intelligence.collection_id / "knowledge_panels.json"
    if knowledge_panels_file.exists():
        st.subheader("📊 Knowledge Panels Available")
        st.success("✅ Knowledge Panels generated for this collection")
        
        if st.button("View Knowledge Panels", key=f"kp_{intelligence.collection_id}"):
            st.switch_page("pages/Knowledge_Panels.py")
    
    # Information Flow Maps
    flow_map_file = Path("output") / "collections" / intelligence.collection_id / "information_flow_map.json"
    if flow_map_file.exists():
        st.subheader("🔄 Information Flow Maps Available")
        st.success("✅ Information Flow Maps generated for this collection")
        
        if st.button("View Information Flows", key=f"if_{intelligence.collection_id}"):
            st.switch_page("pages/Information_Flows.py")

def main():
    """Main collections page"""
    st.title("📹 Collections Management")
    
    # Look for collections
    collections_path = Path("output/collections")
    
    if not collections_path.exists():
        st.warning("No collections directory found. Process some multi-video collections first!")
        
        st.subheader("🚀 Getting Started")
        st.markdown("""
        To create collections, use the CLI commands:
        
        ```bash
        # Process a collection of related videos
        poetry run clipscribe process-collection "topic or series name" \\
            --urls "url1" "url2" "url3" \\
            --collection-type research
        
        # Process a detected series
        poetry run clipscribe process-series "series name" \\
            --urls "url1" "url2" "url3"
        ```
        """)
        return
    
    # Get all collections
    collection_dirs = [d for d in collections_path.iterdir() if d.is_dir()]
    
    if not collection_dirs:
        st.info("No collections found. Process some multi-video collections first!")
        return
    
    st.write(f"Found {len(collection_dirs)} collections")
    
    # Collection selector
    collection_names = [d.name for d in collection_dirs]
    selected_collection = st.selectbox(
        "Select a collection to view:",
        collection_names,
        key="collection_selector"
    )
    
    if selected_collection:
        collection_path = collections_path / selected_collection
        
        # Load collection data
        with st.spinner("Loading collection data..."):
            intelligence = load_collection_data(collection_path)
        
        if intelligence:
            # Show collection details
            st.success(f"✅ Loaded collection: {intelligence.collection_id}")
            
            # Tabs for different views
            tab1, tab2, tab3, tab4 = st.tabs([
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
                show_knowledge_synthesis(intelligence)
            
            # Download options
            st.subheader("⬇️ Download Collection Data")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📄 Download JSON"):
                    json_data = intelligence.model_dump()
                    st.download_button(
                        label="Download multi_video_intelligence.json",
                        data=json.dumps(json_data, indent=2, ensure_ascii=False),
                        file_name=f"{selected_collection}_intelligence.json",
                        mime="application/json"
                    )
            
            with col2:
                # Check for markdown summary
                summary_file = collection_path / "collection_summary.md"
                if summary_file.exists():
                    if st.button("📝 Download Summary"):
                        with open(summary_file, 'r', encoding='utf-8') as f:
                            st.download_button(
                                label="Download collection_summary.md",
                                data=f.read(),
                                file_name=f"{selected_collection}_summary.md",
                                mime="text/markdown"
                            )
            
            with col3:
                if st.button("🗂️ Open Folder"):
                    st.info(f"Collection folder: `{collection_path}`")
        
        else:
            st.error("Could not load collection data. Check the collection format.")

if __name__ == "__main__":
    main() 