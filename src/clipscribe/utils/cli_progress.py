"""
Centralized manager for Rich-based CLI progress displays.

This module provides a single class, CliProgressManager, to handle the complexity
of rendering dynamic, multi-phase progress bars and tables using the Rich library.
It decouples the core application logic from the UI presentation, allowing for
cleaner, more maintainable, and more professional-looking CLI output.
"""

from typing import List, Dict, Optional
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.console import Console

class CliProgressManager:
    """Manages a rich.progress display for multi-phase tasks."""

    def __init__(self, phases: List[str], console: Optional[Console] = None):
        self.phases = phases
        self.console = console or Console()
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TextColumn("Cost: [green]${task.fields[cost]:.4f}"),
            console=self.console,
            transient=True
        )
        self.task_id = self.progress.add_task(
            "[cyan]Processing...",
            total=len(self.phases),
            cost=0.0
        )
        self.current_phase_index = 0

    def __enter__(self):
        self.progress.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.progress.stop()

    def update_phase(self, phase_name: str, status: str, cost: float = 0.0):
        """Update the progress bar to reflect a new phase or status."""
        if phase_name in self.phases:
            phase_index = self.phases.index(phase_name)
            # Advance progress only when moving to a new phase
            if phase_index > self.current_phase_index:
                self.progress.update(self.task_id, advance=(phase_index - self.current_phase_index))
                self.current_phase_index = phase_index

        # Update description and cost regardless
        self.progress.update(
            self.task_id,
            description=f"[cyan]{phase_name}: [yellow]{status}",
            cost=cost
        )

    def complete_phase(self, phase_name: str, cost: float):
        """Mark a phase as complete and advance the progress bar."""
        if phase_name in self.phases:
            phase_index = self.phases.index(phase_name)
            advance_amount = (phase_index - self.current_phase_index) + 1
            self.progress.update(self.task_id, advance=advance_amount)
            self.current_phase_index = phase_index + 1
        
        self.progress.update(
            self.task_id,
            description=f"[green]{phase_name}:  Complete",
            cost=cost
        )

    def log_error(self, phase_name: str, message: str):
        """Stop the progress bar and display an error message."""
        self.progress.update(
            self.task_id,
            description=f"[bold red]Error in {phase_name}: {message}",
            completed=len(self.phases) # Mark as complete to stop spinner
        )
        self.progress.stop()
