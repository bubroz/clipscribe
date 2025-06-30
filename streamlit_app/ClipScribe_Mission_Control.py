"""
ARGOS Mission Control
Interactive Dashboard for Video Intelligence Collections

This is the main entry point for the ARGOS Streamlit interface.
Provides comprehensive management and visualization of video collections,
Timeline Intelligence, Information Flow Maps, and analytics.
"""

import streamlit as st
import sys
from pathlib import Path

# Add the src directory to the path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from clipscribe.config.settings import settings

st.set_page_config(
    page_title="ARGOS Mission Control",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main application entry point"""
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
    }
    .success-banner {
        background: #d4edda;
        color: #155724;
        padding: 0.75rem;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
        margin-bottom: 1rem;
    }
    .completion-banner {
        background: linear-gradient(90deg, #28a745 0%, #20c997 100%);
        color: white;
        padding: 0.75rem;
        border-radius: 5px;
        margin-bottom: 1rem;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🎬 ARGOS Mission Control</h1>
        <p>Enhanced Temporal Intelligence Dashboard</p>
    </div>
    """, unsafe_allow_html=True)

    # v2.17.0 completion banner
    st.markdown("""
    <div class="completion-banner">
        🚀 <strong>v2.17.0 COMPLETE!</strong> Timeline Building Pipeline with enhanced temporal intelligence now available! All 4/4 components operational.
    </div>
    """, unsafe_allow_html=True)

    # Sidebar navigation
    with st.sidebar:
        st.markdown("### 🧭 Navigation")
        
        page = st.selectbox(
            "Choose a page:",
            [
                "🏠 Dashboard",
                "⏰ Timeline Intelligence", 
                "📹 Collections", 
                "🔄 Information Flows",
                "📊 Analytics",
                "🔄 Real-time Processing",
                "⚙️ Settings"
            ]
        )

        st.markdown("---")
        
        # Quick stats in sidebar
        st.markdown("### 📈 Quick Stats")
        
        # Check for output directory (relative to streamlit_app)
        output_path = Path("../output")
        if output_path.exists():
            collections_path = output_path / "collections"
            collections = list(collections_path.glob("*")) if collections_path.exists() else []
            individual_videos = [p for p in output_path.iterdir() 
                               if p.is_dir() and p.name != "collections"]
            
            st.metric("Collections", len(collections))
            st.metric("Individual Videos", len(individual_videos))
            
            # Timeline intelligence stats
            timeline_collections = 0
            for collection in collections:
                timeline_files = [
                    collection / "timeline.json",  # v2.17.0 Timeline Building Pipeline
                    collection / "consolidated_timeline.json"  # Legacy format
                ]
                if any(f.exists() for f in timeline_files):
                    timeline_collections += 1
            
            st.metric("Timeline Collections", timeline_collections)
        else:
            st.info("No processed videos found")

        st.markdown("---")
        st.markdown("### 🔧 Quick Actions")
        
        if st.button("🔄 Refresh Data"):
            st.rerun()
        
        if st.button("📁 Open Output Folder"):
            st.info("Output folder: `./output/`")

    # Main content area based on navigation
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "⏰ Timeline Intelligence":
        show_timeline_intelligence()
    elif page == "📹 Collections":
        show_collections()
    elif page == "🔄 Information Flows":
        show_information_flows()
    elif page == "📊 Analytics":
        show_analytics()
    elif page == "🔄 Real-time Processing":
        show_processing_monitor()
    elif page == "⚙️ Settings":
        show_settings()

def show_dashboard():
    """Display the main dashboard"""
    st.header("🏠 Dashboard")
    
    # v2.17.0 completion status
    st.markdown("### ✅ ARGOS v2.17.0 Status")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Enhanced Processing", "✅ COMPLETE", help="Direct video-to-Gemini processing")
    with col2:
        st.metric("Video Retention", "✅ COMPLETE", help="Smart cost-optimized retention")  
    with col3:
        st.metric("Timeline Synthesis", "✅ COMPLETE", help="LLM-based temporal intelligence")
    with col4:
        st.metric("Timeline Pipeline", "✅ COMPLETE", help="Web research integration")
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>⏰ Timeline Intelligence</h3>
            <p>Enhanced temporal intelligence with web research integration (v2.17.0)</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>📹 Collections</h3>
            <p>Manage multi-video collections with unified timeline analysis</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>🔄 Information Flows</h3>
            <p>Concept evolution tracking across video sequences</p>
        </div>
        """, unsafe_allow_html=True)

    # Recent activity
    st.subheader("🕒 Recent Activity")
    
    output_path = Path("../output")
    if output_path.exists():
        # Get collections first (priority)
        collections_path = output_path / "collections"
        recent_dirs = []
        
        if collections_path.exists():
            # Filter out special directories from collections
            skip_collection_dirs = {"individual_videos", "video_archive", ".DS_Store"}
            collection_dirs = sorted(
                [p for p in collections_path.iterdir() 
                 if p.is_dir() and p.name not in skip_collection_dirs],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            recent_dirs.extend(collection_dirs[:3])  # Top 3 collections
        
        # Then add individual videos (skip special directories)
        skip_dirs = {"collections", "individual_videos", "video_archive", ".DS_Store"}
        individual_dirs = sorted(
            [p for p in output_path.iterdir() 
             if p.is_dir() and p.name not in skip_dirs],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        recent_dirs.extend(individual_dirs[:2])  # Top 2 individual videos
        
        if recent_dirs:
            for i, dir_path in enumerate(recent_dirs):
                # Determine if this is a collection or individual video
                is_collection = "collections" in str(dir_path.parent)
                
                with st.expander(f"📁 {dir_path.name}", expanded=i == 0):
                    # Check what files exist
                    files = list(dir_path.glob("*"))
                    st.write(f"**Files:** {len(files)}")
                    
                    # Show key files based on actual file structure
                    if is_collection:
                        # Collection directories - check our actual files
                        key_files = [
                            "collection_intelligence.json",
                            "timeline.json",
                            "information_flow_map.json",
                            "unified_knowledge_graph.gexf",
                            "information_flow_summary.md"
                        ]
                    else:
                        # Individual video directories - actual file structure
                        key_files = [
                            "knowledge_graph.gexf",
                            "transcript.json",
                            "entities.json",
                            "chimera_format.json"
                        ]
                    
                    for key_file in key_files:
                        if (dir_path / key_file).exists():
                            st.success(f"✅ {key_file}")
                        else:
                            st.warning(f"⚠️ {key_file} (missing)")
                    
                    # Show collection-specific info
                    if is_collection:
                        st.info("📚 Collection - Multi-video temporal intelligence")
                    else:
                        st.info("📹 Individual Video - Single video processing")
        else:
            st.info("No processed videos found. Use the CLI to process some videos first!")
    else:
        st.info("Output directory not found. Process some videos to get started!")

def show_timeline_intelligence():
    """Display Timeline Intelligence page"""
    # Import and run the Timeline Intelligence page
    try:
        # Add streamlit_app to path for proper imports
        streamlit_app_path = Path(__file__).parent
        if str(streamlit_app_path) not in sys.path:
            sys.path.insert(0, str(streamlit_app_path))
        
        from pages.Timeline_Intelligence import main as timeline_main
        timeline_main()
    except ImportError as e:
        st.error(f"Error loading Timeline Intelligence page: {e}")
        st.info("🚧 Timeline Intelligence page requires v2.17.0 Timeline Building Pipeline components.")

def show_collections():
    """Display collections management page"""
    # Import and run the Collections page
    try:
        # Add streamlit_app to path for proper imports
        streamlit_app_path = Path(__file__).parent
        if str(streamlit_app_path) not in sys.path:
            sys.path.insert(0, str(streamlit_app_path))
        
        from pages.Collections import main as collections_main
        collections_main()
    except ImportError as e:
        st.error(f"Error loading Collections page: {e}")
        st.info("🚧 Collections page coming soon! This will show all multi-video collections.")

def show_information_flows():
    """Display Information Flow Maps"""
    # Import and run the Information Flows page
    try:
        # Add streamlit_app to path for proper imports
        streamlit_app_path = Path(__file__).parent
        if str(streamlit_app_path) not in sys.path:
            sys.path.insert(0, str(streamlit_app_path))
        
        from pages.Information_Flows import main as if_main
        if_main()
    except ImportError as e:
        st.error(f"Error loading Information Flows page: {e}")
        st.info("🚧 Information Flow Maps viewer coming soon! This will show concept evolution.")

def show_analytics():
    """Display analytics and metrics"""
    # Import and run the Analytics page
    try:
        # Add streamlit_app to path for proper imports
        streamlit_app_path = Path(__file__).parent
        if str(streamlit_app_path) not in sys.path:
            sys.path.insert(0, str(streamlit_app_path))
        
        from pages.Analytics import main as analytics_main
        analytics_main()
    except ImportError as e:
        st.error(f"Error loading Analytics page: {e}")
        st.info("🚧 Analytics page coming soon! This will show cost tracking and performance metrics.")

def show_processing_monitor():
    """Display the Real-time Processing Monitor"""
    # Import and run the Processing Monitor
    try:
        # Add streamlit_app to path for proper imports
        streamlit_app_path = Path(__file__).parent
        if str(streamlit_app_path) not in sys.path:
            sys.path.insert(0, str(streamlit_app_path))
        
        from components.processing_monitor import main as processing_main
        processing_main()
    except ImportError as e:
        st.error(f"Error loading Processing Monitor: {e}")
        st.info("🚧 Real-time Processing Monitor is a Phase 2 feature!")
        
        # Fallback content
        st.header("🔄 Real-time Processing Monitor")
        st.info("""
        This feature provides:
        - **Live CLI Progress**: Monitor ARGOS commands in real-time
        - **Cost Tracking**: Real-time API cost monitoring
        - **Processing Queue**: Job history and queue management
        - **Auto-refresh**: Live updates every 5 seconds
        
        📋 **Phase 2 Enhancement**: Interactive processing dashboard with live logs!
        """)

def show_settings():
    """Display settings and configuration"""
    st.header("⚙️ Settings")
    
    st.subheader("🔑 API Configuration")
    
    # API Key management
    api_key = st.text_input(
        "Google API Key",
        value="***" if settings.google_api_key else "",
        type="password",
        help="Your Google API key for Gemini access"
    )
    
    if api_key and api_key != "***":
        st.success("✅ API key provided")
    elif settings.google_api_key:
        st.success("✅ API key loaded from environment")
    else:
        st.error("❌ No API key found. Set GOOGLE_API_KEY environment variable.")
    
    st.subheader("🎛️ Processing Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.selectbox(
            "Transcription Model",
            ["gemini-2.5-flash", "gemini-2.5-pro"],
            index=0,
            help="Model for video transcription"
        )
        
        st.selectbox(
            "Analysis Model", 
            ["gemini-2.5-flash", "gemini-2.5-pro"],
            index=0,
            help="Model for intelligence analysis"
        )
    
    with col2:
        st.slider(
            "Confidence Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.8,
            step=0.1,
            help="Confidence threshold for entity extraction"
        )
        
        st.number_input(
            "Cost Warning Threshold ($)",
            min_value=0.0,
            value=1.0,
            step=0.1,
            help="Show warning when cost exceeds this amount"
        )
    
    # v2.17.0 Timeline Settings
    st.subheader("⏰ Timeline Intelligence Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.toggle(
            "Enhanced Temporal Intelligence",
            value=True,
            help="Enable enhanced temporal intelligence processing (v2.17.0)"
        )
        
        st.selectbox(
            "Temporal Intelligence Level",
            ["standard", "enhanced", "maximum"],
            index=1,
            help="Level of temporal intelligence processing"
        )
    
    with col2:
        st.toggle(
            "Web Research Integration",
            value=False,
            help="Enable external research validation (incurs additional costs)"
        )
        
        st.slider(
            "Timeline Confidence Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1,
            help="Minimum confidence for timeline events"
        )

if __name__ == "__main__":
    main() 