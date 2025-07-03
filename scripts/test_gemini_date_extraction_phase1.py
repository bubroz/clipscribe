#!/usr/bin/env python3
"""
Test script for Phase 1 of Gemini Date Extraction - Corrected Version.

This script properly measures the success of date extraction from transcripts,
not relying on the broken Timeline v2.0 integration.
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from clipscribe.retrievers.video_retriever import VideoIntelligenceRetriever

console = Console()

# Test videos from MASTER_TEST_VIDEO_TABLE.md
TEST_VIDEOS = {
    "pegasus_part1": {
        "url": "https://www.youtube.com/watch?v=6ZVj1_SE4Mo",
        "title": "Pegasus Part 1",
        "type": "news",
        "expected_minimum": 5  # News should have many dates
    },
    "pegasus_part2": {
        "url": "https://www.youtube.com/watch?v=xYMWTXIkANM",
        "title": "Pegasus Part 2",
        "type": "news",
        "expected_minimum": 5
    },
    "iran_saudi_part1": {
        "url": "https://www.youtube.com/watch?v=VHcgnRl2xPM",
        "title": "Iran-Saudi Part 1",
        "type": "documentary",
        "expected_minimum": 10  # Historical docs have more dates
    }
}


async def test_date_extraction():
    """Test Phase 1 date extraction success."""
    console.print(Panel(
        "[bold]Phase 1: Gemini Date Extraction Success Metrics[/bold]\n\n"
        "Measuring actual date extraction from transcripts.\n"
        "Previous baseline: 0.33 dates per video (0.7%)",
        title="ClipScribe v2.18.19",
        expand=False
    ))
    
    results = []
    total_dates = 0
    total_visual_dates = 0
    
    for key, video in TEST_VIDEOS.items():
        console.print(f"\n[cyan]Testing: {video['title']}[/cyan]")
        
        output_dir = Path(f"output/gemini_date_test_phase1/{key}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        retriever = VideoIntelligenceRetriever(
            mode='video',
            output_dir=str(output_dir),
            output_formats=['json']
        )
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Processing...", total=None)
            
            try:
                intelligence = await retriever.process_url(video['url'])
                
                if intelligence:
                    retriever.save_all_formats(intelligence, str(output_dir))
                    
                    # Find the output directory
                    subdirs = list(output_dir.glob("20*_youtube_*"))
                    if subdirs:
                        actual_dir = subdirs[0]
                        transcript_file = actual_dir / "transcript.json"
                        
                        if transcript_file.exists():
                            with open(transcript_file) as f:
                                data = json.load(f)
                            
                            dates = data.get('dates', [])
                            visual_dates = data.get('visual_dates', [])
                            
                            num_dates = len(dates)
                            num_visual = len(visual_dates)
                            total = num_dates + num_visual
                            
                            # Calculate success rate
                            success_rate = min((total / video['expected_minimum']) * 100, 100)
                            
                            results.append({
                                'video': video['title'],
                                'type': video['type'],
                                'transcript_dates': num_dates,
                                'visual_dates': num_visual,
                                'total': total,
                                'expected': video['expected_minimum'],
                                'success_rate': success_rate
                            })
                            
                            total_dates += num_dates
                            total_visual_dates += num_visual
                            
                            # Show sample dates
                            if dates:
                                console.print(f"  [green]✓ Found {num_dates} transcript dates[/green]")
                                for i, date in enumerate(dates[:3]):
                                    console.print(f"    • {date.get('original_text')} → {date.get('normalized_date')}")
                                if num_dates > 3:
                                    console.print(f"    ... and {num_dates - 3} more")
            
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                results.append({
                    'video': video['title'],
                    'type': video['type'],
                    'error': str(e)
                })
    
    # Display results
    console.print("\n" + "="*60 + "\n")
    
    table = Table(title="Phase 1 Date Extraction Results", show_header=True)
    table.add_column("Video", style="cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Transcript", justify="right")
    table.add_column("Visual", justify="right")
    table.add_column("Total", justify="right", style="bold")
    table.add_column("Success Rate", justify="right", style="green")
    
    for result in results:
        if 'error' not in result:
            table.add_row(
                result['video'],
                result['type'],
                str(result['transcript_dates']),
                str(result['visual_dates']),
                str(result['total']),
                f"{result['success_rate']:.0f}%"
            )
    
    console.print(table)
    
    # Calculate overall metrics
    avg_dates = total_dates / len(TEST_VIDEOS)
    improvement = avg_dates / 0.33  # Previous baseline was 0.33 dates per video
    
    stats = Panel(
        f"""[bold]Phase 1 Success Metrics:[/bold]
        
Total dates extracted: {total_dates}
Visual dates extracted: {total_visual_dates}
Average per video: {avg_dates:.1f} dates

[bold green]Previous baseline: 0.33 dates per video
Current performance: {avg_dates:.1f} dates per video
Improvement: {improvement:.0f}x better![/bold green]

Target achievement:
- News content (5+ dates): {"✓" if avg_dates >= 5 else "✗"}
- Documentary (10+ dates): {"✓" if any(r.get('total', 0) >= 10 for r in results) else "✗"}
""",
        title="Success Summary",
        expand=False
    )
    console.print(stats)


if __name__ == "__main__":
    asyncio.run(test_date_extraction()) 