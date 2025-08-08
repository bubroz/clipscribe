#!/usr/bin/env python3
"""
Test script for tuning the Date Association algorithm in GeminiDateProcessor.

This script loads a pre-processed video intelligence file and re-runs the
date association logic to allow for rapid testing and tuning of the matching
algorithm to improve the association success rate.

Target: >50% association rate for news content.
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from dateutil import parser

from clipscribe.timeline.gemini_date_processor import GeminiDateProcessor
from clipscribe.models import ExtractedDate
from clipscribe.timeline.models import TemporalEvent, TimelineEvent

console = Console()

# Pre-processed file from our last successful run
TEST_FILE = "output/gemini_date_test_simple/20250702_youtube_6ZVj1_SE4Mo/6ZVj1_SE4Mo.json"

class DateAssociationTester:
    """Tests and tunes the date association logic."""

    def __init__(self, test_file_path: str):
        self.test_file_path = Path(test_file_path)
        if not self.test_file_path.exists():
            raise FileNotFoundError(f"Test file not found: {self.test_file_path}")
        
        self.video_intelligence = self._load_test_data()
        self.processor = GeminiDateProcessor()

    def _load_test_data(self) -> Dict[str, Any]:
        """Loads the JSON data from the test file."""
        console.print(f"Loading test data from [cyan]{self.test_file_path}[/cyan]...")
        with open(self.test_file_path, 'r') as f:
            data = json.load(f)
        console.print(" Test data loaded.")
        return data

    async def run_test(self, window_seconds: float = 60.0) -> Dict[str, Any]:
        """Runs the date association test."""
        
        # Extract dates and events from the loaded data
        extracted_dates_raw = self.video_intelligence.get('dates', [])
        if not extracted_dates_raw:
             console.print("[red]No dates found in the test file.[/red]")
             return {"total_events": 0, "events_with_dates": 0, "success_rate": 0, "dated_events": []}
        extracted_dates = [ExtractedDate(**d) for d in extracted_dates_raw]

        # The timeline_v2 key might be missing if processing failed
        timeline_v2_data = self.video_intelligence.get('timeline_v2', {})
        if not timeline_v2_data:
            console.print("[red]No timeline_v2 data found in the test file.[/red]")
            return {"total_events": 0, "events_with_dates": 0, "success_rate": 0, "dated_events": []}
            
        timeline_events_raw = timeline_v2_data.get('events', [])
        
        # This is a limitation of testing from a JSON file.
        temporal_events = []
        for event_dict in timeline_events_raw:
            try:
                # The 'date' field from JSON is already parsed as a datetime string
                # The model expects a datetime object.
                timestamp_obj = parser.parse(event_dict.get('date')) if event_dict.get('date') else datetime.now()

                event = TemporalEvent(
                    event_id=event_dict.get('event_id', 'evt_temp_id'),
                    timestamp=timestamp_obj,
                    description=event_dict.get('description', ''),
                    source_video_id=self.video_intelligence.get('metadata', {}).get('video_id', 'unknown'),
                    source_video_title=self.video_intelligence.get('metadata', {}).get('title', 'Unknown Title'),
                    video_timestamp_seconds=int(list(event_dict.get('video_timestamps', {}).values())[0] if event_dict.get('video_timestamps') else 0),
                    involved_entities=event_dict.get('involved_entities', []),
                    confidence=event_dict.get('confidence', 0.8),
                    # Reset date_source for re-testing
                    date_source='pending_extraction',
                    # Pass other required fields with defaults
                    content_hash=event_dict.get('content_hash', ''),
                    date_precision=event_dict.get('date_precision', 'unknown'),
                    date_confidence=event_dict.get('date_confidence', 0.0),
                    extracted_date_text=event_dict.get('extracted_date_text', ''),
                    event_type=event_dict.get('event_type', 'inferred'),
                    extraction_method=event_dict.get('extraction_method', 'unknown'),
                )
                event.video_timestamps = event_dict.get('video_timestamps', {})
                temporal_events.append(event)
            except Exception as e:
                console.log(f"Skipping event due to parsing error: {e}")
                pass


        if not extracted_dates:
            console.print("[red]No dates found in the test file.[/red]")
            return {}
        
        if not temporal_events:
            console.print("[red]No timeline events could be parsed from the test file.[/red]")
            return {"total_events": 0, "events_with_dates": 0, "success_rate": 0, "dated_events": []}

        console.print(f"Testing with [yellow]{len(extracted_dates)}[/yellow] dates and [yellow]{len(temporal_events)}[/yellow] events...")
        console.print(f"Association window: [blue]{window_seconds}s[/blue]")

        # Run the association logic
        dated_events = self.processor.associate_dates_with_events(
            temporal_events,
            extracted_dates,
            window_seconds=window_seconds
        )
        
        # Analyze the results
        total_events = len(dated_events)
        events_with_dates = sum(1 for e in dated_events if e.date_source != 'pending_extraction')
        success_rate = (events_with_dates / total_events) * 100 if total_events > 0 else 0
        
        results = {
            "total_events": total_events,
            "events_with_dates": events_with_dates,
            "success_rate": success_rate,
            "dated_events": [e for e in dated_events if e.date_source != 'pending_extraction']
        }
        
        return results

    def display_results(self, results: Dict[str, Any]):
        """Displays the test results in a nice format."""
        
        panel_content = (
            f"Total Events: [bold cyan]{results['total_events']}[/bold cyan]\n"
            f"Events Associated: [bold green]{results['events_with_dates']}[/bold green]\n"
            f"Success Rate: [bold magenta]{results['success_rate']:.2f}%[/bold magenta]"
        )
        
        console.print(Panel(panel_content, title="Date Association Results", expand=False))
        
        if results['dated_events']:
            table = Table(title="Sample Dated Events")
            table.add_column("Timestamp", style="cyan")
            table.add_column("Event Description", style="white")
            table.add_column("Associated Date", style="yellow")
            table.add_column("Source", style="green")

            for event in results['dated_events'][:10]:
                ts = list(event.video_timestamps.values())[0] if event.video_timestamps else "N/A"
                table.add_row(
                    f"{ts}s",
                    event.description[:80] + "...",
                    event.date.strftime('%Y-%m-%d') if event.date else "N/A",
                    event.date_source
                )
            console.print(table)

async def main():
    console.print(Panel("[bold]Date Association Algorithm Tuning Script[/bold]", expand=False))
    try:
        tester = DateAssociationTester(TEST_FILE)
        results = await tester.run_test()
        tester.display_results(results)
    except FileNotFoundError as e:
        console.print(f"[bold red]ERROR: {e}[/bold red]")
        console.print("Please ensure you have run a video process first to generate the necessary file.")

if __name__ == "__main__":
    asyncio.run(main()) 