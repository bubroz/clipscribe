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
import json

import click
from rich.panel import Panel
from rich.table import Table
from rich.logging import RichHandler
from rich import box
from rich.console import Console

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
def transcribe(
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
    """Transcribe a video and extract intelligence."""
    asyncio.run(transcribe_async(ctx, url, output_dir, mode, use_cache, enhance_transcript, clean_graph, skip_cleaning, visualize, performance_report))

async def transcribe_async(
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
    """Async implementation of transcribe command."""
    console = Console()
    
    # Extract all the options from kwargs
    mode = mode
    use_cache = use_cache
    enhance_transcript = enhance_transcript
    extract_entities = True
    extract_topics = True
    extract_key_points = True
    extract_relationships = True
    save_all_formats = True
    api_key = None
    include_timestamps = True
    max_retries = 3
    chunk_duration = 600
    confidence_threshold = 0.8
    cost_threshold = 10.0
    model = 'gemini-2.5-flash'
    use_advanced_extraction = True
    gliner_model = 'urchade/gliner_multi-v2.1'
    rebel_model = 'Babelscape/rebel-large'
    use_llm_validation = True
    domain = None
    performance_report = performance_report
    
    # Log the operation
    logger.info(f"Transcribing video: {url}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Mode: {mode}, Model: {model}")
    
    # Validate URL
    if not url:
        console.print("[red]Error: URL is required[/red]")
        ctx.exit(1)
        
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize retriever
    try:
        retriever = VideoIntelligenceRetriever(
            use_cache=use_cache,
            use_advanced_extraction=use_advanced_extraction,
            domain=domain,
            mode=mode,
            output_dir=str(output_dir),
            enhance_transcript=enhance_transcript
        )
        
        # Set cleaning option
        if clean_graph:
            retriever.clean_graph = True
        elif skip_cleaning:
            retriever.clean_graph = False
        
        # Process video
        result = await retriever.process_url(url)
        
        # Save outputs
        if save_all_formats:
            saved_files = retriever.save_all_formats(result, str(output_dir))
            console.print(f"\n[green]✅ Saved all formats to: {saved_files['directory']}[/green]")
        else:
            # Save just the basic files
            transcript_file = output_dir / "transcript.json"
            with open(transcript_file, 'w', encoding='utf-8') as f:
                json.dump(result.model_dump(), f, ensure_ascii=False, indent=2, default=str)
            console.print(f"\n[green]✅ Saved transcript to: {transcript_file}[/green]")
            
        # Display summary
        _display_results(console, result)
        
        # Display cost
        console.print(f"\n[cyan]Total cost: ${result.processing_cost:.4f}[/cyan]")
        
        # Generate performance report if requested
        if performance_report:
            report_path = output_dir / "performance_report.json"
            performance_data = {
                "url": url,
                "mode": mode,
                "model": model,
                "processing_time": result.processing_time,
                "processing_cost": result.processing_cost,
                "transcript_length": len(result.transcript.full_text) if result.transcript else 0,
                "entity_count": len(result.entities),
                "relationship_count": len(result.relationships) if hasattr(result, 'relationships') else 0,
                "key_point_count": len(result.key_points) if result.key_points else 0
            }
            with open(report_path, 'w') as f:
                json.dump(performance_data, f, indent=2)
            console.print(f"[dim]Performance report saved to: {report_path}[/dim]")
            
    except Exception as e:
        logger.exception("Transcription failed")
        console.print(f"[red]❌ Error: {e}[/red]")
        ctx.exit(1)


def _display_results(console: Console, result):
    """Display transcription results in a formatted table."""
    from rich.table import Table
    from rich import box
    
    results_table = Table(title="Transcription Results", box=box.ROUNDED)
    results_table.add_column("Property", style="cyan")
    results_table.add_column("Value", style="white")
    
    results_table.add_row("Video Title", result.metadata.title)
    
    minutes = int(result.metadata.duration // 60)
    seconds = int(result.metadata.duration % 60)
    results_table.add_row("Duration", f"{minutes}:{seconds:02d}")
    
    platform = result.metadata.url.split('/')[2].replace('www.', '').capitalize()
    results_table.add_row("Platform", platform)
    
    if result.transcript:
        results_table.add_row("Transcript Length", f"{len(result.transcript.full_text)} chars")
        
    results_table.add_row("Entities", str(len(result.entities)))
    
    if hasattr(result, 'relationships') and result.relationships:
        results_table.add_row("Relationships", str(len(result.relationships)))
        
    if result.key_points:
        results_table.add_row("Key Points", str(len(result.key_points)))
        
    if result.topics:
        results_table.add_row("Topics", str(len(result.topics)))
        
    console.print("\n")
    console.print(results_table)


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
def research(ctx: click.Context, query: str, max_results: int, period: Optional[str], sort_by: str, output_dir: Path, **kwargs):
    """Research a topic by analyzing multiple videos."""
    asyncio.run(research_async(ctx, query, max_results, period, sort_by, output_dir, **kwargs))

async def research_async(ctx: click.Context, query: str, max_results: int, period: Optional[str], sort_by: str, output_dir: Path, **kwargs):
    """Async implementation of research command."""
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
def process_collection(
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
    asyncio.run(process_collection_async(
        ctx,
        urls,
        collection_title,
        collection_type,
        auto_detect_series,
        user_confirmed_series,
        output_dir,
        **kwargs
    ))

async def process_collection_async(
    ctx: click.Context,
    urls: tuple,
    collection_title: Optional[str],
    collection_type: str,
    auto_detect_series: bool,
    user_confirmed_series: bool,
    output_dir: Path,
    **kwargs
) -> None:
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
                # Debug logging to track relationships
                logger.info(f"Video {i} processed: {len(getattr(video_result, 'relationships', []))} relationships found")
                
                # Save individual video outputs
                retriever.save_all_formats(video_result, str(video_output_dir))
                video_intelligences.append(video_result)
                console.print(f"✅ Video {i} processed successfully with {len(getattr(video_result, 'relationships', []))} relationships")
            else:
                console.print(f"❌ Failed to process video {i}")
        except Exception as e:
            console.print(f"❌ Error processing video {i}: {e}")
            logger.exception(f"Error processing video {i}")
    
    if not video_intelligences:
        console.print("[red]No videos were successfully processed. Exiting.[/red]")
        return
    
    # Debug: Log relationships before passing to multi-video processor
    for idx, video in enumerate(video_intelligences):
        rel_count = len(getattr(video, 'relationships', []))
        logger.info(f"Before multi-video processing - Video {idx+1}: {rel_count} relationships")
    
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
        
        # The retriever instance used to process the last video will suffice,
        # as save_collection_outputs doesn't depend on single-video state.
        retriever.save_collection_outputs(
            collection=multi_video_result,
            output_dir=str(output_dir)
        )
        
        collection_output_dir = output_dir / multi_video_result.collection_id

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
def process_series(
    ctx: click.Context,
    urls: tuple,
    output_dir: Path,
    series_title: Optional[str],
    **kwargs
) -> None:
    """Process videos as a series with automatic detection and narrative flow analysis."""
    console.print(f"📺 Processing video series: {len(urls)} videos")
    
    # Delegate to process_collection_async with series-specific settings
    asyncio.run(process_collection_async(
        ctx,
        urls=urls,
        collection_title=series_title,
        collection_type='series',
        auto_detect_series=True,
        user_confirmed_series=False,
        output_dir=output_dir,
        **kwargs
    ))


def run_cli():
    """Run the CLI application."""
    # Click's native async support handles this automatically.
    # The previous manual loop management was causing RuntimeWarnings.
    setup_logging()  # Initialize logging
    cli()


if __name__ == "__main__":
    run_cli() 