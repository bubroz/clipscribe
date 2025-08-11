"""
Progress indicators and console output utilities using Rich.

Provides beautiful progress bars, status indicators, and formatted console output
for ClipScribe operations.
"""

import time
from contextlib import contextmanager
from typing import Any, Dict, Optional, Iterator
from datetime import datetime, timedelta

from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeRemainingColumn,
    TimeElapsedColumn,
    MofNCompleteColumn,
    TaskID,
)
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

# Global console instance
console = Console()


class ClipScribeProgress:
    """Main progress tracking class for ClipScribe operations."""

    def __init__(self):
        self.console = console
        self.current_cost = 0.0
        self.start_time = None
        self.phase_times = {}
        self.current_phase = None

    @contextmanager
    def video_processing(self, url: str) -> Iterator[Dict[str, Any]]:
        """Context manager for overall video processing progress."""
        self.start_time = time.time()
        self.current_cost = 0.0
        self.phase_times = {}

        # Defensive guard: check for existing Live context
        if getattr(self.console, "_live", None) is not None:
            raise RuntimeError(
                "A Rich Live display is already active on this console. Only one Live/progress context may be active at a time. Use the provided progress state instead of creating a new one."
            )

        # Simple header
        self.console.print("\n")
        self.console.print(
            Panel(
                f"[bold cyan]Processing Video:[/bold cyan] {url}",
                box=box.ROUNDED,
                padding=(0, 1),
            )
        )

        # Create a simple progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console,
            transient=True,
        ) as progress:
            # Main progress task
            main_task = progress.add_task("Overall Progress", total=7)

            # Progress tracking state
            state = {
                "progress": progress,
                "main_task": main_task,
                "current_phase": None,
                "phases_completed": 0,
                "total_phases": 7,
            }

            yield state

        # Show completion summary
        self._show_completion_summary()

    def update_phase(self, state: Dict[str, Any], phase: str, description: str):
        """Update the current processing phase."""
        # Record timing for previous phase
        if self.current_phase:
            self.phase_times[self.current_phase] = time.time() - self.start_time

        self.current_phase = phase

        # Update progress bar
        if state.get("progress") and state.get("main_task") is not None:
            state["phases_completed"] += 1
            state["progress"].update(state["main_task"], advance=1, description=description)

        # Also log the phase change
        self.log_info(description)

    def update_cost(self, amount: float):
        """Update the running cost total."""
        self.current_cost += amount

    def _show_completion_summary(self):
        """Show a summary panel when processing completes."""
        if not self.start_time:
            return

        total_time = time.time() - self.start_time

        # Create summary table
        summary = Table(
            title="Processing Complete",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan",
        )

        summary.add_column("Metric", style="cyan")
        summary.add_column("Value", style="white")

        # Total time
        summary.add_row("Total Time", str(timedelta(seconds=int(total_time))))

        # Cost with emoji
        cost_emoji = "" if self.current_cost < 0.10 else "" if self.current_cost < 1.00 else ""
        summary.add_row("Total Cost", f"{cost_emoji} ${self.current_cost:.4f}")

        # Phase breakdown if available
        if self.phase_times:
            summary.add_row("", "")  # Spacer
            summary.add_row("[bold]Phase Times[/bold]", "")

            for phase, elapsed in self.phase_times.items():
                summary.add_row(f"  {phase}", f"{elapsed:.1f}s")

        self.console.print("\n")
        self.console.print(summary)
        self.console.print("\n")

    @contextmanager
    def subtask_progress(self, description: str, total: Optional[int] = None):
        """Create a progress bar for a subtask."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold green]{task.description}"),
            BarColumn() if total else TextColumn(""),
            MofNCompleteColumn() if total else TextColumn(""),
            TimeElapsedColumn(),
            console=self.console,
            transient=True,
        ) as progress:
            if total:
                task_id = progress.add_task(description, total=total)
            else:
                task_id = progress.add_task(description)

            yield {"progress": progress, "task_id": task_id}

    def log_info(self, message: str, style: str = "info"):
        """Log an informational message with styling."""
        self.console.print(f"[{style}]ℹ {message}[/{style}]")

    def log_success(self, message: str):
        """Log a success message."""
        self.console.print(f"[green] {message}[/green]")

    def log_warning(self, message: str):
        """Log a warning message."""
        self.console.print(f"[yellow] {message}[/yellow]")

    def log_error(self, message: str):
        """Log an error message."""
        self.console.print(f"[red] {message}[/red]")

    def show_extraction_stats(self, entities: list, relationships: list):
        """Display extraction statistics in a nice table."""
        table = Table(
            title="Extraction Results",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan",
        )

        table.add_column("Category", style="cyan")
        table.add_column("Count", style="white", justify="right")

        # Entity breakdown by type
        entity_types = {}
        for entity in entities:
            # Handle both dict and Pydantic Entity objects
            if hasattr(entity, "type"):
                etype = entity.type
            else:
                etype = entity.get("type", "UNKNOWN")
            entity_types[etype] = entity_types.get(etype, 0) + 1

        table.add_row("Total Entities", str(len(entities)))
        for etype, count in sorted(entity_types.items()):
            table.add_row(f"  {etype}", str(count))

        table.add_row("", "")  # Spacer
        table.add_row("Total Relationships", str(len(relationships)))

        self.console.print("\n")
        self.console.print(table)


# Global progress instance
progress_tracker = ClipScribeProgress()
