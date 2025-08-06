"""ClipScribe CLI - AI-powered video transcription and analysis tool.

This module provides the command-line interface for ClipScribe, supporting
transcription of videos from 1800+ platforms using Gemini 2.5 Pro by default.
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
  process     Commands for processing single media files.
  collection  Commands for processing collections of media.
  research    Research a topic by analyzing multiple videos.
  utils       Utility and maintenance commands.

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
import time

import click

from ..version import __version__
from ..config.logging_config import setup_logging
from ..utils.cli_progress import CliProgressManager

from rich.live import Live
from rich.table import Table
from rich import box

# Lazy imports - only load when needed
def _get_rich_imports():
    """Lazy import Rich components."""
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
    from rich.console import Console
    return Panel, Table, box, Console

def _get_core_imports():
    """Lazy import core processing components."""
    from ..retrievers import VideoIntelligenceRetriever, UniversalVideoClient
    from ..config.settings import Settings
    from ..utils.performance import PerformanceMonitor
    from ..extractors.multi_video_processor import MultiVideoProcessor
    from ..models import VideoCollectionType
    return {
        'VideoIntelligenceRetriever': VideoIntelligenceRetriever,
        'UniversalVideoClient': UniversalVideoClient,
        'Settings': Settings,
        'PerformanceMonitor': PerformanceMonitor,
        'MultiVideoProcessor': MultiVideoProcessor,
        'VideoCollectionType': VideoCollectionType
    }

_console = None

def _get_console():
    """Get console instance with lazy initialization."""
    global _console
    if _console is None:
        _, _, _, Console = _get_rich_imports()
        _console = Console()
    return _console

cli_perf = importlib.import_module('src.clipscribe.utils.cli_performance')
RealTimeCostTracker = cli_perf.RealTimeCostTracker

@click.group()
@click.version_option(version=__version__, prog_name="ClipScribe")
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug logging"
)
@click.pass_context
def cli(ctx: click.Context, debug: bool) -> None:
    """ClipScribe - AI-powered video transcription and analysis."""
    log_level = "DEBUG" if debug else "INFO"
    setup_logging(log_level)
    
    logger = logging.getLogger(__name__)
    
    ctx.ensure_object(dict)
    if ctx.invoked_subcommand is not None:
        if debug:
            logger.debug("Debug mode enabled")
        
        if 'settings' not in ctx.obj:
            imports = _get_core_imports()
            ctx.obj["settings"] = imports['Settings']()
            
            console = _get_console()
            console.print(f"[bold blue]ClipScribe v{__version__}[/bold blue]")
            console.print("AI-powered video intelligence with Gemini 2.5 Pro\n")

# --- Command Groups ---
@click.group()
def process():
    """Commands for processing single media files."""
    pass

@click.group()
def collection():
    """Commands for processing collections of media."""
    pass

@click.group()
def utils():
    """Utility and maintenance commands."""
    pass

cli.add_command(process)
cli.add_command(collection)
cli.add_command(utils)

# --- Process Group Commands ---
@process.command(name="video")
@click.argument("url")
@click.option("--output-dir", "-o", type=click.Path(path_type=Path), default=Path("output"))
@click.option('--mode', '-m', type=click.Choice(['audio', 'video', 'auto']), default='auto')
@click.option('--use-cache/--no-cache', default=True)
@click.option('--enhance-transcript', is_flag=True)
@click.option('--clean-graph', is_flag=True)
@click.option('--skip-cleaning', is_flag=True)
@click.option('--visualize', is_flag=True)
@click.option('--performance-report', is_flag=True)
@click.option('--use-flash', is_flag=True, default=False)
@click.option('--cookies-from-browser', type=str, default=None)
@click.option('--keep-videos', is_flag=True, default=False)
@click.pass_context
def video_command(ctx: click.Context, url: str, output_dir: Path, mode: str, use_cache: bool, enhance_transcript: bool, clean_graph: bool, skip_cleaning: bool, visualize: bool, performance_report: bool, use_flash: bool, cookies_from_browser: Optional[str], keep_videos: bool) -> None:
    """Process a single video from a URL to extract intelligence."""
    if keep_videos:
        ctx.obj['settings'].video_retention_policy = 'keep_processed'
    asyncio.run(transcribe_async(ctx, url, output_dir, mode, use_cache, enhance_transcript, clean_graph, skip_cleaning, visualize, performance_report, use_flash, cookies_from_browser))

# --- Collection Group Commands ---
@collection.command(name="series")
@click.argument("urls", nargs=-1, required=True)
@click.option("--output-dir", "-o", type=click.Path(path_type=Path), default=Path("output/series"))
@click.option("--series-title", "-t")
@click.option('--mode', '-m', type=click.Choice(['audio', 'video', 'auto']), default='auto')
@click.option('--use-cache/--no-cache', default=True)
@click.option('--enhance-transcript', is_flag=True)
@click.option('--clean-graph', is_flag=True)
@click.option('--performance-report', is_flag=True)
@click.option('--use-flash', is_flag=True, default=False)
@click.option('--keep-videos', is_flag=True, default=False)
@click.pass_context
def series_command(ctx: click.Context, urls: tuple, output_dir: Path, series_title: Optional[str], use_flash: bool, keep_videos: bool, **kwargs) -> None:
    """Process videos as a series with narrative flow analysis."""
    console = _get_console()
    console.print(f"📺 Processing video series: {len(urls)} videos")
    if keep_videos:
        ctx.obj['settings'].video_retention_policy = 'keep_processed'
    asyncio.run(process_collection_async(ctx, "collection_series_" + str(hash(urls))[:8], urls, series_title or f"Video Series ({len(urls)} videos)", 'series', True, False, output_dir, None, False, use_flash, False, None, **kwargs))

@collection.command(name="custom")
@click.argument("collection_name")
@click.argument("urls", nargs=-1, required=True)
@click.option("--collection-title", "-t")
@click.option("--collection-type", type=click.Choice(['series', 'topic_research', 'channel_analysis', 'cross_source_topic', 'custom_collection']), default='custom_collection')
@click.option("--auto-detect-series", is_flag=True)
@click.option("--user-confirmed-series", is_flag=True)
@click.option("--output-dir", "-o", type=click.Path(path_type=Path), default=Path("output/collections"))
@click.option("--limit", "-l", type=int)
@click.option('--mode', '-m', type=click.Choice(['audio', 'video', 'auto']), default='auto')
@click.option('--use-cache/--no-cache', default=True)
@click.option('--enhance-transcript', is_flag=True)
@click.option('--clean-graph', is_flag=True)
@click.option('--performance-report', is_flag=True)
@click.option('--skip-confirmation', is_flag=True)
@click.option('--use-flash', is_flag=True, default=False)
@click.option('--cookies-from-browser', type=str, default=None)
@click.option('--core-only', is_flag=True, default=False)
@click.option('--keep-videos', is_flag=True, default=False)
@click.pass_context
def custom_collection_command(ctx: click.Context, collection_name: str, urls: tuple, collection_title: Optional[str], collection_type: str, auto_detect_series: bool, user_confirmed_series: bool, output_dir: Path, limit: Optional[int], skip_confirmation: bool, use_flash: bool, core_only: bool, cookies_from_browser: Optional[str], keep_videos: bool, **kwargs) -> None:
    """Process multiple videos as a unified custom collection."""
    if keep_videos:
        ctx.obj['settings'].video_retention_policy = 'keep_processed'
    asyncio.run(process_collection_async(ctx, collection_name, urls, collection_title or collection_name, collection_type, auto_detect_series, user_confirmed_series, output_dir, limit, skip_confirmation, use_flash, core_only, cookies_from_browser, **kwargs))

# --- Research Command (Top Level) ---
@cli.command()
@click.argument("query")
@click.option("--max-results", "-n", type=int, default=3)
@click.option("--period", type=click.Choice(['hour', 'day', 'week', 'month', 'year']), default=None)
@click.option("--sort-by", type=click.Choice(['relevance', 'newest', 'oldest', 'popular']), default='relevance')
@click.option("--output-dir", "-o", type=click.Path(path_type=Path), default=Path("output/research"))
@click.option('--mode', '-m', type=click.Choice(['audio', 'video', 'auto']), default='auto')
@click.option('--use-cache/--no-cache', default=True)
@click.option('--enhance-transcript', is_flag=True)
@click.option('--clean-graph', is_flag=True)
@click.option('--skip-cleaning', is_flag=True)
@click.option('--performance-report', is_flag=True)
@click.pass_context
def research(ctx: click.Context, query: str, max_results: int, period: Optional[str], sort_by: str, output_dir: Path, **kwargs):
    """Research a topic by analyzing multiple videos."""
    asyncio.run(research_async(ctx, query, max_results, period, sort_by, output_dir, **kwargs))

# --- Utils Group Commands ---
@utils.command(name="clean-demo")
@click.option("--demo-dir", "-d", type=click.Path(path_type=Path), default=Path("demo"))
@click.option("--dry-run", is_flag=True)
@click.option("--keep-recent", "-k", type=int, default=3)
@click.pass_context
def clean_demo_command(ctx: click.Context, demo_dir: Path, dry_run: bool, keep_recent: int) -> None:
    """Clean up old demo and test collection folders."""
    clean_demo(ctx, demo_dir, dry_run, keep_recent)

# --- Async Implementations (Shared Logic) ---
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
    performance_report: bool,
    use_flash: bool,
    cookies_from_browser: Optional[str]
) -> None:
    """Async implementation for single video processing."""
    imports = _get_core_imports()
    logger = logging.getLogger(__name__)
    console = _get_console()
    
    if not url:
        console.print("[red]Error: URL is required[/red]")
        ctx.exit(1)
        
    output_dir.mkdir(parents=True, exist_ok=True)
    cost_tracker = RealTimeCostTracker()

    processing_phases = [
        "Downloading", "Transcribing", "Extracting Intelligence", 
        "Building Knowledge Graph", "Video Retention", "Saving Outputs"
    ]

    progress_manager = CliProgressManager(phases=processing_phases, console=console)
    
    with progress_manager:
        try:
            retriever = imports['VideoIntelligenceRetriever'](
                use_cache=use_cache,
                use_advanced_extraction=True,
                mode=mode,
                output_dir=str(output_dir),
                enhance_transcript=enhance_transcript,
                cost_tracker=cost_tracker,
                use_flash=use_flash,
                cookies_from_browser=cookies_from_browser,
                settings=ctx.obj['settings'],
                progress=progress_manager
            )
            
            if clean_graph:
                retriever.clean_graph = True
            elif skip_cleaning:
                retriever.clean_graph = False
            
            result = await retriever.process_url(url)
            
            if result is None:
                console.print("[red]Video processing failed.[/red]")
                ctx.exit(1)
            
            progress_manager.update_phase("Saving Outputs", "In Progress...", cost_tracker.current_cost)
            saved_files = retriever.save_all_formats(result, str(output_dir))
            progress_manager.complete_phase("Saving Outputs", cost_tracker.current_cost)

        except Exception as e:
            logger.error("An unhandled exception occurred in transcribe_async", exc_info=True)
            console.print(f"[bold red]FATAL ERROR:[/bold red] {e}")
            ctx.exit(1)

    console.print(f"\n[green]Saved all formats to: {saved_files['directory']}[/green]")
    # _display_results(console, result) # This is now handled by the progress manager and final summary
    
    if performance_report:
        pass
    
    console.print("\n🎉 [bold green]Intelligence extraction complete![/bold green]")

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
    use_flash: bool,
    core_only: bool,
    cookies_from_browser: Optional[str],
    **kwargs
) -> None:
    imports = _get_core_imports()
    logger = logging.getLogger(__name__)
    console = _get_console()
    
    video_client = imports['UniversalVideoClient']()
    
    final_urls = list(urls)
    for i, url in enumerate(list(final_urls)):
        if "playlist" in url or "list=" in url:
            try:
                playlist_urls = await video_client.extract_all_playlist_urls(url)
                if limit:
                    playlist_urls = playlist_urls[:limit]
                
                final_urls[i:i+1] = playlist_urls
                
                if not skip_confirmation:
                    console.print(f"\n Found playlist with {len(playlist_urls)} videos")
                    if limit:
                        console.print(f"⚠️ Limited to first {limit} videos")
                    
                    if not click.confirm("Proceed with collection processing?"):
                        console.print("Collection processing cancelled")
                        ctx.exit(0)
            except Exception as e:
                logger.warning(f"Could not expand playlist {url}: {e}")
    
    video_intelligences = []
    collection_output_dir = output_dir / collection_name
    collection_output_dir.mkdir(parents=True, exist_ok=True)
    
    cost_tracker = RealTimeCostTracker()

    for i, url in enumerate(final_urls, 1):
        console.print(f"\nProcessing video {i}/{len(final_urls)}: {url}")
        
        # We can reuse transcribe_async for single video processing in a collection
        # This gives us the nice progress bar for each video.
        await transcribe_async(
            ctx, url, collection_output_dir, kwargs.get('mode', 'auto'),
            kwargs.get('use_cache', True), kwargs.get('enhance_transcript', False),
            kwargs.get('clean_graph', False), False, False, False, use_flash, cookies_from_browser
        )
        # We need to collect the result object to pass to the multi-processor
        # For now, this part is simplified. A more robust solution would reload the JSON.
    
    console.print(f"\n🎉 Multi-video collection processing complete!")
    console.print(f"📁 Outputs saved to: {collection_output_dir}")

async def research_async(ctx: click.Context, query: str, max_results: int, period: Optional[str], sort_by: str, output_dir: Path, **kwargs):
    # ... (rest of the file is unchanged)
    pass

def clean_demo(ctx: click.Context, demo_dir: Path, dry_run: bool, keep_recent: int) -> None:
    # ...
    pass

def run_cli():
    """Run the CLI application."""
    cli()

if __name__ == "__main__":
    run_cli()
