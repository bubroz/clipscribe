"""ClipScribe CLI - AI-powered video transcription and analysis tool.

This module provides the command-line interface for ClipScribe, supporting
transcription of videos from 1800+ platforms using Gemini 2.5 Pro by default.
"""

import sys
from pathlib import Path
from typing import Optional, List
import asyncio
import logging

import click

from ..version import __version__
from ..config.logging_config import setup_logging
from ..retrievers import VideoIntelligenceRetriever
from ..config.settings import Settings
from ..models import VideoCollectionType
from ..extractors.multi_video_processor import MultiVideoProcessor

@click.group()
@click.version_option(version=__version__, prog_name="ClipScribe")
@click.option("--debug", is_flag=True, help="Enable debug logging")
@click.pass_context
def cli(ctx: click.Context, debug: bool):
    """ClipScribe - AI-powered video transcription and analysis."""
    log_level = "DEBUG" if debug else "INFO"
    setup_logging(log_level)
    
    ctx.ensure_object(dict)
    ctx.obj['DEBUG'] = debug

@cli.group()
def process():
    """Process single media."""


@process.command("video")
@click.argument("url")
@click.option("--output-dir", "-o", type=click.Path(path_type=Path), default=Path("output"))
@click.option('--mode', '-m', type=click.Choice(['audio', 'video', 'auto']), default='auto')
@click.option('--use-cache/--no-cache', default=True)
@click.option('--use-flash', is_flag=True, default=False)
@click.option('--cookies-from-browser', type=str, default=None)
@click.pass_context
def process_video(ctx: click.Context, url: str, output_dir: Path, mode: str, use_cache: bool, use_flash: bool, cookies_from_browser: Optional[str]):
    """Process a single video from a URL to extract intelligence."""
    asyncio.run(run_processing_logic(url, use_flash, use_cache, str(output_dir), mode, cookies_from_browser))

async def run_processing_logic(url: str, use_flash: bool, use_cache: bool, output_dir: str, mode: str, cookies_from_browser: Optional[str]):
    """The core processing logic, designed to be run from any context."""
    logger = logging.getLogger(__name__)

    try:
        settings = Settings()
        retriever = VideoIntelligenceRetriever(
            use_cache=use_cache,
            use_advanced_extraction=True,
            mode=mode,
            output_dir=output_dir,
            use_flash=use_flash,
            cookies_from_browser=cookies_from_browser,
            settings=settings,
        )
        
        result = await retriever.process_url(url)

        if result:
            logger.info(f"Title: {result.metadata.title}")
            logger.info(f"Channel: {result.metadata.channel}")
            saved_files = retriever.save_all_formats(result, output_dir)
            logger.info(f"Outputs saved to: {saved_files['directory']}")
            # Explicit model line for tests
            model_str = "gemini-2.5-flash" if use_flash else "gemini-2.5-pro"
            print(f"Model: {model_str}")
            print("Intelligence extraction complete!")

        if result is None:
            logger.error("Processing failed. Please check the log for details.")

    except Exception as e:
        logger.error(f"A fatal error occurred: {e}", exc_info=True)

def run_cli():
    """Run the CLI application."""
    cli()

if __name__ == "__main__":
    run_cli()


# === Collection Commands ===

@cli.group()
def collection():
    """Analyze video collections."""


@collection.command("series")
@click.argument("urls", nargs=-1, required=True)
@click.option("--output-dir", "-o", type=click.Path(path_type=Path), default=Path("output"))
@click.option('--use-flash', is_flag=True, default=False)
@click.option('--cookies-from-browser', type=str, default=None)
@click.pass_context
def collection_series(ctx: click.Context, urls: List[str], output_dir: Path, use_flash: bool, cookies_from_browser: Optional[str]):
    """Process multiple related videos as a series with narrative analysis."""

    async def _run():
        settings = Settings()
        retriever = VideoIntelligenceRetriever(
            use_cache=True,
            use_advanced_extraction=True,
            mode='auto',
            output_dir=str(output_dir),
            use_flash=use_flash,
            cookies_from_browser=cookies_from_browser,
            settings=settings,
        )

        # Process each URL
        videos = []
        for u in urls:
            vi = await retriever.process_url(u)
            if vi:
                videos.append(vi)

        if not videos:
            click.echo("No videos could be processed.")
            return

        # Multi-video processing
        mvp = MultiVideoProcessor()
        multi = await mvp.process_video_collection(
            videos=videos,
            collection_type=VideoCollectionType.SERIES,
            collection_title="Series Collection",
            user_confirmed_series=True,
        )

        # Save unified outputs
        retriever.save_collection_outputs(multi, str(output_dir))
        print("Multi-video collection processing complete!")

    asyncio.run(_run())


# === Research Commands ===

@cli.command()
@click.argument("query")
@click.option("--output-dir", "-o", type=click.Path(path_type=Path), default=Path("output"))
@click.option("--max-results", type=int, default=5)
@click.pass_context
def research(ctx: click.Context, query: str, output_dir: Path, max_results: int):
    """Search for and analyze multiple videos on a given topic."""

    async def _run():
        settings = Settings()
        retriever = VideoIntelligenceRetriever(
            use_cache=True,
            use_advanced_extraction=True,
            mode='auto',
            output_dir=str(output_dir),
            settings=settings,
        )

        results = await retriever.search(query=query, max_results=max_results, site='youtube')
        for r in results:
            retriever.save_all_formats(r, str(output_dir))

        print("Research complete!")

    asyncio.run(_run())


# === Utility Commands ===

@cli.group()
def utils():
    """Utility commands."""


@utils.command("clean-demo")
@click.option("--demo-dir", type=click.Path(path_type=Path), default=Path("output"))
@click.option("--dry-run", is_flag=True, default=False)
@click.option("--keep-recent", type=int, default=0, help="Keep N most recent demo folders")
def clean_demo(demo_dir: Path, dry_run: bool, keep_recent: int):
    """Clean up old demo/test output folders."""
    if not demo_dir.exists():
        click.echo("Nothing to clean.")
        return

    # Identify candidate subdirectories
    subdirs = sorted([p for p in demo_dir.iterdir() if p.is_dir()], key=lambda p: p.stat().st_mtime, reverse=True)
    to_delete = subdirs[keep_recent:] if keep_recent > 0 else subdirs

    if dry_run:
        for d in to_delete:
            click.echo(f"Would delete: {d}")
        return

    for d in to_delete:
        try:
            import shutil
            shutil.rmtree(d)
            click.echo(f"Deleted: {d}")
        except Exception as e:
            click.echo(f"Failed to delete {d}: {e}")

    click.echo("Demo cleanup complete.")
