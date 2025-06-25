#!/usr/bin/env python3
"""
ClipScribe Advanced Features Demo

This script showcases the full power of ClipScribe, including:
- Processing a single video with detailed extraction results.
- Searching for multiple videos on a topic.
- Checking multi-platform support.
- Analyzing processing costs.
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from clipscribe.retrievers import VideoIntelligenceRetriever
from clipscribe.config import Settings
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# --- Setup ---
load_dotenv()
console = Console()
settings = Settings()

# --- Demo Functions ---

async def demo_specific_video(video_url: str = "https://www.youtube.com/watch?v=UjDpW_SOrlw"):
    """
    Processes a single video URL and displays detailed extraction results.
    (Based on the original advanced_extraction_demo.py)
    """
    console.print(f"\n[bold green]🎬 Demo: Processing a Single Video[/bold green]")
    console.print(f"Video URL: {video_url}")
    console.print("-" * 80)

    retriever = VideoIntelligenceRetriever(use_advanced_extraction=True)

    with console.status("[yellow]Processing video with advanced extraction..."):
        result = await retriever.process_url(video_url)

    if not result:
        console.print("[red]Failed to process video.[/red]")
        return

    console.print(f"\n[green]✓ Video processed successfully![/green]")
    console.print(f"Title: {result.metadata.title}")

    # Display detailed results tables and panels
    if hasattr(result, 'processing_stats'):
        stats = result.processing_stats
        table = Table(title="Extraction Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green")
        for key, value in stats.items():
            table.add_row(key.replace('_', ' ').title(), str(value))
        console.print(table)

    if hasattr(result, 'relationships'):
        table = Table(title=f"Top 10 Relationships (of {len(result.relationships)})")
        table.add_column("Subject", style="cyan")
        table.add_column("Predicate", style="green")
        table.add_column("Object", style="yellow")
        for rel in sorted(result.relationships, key=lambda x: x.confidence, reverse=True)[:10]:
            table.add_row(rel.subject, rel.predicate, rel.object)
        console.print(table)

    if hasattr(result, 'key_moments'):
        panel = Panel("\n".join([f"• {f['fact']}" for f in result.key_moments[:10]]), title="Top 10 Key Facts")
        console.print(panel)

    console.print(f"\n[bold]Total Cost: ${result.processing_cost:.4f}[/bold]")


async def demo_video_search(query: str = "James Webb Telescope discoveries"):
    """Searches for and processes multiple videos on a topic."""
    console.print(f"\n[bold green]🔍 Demo: Searching for Videos[/bold green]")
    console.print(f"Query: '{query}'")
    console.print("-" * 80)
    
    retriever = VideoIntelligenceRetriever()
    results = await retriever.search(query, max_results=2)
    
    if not results:
        console.print(f"[yellow]No videos found for '{query}'.[/yellow]")
        return

    console.print(f"✅ Found and processed {len(results)} videos.\n")
    for i, video in enumerate(results, 1):
        console.print(Panel(f"[bold]{video.metadata.title}[/bold]\n{video.summary}", title=f"Video {i} Summary"))
    
    stats = retriever.get_stats()
    console.print(f"\n[bold]Total Search Cost: ${stats['total_cost']:.4f}[/bold]")


def demo_multi_platform():
    """Checks for multi-platform support."""
    console.print(f"\n[bold green]🌐 Demo: Multi-Platform Support[/bold green]")
    console.print("ClipScribe uses yt-dlp to support over 1800+ video and audio sites.")
    console.print("Supported platforms include YouTube, X/Twitter, TikTok, Vimeo, SoundCloud, and many more.")
    console.print("\nRun `poetry run clipscribe platforms` for a list of common sites.")


async def demo_cost_analysis():
    """Provides a breakdown of processing costs."""
    console.print(f"\n[bold green]💰 Demo: Cost Analysis[/bold green]")
    from clipscribe.retrievers.transcriber import GeminiFlashTranscriber
    transcriber = GeminiFlashTranscriber()
    
    table = Table(title="Estimated Processing Costs (Audio Mode)")
    table.add_column("Duration", style="cyan")
    table.add_column("Total Cost", style="green")

    for seconds in [60, 300, 600, 1800, 3600]:
        cost = transcriber._calculate_cost(seconds)
        label = f"{seconds // 60} minutes"
        table.add_row(label, f"${cost:.4f}")
    console.print(table)


async def main():
    """Main function to run the interactive demo menu."""
    if not settings.google_api_key:
        console.print("[red]Error: GOOGLE_API_KEY not found. Please set it in your .env file.[/red]")
        return

    while True:
        console.print("\n" + "="*50)
        console.print("[bold cyan]ClipScribe Advanced Features Demo Menu[/bold cyan]")
        console.print("="*50)
        console.print("1. Process a single video (detailed view)")
        console.print("2. Search for videos on a topic")
        console.print("3. Check multi-platform support")
        console.print("4. Analyze processing costs")
        console.print("5. Exit")
        
        choice = console.input("\nEnter your choice: ")
        
        if choice == '1':
            url = console.input("Enter video URL (or press Enter for default): ")
            url = url if url else "https://www.youtube.com/watch?v=UjDpW_SOrlw"
            await demo_specific_video(url)
        elif choice == '2':
            query = console.input("Enter search query (or press Enter for default): ")
            query = query if query else "Latest AI news"
            await demo_video_search(query)
        elif choice == '3':
            demo_multi_platform()
        elif choice == '4':
            await demo_cost_analysis()
        elif choice == '5':
            console.print("[yellow]Exiting demo.[/yellow]")
            break
        else:
            console.print("[red]Invalid choice. Please try again.[/red]")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nExiting.") 