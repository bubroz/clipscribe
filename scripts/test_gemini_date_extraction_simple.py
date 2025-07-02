#!/usr/bin/env python3
"""
Simple test for Gemini date extraction - Phase 4 debugging.
"""

import asyncio
import json
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from clipscribe.retrievers.video_retriever import VideoIntelligenceRetriever

console = Console()

# Single test video from MASTER_TEST_VIDEO_TABLE.md
TEST_VIDEO = {
    "url": "https://www.youtube.com/watch?v=6ZVj1_SE4Mo",  # PBS Pegasus Part 1
    "title": "Global Spyware Scandal: Exposing Pegasus Part One",
    "expected": "Should have investigation dates, scandal timeline"
}


async def test_date_extraction():
    """Test Gemini date extraction on a single video."""
    console.print(Panel(
        "[bold]Phase 4: Gemini Date Extraction Test (Simple)[/bold]\n\n"
        f"Testing: {TEST_VIDEO['title']}\n"
        f"Expected: {TEST_VIDEO['expected']}",
        title="ClipScribe v2.18.19",
        expand=False
    ))
    
    # Clear any cached version
    output_dir = Path("output/gemini_date_test_simple")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize retriever with video mode and no cache
    retriever = VideoIntelligenceRetriever(
        mode='video',  # Force video mode for enhanced date extraction
        use_cache=False,  # Force fresh processing
        output_dir=str(output_dir),
        output_formats=['json', 'timelinejs']
    )
    
    console.print("\n[yellow]Processing video with fresh transcription...[/yellow]")
    
    try:
        # Process the video
        intelligence = await retriever.process_url(TEST_VIDEO['url'])
        
        if intelligence:
            # Save outputs
            output_path = retriever.save_all_formats(intelligence, str(output_dir))
            
            # Check the raw transcript for dates
            transcript_file = output_dir / list(output_path.keys())[0].parent.name / "transcript.json"
            
            console.print(f"\n[cyan]Checking transcript file: {transcript_file}[/cyan]")
            
            if transcript_file.exists():
                with open(transcript_file) as f:
                    transcript_data = json.load(f)
                
                # Check for dates field
                console.print("\n[bold]Raw Gemini Response Analysis:[/bold]")
                console.print(f"Has 'dates' field: {'dates' in transcript_data}")
                console.print(f"Has 'visual_dates' field: {'visual_dates' in transcript_data}")
                console.print(f"Has 'temporal_intelligence' field: {'temporal_intelligence' in transcript_data}")
                
                if 'dates' in transcript_data and transcript_data['dates']:
                    console.print(f"\n[green]✓ Found {len(transcript_data['dates'])} dates![/green]")
                    for i, date in enumerate(transcript_data['dates'][:5]):
                        console.print(f"  Date {i+1}: {date}")
                else:
                    console.print("\n[red]✗ No dates found in transcript![/red]")
                
                # Check analysis field
                if 'analysis' in transcript_data:
                    analysis = transcript_data['analysis']
                    console.print(f"\nAnalysis fields: {list(analysis.keys())}")
                    
                    # Check if dates might be in entities
                    if 'entities' in analysis and analysis['entities']:
                        date_entities = [e for e in analysis['entities'] if e.get('type') == 'DATE']
                        console.print(f"Date entities found: {len(date_entities)}")
                
                # Check timeline data
                timeline_file = output_dir / list(output_path.keys())[0].parent.name / "timeline_js.json"
                if timeline_file.exists():
                    with open(timeline_file) as f:
                        timeline_data = json.load(f)
                    
                    events = timeline_data.get('events', [])
                    events_with_dates = 0
                    
                    console.print(f"\n[bold]Timeline Analysis:[/bold]")
                    console.print(f"Total events: {len(events)}")
                    
                    for event in events:
                        if event.get('start_date') and event['start_date'].get('year') != '2025':
                            events_with_dates += 1
                    
                    console.print(f"Events with real dates: {events_with_dates}")
                    console.print(f"Success rate: {(events_with_dates/len(events)*100) if events else 0:.1f}%")
                    
                    # Show sample events
                    console.print("\n[bold]Sample Events:[/bold]")
                    for i, event in enumerate(events[:3]):
                        date = event.get('start_date', {})
                        console.print(f"\nEvent {i+1}:")
                        console.print(f"  Text: {event.get('text', {}).get('headline', '')[:60]}...")
                        console.print(f"  Date: {date}")
                        console.print(f"  Has real date: {date.get('year') != '2025'}")
            
            else:
                console.print("[red]Transcript file not found![/red]")
                
        else:
            console.print("[red]Failed to process video![/red]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_date_extraction()) 