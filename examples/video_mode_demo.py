#!/usr/bin/env python3
"""
Video Mode Demo - Shows the difference between audio and video processing modes.

This demonstrates when and why you'd want to use video mode vs audio mode.
"""

import asyncio
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


async def demo_mode_comparison():
    """Show the differences between processing modes."""
    
    console.print("\n[bold cyan]ClipScribe Processing Modes Comparison[/bold cyan]\n")
    
    # Create comparison table
    table = Table(title="When to Use Each Mode")
    table.add_column("Mode", style="cyan", width=12)
    table.add_column("Best For", style="green", width=30)
    table.add_column("Cost", style="yellow", width=15)
    table.add_column("Speed", style="magenta", width=12)
    table.add_column("Captures", style="white", width=30)
    
    # Audio mode
    table.add_row(
        "Audio",
        "• Podcasts\n• Interviews\n• News briefings\n• Meetings",
        "$0.002/min\n($0.12/hour)",
        "Fast\n(2-5 min/hr)",
        "• Speech\n• Speaker changes\n• Audio events"
    )
    
    # Video mode
    table.add_row(
        "Video",
        "• Tutorials\n• Presentations\n• Lectures\n• Code demos",
        "~$0.02/min\n($1.20/hour)",
        "Slower\n(5-10 min/hr)",
        "• Speech\n• On-screen text\n• Slides\n• Code\n• Diagrams\n• Visual elements"
    )
    
    # Auto mode
    table.add_row(
        "Auto",
        "• Unknown content\n• Mixed content\n• Let AI decide",
        "Varies",
        "Varies",
        "Depends on detected content type"
    )
    
    console.print(table)
    
    # Show example scenarios
    console.print("\n[bold]Example Scenarios:[/bold]\n")
    
    scenarios = [
        {
            "title": "🎙️ Joe Rogan Podcast",
            "url": "https://youtube.com/watch?v=podcast",
            "recommendation": "Audio Mode",
            "reason": "3-hour conversation, no visual content",
            "savings": "Save $3.24 vs video mode"
        },
        {
            "title": "💻 Python Tutorial with Live Coding",
            "url": "https://youtube.com/watch?v=tutorial",
            "recommendation": "Video Mode",
            "reason": "Code on screen, IDE demonstration",
            "benefit": "Captures actual code snippets"
        },
        {
            "title": "📊 Business Presentation",
            "url": "https://youtube.com/watch?v=presentation",
            "recommendation": "Video Mode",
            "reason": "Slides with charts and data",
            "benefit": "Extracts slide content and data"
        },
        {
            "title": "📰 Pentagon Press Briefing",
            "url": "https://youtube.com/watch?v=668oKOJ43_E",
            "recommendation": "Audio Mode",
            "reason": "Talking head, no slides",
            "savings": "Got 193 relationships from audio alone!"
        }
    ]
    
    for scenario in scenarios:
        panel = Panel(
            f"[yellow]Recommended:[/yellow] {scenario['recommendation']}\n"
            f"[dim]Reason:[/dim] {scenario['reason']}\n"
            f"[green]{scenario.get('savings', scenario.get('benefit', ''))}[/green]",
            title=scenario['title'],
            border_style="blue"
        )
        console.print(panel)
        console.print()
    
    # Show sample outputs
    console.print("[bold]Sample Output Differences:[/bold]\n")
    
    # Audio mode output
    audio_output = Panel(
        """[Transcript]
"Today we'll learn about Python decorators. A decorator is a 
function that takes another function and extends its behavior 
without explicitly modifying it..."

[Entities]
- Python (TECHNOLOGY)
- decorators (CONCEPT)

[Key Points]
- Decorators extend function behavior
- Use @ syntax for decoration""",
        title="Audio Mode Output",
        border_style="green"
    )
    
    # Video mode output
    video_output = Panel(
        """[Transcript with Visual Elements]
"Today we'll learn about Python decorators. [VISUAL: Code editor 
opens showing decorator example]

[CODE ON SCREEN]:
@timer_decorator
def slow_function():
    time.sleep(1)
    return "Done"

A decorator is a function that takes another function..."

[Visual Elements Detected]
- IDE: VS Code with Python extension
- Code snippets: 3 decorator examples
- Terminal output showing execution times

[Entities]
- Python (TECHNOLOGY)
- decorators (CONCEPT)  
- VS Code (SOFTWARE)
- timer_decorator (CODE_ELEMENT)
- slow_function (CODE_ELEMENT)""",
        title="Video Mode Output",
        border_style="yellow"
    )
    
    console.print(audio_output)
    console.print()
    console.print(video_output)
    
    # Cost calculator
    console.print("\n[bold]Quick Cost Calculator:[/bold]\n")
    
    durations = [10, 30, 60, 120]  # minutes
    
    calc_table = Table(title="Processing Costs by Duration")
    calc_table.add_column("Duration", style="cyan")
    calc_table.add_column("Audio Mode", style="green")
    calc_table.add_column("Video Mode", style="yellow")
    calc_table.add_column("Savings", style="magenta")
    
    for mins in durations:
        audio_cost = mins * 0.002
        video_cost = mins * 0.02
        savings = video_cost - audio_cost
        
        calc_table.add_row(
            f"{mins} min",
            f"${audio_cost:.3f}",
            f"${video_cost:.2f}",
            f"${savings:.2f} ({int(savings/audio_cost*100)}% more)"
        )
    
    console.print(calc_table)


async def main():
    """Run the demo."""
    console.print("[bold]ClipScribe Video Mode Demo[/bold]")
    console.print("[dim]Understanding when to use each processing mode[/dim]\n")
    
    await demo_mode_comparison()
    
    console.print("\n[bold green]Ready to try it?[/bold green]")
    console.print("\n[cyan]Examples:[/cyan]")
    console.print("clipscribe transcribe 'URL' --mode audio    # Fast & cheap")
    console.print("clipscribe transcribe 'URL' --mode video    # Full analysis")
    console.print("clipscribe transcribe 'URL' --mode auto     # Let AI decide")
    
    console.print("\n[dim]Pro tip: Start with audio mode. If you need visual content, run video mode.[/dim]")


if __name__ == "__main__":
    asyncio.run(main()) 