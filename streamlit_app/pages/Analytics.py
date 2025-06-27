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
    """Show cost overview metrics"""
    
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
    
    # Cost trends
    st.subheader("📈 Cost Trends")
    
    # Sort costs by date
    sorted_costs = sorted(costs, key=lambda x: x.get('date', ''), reverse=True)
    
    # Recent costs table
    if sorted_costs:
        st.subheader("Recent Processing Costs")
        
        for cost in sorted_costs[:10]:  # Show last 10
            with st.expander(f"{cost['collection_id']} - ${cost['total_cost']:.2f}", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Date:** {cost['date']}")
                    st.write(f"**Videos:** {cost['video_count']}")
                    st.write(f"**Total Cost:** ${cost['total_cost']:.2f}")
                
                with col2:
                    if cost['video_count'] > 0:
                        cost_per_video = cost['total_cost'] / cost['video_count']
                        st.write(f"**Cost per Video:** ${cost_per_video:.2f}")
                    
                    minutes = int(cost['processing_time'] // 60)
                    st.write(f"**Processing Time:** {minutes} minutes")

def show_performance_metrics():
    """Show performance and system metrics"""
    
    st.subheader("⚡ Performance Metrics")
    
    # System info
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💻 System Information")
        
        # Get Python version
        import sys
        st.write(f"**Python Version:** {sys.version.split()[0]}")
        
        # Check for key dependencies
        try:
            import torch
            st.write(f"**PyTorch:** {torch.__version__}")
            
            # Check for GPU
            if torch.cuda.is_available():
                st.success("🟢 CUDA GPU Available")
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                st.success("🟢 Apple Metal GPU Available")
            else:
                st.warning("🟡 CPU Only")
        except ImportError:
            st.warning("⚠️ PyTorch not available")
        
        # Check disk space
        try:
            import shutil
            total, used, free = shutil.disk_usage(".")
            free_gb = free // (1024**3)
            total_gb = total // (1024**3)
            st.write(f"**Disk Space:** {free_gb}GB free / {total_gb}GB total")
        except:
            st.write("**Disk Space:** Unable to determine")
    
    with col2:
        st.markdown("### 🔧 Model Status")
        
        # Check model cache
        model_paths = [
            "~/.cache/huggingface/transformers",
            "~/.cache/spacy",
            "~/.cache/clipscribe"
        ]
        
        for path_str in model_paths:
            path = Path(path_str).expanduser()
            if path.exists():
                try:
                    size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
                    size_mb = size / (1024**2)
                    st.write(f"**{path.name}:** {size_mb:.1f} MB")
                except:
                    st.write(f"**{path.name}:** Present")
            else:
                st.write(f"**{path.name}:** Not found")

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