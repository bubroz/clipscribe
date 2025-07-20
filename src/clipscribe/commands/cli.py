"""ClipScribe CLI - AI-powered video transcription and analysis tool.

This module provides the command-line interface for ClipScribe, supporting
transcription of videos from 1800+ platforms using Gemini 2.5 Flash.
"""

import sys
import importlib

# Fast path for version check - bypass Click entirely for performance
def _check_fast_commands():
    """Handle simple commands without loading heavy frameworks."""
    if len(sys.argv) >= 2 and sys.argv[1] in ['--version', '-V']:
        from ..version import __version__
        print(f"ClipScribe, version {__version__}")
        sys.exit(0)
    elif len(sys.argv) >= 2 and sys.argv[1] in ['--help', '-h']:
        print("""ClipScribe - AI-powered video transcription and analysis.

Usage: clipscribe [OPTIONS] COMMAND [ARGS]...

Commands:
  transcribe          Transcribe a video and extract intelligence
  research           Research a topic by analyzing multiple videos  
  process-collection Process multiple videos as a unified collection
  process-series     Process videos as a series

Options:
  --version          Show version
  --help             Show this help message
  --debug            Enable debug logging

For detailed help: clipscribe COMMAND --help""")
        sys.exit(0)

# Check for fast commands first
_check_fast_commands()

# Only import heavy frameworks if we need them
import asyncio
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

from ..version import __version__

# Lazy imports - only load when needed
def _get_rich_imports():
    """Lazy import Rich components."""
    from rich.panel import Panel
    from rich.table import Table
    from rich.logging import RichHandler
    from rich import box
    from rich.console import Console
    return Panel, Table, RichHandler, box, Console

def _get_core_imports():
    """Lazy import core processing components."""
    from ..retrievers import VideoIntelligenceRetriever, UniversalVideoClient
    from ..config.settings import Settings
    from ..utils.logging import setup_logging
    from ..utils.progress import progress_tracker
    from ..utils.performance import PerformanceMonitor
    from ..utils.batch_progress import BatchProgress
    from ..extractors.series_detector import SeriesDetector
    from ..extractors.multi_video_processor import MultiVideoProcessor
    from ..models import VideoCollectionType
    return {
        'VideoIntelligenceRetriever': VideoIntelligenceRetriever,
        'UniversalVideoClient': UniversalVideoClient,
        'Settings': Settings,
        'setup_logging': setup_logging,
        'progress_tracker': progress_tracker,
        'PerformanceMonitor': PerformanceMonitor,
        'BatchProgress': BatchProgress,
        'SeriesDetector': SeriesDetector,
        'MultiVideoProcessor': MultiVideoProcessor,
        'VideoCollectionType': VideoCollectionType
    }

# Initialize minimal console (no heavy imports)
_console = None

def _get_console():
    """Get console instance with lazy initialization."""
    global _console
    if _console is None:
        Panel, Table, RichHandler, box, Console = _get_rich_imports()
        _console = Console()
    return _console

def _setup_rich_logging():
    """Setup Rich logging only when needed."""
    Panel, Table, RichHandler, box, Console = _get_rich_imports()
    console = _get_console()
    
    # Configure logging with Rich
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, show_path=False)]
    )
    return logging.getLogger(__name__)

# Add import for real-time cost tracking and progress
cli_perf = importlib.import_module('src.clipscribe.utils.cli_performance')
RealTimeCostTracker = cli_perf.RealTimeCostTracker
AsyncProgressIndicator = cli_perf.AsyncProgressIndicator

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

    # Only setup logging if debug or running actual commands
    if debug or ctx.invoked_subcommand is not None:
        logger = _setup_rich_logging()
        if debug:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.debug("Debug mode enabled")
        
        # Load settings only when needed
        imports = _get_core_imports()
        ctx.obj["settings"] = imports['Settings']()
        
        console = _get_console()
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
    # Lazy import all processing components
    imports = _get_core_imports()
    logger = _setup_rich_logging()
    console = _get_console()
    
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
    
    # Initialize real-time cost tracker and progress indicator
    cost_tracker = RealTimeCostTracker()
    progress_indicator = AsyncProgressIndicator(cost_tracker)

    # Initialize retriever
    try:
        retriever = imports['VideoIntelligenceRetriever'](
            use_cache=use_cache,
            use_advanced_extraction=use_advanced_extraction,
            domain=domain,
            mode=mode,
            output_dir=str(output_dir),
            enhance_transcript=enhance_transcript,
            cost_tracker=cost_tracker  # Pass cost tracker to retriever
        )
        
        # Set cleaning option
        if clean_graph:
            retriever.clean_graph = True
        elif skip_cleaning:
            retriever.clean_graph = False
        
        # Use progress indicator context for live updates
        async with progress_indicator.video_processing_progress(url) as state:
            # Process video and update cost at each phase
            result = await retriever.process_url(url, progress_state=state)
            
            # Check if result is None
            if result is None:
                console.print("[red]❌ Video processing returned no result[/red]")
                console.print("[yellow]Check logs for details about what went wrong[/yellow]")
                ctx.exit(1)
            
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
            
            # Show final cost summary (handled by progress indicator)
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


def _display_results(console, result):
    """Display transcription results in a formatted table."""
    # Lazy import Rich components
    Panel, Table, RichHandler, box, Console = _get_rich_imports()
    
    results_table = Table(title="Transcription Results", box=box.ROUNDED)
    results_table.add_column("Property", style="cyan")
    results_table.add_column("Value", style="white")
    
    if result.metadata and result.metadata.title:
        results_table.add_row("Video Title", result.metadata.title)
    else:
        results_table.add_row("Video Title", "Unknown")
    
    if result.metadata and result.metadata.duration:
        minutes = int(result.metadata.duration // 60)
        seconds = int(result.metadata.duration % 60)
        results_table.add_row("Duration", f"{minutes}:{seconds:02d}")
    else:
        results_table.add_row("Duration", "Unknown")
    
    if result.metadata and result.metadata.url:
        platform = result.metadata.url.split('/')[2].replace('www.', '').capitalize()
        results_table.add_row("Platform", platform)
    else:
        results_table.add_row("Platform", "Unknown")
    
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
    # Lazy import all processing components
    imports = _get_core_imports()
    logger = _setup_rich_logging()
    console = _get_console()
    
    # Create a semaphore to limit concurrency
    concurrency = 3
    semaphore = asyncio.Semaphore(concurrency)

    console.print(f"🔬 Researching: '{query}' (max {max_results} videos, {concurrency} at a time)...")
    
    # 1. Search
    video_client = imports['UniversalVideoClient']()
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

    async def process_video(video_meta, batch_progress):
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
                "performance_monitor": imports['PerformanceMonitor'](video_output_dir) if kwargs.get('performance_report') else None,
                "progress_hook": progress_hook # Pass the hook
            }

            try:
                retriever = imports['VideoIntelligenceRetriever'](**retriever_kwargs)
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

    async with imports['BatchProgress']() as batch_progress:
        batch_progress.add_overall_task(total=len(search_results))
        tasks = [process_video(video, batch_progress) for video in search_results]
        await asyncio.gather(*tasks)

    console.print(f"\n🎉 Research complete! Outputs are in {output_dir}")


@cli.command()
@click.argument("collection_name")
@click.argument("urls", nargs=-1, required=True)
@click.option(
    "--collection-title",
    "-t",
    help="Title for the video collection (defaults to collection_name)"
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
@click.option(
    "--limit",
    "-l",
    type=int,
    help="Limit the number of videos to process from playlists"
)
@click.option('--mode', '-m', type=click.Choice(['audio', 'video', 'auto']), default='audio')
@click.option('--use-cache/--no-cache', default=True)
@click.option('--enhance-transcript', is_flag=True)
@click.option('--clean-graph', is_flag=True)
@click.option('--performance-report', is_flag=True)
@click.option('--skip-confirmation', is_flag=True, help="Skip playlist preview and confirmation")
@click.pass_context
def process_collection(
    ctx: click.Context,
    collection_name: str,
    urls: tuple,
    collection_title: Optional[str],
    collection_type: str,
    auto_detect_series: bool,
    user_confirmed_series: bool,
    output_dir: Path,
    limit: Optional[int],
    skip_confirmation: bool,
    **kwargs
) -> None:
    """Process multiple videos as a unified collection with cross-video intelligence.
    
    COLLECTION_NAME: Name for the collection (used in output directory)
    URLS: Video URLs or playlist URLs to process
    """
    asyncio.run(process_collection_async(
        ctx,
        collection_name,
        urls,
        collection_title or collection_name,
        collection_type,
        auto_detect_series,
        user_confirmed_series,
        output_dir,
        limit,
        skip_confirmation,
        **kwargs
    ))

async def process_collection_async(
    ctx: click.Context,
    collection_name: str,
    urls: tuple,
    collection_title: str,
    collection_type: str,
    auto_detect_series: bool,
    user_confirmed_series: bool,
    output_dir: Path,
    limit: Optional[int],
    skip_confirmation: bool,
    **kwargs
) -> None:
    # Lazy import all processing components
    imports = _get_core_imports()
    Panel, Table, RichHandler, box, Console = _get_rich_imports()
    logger = _setup_rich_logging()
    console = _get_console()
    
    video_client = imports['UniversalVideoClient']()
    
    # Step 0: Handle playlist URLs and show preview
    final_urls = []
    total_estimated_cost = 0.0
    
    for url in urls:
        if video_client.is_playlist_url(url):
            if not skip_confirmation:
                console.print(f"🎵 [yellow]Playlist detected:[/yellow] {url}")
                console.print("📋 Extracting playlist preview...")
                
                try:
                    preview_videos, total_count = await video_client.extract_playlist_preview(url, max_preview=20)
                    
                    # Show playlist preview
                    console.print(f"\n📊 [bold]Playlist Preview[/bold] ({len(preview_videos)} of {total_count} videos)")
                    
                    preview_table = Table(box=box.SIMPLE)
                    preview_table.add_column("#", style="dim", width=3)
                    preview_table.add_column("Title", style="white", min_width=40)
                    preview_table.add_column("Channel", style="cyan", width=20)
                    preview_table.add_column("Duration", style="green", width=8)
                    
                    total_duration = 0
                    for i, video in enumerate(preview_videos[:15], 1):  # Show first 15
                        if video.duration and isinstance(video.duration, (int, float)):
                            duration_min = int(video.duration // 60)
                            duration_sec = int(video.duration % 60)
                            duration_str = f"{duration_min}:{duration_sec:02d}"
                            total_duration += video.duration
                        else:
                            duration_str = "?"
                        
                        preview_table.add_row(
                            str(i),
                            video.title[:40] + "..." if len(video.title) > 40 else video.title,
                            video.channel[:18] + "..." if len(video.channel) > 18 else video.channel,
                            duration_str
                        )
                    
                    if len(preview_videos) > 15:
                        preview_table.add_row("...", f"+ {len(preview_videos) - 15} more videos", "", "")
                    
                    console.print(preview_table)
                    
                    # Estimate cost
                    estimated_cost_per_minute = 0.0025  # Enhanced temporal intelligence cost
                    total_minutes = total_duration / 60 if total_duration > 0 else 0
                    playlist_estimated_cost = total_minutes * estimated_cost_per_minute
                    total_estimated_cost += playlist_estimated_cost
                    
                    console.print(f"\n💰 [bold]Cost Estimate for Playlist:[/bold]")
                    console.print(f"   📊 Total videos: [yellow]{total_count}[/yellow]")
                    console.print(f"   ⏱️  Total duration: [cyan]{total_minutes:.1f} minutes[/cyan]")
                    console.print(f"   💵 Estimated cost: [green]${playlist_estimated_cost:.2f}[/green]")
                    
                    if total_count > 50:
                        console.print(f"\n[yellow]⚠️  Large playlist detected ({total_count} videos)[/yellow]")
                        console.print("Consider processing smaller batches for better cost control.")
                    
                    # User confirmation
                    if not click.confirm(f"\nProcess all {total_count} videos from this playlist?"):
                        console.print("❌ Playlist processing cancelled.")
                        ctx.exit(0)
                    
                    # Extract all URLs (with limit if specified)
                    console.print("🔄 Extracting video URLs from playlist...")
                    playlist_urls = await video_client.extract_all_playlist_urls(url)
                    
                    # Apply limit if specified
                    if limit and len(playlist_urls) > limit:
                        playlist_urls = playlist_urls[:limit]
                        console.print(f"✅ Extracted {len(playlist_urls)} video URLs (limited from {total_count})")
                    else:
                        console.print(f"✅ Extracted {len(playlist_urls)} video URLs")
                    
                    final_urls.extend(playlist_urls)
                    
                except Exception as e:
                    console.print(f"[red]❌ Failed to extract playlist: {e}[/red]")
                    console.print("Try using individual video URLs instead.")
                    ctx.exit(1)
            else:
                # Skip confirmation, extract all URLs
                try:
                    playlist_urls = await video_client.extract_all_playlist_urls(url)
                    
                    # Apply limit if specified
                    if limit and len(playlist_urls) > limit:
                        playlist_urls = playlist_urls[:limit]
                        console.print(f"📋 Processing first {limit} videos from playlist")
                    
                    final_urls.extend(playlist_urls)
                except Exception as e:
                    console.print(f"[red]❌ Failed to extract playlist: {e}[/red]")
                    ctx.exit(1)
        else:
            # Regular video URL
            final_urls.append(url)
    
    # Final confirmation for large collections
    if len(final_urls) > 10 and not skip_confirmation:
        console.print(f"\n🎬 [bold]Final Collection Summary:[/bold]")
        console.print(f"   📊 Total videos to process: [yellow]{len(final_urls)}[/yellow]")
        if total_estimated_cost > 0:
            console.print(f"   💵 Estimated total cost: [green]${total_estimated_cost:.2f}[/green]")
        
        if not click.confirm(f"\nProceed with processing {len(final_urls)} videos?"):
            console.print("❌ Collection processing cancelled.")
            ctx.exit(0)
    
    console.print(f"🎬 Processing video collection: {len(final_urls)} videos")
    
    # Convert collection type string to enum
    collection_type_enum = imports['VideoCollectionType'](collection_type)
    
    # Step 1: Process individual videos
    console.print("\n📹 Step 1: Processing individual videos...")
    video_intelligences = []
    
    for i, url in enumerate(final_urls, 1):
        console.print(f"Processing video {i}/{len(final_urls)}: {url}")
        
        # Create individual output directory
        video_output_dir = output_dir / f"individual_videos" / f"video_{i}"
        video_output_dir.mkdir(parents=True, exist_ok=True)
        
        retriever = imports['VideoIntelligenceRetriever'](
            use_cache=kwargs.get('use_cache', True),
            mode=kwargs.get('mode', 'audio'),
            output_dir=video_output_dir,
            enhance_transcript=kwargs.get('enhance_transcript', False),
            performance_monitor=imports['PerformanceMonitor'](video_output_dir) if kwargs.get('performance_report') else None
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
        # PERFORMANCE FIX: Disable AI validation for fast processing (was causing 18-minute delays)
        multi_processor = imports['MultiVideoProcessor'](use_ai_validation=False)
        
        # Auto-detect series if requested
        if auto_detect_series and collection_type_enum != imports['VideoCollectionType'].SERIES:
            console.print("🔍 Detecting series patterns...")
            series_detector = imports['SeriesDetector']()
            detection_result = await series_detector.detect_series(video_intelligences)
            
            if detection_result.is_series:
                console.print(f"✅ Series detected with {detection_result.confidence:.2f} confidence")
                if detection_result.user_confirmation_needed:
                    console.print(f"📋 Detection method: {detection_result.detection_method}")
                    console.print(f"🎯 Suggested groupings: {len(detection_result.suggested_grouping)} groups")
                collection_type_enum = imports['VideoCollectionType'].SERIES
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
    console = _get_console()
    console.print(f"📺 Processing video series: {len(urls)} videos")
    
    # Delegate to process_collection_async with series-specific settings
    asyncio.run(process_collection_async(
        ctx,
        collection_name="series_" + str(hash(urls))[:8],
        urls=urls,
        collection_title=series_title or f"Video Series ({len(urls)} videos)",
        collection_type='series',
        auto_detect_series=True,
        user_confirmed_series=False,
        output_dir=output_dir,
        skip_confirmation=False,
        **kwargs
    ))

@cli.command()
@click.option(
    "--demo-dir",
    "-d",
    type=click.Path(path_type=Path),
    default=Path("demo"),
    help="Demo directory to clean"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be deleted without actually deleting"
)
@click.option(
    "--keep-recent",
    "-k",
    type=int,
    default=3,
    help="Number of recent collections to keep per test directory"
)
@click.pass_context
def clean_demo(ctx: click.Context, demo_dir: Path, dry_run: bool, keep_recent: int) -> None:
    """Clean up old demo and test collection folders."""
    console = _get_console()
    
    if not demo_dir.exists():
        console.print(f"[yellow]Demo directory not found: {demo_dir}[/yellow]")
        return
    
    console.print(f"🧹 Cleaning demo directory: {demo_dir}")
    
    total_size = 0
    folders_to_delete = []
    
    # Find all test directories
    test_dirs = [d for d in demo_dir.iterdir() if d.is_dir() and ("test" in d.name or "cnbc" in d.name)]
    
    for test_dir in test_dirs:
        console.print(f"\n📁 Checking: {test_dir.name}")
        
        # Find all collection folders
        collection_folders = []
        for item in test_dir.iterdir():
            if item.is_dir() and "collection_" in item.name:
                # Extract timestamp from folder name
                try:
                    parts = item.name.split("_")
                    if len(parts) >= 2:
                        timestamp = int(parts[1])
                        collection_folders.append((timestamp, item))
                except (ValueError, IndexError):
                    continue
        
        # Sort by timestamp (newest first)
        collection_folders.sort(reverse=True)
        
        # Mark old folders for deletion
        if len(collection_folders) > keep_recent:
            for _, folder in collection_folders[keep_recent:]:
                folders_to_delete.append(folder)
                # Calculate size
                folder_size = sum(f.stat().st_size for f in folder.rglob("*") if f.is_file())
                total_size += folder_size
    
    if not folders_to_delete:
        console.print("[green]✅ No old collections to clean up![/green]")
        return
    
    # Display what will be deleted
    console.print(f"\n🗑️  Found {len(folders_to_delete)} old collections to delete")
    console.print(f"💾 Total space to reclaim: {total_size / (1024 * 1024):.2f} MB")
    
    if dry_run:
        console.print("\n[yellow]DRY RUN - Would delete:[/yellow]")
        for folder in folders_to_delete[:10]:  # Show first 10
            console.print(f"  - {folder.relative_to(demo_dir)}")
        if len(folders_to_delete) > 10:
            console.print(f"  ... and {len(folders_to_delete) - 10} more")
    else:
        # Confirm deletion
        if not click.confirm(f"\nDelete {len(folders_to_delete)} old collections?"):
            console.print("❌ Cleanup cancelled")
            return
        
        # Delete folders
        import shutil
        deleted = 0
        with console.status("[bold green]Deleting old collections...") as status:
            for folder in folders_to_delete:
                try:
                    shutil.rmtree(folder)
                    deleted += 1
                    status.update(f"[bold green]Deleted {deleted}/{len(folders_to_delete)} folders...")
                except Exception as e:
                    console.print(f"[red]Error deleting {folder}: {e}[/red]")
        
        console.print(f"\n[green]✅ Cleaned up {deleted} old collections![/green]")
        console.print(f"[green]💾 Reclaimed {total_size / (1024 * 1024):.2f} MB of disk space[/green]")


def run_cli():
    """Run the CLI application."""
    # Click's native async support handles this automatically.
    # The previous manual loop management was causing RuntimeWarnings.
    imports = _get_core_imports()
    imports['setup_logging']()  # Initialize logging
    cli()


if __name__ == "__main__":
    run_cli() 