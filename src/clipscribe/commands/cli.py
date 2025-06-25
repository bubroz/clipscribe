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
@click.option("--output-dir", "-o", type=click.Path(path_type=Path), default=Path("output/research"))
@click.option('--mode', '-m', type=click.Choice(['audio', 'video', 'auto']), default='audio')
@click.option('--use-cache/--no-cache', default=True)
@click.option('--enhance-transcript', is_flag=True)
@click.option('--clean-graph', is_flag=True)
@click.option('--skip-cleaning', is_flag=True)
@click.option('--performance-report', is_flag=True)
@click.pass_context
async def research(ctx: click.Context, query: str, max_results: int, output_dir: Path, **kwargs):
    """Research a topic by analyzing multiple videos."""
    console.print(f"🔬 Researching: '{query}'...")
    
    # 1. Search
    video_client = UniversalVideoClient()
    search_results = await video_client.search_videos(query, max_results=max_results)
    
    if not search_results:
        console.print(f"[red]No videos found for '{query}'.[/red]")
        return
        
    console.print(f"[green]✓ Found {len(search_results)} videos. Starting batch processing...[/green]")

    async def process_video(video_meta):
        video_output_dir = output_dir / f"youtube_{video_meta.video_id}"
        
        # Create a clean set of args for the retriever
        retriever_kwargs = {
            "use_cache": kwargs.get('use_cache', True),
            "mode": kwargs.get('mode', 'audio'),
            "output_dir": video_output_dir,
            "enhance_transcript": kwargs.get('enhance_transcript', False),
            "performance_monitor": PerformanceMonitor(video_output_dir) if kwargs.get('performance_report') else None
        }

        console.print(f"Processing: {video_meta.url}")
        try:
            retriever = VideoIntelligenceRetriever(**retriever_kwargs)
            if kwargs.get('skip_cleaning'): retriever.clean_graph = False
            elif kwargs.get('clean_graph'): retriever.clean_graph = True

            video_result = await retriever.process_url(video_meta.url)
            if video_result:
                retriever.save_all_formats(video_result, str(video_output_dir), True)
                console.print(f"[green]✓ Processed: {video_meta.title}[/green]")
        except Exception as e:
            console.print(f"[red]✗ Failed {video_meta.title}: {e}[/red]")
        finally:
            if retriever_kwargs["performance_monitor"]:
                retriever_kwargs["performance_monitor"].save_report()
        
    tasks = [process_video(video) for video in search_results]
    await asyncio.gather(*tasks)

    console.print(f"\n🎉 Research complete! Outputs are in {output_dir}")


def run_cli():
    """Run the CLI application."""
    # Handle async commands properly
    if len(sys.argv) > 1 and sys.argv[1] in ["transcribe", "research"]:
        # These are async commands
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Create a sync wrapper for Click
            def sync_wrapper():
                future = asyncio.ensure_future(cli.main(standalone_mode=False))
                loop.run_until_complete(future)
            
            sync_wrapper()
        finally:
            loop.close()
    else:
        # Regular sync commands
        cli()


if __name__ == "__main__":
    run_cli() 