"""ClipScribe CLI - AI-powered video transcription and analysis tool.

This module provides the command-line interface for ClipScribe, supporting
transcription of videos from 1800+ platforms using Gemini 2.5 Flash.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional, List
import logging
from urllib.parse import urlparse
import os
import subprocess
import webbrowser
import platform

import click
from rich.panel import Panel
from rich.table import Table
from rich.logging import RichHandler
from rich import box

from ..retrievers import VideoIntelligenceRetriever, UniversalVideoClient
from ..config.settings import Settings
from ..utils.logging import setup_logging
from ..utils.progress import progress_tracker, console
from ..utils.performance import PerformanceMonitor
from ..version import __version__
from ..utils.batch_progress import BatchProgress
from ..extractors.series_detector import SeriesDetector
from ..extractors.multi_video_processor import MultiVideoProcessor
from ..models import VideoCollectionType

# Configure logging with Rich using the shared console
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, show_path=False)]
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version=__version__, prog_name="ClipScribe")
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug logging"
)
@click.pass_context
def cli(ctx: click.Context, debug: bool) -> None:
    """ClipScribe - AI-powered video transcription and analysis.

    Transcribe videos from YouTube, Vimeo, and 1800+ other platforms
    using Google's Gemini 2.5 Flash for fast, accurate results.
    """
    ctx.ensure_object(dict)

    # Set up logging
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")

    # Load settings
    ctx.obj["settings"] = Settings()

    console.print(f"[bold blue]ClipScribe v{__version__}[/bold blue]")
    console.print("AI-powered video transcription with Gemini 2.5 Flash\n")


@cli.command()
@click.argument("url")
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(exists=False, file_okay=False, dir_okay=True, path_type=Path),
    default=Path("output"),
    help="Output directory for transcripts"
)
@click.option(
    '--mode', '-m',
    type=click.Choice(['audio', 'video', 'auto'], case_sensitive=False),
    default='audio',
    help="Processing mode."
)
@click.option(
    '--use-cache/--no-cache',
    default=True,
    help='Use cached results if available.'
)
@click.option(
    '--enhance-transcript',
    is_flag=True,
    help='Add speaker diarization and timestamps to transcript (adds cost).'
)
@click.option(
    '--clean-graph',
    is_flag=True,
    help='Clean knowledge graph with AI to remove noise and fix errors (adds small cost).'
)
@click.option(
    '--skip-cleaning',
    is_flag=True,
    help='Skip graph cleaning entirely to see raw extraction results.'
)
@click.option(
    '--visualize',
    is_flag=True,
    help='Generate interactive visualization after extraction.'
)
@click.option(
    '--performance-report',
    is_flag=True,
    help='Generate a detailed performance report for the run.'
)
@click.pass_context
async def transcribe(
    ctx: click.Context,
    url: str,
    output_dir: Path,
    mode: str,
    use_cache: bool,
    enhance_transcript: bool,
    clean_graph: bool,
    skip_cleaning: bool,
    visualize: bool,
    performance_report: bool
) -> None:
    """Transcribe a video from URL using Gemini 2.5 Flash."""
    settings = ctx.obj["settings"]
    output_dir.mkdir(parents=True, exist_ok=True)
    perf_monitor = PerformanceMonitor(output_dir) if performance_report else None

    try:
        with progress_tracker.video_processing(url) as progress_state:
            progress_tracker.update_phase(progress_state, "init", "Initializing video retriever...")
            retriever = VideoIntelligenceRetriever(
                use_cache=use_cache,
                mode=mode,
                output_dir=output_dir,
                enhance_transcript=enhance_transcript,
                progress_tracker=progress_tracker,
                performance_monitor=perf_monitor
            )
            if skip_cleaning:
                retriever.clean_graph = False
            elif clean_graph:
                retriever.clean_graph = True

            progress_tracker.update_phase(progress_state, "process", "Processing video...")
            video_result = await retriever.process_url(url, progress_state=progress_state)

            if not video_result:
                progress_tracker.log_error("Failed to process video")
                sys.exit(1)

            progress_tracker.update_phase(progress_state, "save", "Saving output files...")
            saved_files = retriever.save_all_formats(
                video_result,
                output_dir=str(output_dir),
                include_chimera_format=True
            )
            progress_tracker.update_phase(progress_state, "complete", "Processing complete!")

        if hasattr(video_result, 'entities') and hasattr(video_result, 'relationships'):
            progress_tracker.show_extraction_stats(
                video_result.entities,
                video_result.relationships
            )

        results_table = Table(title="Transcription Results", box=box.ROUNDED)
        results_table.add_column("Property", style="cyan")
        results_table.add_column("Value", style="white")
        results_table.add_row("Video Title", video_result.metadata.title)
        minutes = int(video_result.metadata.duration // 60)
        seconds = int(video_result.metadata.duration % 60)
        results_table.add_row("Duration", f"{minutes}:{seconds:02d}")
        results_table.add_row("Platform", video_result.metadata.url.split('/')[2].replace('www.', '').capitalize())
        results_table.add_row("Processing Mode", mode.upper())
        results_table.add_row("Cost", f"${video_result.processing_cost:.4f}")
        results_table.add_row("Output Directory", str(output_dir))
        console.print("\n")
        console.print(results_table)

        if visualize and 'knowledge_graph' in saved_files:
            pass # Placeholder for viz logic

        progress_tracker.log_success("Transcription complete!")

    except KeyboardInterrupt:
        progress_tracker.log_warning("Transcription cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.exception("Transcription failed")
        progress_tracker.log_error(f"Error: {str(e)}")
        sys.exit(1)
    finally:
        if perf_monitor:
            perf_monitor.save_report()
            progress_tracker.log_info(f"Performance report saved to {perf_monitor.output_dir}")


@cli.command()
@click.argument("query")
@click.option("--max-results", "-n", type=int, default=2)
@click.option(
    "--period",
    type=click.Choice(['hour', 'day', 'week', 'month', 'year'], case_sensitive=False),
    default=None,
    help="Filter search results by time period."
)
@click.option(
    "--sort-by",
    type=click.Choice(['relevance', 'newest', 'oldest', 'popular'], case_sensitive=False),
    default='relevance',
    help="Sort order for channel or topic search."
)
@click.option("--output-dir", "-o", type=click.Path(path_type=Path), default=Path("output/research"))
@click.option('--mode', '-m', type=click.Choice(['audio', 'video', 'auto']), default='audio')
@click.option('--use-cache/--no-cache', default=True)
@click.option('--enhance-transcript', is_flag=True)
@click.option('--clean-graph', is_flag=True)
@click.option('--skip-cleaning', is_flag=True)
@click.option('--performance-report', is_flag=True)
@click.pass_context
async def research(ctx: click.Context, query: str, max_results: int, period: Optional[str], sort_by: str, output_dir: Path, **kwargs):
    """Research a topic by analyzing multiple videos."""
    # Create a semaphore to limit concurrency
    concurrency = 3
    semaphore = asyncio.Semaphore(concurrency)

    console.print(f"🔬 Researching: '{query}' (max {max_results} videos, {concurrency} at a time)...")
    
    # 1. Search
    video_client = UniversalVideoClient()
    search_results = []

    # Check if the query is a YouTube channel URL
    is_channel_search = "youtube.com/" in query and ("@" in query or "/channel/" in query or "/c/" in query)

    if is_channel_search:
        console.print(f"Searching YouTube channel: {query}")
        search_results = await video_client.search_channel(query, max_results=max_results, sort_by=sort_by)
    else:
        console.print(f"Searching for topic: {query}")
        search_results = await video_client.search_videos(query, max_results=max_results, period=period)
    
    if not search_results:
        console.print(f"[red]No videos found for '{query}'.[/red]")
        return
        
    console.print(f"[green]✓ Found {len(search_results)} videos. Starting batch processing...[/green]")

    async def process_video(video_meta, batch_progress: BatchProgress):
        """Helper to process a single video with progress and semaphore."""
        async with semaphore:
            task_id = batch_progress.add_video_task(video_meta.url)
            video_output_dir = output_dir / f"youtube_{video_meta.video_id}"
            
            # Create a progress hook for the retriever to call
            def progress_hook(update):
                description = update.get("description", "Processing...")
                progress = update.get("progress", 0) # Progress is 0-100
                batch_progress.update_video_progress(video_meta.url, advance=(progress/100.0), description=description)

            retriever_kwargs = {
                "use_cache": kwargs.get('use_cache', True),
                "mode": kwargs.get('mode', 'audio'),
                "output_dir": video_output_dir,
                "enhance_transcript": kwargs.get('enhance_transcript', False),
                "performance_monitor": PerformanceMonitor(video_output_dir) if kwargs.get('performance_report') else None,
                "progress_hook": progress_hook # Pass the hook
            }

            try:
                retriever = VideoIntelligenceRetriever(**retriever_kwargs)
                if kwargs.get('skip_cleaning'): retriever.clean_graph = False
                elif kwargs.get('clean_graph'): retriever.clean_graph = True

                video_result = await retriever.process_url(video_meta.url)
                if video_result:
                    retriever.save_all_formats(video_result, str(video_output_dir), True)
                
                batch_progress.complete_video_task(video_meta.url)
            except Exception as e:
                batch_progress.fail_video_task(video_meta.url, f"Error: {e}")
            finally:
                if retriever_kwargs["performance_monitor"]:
                    retriever_kwargs["performance_monitor"].save_report()

    async with BatchProgress() as batch_progress:
        batch_progress.add_overall_task(total=len(search_results))
        tasks = [process_video(video, batch_progress) for video in search_results]
        await asyncio.gather(*tasks)

    console.print(f"\n🎉 Research complete! Outputs are in {output_dir}")


@cli.command()
@click.argument("urls", nargs=-1, required=True)
@click.option(
    "--collection-title",
    "-t",
    help="Title for the video collection"
)
@click.option(
    "--collection-type",
    type=click.Choice(['series', 'topic_research', 'channel_analysis', 'cross_source_topic', 'custom_collection']),
    default='custom_collection',
    help="Type of video collection for processing strategy"
)
@click.option(
    "--auto-detect-series",
    is_flag=True,
    help="Automatically detect if videos form a series"
)
@click.option(
    "--user-confirmed-series",
    is_flag=True,
    help="User confirms this is a series (skips detection)"
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path),
    default=Path("output/collections"),
    help="Output directory for collection analysis"
)
@click.option('--mode', '-m', type=click.Choice(['audio', 'video', 'auto']), default='audio')
@click.option('--use-cache/--no-cache', default=True)
@click.option('--enhance-transcript', is_flag=True)
@click.option('--clean-graph', is_flag=True)
@click.option('--performance-report', is_flag=True)
@click.pass_context
async def process_collection(
    ctx: click.Context,
    urls: tuple,
    collection_title: Optional[str],
    collection_type: str,
    auto_detect_series: bool,
    user_confirmed_series: bool,
    output_dir: Path,
    **kwargs
) -> None:
    """Process multiple videos as a unified collection with cross-video intelligence."""
    console.print(f"🎬 Processing video collection: {len(urls)} videos")
    
    # Convert collection type string to enum
    collection_type_enum = VideoCollectionType(collection_type)
    
    # Step 1: Process individual videos
    console.print("\n📹 Step 1: Processing individual videos...")
    video_intelligences = []
    
    for i, url in enumerate(urls, 1):
        console.print(f"Processing video {i}/{len(urls)}: {url}")
        
        # Create individual output directory
        video_output_dir = output_dir / f"individual_videos" / f"video_{i}"
        video_output_dir.mkdir(parents=True, exist_ok=True)
        
        retriever = VideoIntelligenceRetriever(
            use_cache=kwargs.get('use_cache', True),
            mode=kwargs.get('mode', 'audio'),
            output_dir=video_output_dir,
            enhance_transcript=kwargs.get('enhance_transcript', False),
            performance_monitor=PerformanceMonitor(video_output_dir) if kwargs.get('performance_report') else None
        )
        
        if kwargs.get('clean_graph'):
            retriever.clean_graph = True
        
        try:
            video_result = await retriever.process_url(url)
            if video_result:
                # Save individual video outputs
                retriever.save_all_formats(video_result, str(video_output_dir))
                video_intelligences.append(video_result)
                console.print(f"✅ Video {i} processed successfully")
            else:
                console.print(f"❌ Failed to process video {i}")
        except Exception as e:
            console.print(f"❌ Error processing video {i}: {e}")
    
    if not video_intelligences:
        console.print("[red]No videos were successfully processed. Exiting.[/red]")
        return
    
    # Step 2: Multi-video intelligence processing
    console.print(f"\n🧠 Step 2: Multi-video intelligence analysis...")
    
    try:
        multi_processor = MultiVideoProcessor(use_ai_validation=True)
        
        # Auto-detect series if requested
        if auto_detect_series and collection_type_enum != VideoCollectionType.SERIES:
            console.print("🔍 Detecting series patterns...")
            series_detector = SeriesDetector()
            detection_result = await series_detector.detect_series(video_intelligences)
            
            if detection_result.is_series:
                console.print(f"✅ Series detected with {detection_result.confidence:.2f} confidence")
                if detection_result.user_confirmation_needed:
                    console.print(f"📋 Detection method: {detection_result.detection_method}")
                    console.print(f"🎯 Suggested groupings: {len(detection_result.suggested_grouping)} groups")
                collection_type_enum = VideoCollectionType.SERIES
                user_confirmed_series = True
            else:
                console.print("ℹ️ No series pattern detected")
        
        # Process collection
        multi_video_result = await multi_processor.process_video_collection(
            videos=video_intelligences,
            collection_type=collection_type_enum,
            collection_title=collection_title,
            user_confirmed_series=user_confirmed_series
        )
        
        # Step 3: Save unified outputs
        console.print("\n💾 Step 3: Saving unified collection outputs...")
        
        collection_output_dir = output_dir / multi_video_result.collection_id
        collection_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save main collection intelligence
        import json
        with open(collection_output_dir / "multi_video_intelligence.json", "w", encoding="utf-8") as f:
            json.dump(multi_video_result.dict(), f, indent=2, ensure_ascii=False, default=str)
        
        # Save unified knowledge graph
        if multi_video_result.unified_knowledge_graph:
            with open(collection_output_dir / "unified_knowledge_graph.json", "w", encoding="utf-8") as f:
                json.dump(multi_video_result.unified_knowledge_graph, f, indent=2, ensure_ascii=False)
        
        # Save collection summary as markdown
        with open(collection_output_dir / "collection_summary.md", "w", encoding="utf-8") as f:
            f.write(f"# {multi_video_result.collection_title}\n\n")
            f.write(f"**Collection Type:** {multi_video_result.collection_type.value}\n")
            f.write(f"**Videos:** {len(multi_video_result.video_ids)}\n")
            f.write(f"**Created:** {multi_video_result.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## Summary\n\n{multi_video_result.collection_summary}\n\n")
            
            if multi_video_result.key_insights:
                f.write("## Key Insights\n\n")
                for insight in multi_video_result.key_insights:
                    f.write(f"- {insight}\n")
                f.write("\n")
            
            f.write(f"## Statistics\n\n")
            f.write(f"- **Unified Entities:** {len(multi_video_result.unified_entities)}\n")
            f.write(f"- **Cross-Video Relationships:** {len(multi_video_result.cross_video_relationships)}\n")
            f.write(f"- **Processing Cost:** ${multi_video_result.total_processing_cost:.4f}\n")
            f.write(f"- **Processing Time:** {multi_video_result.total_processing_time:.1f} seconds\n")
        
        # Display results
        results_table = Table(title="Multi-Video Collection Results", box=box.ROUNDED)
        results_table.add_column("Property", style="cyan")
        results_table.add_column("Value", style="white")
        results_table.add_row("Collection Title", multi_video_result.collection_title)
        results_table.add_row("Collection Type", multi_video_result.collection_type.value)
        results_table.add_row("Videos Processed", str(len(multi_video_result.video_ids)))
        results_table.add_row("Unified Entities", str(len(multi_video_result.unified_entities)))
        results_table.add_row("Cross-Video Relationships", str(len(multi_video_result.cross_video_relationships)))
        results_table.add_row("Key Insights", str(len(multi_video_result.key_insights)))
        results_table.add_row("Total Cost", f"${multi_video_result.total_processing_cost:.4f}")
        results_table.add_row("Entity Resolution Quality", f"{multi_video_result.entity_resolution_quality:.2f}")
        results_table.add_row("Narrative Coherence", f"{multi_video_result.narrative_coherence:.2f}")
        results_table.add_row("Output Directory", str(collection_output_dir))
        
        console.print("\n")
        console.print(results_table)
        
        console.print(f"\n🎉 Multi-video collection processing complete!")
        console.print(f"📁 Outputs saved to: {collection_output_dir}")
        
    except Exception as e:
        logger.exception("Multi-video processing failed")
        console.print(f"[red]❌ Multi-video processing failed: {e}[/red]")


@cli.command()
@click.argument("urls", nargs=-1, required=True)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path),
    default=Path("output/series"),
    help="Output directory for series analysis"
)
@click.option(
    "--series-title",
    "-t",
    help="Title for the video series (auto-detected if not provided)"
)
@click.option('--mode', '-m', type=click.Choice(['audio', 'video', 'auto']), default='audio')
@click.option('--use-cache/--no-cache', default=True)
@click.option('--enhance-transcript', is_flag=True)
@click.option('--clean-graph', is_flag=True)
@click.option('--performance-report', is_flag=True)
@click.pass_context
async def process_series(
    ctx: click.Context,
    urls: tuple,
    output_dir: Path,
    series_title: Optional[str],
    **kwargs
) -> None:
    """Process videos as a series with automatic detection and narrative flow analysis."""
    console.print(f"📺 Processing video series: {len(urls)} videos")
    
    # Delegate to process_collection with series-specific settings
    await process_collection.callback(
        ctx,
        urls=urls,
        collection_title=series_title,
        collection_type='series',
        auto_detect_series=True,
        user_confirmed_series=False,
        output_dir=output_dir,
        **kwargs
    )


def run_cli():
    """Run the CLI application."""
    # Handle async commands properly
    if len(sys.argv) > 1 and sys.argv[1] in ["transcribe", "research", "process-collection", "process-series"]:
        # These are async commands
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Create a sync wrapper for Click
            def sync_wrapper():
                # Call CLI directly, not as a coroutine
                cli.main(standalone_mode=False)
            
            sync_wrapper()
        finally:
            loop.close()
    else:
        # Regular sync commands
        cli()


if __name__ == "__main__":
    run_cli() 