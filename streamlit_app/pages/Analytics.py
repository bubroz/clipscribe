"""
Analytics Page
Cost tracking, performance metrics, and system monitoring
"""

import streamlit as st
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
import os
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

# Add the src directory to the path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

def load_collection_costs():
    """Load cost data from all collections"""
    collections_path = Path("output/collections")
    
    if not collections_path.exists():
        return []
    
    costs = []
    for collection_dir in collections_path.iterdir():
        if collection_dir.is_dir():
            # Look for manifest files
            manifest_file = collection_dir / "manifest.json"
            if manifest_file.exists():
                try:
                    with open(manifest_file, 'r', encoding='utf-8') as f:
                        manifest = json.load(f)
                        
                    cost_data = {
                        'collection_id': collection_dir.name,
                        'date': manifest.get('processing_date', 'Unknown'),
                        'total_cost': manifest.get('processing_cost', 0.0),
                        'video_count': manifest.get('video_count', 0),
                        'processing_time': manifest.get('processing_time_seconds', 0)
                    }
                    costs.append(cost_data)
                except Exception as e:
                    st.error(f"Error loading manifest from {collection_dir.name}: {e}")
    
    # Also check individual videos
    output_path = Path("output")
    if output_path.exists():
        for item in output_path.iterdir():
            if item.is_dir() and item.name != "collections":
                manifest_file = item / "manifest.json"
                if manifest_file.exists():
                    try:
                        with open(manifest_file, 'r', encoding='utf-8') as f:
                            manifest = json.load(f)
                        
                        cost_data = {
                            'collection_id': f"Single: {item.name}",
                            'date': manifest.get('processing_date', 'Unknown'),
                            'total_cost': manifest.get('processing_cost', 0.0),
                            'video_count': 1,
                            'processing_time': manifest.get('processing_time_seconds', 0)
                        }
                        costs.append(cost_data)
                    except Exception as e:
                        continue
    
    return costs

def show_cost_overview(costs: List[Dict]):
    """Show cost overview metrics with interactive charts"""
    
    if not costs:
        st.info("No cost data available. Process some videos to see analytics.")
        return
    
    # Calculate totals
    total_cost = sum(cost['total_cost'] for cost in costs)
    total_videos = sum(cost['video_count'] for cost in costs)
    total_time = sum(cost['processing_time'] for cost in costs)
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Cost", f"${total_cost:.2f}")
    
    with col2:
        st.metric("Total Videos", total_videos)
    
    with col3:
        avg_cost_per_video = total_cost / total_videos if total_videos > 0 else 0
        st.metric("Avg Cost/Video", f"${avg_cost_per_video:.2f}")
    
    with col4:
        hours = int(total_time // 3600)
        minutes = int((total_time % 3600) // 60)
        st.metric("Total Processing Time", f"{hours}h {minutes}m")
    
    # Enhanced cost trends with interactive charts
    st.subheader("📈 Interactive Cost Analysis")
    
    if len(costs) > 1:
        # Prepare cost trend data
        cost_df = pd.DataFrame(costs)
        cost_df['date'] = pd.to_datetime(cost_df['date'], errors='coerce')
        cost_df = cost_df.sort_values('date').dropna(subset=['date'])
        
        if not cost_df.empty:
            # Cost trend over time
            fig_trend = go.Figure()
            
            fig_trend.add_trace(go.Scatter(
                x=cost_df['date'],
                y=cost_df['total_cost'],
                mode='lines+markers',
                name='Total Cost',
                line=dict(color='blue', width=3),
                marker=dict(size=8),
                hovertemplate="<b>%{y:.2f}</b><br>Date: %{x}<br>Collection: %{customdata}<extra></extra>",
                customdata=cost_df['collection_id']
            ))
            
            fig_trend.update_layout(
                title="Cost Trend Over Time",
                xaxis_title="Date",
                yaxis_title="Cost ($)",
                height=400,
                hovermode='closest'
            )
            
            st.plotly_chart(fig_trend, use_container_width=True)
            
            # Cost efficiency analysis
            col1, col2 = st.columns(2)
            
            with col1:
                # Cost per video scatter plot
                fig_efficiency = go.Figure()
                
                fig_efficiency.add_trace(go.Scatter(
                    x=cost_df['video_count'],
                    y=cost_df['total_cost'] / cost_df['video_count'],
                    mode='markers',
                    marker=dict(
                        size=cost_df['processing_time'] / 60,  # Size by processing time
                        color=cost_df['total_cost'],
                        colorscale='Viridis',
                        colorbar=dict(title="Total Cost ($)"),
                        sizemin=5,
                        sizemax=25
                    ),
                    text=cost_df['collection_id'],
                    hovertemplate="<b>%{text}</b><br>" +
                                 "Videos: %{x}<br>" +
                                 "Cost/Video: $%{y:.2f}<br>" +
                                 "Processing Time: %{marker.size:.0f} min<extra></extra>"
                ))
                
                fig_efficiency.update_layout(
                    title="Cost Efficiency Analysis",
                    xaxis_title="Number of Videos",
                    yaxis_title="Cost per Video ($)",
                    height=400
                )
                
                st.plotly_chart(fig_efficiency, use_container_width=True)
            
            with col2:
                # Processing time vs cost
                fig_time_cost = go.Figure()
                
                fig_time_cost.add_trace(go.Scatter(
                    x=cost_df['processing_time'] / 60,  # Convert to minutes
                    y=cost_df['total_cost'],
                    mode='markers',
                    marker=dict(
                        size=cost_df['video_count'] * 3,
                        color='orange',
                        line=dict(width=1, color='white')
                    ),
                    text=cost_df['collection_id'],
                    hovertemplate="<b>%{text}</b><br>" +
                                 "Processing Time: %{x:.0f} min<br>" +
                                 "Total Cost: $%{y:.2f}<br>" +
                                 "Videos: %{marker.size:.0f}<extra></extra>"
                ))
                
                fig_time_cost.update_layout(
                    title="Processing Time vs Cost",
                    xaxis_title="Processing Time (minutes)",
                    yaxis_title="Total Cost ($)",
                    height=400
                )
                
                st.plotly_chart(fig_time_cost, use_container_width=True)
    
    # Recent costs table (enhanced)
    st.subheader("Recent Processing History")
    
    # Sort costs by date
    sorted_costs = sorted(costs, key=lambda x: x.get('date', ''), reverse=True)
    
    if sorted_costs:
        # Create enhanced table
        recent_df = pd.DataFrame([
            {
                'Collection': cost['collection_id'],
                'Date': cost['date'],
                'Videos': cost['video_count'],
                'Total Cost': f"${cost['total_cost']:.2f}",
                'Cost/Video': f"${cost['total_cost']/cost['video_count']:.2f}" if cost['video_count'] > 0 else "$0.00",
                'Processing Time': f"{int(cost['processing_time']//60)}m {int(cost['processing_time']%60)}s"
            }
            for cost in sorted_costs[:10]
        ])
        
        st.dataframe(recent_df, use_container_width=True)

def show_performance_metrics():
    """Show enhanced performance and system metrics with gauges and charts"""
    
    st.subheader("⚡ Enhanced Performance Dashboard")
    
    # System info with gauges
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💻 System Performance")
        
        # Get system metrics
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('.')
            
            # CPU gauge
            fig_cpu = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = cpu_percent,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "CPU Usage (%)"},
                delta = {'reference': 50},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "yellow"},
                        {'range': [80, 100], 'color': "red"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            fig_cpu.update_layout(height=250)
            st.plotly_chart(fig_cpu, use_container_width=True)
            
            # Memory usage
            memory_percent = memory.percent
            fig_memory = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = memory_percent,
                title = {'text': "Memory Usage (%)"},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "green"},
                    'steps': [
                        {'range': [0, 60], 'color': "lightgray"},
                        {'range': [60, 85], 'color': "yellow"},
                        {'range': [85, 100], 'color': "red"}
                    ]
                }
            ))
            fig_memory.update_layout(height=250)
            st.plotly_chart(fig_memory, use_container_width=True)
            
        except ImportError:
            st.warning("📊 Install psutil for enhanced system monitoring: `pip install psutil`")
            
            # Fallback system info
            import sys
            st.write(f"**Python Version:** {sys.version.split()[0]}")
            
            # Check disk space
            try:
                import shutil
                total, used, free = shutil.disk_usage(".")
                free_gb = free // (1024**3)
                total_gb = total // (1024**3)
                
                disk_percent = (used / total) * 100
                fig_disk = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = disk_percent,
                    title = {'text': f"Disk Usage (%) - {free_gb}GB free"},
                    gauge = {
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "purple"},
                        'steps': [
                            {'range': [0, 70], 'color': "lightgray"},
                            {'range': [70, 90], 'color': "yellow"},
                            {'range': [90, 100], 'color': "red"}
                        ]
                    }
                ))
                fig_disk.update_layout(height=300)
                st.plotly_chart(fig_disk, use_container_width=True)
            except:
                st.write("**Disk Space:** Unable to determine")
    
    with col2:
        st.markdown("### 🔧 Model & Cache Status")
        
        # Check for key dependencies with status indicators
        dependency_status = []
        
        try:
            import torch
            torch_version = torch.__version__
            dependency_status.append({"name": "PyTorch", "version": torch_version, "status": "✅"})
            
            # GPU status
            if torch.cuda.is_available():
                gpu_info = "CUDA GPU Available"
                gpu_status = "🟢"
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                gpu_info = "Apple Metal GPU"
                gpu_status = "🟢"
            else:
                gpu_info = "CPU Only"
                gpu_status = "🟡"
            
            dependency_status.append({"name": "GPU Support", "version": gpu_info, "status": gpu_status})
            
        except ImportError:
            dependency_status.append({"name": "PyTorch", "version": "Not installed", "status": "⚠️"})
        
        # Check model cache sizes
        model_paths = [
            ("HuggingFace", "~/.cache/huggingface/transformers"),
            ("SpaCy", "~/.cache/spacy"),
            ("ClipScribe", "~/.cache/clipscribe")
        ]
        
        cache_data = []
        for name, path_str in model_paths:
            path = Path(path_str).expanduser()
            if path.exists():
                try:
                    size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
                    size_mb = size / (1024**2)
                    cache_data.append({"name": name, "size_mb": size_mb, "status": "✅"})
                except:
                    cache_data.append({"name": name, "size_mb": 0, "status": "⚠️"})
            else:
                cache_data.append({"name": name, "size_mb": 0, "status": "❌"})
        
        # Cache size visualization
        if cache_data:
            cache_df = pd.DataFrame(cache_data)
            
            fig_cache = go.Figure(data=[go.Bar(
                x=cache_df['name'],
                y=cache_df['size_mb'],
                marker_color=['green' if status == '✅' else 'orange' if status == '⚠️' else 'red' 
                             for status in cache_df['status']],
                text=[f"{size:.0f} MB" for size in cache_df['size_mb']],
                textposition='auto'
            )])
            
            fig_cache.update_layout(
                title="Model Cache Sizes",
                xaxis_title="Cache Type",
                yaxis_title="Size (MB)",
                height=300
            )
            
            st.plotly_chart(fig_cache, use_container_width=True)
        
        # Dependency status table
        if dependency_status:
            dep_df = pd.DataFrame(dependency_status)
            st.markdown("#### Dependency Status")
            st.dataframe(dep_df, use_container_width=True)

def show_api_usage():
    """Show API usage and quota information"""
    
    st.subheader("🔑 API Usage")
    
    # API key status
    from clipscribe.config.settings import settings
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔐 API Key Status")
        
        if settings.google_api_key:
            st.success("✅ Google API Key configured")
            
            # Mask the key for display
            key_preview = settings.google_api_key[:8] + "..." + settings.google_api_key[-4:]
            st.write(f"**Key:** {key_preview}")
        else:
            st.error("❌ No Google API Key found")
            st.info("Set GOOGLE_API_KEY environment variable")
    
    with col2:
        st.markdown("### 📊 Usage Estimates")
        
        costs = load_collection_costs()
        if costs:
            total_cost = sum(cost['total_cost'] for cost in costs)
            total_videos = sum(cost['video_count'] for cost in costs)
            
            # Estimate usage patterns
            if total_videos > 0:
                avg_cost = total_cost / total_videos
                
                st.write(f"**Average per video:** ${avg_cost:.3f}")
                
                # Project monthly costs at different usage levels
                st.write("**Monthly projections:**")
                for videos_per_month in [10, 50, 100]:
                    monthly_cost = videos_per_month * avg_cost
                    st.write(f"• {videos_per_month} videos/month: ${monthly_cost:.2f}")

def show_quality_metrics():
    """Show extraction quality metrics"""
    
    st.subheader("🎯 Quality Metrics")
    
    # Look for recent processing logs or manifests with quality data
    output_path = Path("output")
    quality_data = []
    
    if output_path.exists():
        for item in output_path.rglob("manifest.json"):
            try:
                with open(item, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                
                if 'extraction_stats' in manifest:
                    stats = manifest['extraction_stats']
                    quality_data.append({
                        'source': item.parent.name,
                        'entities': stats.get('total_entities', 0),
                        'relationships': stats.get('total_relationships', 0),
                        'confidence': stats.get('avg_confidence', 0)
                    })
            except:
                continue
    
    if quality_data:
        st.subheader("Extraction Quality Overview")
        
        # Average metrics
        avg_entities = sum(d['entities'] for d in quality_data) / len(quality_data)
        avg_relationships = sum(d['relationships'] for d in quality_data) / len(quality_data)
        avg_confidence = sum(d['confidence'] for d in quality_data) / len(quality_data)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Avg Entities/Video", f"{avg_entities:.0f}")
        
        with col2:
            st.metric("Avg Relationships/Video", f"{avg_relationships:.0f}")
        
        with col3:
            st.metric("Avg Confidence", f"{avg_confidence:.2f}")
    
    else:
        st.info("No quality metrics available yet.")

def show_optimization_recommendations():
    """Show optimization recommendations"""
    
    st.subheader("💡 Optimization Recommendations")
    
    costs = load_collection_costs()
    recommendations = []
    
    if costs:
        total_cost = sum(cost['total_cost'] for cost in costs)
        total_videos = sum(cost['video_count'] for cost in costs)
        
        if total_videos > 0:
            avg_cost_per_video = total_cost / total_videos
            
            # Cost-based recommendations
            if avg_cost_per_video > 1.0:
                recommendations.append({
                    'type': 'warning',
                    'title': 'High Per-Video Cost',
                    'message': f'Average cost of ${avg_cost_per_video:.2f}/video is above $1.00 threshold.',
                    'action': 'Consider using Gemini 1.5 Flash instead of Pro for transcription.'
                })
            
            if avg_cost_per_video > 0.5:
                recommendations.append({
                    'type': 'info',
                    'title': 'Cost Optimization',
                    'message': 'Consider batch processing multiple videos to amortize setup costs.',
                    'action': 'Use process-collection command for related videos.'
                })
    
    # System-based recommendations
    try:
        import torch
        if not torch.cuda.is_available() and not (hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()):
            recommendations.append({
                'type': 'info',
                'title': 'GPU Acceleration',
                'message': 'GPU not detected. Local models will run slower.',
                'action': 'Consider cloud processing or GPU upgrade for better performance.'
            })
    except ImportError:
        recommendations.append({
            'type': 'warning',
            'title': 'Missing Dependencies',
            'message': 'PyTorch not available. Some features may not work.',
            'action': 'Run: poetry install to ensure all dependencies are installed.'
        })
    
    # Display recommendations
    if recommendations:
        for rec in recommendations:
            if rec['type'] == 'warning':
                st.warning(f"⚠️ **{rec['title']}**: {rec['message']}\n\n💡 *{rec['action']}*")
            else:
                st.info(f"💡 **{rec['title']}**: {rec['message']}\n\n🎯 *{rec['action']}*")
    else:
        st.success("🎉 No optimization recommendations at this time. System looks good!")

def main():
    """Main Analytics page"""
    st.title("📊 Analytics")
    
    # Load cost data
    costs = load_collection_costs()
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💰 Cost Overview",
        "⚡ Performance",
        "🔑 API Usage",
        "🎯 Quality",
        "💡 Optimization"
    ])
    
    with tab1:
        show_cost_overview(costs)
    
    with tab2:
        show_performance_metrics()
    
    with tab3:
        show_api_usage()
    
    with tab4:
        show_quality_metrics()
    
    with tab5:
        show_optimization_recommendations()

if __name__ == "__main__":
    main() 