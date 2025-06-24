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

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.logging import RichHandler

from ..retrievers import VideoIntelligenceRetriever
from ..config.settings import Settings
from ..utils.logging import setup_logging
from ..version import __version__

# Initialize Rich console for beautiful output
console = Console()

# Configure logging with Rich
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console)]
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
    "--format",
    "-f",
    type=click.Choice(['txt', 'srt', 'vtt', 'json', 'md', 'all'], case_sensitive=False),
    default='txt',
    help='Output format for transcription'
)
@click.option(
    "--language",
    "-l",
    default="en",
    help="Language code for transcription (e.g., en, es, fr)"
)
@click.option(
    "--include-timestamps",
    is_flag=True,
    help="Include word-level timestamps in transcript"
)
@click.option(
    "--enhance",
    is_flag=True,
    help="Enable AI enhancement for better formatting and clarity"
)
@click.option(
    '--mode', '-m',
    type=click.Choice(['audio', 'video', 'auto'], case_sensitive=False),
    default='audio',
    help="""Processing mode:
    
    • audio (default): Extract audio only - Fast & cheap ($0.002/min)
      Best for: Podcasts, interviews, meetings, news briefings
      
    • video: Process full video with visual analysis - Slower & expensive (~$0.02/min) 
      Best for: Tutorials with code, presentations with slides, educational content
      
    • auto: Let ClipScribe detect the best mode based on content analysis
    """
)
@click.option(
    '--use-cache/--no-cache',
    default=True,
    help='Use cached results if available'
)
@click.pass_context
async def transcribe(
    ctx: click.Context,
    url: str,
    output_dir: Path,
    format: str,
    language: str,
    include_timestamps: bool,
    enhance: bool,
    mode: str,
    use_cache: bool
) -> None:
    """Transcribe a video from URL using Gemini 2.5 Flash.
    
    Supports 1800+ platforms including YouTube, Vimeo, TikTok, and more.
    
    Examples:
    
        # Basic transcription
        clipscribe transcribe "https://youtube.com/watch?v=..."
        
        # With options
        clipscribe transcribe "https://vimeo.com/..." -o transcripts -f srt --enhance
    """
    settings = ctx.obj["settings"]
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        with console.status("[bold green]Initializing video retriever...") as status:
            # Create retriever
            try:
                retriever = VideoIntelligenceRetriever(
                    enhance_transcript=enhance,
                    output_formats=[format] if format != "all" else ["txt", "json", "srt", "vtt"],
                    output_dir=output_dir,
                    mode=mode,
                    use_cache=use_cache
                )
            except TypeError:
                # Fallback for older retriever API
                retriever = VideoIntelligenceRetriever()
            
            # Show mode selection info
            console.print(f"\n[cyan]Processing mode:[/cyan] {mode.upper()}")
            
            if mode == "audio":
                console.print("[green]✓[/green] Using audio-only extraction (fast & cost-effective)")
                console.print("  [dim]Perfect for podcasts, interviews, and talking-head videos[/dim]")
            elif mode == "video":
                console.print("[yellow]⚠[/yellow] Using full video analysis (slower & more expensive)")
                console.print("  [dim]Captures visual content like slides, code, and diagrams[/dim]")
                console.print("  [dim]Cost estimate: ~10x more than audio mode[/dim]")
            else:  # auto
                console.print("[blue]🤖[/blue] Auto-detecting best mode based on content...")
                console.print("  [dim]Will analyze video characteristics to choose[/dim]")
            
            console.print()  # blank line
            
            # Process the video
            status.update("[bold green]Processing video...")
            video_result = await retriever.process_url(url)
            
            if not video_result:
                console.print("[red]Failed to process video[/red]")
                sys.exit(1)
            
            # Save the transcript in requested formats
            status.update("[bold green]Saving transcript...")
            saved_files = retriever.save_all_formats(
                video_result,
                output_dir=str(output_dir),
                include_chimera_format=False
            )
            
            # Display results
            console.print("\n[bold green]✓ Transcription complete![/bold green]\n")
            
            # Create results table
            table = Table(title="Transcription Results")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")
            
            # Video metadata
            table.add_row("Video Title", video_result.metadata.title)
            table.add_row("Duration", f"{video_result.metadata.duration // 60}:{video_result.metadata.duration % 60:02d}")
            
            # Extract platform from URL
            parsed_url = urlparse(video_result.metadata.url)
            platform = parsed_url.netloc.replace('www.', '').split('.')[0].title()
            table.add_row("Platform", platform)
            
            table.add_row("Language", video_result.transcript.language)
            
            # Processing info
            table.add_row("Processing Mode", mode.upper())
            table.add_row("Processing Time", f"{video_result.processing_time:.1f}s")
            table.add_row("Cost", f"${video_result.processing_cost:.4f}")
            
            # Entity extraction results
            if hasattr(video_result, 'entities') and video_result.entities:
                table.add_row("Entities Found", str(len(video_result.entities)))
            
            if hasattr(video_result, 'relationships') and video_result.relationships:
                table.add_row("Relationships", str(len(video_result.relationships)))
            
            # Output files
            table.add_row("Output Directory", str(output_dir))
            if saved_files:
                file_list = ", ".join(Path(f).name for f in saved_files.values())
                table.add_row("Files Created", file_list)
            
            console.print(table)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Transcription cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        logger.exception("Transcription failed")
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("query")
@click.option(
    "--max-results",
    "-n",
    type=int,
    default=5,
    help="Maximum number of videos to analyze"
)
@click.option(
    "--output-dir",
    "-o", 
    type=click.Path(exists=False, file_okay=False, dir_okay=True, path_type=Path),
    default=Path("output/research"),
    help="Output directory for research results"
)
@click.option(
    "--platforms",
    "-p",
    multiple=True,
    help="Specific platforms to search (e.g., youtube, vimeo)"
)
@click.pass_context
async def research(
    ctx: click.Context,
    query: str,
    max_results: int,
    output_dir: Path,
    platforms: tuple
) -> None:
    """Research a topic across multiple video platforms.
    
    Analyzes videos from multiple sources to create a comprehensive
    research report on the given topic.
    
    Examples:
    
        # Basic research
        clipscribe research "machine learning tutorials"
        
        # Platform-specific research  
        clipscribe research "cooking recipes" -p youtube -p vimeo -n 10
    """
    settings = ctx.obj["settings"]
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    console.print(f"[bold]Researching:[/bold] {query}")
    console.print(f"[dim]Max videos: {max_results}, Platforms: {platforms or 'all'}[/dim]\n")
    
    # Implementation placeholder
    console.print("[yellow]Research feature coming soon![/yellow]")
    console.print("This will analyze multiple videos to create comprehensive reports.")


@cli.command()
@click.option(
    "--full",
    is_flag=True,
    help="Show full configuration including API keys (hidden by default)"
)
@click.pass_context
def config(ctx: click.Context, full: bool) -> None:
    """Show current configuration."""
    settings = ctx.obj["settings"]
    
    table = Table(title="ClipScribe Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    # Basic settings
    table.add_row("Output Directory", str(settings.output_dir))
    table.add_row("Default Language", settings.default_language)
    table.add_row("AI Model", settings.ai_model)
    
    # API keys (masked unless --full)
    if full:
        table.add_row("Google API Key", settings.google_api_key or "[not set]")
    else:
        key = settings.google_api_key
        masked_key = f"{key[:8]}...{key[-4:]}" if key else "[not set]"
        table.add_row("Google API Key", masked_key)
    
    console.print(table)


@cli.command()
def platforms() -> None:
    """List all supported video platforms."""
    console.print("[bold]Supported Platforms[/bold]")
    console.print("ClipScribe supports 1800+ video platforms through yt-dlp\n")
    
    # Show popular platforms
    popular = [
        "YouTube", "Vimeo", "TikTok", "Instagram", "Facebook",
        "Twitter/X", "Dailymotion", "Twitch", "Reddit", "LinkedIn"
    ]
    
    console.print("[cyan]Popular platforms:[/cyan]")
    for platform in popular:
        console.print(f"  • {platform}")
    
    console.print("\n[dim]And 1790+ more platforms![/dim]")
    console.print("\nFor a complete list, visit: https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md")


def run_cli() -> None:
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