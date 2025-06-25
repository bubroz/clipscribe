import streamlit as st
import asyncio
from pathlib import Path
import os
import time
import pandas as pd

from src.clipscribe.retrievers import VideoIntelligenceRetriever, UniversalVideoClient
from src.clipscribe.utils.performance import PerformanceMonitor
import logging

logger = logging.getLogger(__name__)

# --- Page Config ---
st.set_page_config(
    page_title="ClipScribe Web UI",
    page_icon="🚀",
    layout="wide",
)

# --- App State ---
def initialize_session_state():
    """Initialize all session state variables."""
    defaults = {
        'processing': False,
        'video_result': None,
        'output_dir': None,
        'research_results': [],
        'research_in_progress': False,
        'processed_results': {},
        'research_df_data': []
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

async def process_video_url(url, output_dir, mode, use_cache, clean_graph):
    """The main async function to process a video."""
    st.session_state.processing = True
    st.session_state.video_result = None
    
    status_placeholder = st.empty()
    progress_bar = st.progress(0, "Initializing...")

    def streamlit_progress_hook(update):
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
        
        result = await retriever.process_url(url)
        
        if result:
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

async def run_research_search(query: str, search_type: str, max_results: int, period: str, sort_by: str):
    """Runs the backend search for videos."""
    st.session_state.research_in_progress = True
    st.session_state.research_results = []
    st.session_state.research_df_data = [] # Clear previous results
    
    try:
        video_client = UniversalVideoClient()
        search_results = []

        is_channel_search = search_type == "Channel URL"

        if is_channel_search:
            if "youtube.com/" not in query and "youtu.be/" not in query:
                st.error("Please enter a valid YouTube channel URL.")
                return
            search_results = await video_client.search_channel(query, max_results=max_results, sort_by=sort_by)
        else:
            search_results = await video_client.search_videos(query, max_results=max_results, period=period)
        
        st.session_state.research_results = search_results
    except Exception as e:
        st.error(f"An error occurred during search: {e}")
    finally:
        st.session_state.research_in_progress = False

async def process_video_for_batch(video_meta, sidebar_config):
    """Processes a single video for a batch job."""
    video_output_dir = Path(f"output/research/youtube_{video_meta.video_id}")
    video_output_dir.mkdir(parents=True, exist_ok=True)

    retriever = VideoIntelligenceRetriever(
        use_cache=sidebar_config['use_cache'],
        mode=sidebar_config['processing_mode'],
        output_dir=video_output_dir,
        progress_hook=None
    )
    retriever.clean_graph = sidebar_config['clean_graph']
    
    try:
        result = await retriever.process_url(video_meta.url)
        if result:
            retriever.save_all_formats(
                result, 
                output_dir=str(video_output_dir),
                include_chimera_format=True
            )
            st.session_state.processed_results[video_meta.url] = result
        return video_meta.url, "Complete"
    except Exception as e:
        logger.error(f"Error processing {video_meta.url}: {e}")
        return video_meta.url, "Error"

async def run_batch_processing(sidebar_config):
    """Runs the full batch processing job in the background."""
    st.session_state.research_in_progress = True
    results_to_process = [
        video for video in st.session_state.research_results 
        if video.url not in st.session_state.processed_results
    ]
    
    # Update the UI to show "Processing" for all pending videos
    for row in st.session_state.research_df_data:
        if row["Status"] == "Pending":
            row["Status"] = "Processing..."
    
    tasks = [process_video_for_batch(video, sidebar_config) for video in results_to_process]
    
    if not tasks:
        st.toast("All videos have already been processed.")
        st.session_state.research_in_progress = False
        return

    progress_text = f"Processing {len(tasks)} videos..."
    progress_bar = st.progress(0, text=progress_text)
    
    for i, future in enumerate(asyncio.as_completed(tasks)):
        url, status = await future
        for row in st.session_state.research_df_data:
            if row["URL"] == url:
                row["Status"] = status
        
        progress_value = (i + 1) / len(tasks)
        progress_bar.progress(progress_value, text=f"Processed {i + 1} of {len(tasks)} videos.")
        
        # We need to rerun to update the data editor with the new status
        st.rerun()

    st.session_state.research_in_progress = False
    st.rerun()

# --- UI Rendering Functions ---
async def render_single_video_tab(sidebar_config):
    """Renders the UI for the single video analysis tab."""
    st.markdown("Transform any video into structured, searchable knowledge.")
url = st.text_input("Enter Video URL", placeholder="https://www.youtube.com/watch?v=...")

    if st.button("Analyze Video", type="primary", disabled=st.session_state.get('processing', False)):
    if url:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        video_id = url.split("=")[-1] if "youtube" in url else url.split("/")[-1]
        output_dir = Path(f"output/streamlit_{timestamp}_{video_id}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
            await process_video_url(
                url, output_dir,
                mode=sidebar_config['processing_mode'],
                use_cache=sidebar_config['use_cache'],
                clean_graph=sidebar_config['clean_graph']
        )
    else:
        st.warning("Please enter a URL.")

    if st.session_state.get('video_result'):
        render_video_results(st.session_state.video_result, st.session_state.output_dir)

async def render_research_tab(sidebar_config):
    """Renders the UI for the research tab."""
    st.header("🔬 Research")
    st.markdown("Perform batch analysis by searching for videos by topic or channel.")

    search_type = st.radio("Search Type", ["Topic", "Channel URL"], horizontal=True)
    query = st.text_input("Search Query", placeholder="e.g., 'AI in healthcare' or 'https://www.youtube.com/@pbsnewshour'")

    col1, col2, col3 = st.columns(3)
    with col1:
        max_results = st.number_input("Max Videos", min_value=1, max_value=50, value=5)
    with col2:
        period = st.selectbox("Time Period", ["any", "hour", "today", "week", "month", "year"], index=0, help="Filter by upload date (topic search only).")
    with col3:
        sort_by = st.selectbox("Sort By", ["relevance", "view_count", "upload_date", "rating"], index=0, help="Sort order (channel search only).")
    
    if st.button("Search for Videos", type="primary", disabled=st.session_state.research_in_progress):
        if query:
            with st.spinner(f"Searching for {search_type}: {query}..."):
                await run_research_search(query, search_type, max_results, period, sort_by)
            st.rerun()
        else:
            st.warning("Please enter a search query.")
    
    if st.session_state.research_results or st.session_state.research_df_data:
        await render_research_results(sidebar_config)

async def render_research_results(sidebar_config):
    """Renders the research results in a dataframe and shows processing options."""
    if not st.session_state.research_df_data and st.session_state.research_results:
        st.session_state.research_df_data = [
            {
                "Title": r.title, "Channel": r.channel, "Duration (s)": r.duration,
                "Views": r.view_count, "URL": r.url, "Status": "Pending"
            } for r in st.session_state.research_results
        ]
    
    if not st.session_state.research_df_data:
        st.info("No videos found for your query.")
        return

    st.success(f"Found {len(st.session_state.research_df_data)} videos.")
    df = pd.DataFrame(st.session_state.research_df_data)
    
    st.data_editor(df, key="research_results_editor", use_container_width=True,
                   disabled=["Title", "Channel", "Duration (s)", "Views", "URL", "Status"], hide_index=True)

    if st.button("Process All Videos", type="primary", disabled=st.session_state.research_in_progress):
        await run_batch_processing(sidebar_config)

def render_video_results(result, output_dir):
    """Renders the results of a single video analysis."""
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
        subdirectories = [d for d in output_dir.iterdir() if d.is_dir()]
        if subdirectories:
            files_dir = subdirectories[0]
            for filename in os.listdir(files_dir):
                file_path = files_dir / filename
                if file_path.is_file():
                    with open(file_path, "rb") as f:
                        st.download_button(
                            label=f"Download {filename}", data=f, file_name=filename,
                            mime="application/octet-stream"
                        )
        else:
            st.warning("Could not find output directory with files.") 

async def main():
    """The main Streamlit application logic."""
    initialize_session_state()
    st.title("🚀 ClipScribe Web UI")

    # --- Sidebar Configuration ---
    st.sidebar.title("⚙️ Configuration")
    processing_mode = st.sidebar.selectbox(
        "Processing Mode", options=["audio", "video", "auto"], index=2,
        help="**Audio**: Fastest. **Video**: Slower. **Auto**: Detects best mode."
    )
    use_cache = st.sidebar.checkbox("Use Cache", value=True, help="Use cached results.")
    clean_graph = st.sidebar.checkbox("Clean Knowledge Graph", value=True, help="Refine graph with an AI pass.")
    
    sidebar_config = {
        "processing_mode": processing_mode,
        "use_cache": use_cache,
        "clean_graph": clean_graph
    }

    tab1, tab2 = st.tabs(["🔎 Single Video Analysis", "🔬 Research"])

    with tab1:
        await render_single_video_tab(sidebar_config)

    with tab2:
        await render_research_tab(sidebar_config)

if __name__ == "__main__":
    asyncio.run(main())