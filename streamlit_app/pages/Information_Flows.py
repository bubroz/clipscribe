"""
Information Flow Maps Page
Interactive exploration of concept evolution tracking
"""

import streamlit as st
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add the src directory to the path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from clipscribe.models import InformationFlowMap, ConceptNode, ConceptCluster, ConceptEvolutionPath

def load_information_flow_map(collection_path: Path) -> InformationFlowMap:
    """Load information flow map data"""
    flow_file = collection_path / "information_flow_map.json"
    if flow_file.exists():
        with open(flow_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return InformationFlowMap.model_validate(data)
    return None

def show_flow_overview(flow_map: InformationFlowMap):
    """Show overview of information flow map"""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Concepts", len(flow_map.concept_nodes))
    
    with col2:
        st.metric("Video Flows", len(flow_map.video_flows))
    
    with col3:
        st.metric("Evolution Paths", len(flow_map.evolution_paths))
    
    with col4:
        st.metric("Concept Clusters", len(flow_map.concept_clusters))
    
    # Flow pattern analysis
    if flow_map.flow_pattern_analysis:
        st.subheader("📊 Flow Pattern Analysis")
        
        with st.expander("Learning Progression", expanded=True):
            st.write(flow_map.flow_pattern_analysis.learning_progression)
        
        if flow_map.flow_pattern_analysis.strategic_insights:
            with st.expander("Strategic Insights", expanded=False):
                for insight in flow_map.flow_pattern_analysis.strategic_insights:
                    st.write(f"• {insight}")

def show_concept_explorer(flow_map: InformationFlowMap):
    """Interactive concept explorer with maturity levels"""
    
    st.subheader("🔍 Concept Explorer")
    
    # Search and filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_term = st.text_input("Search concepts:", key="concept_search")
    
    with col2:
        # Maturity level filter
        maturity_levels = ["All", "mentioned", "introduced", "explained", "analyzed", "synthesized", "evolved"]
        selected_maturity = st.selectbox("Filter by maturity:", maturity_levels, key="maturity_filter")
    
    with col3:
        sort_by = st.selectbox(
            "Sort by:", 
            ["Maturity Level", "Video Count", "Name"], 
            key="concept_sort"
        )
    
    # Filter concepts
    filtered_concepts = flow_map.concept_nodes
    
    if search_term:
        filtered_concepts = [c for c in filtered_concepts 
                           if search_term.lower() in c.concept_name.lower()]
    
    if selected_maturity != "All":
        filtered_concepts = [c for c in filtered_concepts if c.maturity_level == selected_maturity]
    
    # Sort concepts
    maturity_order = ["mentioned", "introduced", "explained", "analyzed", "synthesized", "evolved"]
    
    if sort_by == "Maturity Level":
        filtered_concepts = sorted(filtered_concepts, 
                                 key=lambda x: maturity_order.index(x.maturity_level) if x.maturity_level in maturity_order else 0, 
                                 reverse=True)
    elif sort_by == "Video Count":
        filtered_concepts = sorted(filtered_concepts, key=lambda x: len(x.context_videos), reverse=True)
    else:  # Name
        filtered_concepts = sorted(filtered_concepts, key=lambda x: x.concept_name)
    
    # Display results
    st.write(f"Found {len(filtered_concepts)} concepts")
    
    # Concept grid with maturity indicators
    for concept in filtered_concepts[:20]:  # Show first 20
        with st.expander(f"{concept.concept_name} ({concept.maturity_level})", expanded=False):
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Maturity Level:** {concept.maturity_level}")
                
                # Maturity level visualization
                maturity_colors = {
                    "mentioned": "🔘",
                    "introduced": "🟡",
                    "explained": "🟠", 
                    "analyzed": "🔵",
                    "synthesized": "🟣",
                    "evolved": "🟢"
                }
                
                maturity_indicator = maturity_colors.get(concept.maturity_level, "⚪")
                st.markdown(f"**Status:** {maturity_indicator} {concept.maturity_level.title()}")
                
                if concept.context:
                    st.write(f"**Context:** {concept.context}")
                
                if concept.dependencies:
                    st.write("**Builds on:**")
                    for dep in concept.dependencies:
                        st.write(f"• {dep.prerequisite_concept} ({dep.dependency_type})")
            
            with col2:
                st.write(f"**Videos:** {len(concept.context_videos)}")
                if concept.context_videos:
                    st.write("**Appears in:**")
                    for video_id in concept.context_videos[:3]:  # Show first 3
                        st.write(f"• Video {video_id}")

def show_evolution_paths(flow_map: InformationFlowMap):
    """Show concept evolution paths"""
    
    st.subheader("🛤️ Concept Evolution Paths")
    
    if not flow_map.evolution_paths:
        st.info("No evolution paths found.")
        return
    
    for path in flow_map.evolution_paths:
        with st.expander(f"Path: {path.concept_name}", expanded=False):
            
            st.write(f"**Concept:** {path.concept_name}")
            st.write(f"**Journey:** {path.initial_maturity} → {path.final_maturity}")
            
            if path.progression_steps:
                st.subheader("Progression Steps")
                for i, step in enumerate(path.progression_steps, 1):
                    st.markdown(f"**Step {i}:** {step.maturity_achieved}")
                    st.write(f"*Video:* {step.video_title}")
                    if step.context:
                        st.write(f"*Context:* {step.context}")
                    st.markdown("---")
            
            if path.key_dependencies:
                st.subheader("Key Dependencies")
                for dep in path.key_dependencies:
                    st.write(f"• **{dep.prerequisite_concept}** ({dep.dependency_type})")

def show_concept_clusters(flow_map: InformationFlowMap):
    """Show concept clusters by theme"""
    
    st.subheader("🎭 Concept Clusters")
    
    if not flow_map.concept_clusters:
        st.info("No concept clusters found.")
        return
    
    for cluster in flow_map.concept_clusters:
        with st.expander(f"Cluster: {cluster.theme}", expanded=False):
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Theme:** {cluster.theme}")
                
                if cluster.description:
                    st.write(f"**Description:** {cluster.description}")
                
                st.write("**Concepts in this cluster:**")
                for concept_name in cluster.concept_names:
                    # Find the concept to get its maturity
                    concept = next((c for c in flow_map.concept_nodes if c.concept_name == concept_name), None)
                    if concept:
                        maturity_indicator = {
                            "mentioned": "🔘",
                            "introduced": "🟡", 
                            "explained": "🟠",
                            "analyzed": "🔵",
                            "synthesized": "🟣",
                            "evolved": "🟢"
                        }.get(concept.maturity_level, "⚪")
                        st.write(f"• {maturity_indicator} {concept_name}")
                    else:
                        st.write(f"• {concept_name}")
            
            with col2:
                st.metric("Concepts", len(cluster.concept_names))
                
                # Calculate cluster maturity distribution
                if cluster.concept_names:
                    maturities = []
                    for concept_name in cluster.concept_names:
                        concept = next((c for c in flow_map.concept_nodes if c.concept_name == concept_name), None)
                        if concept:
                            maturities.append(concept.maturity_level)
                    
                    if maturities:
                        st.write("**Maturity Mix:**")
                        maturity_counts = {}
                        for m in maturities:
                            maturity_counts[m] = maturity_counts.get(m, 0) + 1
                        
                        for maturity, count in maturity_counts.items():
                            st.write(f"{maturity}: {count}")

def show_video_flows(flow_map: InformationFlowMap):
    """Show per-video information flows"""
    
    st.subheader("📹 Video Information Flows")
    
    if not flow_map.video_flows:
        st.info("No video flows found.")
        return
    
    for flow in flow_map.video_flows:
        with st.expander(f"Video: {flow.video_title}", expanded=False):
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Video:** {flow.video_title}")
                
                if flow.concepts_introduced:
                    st.subheader("🆕 Concepts Introduced")
                    for concept in flow.concepts_introduced:
                        st.write(f"• {concept}")
                
                if flow.concepts_developed:
                    st.subheader("📈 Concepts Developed")
                    for concept in flow.concepts_developed:
                        st.write(f"• {concept}")
                
                if flow.concepts_concluded:
                    st.subheader("✅ Concepts Concluded")
                    for concept in flow.concepts_concluded:
                        st.write(f"• {concept}")
            
            with col2:
                total_concepts = (len(flow.concepts_introduced or []) + 
                                len(flow.concepts_developed or []) + 
                                len(flow.concepts_concluded or []))
                st.metric("Total Concepts", total_concepts)
                
                st.write("**Breakdown:**")
                st.write(f"Introduced: {len(flow.concepts_introduced or [])}")
                st.write(f"Developed: {len(flow.concepts_developed or [])}")
                st.write(f"Concluded: {len(flow.concepts_concluded or [])}")

def show_flow_visualization(flow_map: InformationFlowMap):
    """Show flow visualization (placeholder for now)"""
    
    st.subheader("🌊 Flow Visualization")
    
    # For now, show flow statistics
    st.info("Interactive flow visualization coming soon!")
    
    # Show flow statistics
    if flow_map.concept_nodes:
        st.subheader("Concept Maturity Distribution")
        
        maturity_counts = {}
        for concept in flow_map.concept_nodes:
            maturity_counts[concept.maturity_level] = maturity_counts.get(concept.maturity_level, 0) + 1
        
        for maturity, count in sorted(maturity_counts.items()):
            percentage = (count / len(flow_map.concept_nodes)) * 100
            st.write(f"**{maturity.title()}:** {count} ({percentage:.1f}%)")
    
    # Concept dependency graph (simplified view)
    if flow_map.concept_nodes:
        st.subheader("Concept Dependencies")
        
        concepts_with_deps = [c for c in flow_map.concept_nodes if c.dependencies]
        
        if concepts_with_deps:
            for concept in concepts_with_deps[:10]:  # Show first 10
                st.write(f"**{concept.concept_name}** depends on:")
                for dep in concept.dependencies:
                    st.write(f"  • {dep.prerequisite_concept} ({dep.dependency_type})")
        else:
            st.info("No concept dependencies found.")

def main():
    """Main Information Flows page"""
    st.title("🔄 Information Flow Maps")
    
    # Get available collections
    collections_path = Path("output/collections")
    
    if not collections_path.exists():
        st.warning("No collections found. Process some multi-video collections first!")
        return
    
    # Find collections with information flow maps
    collection_dirs = [d for d in collections_path.iterdir() if d.is_dir()]
    collections_with_flows = []
    
    for cdir in collection_dirs:
        if (cdir / "information_flow_map.json").exists():
            collections_with_flows.append(cdir.name)
    
    if not collections_with_flows:
        st.warning("No collections with Information Flow Maps found.")
        st.info("Information Flow Maps are generated automatically for multi-video collections.")
        return
    
    # Collection selector
    selected_collection = st.selectbox(
        "Select a collection:",
        collections_with_flows,
        key="if_collection_selector"
    )
    
    if selected_collection:
        collection_path = collections_path / selected_collection
        
        # Load information flow map
        with st.spinner("Loading Information Flow Map..."):
            flow_map = load_information_flow_map(collection_path)
        
        if flow_map:
            st.success(f"✅ Loaded flow map with {len(flow_map.concept_nodes)} concepts")
            
            # Main tabs
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                "📊 Overview",
                "🔍 Concept Explorer",
                "🛤️ Evolution Paths", 
                "🎭 Clusters",
                "📹 Video Flows",
                "🌊 Visualization"
            ])
            
            with tab1:
                show_flow_overview(flow_map)
            
            with tab2:
                show_concept_explorer(flow_map)
            
            with tab3:
                show_evolution_paths(flow_map)
            
            with tab4:
                show_concept_clusters(flow_map)
            
            with tab5:
                show_video_flows(flow_map)
            
            with tab6:
                show_flow_visualization(flow_map)
            
            # Download options
            st.subheader("⬇️ Download Information Flow Map")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📄 Download JSON"):
                    json_data = flow_map.model_dump()
                    st.download_button(
                        label="Download information_flow_map.json",
                        data=json.dumps(json_data, indent=2, ensure_ascii=False),
                        file_name=f"{selected_collection}_flow_map.json",
                        mime="application/json"
                    )
            
            with col2:
                # Check for markdown summary
                summary_file = collection_path / "information_flow_summary.md"
                if summary_file.exists():
                    if st.button("📝 Download Summary"):
                        with open(summary_file, 'r', encoding='utf-8') as f:
                            st.download_button(
                                label="Download information_flow_summary.md",
                                data=f.read(),
                                file_name=f"{selected_collection}_flow_summary.md",
                                mime="text/markdown"
                            )
        
        else:
            st.error("Could not load Information Flow Map data.")

if __name__ == "__main__":
    main() 