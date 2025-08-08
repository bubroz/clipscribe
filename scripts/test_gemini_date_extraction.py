#!/usr/bin/env python3
"""
Test script for Phase 4 of Gemini Date Extraction.

This script processes test videos and evaluates the date extraction performance,
comparing against the target 70-85% success rate for news content.
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.syntax import Syntax

from clipscribe.models import VideoIntelligence
from clipscribe.retrievers.video_retriever import VideoIntelligenceRetriever

console = Console()

# Test videos from MASTER_TEST_VIDEO_TABLE.md - ALWAYS USE THESE!
TEST_VIDEOS = {
    "pegasus_part1": {
        "url": "https://www.youtube.com/watch?v=6ZVj1_SE4Mo",  # PBS FRONTLINE Pegasus Part 1
        "title": "Global Spyware Scandal: Exposing Pegasus Part One",
        "expected_dates": ["investigation timeline", "scandal dates", "NSO Group events"],
        "type": "news",
        "notes": "FRONTLINE PBS - excellent for timeline extraction testing"
    },
    "pegasus_part2": {
        "url": "https://www.youtube.com/watch?v=xYMWTXIkANM",  # PBS FRONTLINE Pegasus Part 2
        "title": "Global Spyware Scandal: Exposing Pegasus Part Two",
        "expected_dates": ["investigation conclusions", "timeline events"],
        "type": "news",
        "notes": "FRONTLINE PBS - investigation conclusions"
    },
    "iran_saudi_part1": {
        "url": "https://www.youtube.com/watch?v=VHcgnRl2xPM",  # Iran-Saudi Arabia Part 1
        "title": "Bitter Rivals: Iran and Saudi Arabia, Part One",
        "expected_dates": ["historical dates", "geopolitical timeline", "conflict dates"],
        "type": "documentary",
        "notes": "FRONTLINE PBS - historical timeline extraction"
    }
}


class GeminiDateExtractionTester:
    """Test harness for evaluating Gemini date extraction performance."""
    
    def __init__(self):
        self.console = console
        self.results: Dict[str, Dict] = {}
        
    async def test_video(self, video_key: str, video_info: dict) -> Dict:
        """Test date extraction on a single video."""
        self.console.print(f"\n[bold blue]Testing: {video_info['title']}[/bold blue]")
        self.console.print(f"URL: {video_info['url']}")
        self.console.print(f"Type: {video_info['type']}")
        
        output_dir = Path(f"output/gemini_date_test/{video_key}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Process the video
        retriever = VideoIntelligenceRetriever(
            mode='video',  # Critical for visual date extraction
            output_dir=str(output_dir),
            output_formats=['json', 'timelinejs']  # Include timeline formats
        )
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Processing video...", total=None)
            
            try:
                # Process with video mode to enable visual date extraction
                intelligence = await retriever.process_url(
                    video_info['url']
                )
                
                progress.update(task, description="Analyzing results...")
                
                if intelligence:
                    # Save outputs
                    retriever.save_all_formats(intelligence, str(output_dir))
                    
                    # Analyze the results
                    result = await self._analyze_results(intelligence, output_dir)
                    result['video_info'] = video_info
                    
                    return result
                else:
                    raise Exception("Failed to process video")
                
            except Exception as e:
                self.console.print(f"[red]Error processing {video_key}: {e}[/red]")
                return {
                    'video_info': video_info,
                    'error': str(e),
                    'success': False
                }
    
    async def _analyze_results(self, intelligence: VideoIntelligence, output_dir: Path) -> Dict:
        """Analyze the date extraction results."""
        result = {
            'total_events': 0,
            'events_with_dates': 0,
            'transcript_dates': [],
            'visual_dates': [],
            'unique_dates': set(),
            'date_sources': {'transcript': 0, 'visual': 0, 'both': 0, 'none': 0},
            'timeline_events': []
        }
        
        # Load the timeline data
        timeline_path = output_dir / "timeline_js.json"
        if timeline_path.exists():
            with open(timeline_path) as f:
                timeline_data = json.load(f)
                
            events = timeline_data.get('events', [])
            result['total_events'] = len(events)
            
            for event in events:
                result['timeline_events'].append({
                    'text': event.get('text', {}).get('text', '')[:100] + '...',
                    'has_date': bool(event.get('start_date')),
                    'date': event.get('start_date'),
                    'sources': event.get('date_sources', [])
                })
                
                if event.get('start_date'):
                    result['events_with_dates'] += 1
                    
                    # Analyze date sources
                    sources = event.get('date_sources', [])
                    has_transcript = any(s['source'] == 'transcript' for s in sources)
                    has_visual = any(s['source'] == 'visual' for s in sources)
                    
                    if has_transcript and has_visual:
                        result['date_sources']['both'] += 1
                    elif has_transcript:
                        result['date_sources']['transcript'] += 1
                    elif has_visual:
                        result['date_sources']['visual'] += 1
                        
                    # Collect unique dates
                    date_str = event['start_date'].get('display_date', '')
                    if date_str:
                        result['unique_dates'].add(date_str)
                else:
                    result['date_sources']['none'] += 1
        
        # Check the raw transcript data for date information
        transcript_path = output_dir / "transcript.json"
        if transcript_path.exists():
            with open(transcript_path) as f:
                transcript_data = json.load(f)
                
            # Check if dates were extracted in the enhanced schema
            if 'dates' in transcript_data:
                result['transcript_dates'] = transcript_data['dates']
            
            if 'visual_dates' in transcript_data:
                result['visual_dates'] = transcript_data['visual_dates']
        
        # Calculate success rate
        if result['total_events'] > 0:
            result['success_rate'] = (result['events_with_dates'] / result['total_events']) * 100
        else:
            result['success_rate'] = 0
            
        result['unique_dates'] = list(result['unique_dates'])
        result['success'] = True
        
        return result
    
    def generate_report(self):
        """Generate a comprehensive test report."""
        self.console.print("\n[bold green]═══ Gemini Date Extraction Test Report ═══[/bold green]\n")
        
        # Summary table
        table = Table(title="Test Results Summary", show_header=True, header_style="bold magenta")
        table.add_column("Video", style="cyan", no_wrap=True)
        table.add_column("Type", style="yellow")
        table.add_column("Total Events", justify="right")
        table.add_column("Events w/ Dates", justify="right")
        table.add_column("Success Rate", justify="right", style="green")
        table.add_column("Visual Dates", justify="right", style="blue")
        
        total_events = 0
        total_with_dates = 0
        
        for key, result in self.results.items():
            if result.get('success'):
                total_events += result['total_events']
                total_with_dates += result['events_with_dates']
                
                visual_count = result['date_sources']['visual'] + result['date_sources']['both']
                
                table.add_row(
                    result['video_info']['title'][:30] + '...',
                    result['video_info']['type'],
                    str(result['total_events']),
                    str(result['events_with_dates']),
                    f"{result['success_rate']:.1f}%",
                    str(visual_count)
                )
            else:
                table.add_row(
                    result['video_info']['title'][:30] + '...',
                    result['video_info']['type'],
                    "ERROR",
                    "-",
                    "-",
                    "-"
                )
        
        self.console.print(table)
        
        # Overall statistics
        if total_events > 0:
            overall_rate = (total_with_dates / total_events) * 100
            
            stats_panel = Panel(
                f"""[bold]Overall Performance:[/bold]
                
Total Events Processed: {total_events}
Events with Dates: {total_with_dates}
Overall Success Rate: [bold green]{overall_rate:.1f}%[/bold green]

[bold]Target Rates:[/bold]
News Content Target: 70-85%
Average Content Target: 40-50%
Previous Rate: 0.7%

[bold]Improvement:[/bold]
{overall_rate / 0.7:.0f}x improvement over previous implementation!
""",
                title="Performance Summary",
                expand=False
            )
            self.console.print(stats_panel)
        
        # Detailed breakdowns
        for key, result in self.results.items():
            if result.get('success') and result['total_events'] > 0:
                self.console.print(f"\n[bold cyan]Detailed Results: {result['video_info']['title']}[/bold cyan]")
                
                # Date source breakdown
                sources = result['date_sources']
                self.console.print(f"Date Sources:")
                self.console.print(f"  - Transcript only: {sources['transcript']}")
                self.console.print(f"  - Visual only: {sources['visual']}")
                self.console.print(f"  - Both sources: {sources['both']}")
                self.console.print(f"  - No date: {sources['none']}")
                
                # Sample events with dates
                if result['events_with_dates'] > 0:
                    self.console.print(f"\nSample Events with Dates:")
                    count = 0
                    for event in result['timeline_events']:
                        if event['has_date'] and count < 3:
                            self.console.print(f"  • {event['text']}")
                            self.console.print(f"    Date: {event['date'].get('display_date', 'Unknown')}")
                            count += 1
        
        # Save detailed report
        report_path = Path("output/gemini_date_test/test_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump({
                'test_date': datetime.now().isoformat(),
                'results': self.results,
                'summary': {
                    'total_events': total_events,
                    'events_with_dates': total_with_dates,
                    'overall_success_rate': (total_with_dates / total_events * 100) if total_events > 0 else 0
                }
            }, f, indent=2, default=str)
        
        self.console.print(f"\n[dim]Detailed report saved to: {report_path}[/dim]")


async def main():
    """Run the Gemini date extraction tests."""
    tester = GeminiDateExtractionTester()
    
    console.print(Panel(
        "[bold]Phase 4: Gemini Date Extraction Testing[/bold]\n\n"
        "Testing multimodal date extraction from video content.\n"
        "Target: 70-85% success rate for news content.",
        title="ClipScribe v2.18.19",
        expand=False
    ))
    
    # Test each video
    for video_key, video_info in TEST_VIDEOS.items():
        result = await tester.test_video(video_key, video_info)
        tester.results[video_key] = result
        
        # Quick feedback
        if result.get('success'):
            rate = result['success_rate']
            if rate >= 70:
                console.print(f"[bold green] Success rate: {rate:.1f}%[/bold green]")
            elif rate >= 40:
                console.print(f"[yellow] Success rate: {rate:.1f}%[/yellow]")
            else:
                console.print(f"[red] Success rate: {rate:.1f}%[/red]")
    
    # Generate comprehensive report
    tester.generate_report()
    
    console.print("\n[bold green]Testing complete![/bold green]")


if __name__ == "__main__":
    asyncio.run(main()) 