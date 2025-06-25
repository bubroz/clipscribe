import streamlit as st
import asyncio
from pathlib import Path
import os
import time

from src.clipscribe.retrievers import VideoIntelligenceRetriever
from src.clipscribe.utils.performance import PerformanceMonitor

# --- Page Config ---
st.set_page_config(
    page_title="ClipScribe Web UI",
    page_icon="🚀",
    layout="wide",
)

# --- App State ---
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'video_result' not in st.session_state:
    st.session_state.video_result = None
if 'output_dir' not in st.session_state:
    st.session_state.output_dir = None

# --- UI Layout ---
st.sidebar.title("⚙️ Configuration")
processing_mode = st.sidebar.selectbox(
    "Processing Mode",
    options=["audio", "video", "auto"],
    index=0,
    help="**Audio**: Fastest, for podcasts/talks. **Video**: Slower, for visual content. **Auto**: Detects best mode."
)
use_cache = st.sidebar.checkbox(
    "Use Cache",
    value=True,
    help="Use previously downloaded/processed results to speed up analysis."
)
clean_graph = st.sidebar.checkbox(
    "Clean Knowledge Graph",
    value=True,
    help="Use an AI pass to clean and refine the extracted knowledge graph (adds a small cost)."
)

# --- Helper Functions ---
def run_async(func):
    """A wrapper to run async functions in Streamlit."""
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))
    return wrapper

@run_async
async def process_video_url(url, output_dir, mode, use_cache, clean_graph):
    """The main async function to process a video."""
    st.session_state.processing = True
    st.session_state.video_result = None
    
    status_placeholder = st.empty()
    progress_bar = st.progress(0, "Initializing...")

    def streamlit_progress_hook(update):
        """Callback to update the Streamlit UI."""
        # This is a simple implementation. A more robust one might
        # map phases to percentage completion.
        description = update.get("description", "Processing...")
        progress_value = update.get("progress", 0)
        status_placeholder.info(f"⚙️ {description}")
        progress_bar.progress(progress_value, text=description)

    try:
        retriever = VideoIntelligenceRetriever(
            use_cache=use_cache,
            mode=mode,
            output_dir=output_dir,
            progress_hook=streamlit_progress_hook
        )
        retriever.clean_graph = clean_graph
        
        # We need to adapt the retriever to call the hook with percentages.
        # For now, this will just show text updates.
        result = await retriever.process_url(url)
        
        if result:
            # Now, save all the output files, including the report
            streamlit_progress_hook({"description": "Saving output files...", "progress": 95})
            retriever.save_all_formats(
                result, 
                output_dir=str(output_dir),
                include_chimera_format=True
            )
            
        st.session_state.video_result = result
        st.session_state.output_dir = output_dir

    except Exception as e:
        st.error(f"An error occurred: {e}")
    finally:
        st.session_state.processing = False
        progress_bar.empty()
        status_placeholder.empty()

# --- UI Layout ---
st.title("🚀 ClipScribe Web UI")
st.markdown("Transform any video into structured, searchable knowledge. Enter a URL from YouTube, X/Twitter, TikTok, or 1800+ other platforms to get started.")

url = st.text_input("Enter Video URL", placeholder="https://www.youtube.com/watch?v=...")

if st.button("Analyze Video", type="primary", disabled=st.session_state.processing):
    if url:
        # Create a unique output directory for this run
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        video_id = url.split("=")[-1] if "youtube" in url else url.split("/")[-1]
        output_dir = Path(f"output/streamlit_{timestamp}_{video_id}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        process_video_url(
            url, 
            output_dir,
            mode=processing_mode,
            use_cache=use_cache,
            clean_graph=clean_graph
        )
    else:
        st.warning("Please enter a URL.")

# --- Results Display ---
if st.session_state.video_result:
    result = st.session_state.video_result
    st.success("Analysis Complete!")
    
    st.header(result.metadata.title)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Duration", f"{int(result.metadata.duration // 60)}m {int(result.metadata.duration % 60)}s")
    col2.metric("Entities", len(result.entities))
    col3.metric("Relationships", len(getattr(result, 'relationships', [])))

    with st.expander("📝 Executive Summary", expanded=True):
        st.markdown(result.summary)

    with st.expander("📊 Markdown Report"):
        try:
            # The report is in the subdirectory, find it first
            output_dir = st.session_state.output_dir
            subdirectories = [d for d in output_dir.iterdir() if d.is_dir()]
            if subdirectories:
                report_path = subdirectories[0] / "report.md"
                with open(report_path, "r", encoding="utf-8") as f:
                    report_content = f.read()
                st.markdown(report_content, unsafe_allow_html=True)
            else:
                st.warning("Markdown report not found.")
        except FileNotFoundError:
            st.warning("Markdown report not found.")

    with st.expander("🗂️ Download Files"):
        # List and provide download buttons for all generated files
        output_dir = st.session_state.output_dir
        
        # The actual files are in a subdirectory, let's find it
        subdirectories = [d for d in output_dir.iterdir() if d.is_dir()]
        if subdirectories:
            files_dir = subdirectories[0]
            for filename in os.listdir(files_dir):
                file_path = files_dir / filename
                if file_path.is_file(): # Ensure we only try to open files
                    with open(file_path, "rb") as f:
                        st.download_button(
                            label=f"Download {filename}",
                            data=f,
                            file_name=filename,
                            mime="application/octet-stream"
                        )
        else:
            st.warning("Could not find output directory with files.") 