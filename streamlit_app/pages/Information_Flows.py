"""
Information Flow Maps Page
Interactive exploration of concept evolution tracking
"""

import streamlit as st
import json
import sys
from pathlib import Path
from typing import Dict, List, Any
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import networkx as nx
import pandas as pd
import numpy as np

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
    """Show interactive flow visualizations using Plotly"""
    
    st.subheader("🌊 Interactive Flow Visualizations")
    
    # Visualization type selector
    viz_type = st.selectbox(
        "Choose visualization:",
        [
            "Concept Evolution Timeline",
            "Dependency Network",
            "Maturity Distribution",
            "Video Flow Diagram",
            "Concept Clusters Map"
        ],
        key="flow_viz_type"
    )
    
    if viz_type == "Concept Evolution Timeline":
        show_concept_timeline(flow_map)
    elif viz_type == "Dependency Network":
        show_dependency_network(flow_map)
    elif viz_type == "Maturity Distribution":
        show_maturity_distribution(flow_map)
    elif viz_type == "Video Flow Diagram":
        show_video_flow_diagram(flow_map)
    elif viz_type == "Concept Clusters Map":
        show_clusters_visualization(flow_map)

def show_concept_timeline(flow_map: InformationFlowMap):
    """Interactive concept evolution timeline"""
    
    st.markdown("### 📈 Concept Evolution Timeline")
    
    if not flow_map.evolution_paths:
        st.info("No evolution paths available for timeline visualization.")
        return
    
    # Prepare timeline data
    timeline_data = []
    maturity_order = ["mentioned", "introduced", "explained", "analyzed", "synthesized", "evolved"]
    colors = px.colors.qualitative.Set3
    
    for i, path in enumerate(flow_map.evolution_paths):
        if path.progression_steps:
            for step_idx, step in enumerate(path.progression_steps):
                timeline_data.append({
                    'concept': path.concept_name,
                    'video': step.video_title,
                    'maturity': step.maturity_achieved,
                    'maturity_level': maturity_order.index(step.maturity_achieved) if step.maturity_achieved in maturity_order else 0,
                    'step': step_idx,
                    'context': step.context or '',
                    'color': colors[i % len(colors)]
                })
    
    if not timeline_data:
        st.info("No progression steps found for timeline.")
        return
    
    df = pd.DataFrame(timeline_data)
    
    # Create timeline visualization
    fig = go.Figure()
    
    for concept in df['concept'].unique():
        concept_data = df[df['concept'] == concept].sort_values('step')
        
        fig.add_trace(go.Scatter(
            x=concept_data['step'],
            y=concept_data['maturity_level'],
            mode='lines+markers',
            name=concept,
            text=concept_data['maturity'],
            hovertemplate="<b>%{text}</b><br>" +
                         "Concept: " + concept + "<br>" +
                         "Video: %{customdata[0]}<br>" +
                         "Context: %{customdata[1]}<extra></extra>",
            customdata=list(zip(concept_data['video'], concept_data['context'])),
            line=dict(width=3),
            marker=dict(size=10)
        ))
    
    fig.update_layout(
        title="Concept Maturity Evolution Across Videos",
        xaxis_title="Video Sequence",
        yaxis_title="Maturity Level",
        yaxis=dict(
            tickmode='array',
            tickvals=list(range(len(maturity_order))),
            ticktext=maturity_order
        ),
        height=500,
        hovermode='closest'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_dependency_network(flow_map: InformationFlowMap):
    """Interactive concept dependency network"""
    
    st.markdown("### 🔗 Concept Dependency Network")
    
    # Collect dependencies
    G = nx.DiGraph()
    concept_info = {}
    
    for concept in flow_map.concept_nodes:
        concept_info[concept.concept_name] = {
            'maturity': concept.maturity_level,
            'videos': len(concept.context_videos),
            'context': concept.context or ''
        }
        
        G.add_node(concept.concept_name)
        
        if concept.dependencies:
            for dep in concept.dependencies:
                G.add_edge(dep.prerequisite_concept, concept.concept_name, 
                          relationship=dep.dependency_type)
    
    if len(G.nodes()) == 0:
        st.info("No concept dependencies found.")
        return
    
    # Layout options
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.markdown("#### Network Controls")
        layout_type = st.selectbox("Layout:", ["Spring", "Hierarchical", "Circular"])
        max_nodes = st.slider("Max nodes:", 5, min(30, len(G.nodes())), 15)
    
    with col1:
        # Filter to most connected nodes
        node_degrees = dict(G.degree())
        top_nodes = sorted(node_degrees.items(), key=lambda x: x[1], reverse=True)[:max_nodes]
        top_node_names = [name for name, degree in top_nodes]
        subgraph = G.subgraph(top_node_names).copy()
        
        # Calculate layout
        if layout_type == "Spring":
            pos = nx.spring_layout(subgraph, k=2, iterations=50)
        elif layout_type == "Hierarchical":
            pos = nx.nx_agraph.graphviz_layout(subgraph, prog='dot') if hasattr(nx, 'nx_agraph') else nx.spring_layout(subgraph)
        else:  # Circular
            pos = nx.circular_layout(subgraph)
        
        # Create network plot
        edge_x, edge_y = [], []
        for edge in subgraph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=2, color='rgba(100,100,100,0.5)'),
            hoverinfo='none',
            mode='lines',
            showlegend=False
        )
        
        # Node colors by maturity level
        maturity_colors = {
            "mentioned": "lightblue",
            "introduced": "yellow",
            "explained": "orange",
            "analyzed": "blue",
            "synthesized": "purple",
            "evolved": "green"
        }
        
        node_colors = [maturity_colors.get(concept_info.get(node, {}).get('maturity', ''), 'gray') 
                      for node in subgraph.nodes()]
        
        node_trace = go.Scatter(
            x=[pos[node][0] for node in subgraph.nodes()],
            y=[pos[node][1] for node in subgraph.nodes()],
            mode='markers+text',
            text=list(subgraph.nodes()),
            textposition="middle center",
            textfont=dict(size=8, color="white"),
            hovertemplate="<b>%{text}</b><br>" +
                         "Maturity: %{customdata[0]}<br>" +
                         "Videos: %{customdata[1]}<br>" +
                         "Dependencies: %{customdata[2]}<extra></extra>",
            customdata=[[
                concept_info.get(node, {}).get('maturity', 'Unknown'),
                concept_info.get(node, {}).get('videos', 0),
                subgraph.in_degree(node)
            ] for node in subgraph.nodes()],
            marker=dict(
                size=15,
                color=node_colors,
                line=dict(width=2, color="white")
            ),
            showlegend=False
        )
        
        fig = go.Figure(data=[edge_trace, node_trace],
                       layout=go.Layout(
                           title=f"Concept Dependency Network ({len(subgraph.nodes())} concepts)",
                           showlegend=False,
                           hovermode='closest',
                           margin=dict(b=20,l=5,r=5,t=40),
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           height=500
                       ))
        
        st.plotly_chart(fig, use_container_width=True)

def show_maturity_distribution(flow_map: InformationFlowMap):
    """Interactive maturity distribution charts"""
    
    st.markdown("### 📊 Concept Maturity Distribution")
    
    if not flow_map.concept_nodes:
        st.info("No concepts available for maturity analysis.")
        return
    
    # Prepare maturity data
    maturity_counts = {}
    maturity_by_cluster = {}
    
    for concept in flow_map.concept_nodes:
        maturity = concept.maturity_level
        maturity_counts[maturity] = maturity_counts.get(maturity, 0) + 1
        
        # Find cluster for this concept
        cluster_name = "Unclustered"
        for cluster in flow_map.concept_clusters:
            if concept.concept_name in cluster.concept_names:
                cluster_name = cluster.theme
                break
        
        if cluster_name not in maturity_by_cluster:
            maturity_by_cluster[cluster_name] = {}
        maturity_by_cluster[cluster_name][maturity] = maturity_by_cluster[cluster_name].get(maturity, 0) + 1
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Overall maturity distribution pie chart
        fig_pie = go.Figure(data=[go.Pie(
            labels=list(maturity_counts.keys()),
            values=list(maturity_counts.values()),
            hole=0.3,
            marker_colors=px.colors.qualitative.Set3
        )])
        
        fig_pie.update_layout(
            title="Overall Maturity Distribution",
            height=400
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Maturity progression bar chart
        maturity_order = ["mentioned", "introduced", "explained", "analyzed", "synthesized", "evolved"]
        ordered_counts = [maturity_counts.get(m, 0) for m in maturity_order]
        
        fig_bar = go.Figure(data=[go.Bar(
            x=maturity_order,
            y=ordered_counts,
            marker_color=px.colors.qualitative.Set2
        )])
        
        fig_bar.update_layout(
            title="Maturity Progression",
            xaxis_title="Maturity Level",
            yaxis_title="Number of Concepts",
            height=400
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Cluster-based maturity heatmap
    if len(maturity_by_cluster) > 1:
        st.markdown("#### Maturity by Concept Cluster")
        
        # Prepare heatmap data
        clusters = list(maturity_by_cluster.keys())
        maturities = maturity_order
        
        heatmap_data = []
        for cluster in clusters:
            row = []
            for maturity in maturities:
                row.append(maturity_by_cluster[cluster].get(maturity, 0))
            heatmap_data.append(row)
        
        fig_heatmap = go.Figure(data=go.Heatmap(
            z=heatmap_data,
            x=maturities,
            y=clusters,
            colorscale='Viridis',
            showscale=True
        ))
        
        fig_heatmap.update_layout(
            title="Concept Maturity by Cluster",
            xaxis_title="Maturity Level",
            yaxis_title="Concept Cluster",
            height=300
        )
        
        st.plotly_chart(fig_heatmap, use_container_width=True)

def show_video_flow_diagram(flow_map: InformationFlowMap):
    """Sankey diagram showing concept flow between videos"""
    
    st.markdown("### 🌊 Video Concept Flow Diagram")
    
    if not flow_map.video_flows:
        st.info("No video flows available for diagram.")
        return
    
    # Collect flow data
    all_concepts = set()
    video_concept_data = []
    
    for flow in flow_map.video_flows:
        video_title = flow.video_title[:30] + "..." if len(flow.video_title) > 30 else flow.video_title
        
        for concept in (flow.concepts_introduced or []):
            all_concepts.add(concept)
            video_concept_data.append({
                'video': video_title,
                'concept': concept,
                'flow_type': 'introduced',
                'value': 1
            })
        
        for concept in (flow.concepts_developed or []):
            all_concepts.add(concept)
            video_concept_data.append({
                'video': video_title,
                'concept': concept,
                'flow_type': 'developed',
                'value': 1
            })
    
    if not video_concept_data:
        st.info("No concept flows found between videos.")
        return
    
    # Create flow summary
    flow_summary = {}
    for item in video_concept_data:
        key = (item['video'], item['concept'], item['flow_type'])
        flow_summary[key] = flow_summary.get(key, 0) + item['value']
    
    # Display flow summary table
    st.markdown("#### Concept Flow Summary")
    
    flow_df = pd.DataFrame([
        {
            'Video': video,
            'Concept': concept,
            'Flow Type': flow_type,
            'Count': count
        }
        for (video, concept, flow_type), count in flow_summary.items()
    ])
    
    # Interactive flow table
    if not flow_df.empty:
        st.dataframe(
            flow_df.sort_values(['Video', 'Flow Type', 'Count'], ascending=[True, True, False]),
            use_container_width=True
        )
        
        # Flow type distribution
        flow_type_counts = flow_df.groupby('Flow Type')['Count'].sum()
        
        fig_flow = go.Figure(data=[go.Bar(
            x=flow_type_counts.index,
            y=flow_type_counts.values,
            marker_color=['lightblue', 'orange']
        )])
        
        fig_flow.update_layout(
            title="Concept Flow Types Across Videos",
            xaxis_title="Flow Type",
            yaxis_title="Total Concepts",
            height=300
        )
        
        st.plotly_chart(fig_flow, use_container_width=True)

def show_clusters_visualization(flow_map: InformationFlowMap):
    """Interactive concept clusters visualization"""
    
    st.markdown("### 🎭 Concept Clusters Visualization")
    
    if not flow_map.concept_clusters:
        st.info("No concept clusters available for visualization.")
        return
    
    # Prepare cluster data
    cluster_data = []
    concept_cluster_map = {}
    
    for cluster in flow_map.concept_clusters:
        for concept_name in cluster.concept_names:
            # Find concept details
            concept = next((c for c in flow_map.concept_nodes if c.concept_name == concept_name), None)
            if concept:
                cluster_data.append({
                    'concept': concept_name,
                    'cluster': cluster.theme,
                    'maturity': concept.maturity_level,
                    'videos': len(concept.context_videos),
                    'description': cluster.description or ''
                })
                concept_cluster_map[concept_name] = cluster.theme
    
    if not cluster_data:
        st.info("No concept cluster data available.")
        return
    
    df = pd.DataFrame(cluster_data)
    
    # Cluster size distribution
    col1, col2 = st.columns(2)
    
    with col1:
        cluster_sizes = df.groupby('cluster').size()
        
        fig_cluster_size = go.Figure(data=[go.Bar(
            x=cluster_sizes.index,
            y=cluster_sizes.values,
            marker_color=px.colors.qualitative.Pastel
        )])
        
        fig_cluster_size.update_layout(
            title="Concepts per Cluster",
            xaxis_title="Cluster Theme",
            yaxis_title="Number of Concepts",
            height=400
        )
        
        st.plotly_chart(fig_cluster_size, use_container_width=True)
    
    with col2:
        # Cluster maturity distribution
        maturity_cluster = df.groupby(['cluster', 'maturity']).size().unstack(fill_value=0)
        
        fig_maturity_cluster = go.Figure()
        
        colors = px.colors.qualitative.Set3
        for i, maturity in enumerate(maturity_cluster.columns):
            fig_maturity_cluster.add_trace(go.Bar(
                name=maturity,
                x=maturity_cluster.index,
                y=maturity_cluster[maturity],
                marker_color=colors[i % len(colors)]
            ))
        
        fig_maturity_cluster.update_layout(
            title="Cluster Maturity Distribution",
            xaxis_title="Cluster Theme",
            yaxis_title="Number of Concepts",
            barmode='stack',
            height=400
        )
        
        st.plotly_chart(fig_maturity_cluster, use_container_width=True)
    
    # Detailed cluster table
    st.markdown("#### Cluster Details")
    st.dataframe(
        df[['concept', 'cluster', 'maturity', 'videos']].sort_values(['cluster', 'maturity']),
        use_container_width=True
    )

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