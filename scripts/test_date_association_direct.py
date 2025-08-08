#!/usr/bin/env python3
"""
A simple, direct test script for the date association algorithm.
This script has minimal imports to avoid circular dependency issues.
"""

import json
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from dateutil import parser
from datetime import datetime

# Manually add the project src to the path
import sys
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from clipscribe.timeline.gemini_date_processor import GeminiDateProcessor
from clipscribe.models import ExtractedDate
from clipscribe.timeline.models import TemporalEvent

console = Console()
TEST_FILE = "output/gemini_date_test_simple/20250702_youtube_6ZVj1_SE4Mo/6ZVj1_SE4Mo.json"

def run_direct_test():
    console.print(Panel("[bold yellow]Direct Date Association Test[/bold yellow]"))
    
    # 1. Load the data
    try:
        with open(TEST_FILE, 'r') as f:
            data = json.load(f)
        console.print(f" Loaded test data from [cyan]{TEST_FILE}[/cyan]")
    except FileNotFoundError:
        console.print(f"[red]Error: Test file not found at {TEST_FILE}[/red]")
        console.print("Please run `poetry run python scripts/test_gemini_date_extraction_simple.py` first.")
        return

    # 2. Manually extract the data we need
    dates_raw = data.get('dates', [])
    events_raw = data.get('timeline_v2', {}).get('events', [])

    if not dates_raw or not events_raw:
        console.print("[red]Error: Dates or timeline events not found in the JSON file.[/red]")
        return

    extracted_dates = [ExtractedDate(**d) for d in dates_raw]
    
    temporal_events = []
    for event_dict in events_raw:
        try:
            # The JSON has all the fields, so we can directly parse it
            event_dict['date_source'] = 'pending_extraction'
            event = TemporalEvent(**event_dict)
            temporal_events.append(event)
        except Exception as e:
            pass # Ignore parsing errors for this direct test

    console.print(f"Testing with [yellow]{len(extracted_dates)}[/yellow] dates and [yellow]{len(temporal_events)}[/yellow] events.")

    # 3. Directly call the processor
    processor = GeminiDateProcessor()
    dated_events = processor.associate_dates_with_events(
        temporal_events,
        extracted_dates,
        window_seconds=60.0
    )

    # 4. Report the results
    total_events = len(dated_events)
    events_with_dates = sum(1 for e in dated_events if e.date_source != 'pending_extraction')
    success_rate = (events_with_dates / total_events) * 100 if total_events > 0 else 0

    panel_content = (
        f"Total Events: [bold cyan]{total_events}[/bold cyan]\n"
        f"Events Associated: [bold green]{events_with_dates}[/bold green]\n"
        f"Success Rate: [bold magenta]{success_rate:.2f}%[/bold magenta]"
    )
    console.print(Panel(panel_content, title="Date Association Results", expand=False))

    if events_with_dates > 0:
        table = Table(title="Dated Events")
        table.add_column("Timestamp", style="cyan")
        table.add_column("Event Description", style="white")
        table.add_column("Associated Date", style="yellow")
        for event in dated_events:
            if event.date_source != 'pending_extraction':
                ts = list(event.video_timestamps.values())[0] if event.video_timestamps else "N/A"
                table.add_row(
                    f"{ts}s",
                    event.description[:80] + "...",
                    event.date.strftime('%Y-%m-%d')
                )
        console.print(table)


if __name__ == "__main__":
    run_direct_test() 