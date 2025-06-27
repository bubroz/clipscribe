"""
Knowledge Panels Page
Interactive exploration of entity-centric intelligence synthesis
"""

import streamlit as st
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add the src directory to the path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from clipscribe.models import KnowledgePanelCollection, KnowledgePanel

def load_knowledge_panels(collection_path: Path) -> KnowledgePanelCollection:
    """Load knowledge panels data"""
    panels_file = collection_path / "knowledge_panels.json"
    if panels_file.exists():
        with open(panels_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return KnowledgePanelCollection.model_validate(data)
    return None

def show_panels_overview(panels: KnowledgePanelCollection):
    """Show overview of knowledge panels"""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Entity Panels", len(panels.panels))
    
    with col2:
        total_activities = sum(len(panel.activities) for panel in panels.panels)
        st.metric("Total Activities", total_activities)
    
    with col3:
        total_quotes = sum(len(panel.quotes) for panel in panels.panels)
        st.metric("Total Quotes", total_quotes)
    
    with col4:
        total_relationships = sum(len(panel.relationships) for panel in panels.panels)
        st.metric("Total Relationships", total_relationships)
    
    # Collection-level insights
    if panels.collection_analysis:
        st.subheader("🧠 Collection-Level Analysis")
        
        with st.expander("Key Entities Analysis", expanded=True):
            if panels.collection_analysis.key_entities:
                for entity in panels.collection_analysis.key_entities:
                    st.write(f"**{entity}**")
        
        if panels.collection_analysis.network_insights:
            with st.expander("Network Insights", expanded=False):
                for insight in panels.collection_analysis.network_insights:
                    st.write(f"• {insight}")

def show_entity_panel(panel: KnowledgePanel):
    """Display detailed view of a single entity panel"""
    
    # Panel header
    st.markdown(f"### {panel.entity_name}")
    st.markdown(f"**Type:** {panel.entity_type} | **Videos:** {panel.video_count} | **Mentions:** {panel.mention_count}")
    
    # Executive summary
    if panel.executive_summary:
        st.subheader("📋 Executive Summary")
        st.write(panel.executive_summary)
    
    # Portrayal analysis
    if panel.portrayal_analysis:
        st.subheader("🎭 Portrayal Analysis")
        st.write(panel.portrayal_analysis)
    
    # Significance assessment
    if panel.significance_assessment:
        st.subheader("⭐ Significance Assessment")
        st.write(panel.significance_assessment)
    
    # Strategic insights
    if panel.strategic_insights:
        st.subheader("🎯 Strategic Insights")
        for insight in panel.strategic_insights:
            st.write(f"• {insight}")
    
    # Activities
    if panel.activities:
        st.subheader("📋 Activities")
        for activity in panel.activities:
            with st.expander(f"Activity: {activity.description[:100]}...", expanded=False):
                st.write(f"**Description:** {activity.description}")
                st.write(f"**Videos:** {', '.join(activity.source_videos)}")
                if activity.context:
                    st.write(f"**Context:** {activity.context}")
    
    # Quotes
    if panel.quotes:
        st.subheader("💬 Notable Quotes")
        for quote in panel.quotes:
            with st.expander(f"Quote: {quote.text[:50]}...", expanded=False):
                st.markdown(f"> {quote.text}")
                st.write(f"**Video:** {quote.source_video}")
                if quote.context:
                    st.write(f"**Context:** {quote.context}")
    
    # Relationships
    if panel.relationships:
        st.subheader("🔗 Key Relationships")
        for relationship in panel.relationships:
            with st.expander(f"{relationship.target_entity} ({relationship.relationship_type})", expanded=False):
                st.write(f"**Target:** {relationship.target_entity}")
                st.write(f"**Type:** {relationship.relationship_type}")
                st.write(f"**Description:** {relationship.description}")
                if relationship.examples:
                    st.write("**Examples:**")
                    for example in relationship.examples:
                        st.write(f"• {example}")
    
    # Attribute evolution
    if panel.attribute_evolution:
        st.subheader("📈 Attribute Evolution")
        for evolution in panel.attribute_evolution:
            with st.expander(f"{evolution.attribute}: {evolution.initial_value} → {evolution.final_value}"):
                st.write(f"**Attribute:** {evolution.attribute}")
                st.write(f"**Change:** {evolution.initial_value} → {evolution.final_value}")
                st.write(f"**Videos:** {', '.join(evolution.source_videos)}")
                if evolution.context:
                    st.write(f"**Context:** {evolution.context}")

def show_entity_explorer(panels: KnowledgePanelCollection):
    """Interactive entity explorer with filtering and search"""
    
    st.subheader("🔍 Entity Explorer")
    
    # Search and filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_term = st.text_input("Search entities:", key="entity_search")
    
    with col2:
        # Get unique entity types
        entity_types = list(set(panel.entity_type for panel in panels.panels))
        selected_type = st.selectbox("Filter by type:", ["All"] + entity_types, key="type_filter")
    
    with col3:
        sort_by = st.selectbox(
            "Sort by:", 
            ["Video Count", "Mention Count", "Name"], 
            key="sort_option"
        )
    
    # Filter panels
    filtered_panels = panels.panels
    
    if search_term:
        filtered_panels = [p for p in filtered_panels 
                          if search_term.lower() in p.entity_name.lower()]
    
    if selected_type != "All":
        filtered_panels = [p for p in filtered_panels if p.entity_type == selected_type]
    
    # Sort panels
    if sort_by == "Video Count":
        filtered_panels = sorted(filtered_panels, key=lambda x: x.video_count, reverse=True)
    elif sort_by == "Mention Count":
        filtered_panels = sorted(filtered_panels, key=lambda x: x.mention_count, reverse=True)
    else:  # Name
        filtered_panels = sorted(filtered_panels, key=lambda x: x.entity_name)
    
    # Display results
    st.write(f"Found {len(filtered_panels)} entities")
    
    # Entity grid
    cols = st.columns(3)
    for i, panel in enumerate(filtered_panels):
        with cols[i % 3]:
            with st.container():
                st.markdown(f"**{panel.entity_name}**")
                st.markdown(f"*{panel.entity_type}*")
                st.markdown(f"📹 {panel.video_count} videos | 💬 {panel.mention_count} mentions")
                
                if st.button(f"View Details", key=f"view_{panel.entity_name}_{i}"):
                    st.session_state.selected_entity = panel.entity_name
                
                st.markdown("---")

def show_network_visualization(panels: KnowledgePanelCollection):
    """Show entity relationship network (placeholder for now)"""
    
    st.subheader("🕸️ Entity Relationship Network")
    
    # For now, show relationship stats
    st.info("Interactive network visualization coming soon!")
    
    # Show relationship summary
    all_relationships = []
    for panel in panels.panels:
        for rel in panel.relationships:
            all_relationships.append({
                'source': panel.entity_name,
                'target': rel.target_entity,
                'type': rel.relationship_type
            })
    
    if all_relationships:
        st.write(f"**Total Relationships:** {len(all_relationships)}")
        
        # Relationship type distribution
        rel_types = {}
        for rel in all_relationships:
            rel_types[rel['type']] = rel_types.get(rel['type'], 0) + 1
        
        st.subheader("Relationship Type Distribution")
        for rel_type, count in sorted(rel_types.items(), key=lambda x: x[1], reverse=True):
            st.write(f"**{rel_type}:** {count}")

def main():
    """Main Knowledge Panels page"""
    st.title("👥 Knowledge Panels")
    
    # Get available collections
    collections_path = Path("output/collections")
    
    if not collections_path.exists():
        st.warning("No collections found. Process some multi-video collections first!")
        return
    
    # Find collections with knowledge panels
    collection_dirs = [d for d in collections_path.iterdir() if d.is_dir()]
    collections_with_panels = []
    
    for cdir in collection_dirs:
        if (cdir / "knowledge_panels.json").exists():
            collections_with_panels.append(cdir.name)
    
    if not collections_with_panels:
        st.warning("No collections with Knowledge Panels found.")
        st.info("Knowledge Panels are generated automatically for multi-video collections.")
        return
    
    # Collection selector
    selected_collection = st.selectbox(
        "Select a collection:",
        collections_with_panels,
        key="kp_collection_selector"
    )
    
    if selected_collection:
        collection_path = collections_path / selected_collection
        
        # Load knowledge panels
        with st.spinner("Loading Knowledge Panels..."):
            panels = load_knowledge_panels(collection_path)
        
        if panels:
            st.success(f"✅ Loaded {len(panels.panels)} entity panels")
            
            # Main tabs
            tab1, tab2, tab3, tab4 = st.tabs([
                "📊 Overview",
                "🔍 Entity Explorer", 
                "👤 Panel Details",
                "🕸️ Network View"
            ])
            
            with tab1:
                show_panels_overview(panels)
            
            with tab2:
                show_entity_explorer(panels)
            
            with tab3:
                # Entity selection for detailed view
                if 'selected_entity' not in st.session_state:
                    st.session_state.selected_entity = panels.panels[0].entity_name if panels.panels else None
                
                entity_names = [panel.entity_name for panel in panels.panels]
                selected_entity_name = st.selectbox(
                    "Select entity for detailed view:",
                    entity_names,
                    index=entity_names.index(st.session_state.selected_entity) if st.session_state.selected_entity in entity_names else 0,
                    key="entity_detail_selector"
                )
                
                # Find and show the selected panel
                selected_panel = next((p for p in panels.panels if p.entity_name == selected_entity_name), None)
                if selected_panel:
                    show_entity_panel(selected_panel)
            
            with tab4:
                show_network_visualization(panels)
            
            # Download options
            st.subheader("⬇️ Download Knowledge Panels")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📄 Download JSON"):
                    json_data = panels.model_dump()
                    st.download_button(
                        label="Download knowledge_panels.json",
                        data=json.dumps(json_data, indent=2, ensure_ascii=False),
                        file_name=f"{selected_collection}_knowledge_panels.json",
                        mime="application/json"
                    )
            
            with col2:
                # Check for markdown summary
                summary_file = collection_path / "knowledge_panels_summary.md"
                if summary_file.exists():
                    if st.button("📝 Download Summary"):
                        with open(summary_file, 'r', encoding='utf-8') as f:
                            st.download_button(
                                label="Download knowledge_panels_summary.md",
                                data=f.read(),
                                file_name=f"{selected_collection}_panels_summary.md",
                                mime="text/markdown"
                            )
        
        else:
            st.error("Could not load Knowledge Panels data.")

if __name__ == "__main__":
    main() 