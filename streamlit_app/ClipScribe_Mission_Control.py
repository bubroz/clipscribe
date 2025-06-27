"""
ClipScribe Mission Control
Interactive Dashboard for Video Intelligence Collections

This is the main entry point for the ClipScribe Streamlit interface.
Provides comprehensive management and visualization of video collections,
Knowledge Panels, Information Flow Maps, and analytics.
"""

import streamlit as st
import sys
from pathlib import Path

# Add the src directory to the path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from clipscribe.config.settings import settings

st.set_page_config(
    page_title="ClipScribe Mission Control",
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
    .phase2-banner {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
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
        <h1>🎬 ClipScribe Mission Control</h1>
        <p>Interactive Video Intelligence Dashboard</p>
    </div>
    """, unsafe_allow_html=True)

    # Phase 2 announcement banner
    st.markdown("""
    <div class="phase2-banner">
        🚀 <strong>v2.16.0 Phase 2 Released!</strong> Enhanced visualizations, real-time processing monitoring, and interactive network graphs now available!
    </div>
    """, unsafe_allow_html=True)

    # Sidebar navigation
    with st.sidebar:
        st.markdown("### 🧭 Navigation")
        
        page = st.selectbox(
            "Choose a page:",
            [
                "🏠 Dashboard",
                "📹 Collections", 
                "👥 Knowledge Panels",
                "🔄 Information Flows",
                "📊 Analytics",
                "🔄 Real-time Processing",
                "⚙️ Settings"
            ]
        )

        st.markdown("---")
        
        # Quick stats in sidebar
        st.markdown("### 📈 Quick Stats")
        
        # Check for output directory
        output_path = Path("output")
        if output_path.exists():
            collections = list(output_path.glob("collections/*"))
            individual_videos = [p for p in output_path.iterdir() 
                               if p.is_dir() and p.name != "collections"]
            
            st.metric("Collections", len(collections))
            st.metric("Individual Videos", len(individual_videos))
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
    elif page == "📹 Collections":
        show_collections()
    elif page == "👥 Knowledge Panels":
        show_knowledge_panels()
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
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>📹 Collections</h3>
            <p>Manage multi-video collections with unified analysis</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>👥 Knowledge Panels</h3>
            <p>Entity-centric intelligence synthesis</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>🔄 Information Flows</h3>
            <p>Concept evolution tracking</p>
        </div>
        """, unsafe_allow_html=True)

    # Recent activity
    st.subheader("🕒 Recent Activity")
    
    output_path = Path("output")
    if output_path.exists():
        # Get recent directories
        recent_dirs = sorted(
            [p for p in output_path.iterdir() if p.is_dir()],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )[:5]
        
        if recent_dirs:
            for i, dir_path in enumerate(recent_dirs):
                with st.expander(f"📁 {dir_path.name}", expanded=i == 0):
                    # Check what files exist
                    files = list(dir_path.glob("*"))
                    st.write(f"**Files:** {len(files)}")
                    
                    # Show key files
                    key_files = [
                        "manifest.json",
                        "video_intelligence.json", 
                        "knowledge_panels.json",
                        "information_flow_map.json"
                    ]
                    
                    for key_file in key_files:
                        if (dir_path / key_file).exists():
                            st.success(f"✅ {key_file}")
                        else:
                            st.warning(f"⚠️ {key_file} (missing)")
        else:
            st.info("No processed videos found. Use the CLI to process some videos first!")
    else:
        st.info("Output directory not found. Process some videos to get started!")

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

def show_knowledge_panels():
    """Display Knowledge Panels viewer"""
    # Import and run the Knowledge Panels page
    try:
        # Add streamlit_app to path for proper imports
        streamlit_app_path = Path(__file__).parent
        if str(streamlit_app_path) not in sys.path:
            sys.path.insert(0, str(streamlit_app_path))
        
        from pages.Knowledge_Panels import main as kp_main
        kp_main()
    except ImportError as e:
        st.error(f"Error loading Knowledge Panels page: {e}")
        st.info("🚧 Knowledge Panels viewer coming soon! This will show entity-centric intelligence.")

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
        - **Live CLI Progress**: Monitor ClipScribe commands in real-time
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
            ["gemini-1.5-flash", "gemini-1.5-pro"],
            index=0,
            help="Model for video transcription"
        )
        
        st.selectbox(
            "Analysis Model", 
            ["gemini-1.5-flash", "gemini-1.5-pro"],
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

if __name__ == "__main__":
    main() 