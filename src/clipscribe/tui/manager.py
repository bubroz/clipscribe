"""
manager.py - The Deco-Futurist TUI Manager for ClipScribe

This module contains the TuiManager, a sophisticated class responsible for
rendering the entire terminal user interface using the rich library's Layout
and Panel features. It creates a stable, aesthetically pleasing, and highly
informative display that separates UI rendering from backend processing.
"""

import logging
from typing import List, Optional

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.logging import RichHandler
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich import box

from ..version import __version__

class TuiManager:
    """Manages the Deco-Futurist TUI layout and progress display."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.progress = self._create_progress_bar()
        self.log_handler = RichHandler(show_path=False, console=self.console)
        self.log_handler.setFormatter(logging.Formatter("%(message)s"))
        
        # Capture logs
        logging.getLogger().addHandler(self.log_handler)
        
        self.layout = self._create_layout()
        self.live = Live(self.layout, screen=True, console=self.console, transient=True)

    def _create_layout(self) -> Layout:
        """Creates the rich.Layout for the TUI."""
        layout = Layout(name="root")
        layout.split(
            Layout(name="header", size=3),
            Layout(ratio=1, name="main"),
            Layout(size=1, name="footer"),
        )
        layout["main"].split_row(
            Layout(name="side"), Layout(name="body", ratio=2)
        )
        layout["side"].split(Layout(name="progress_panel"))
        
        # Header Panel
        header_panel = Panel(
            f"[bold cyan]CLIPSCRIBE v{__version__}[/] - AI Video Intelligence Engine",
            box=box.HEAVY,
            expand=True,
            style="bold white on black"
        )
        layout["header"].update(header_panel)
        
        # Progress Panel
        layout["progress_panel"].update(self.progress)
        
        # Log Panel
        log_panel = Panel(
            self.log_handler.renderables,
            title="[bold yellow]Processing Log[/]",
            box=box.ROUNDED,
            border_style="dim"
        )
        layout["body"].update(log_panel)

        # Footer
        layout["footer"].update("[dim]Press Ctrl+C to exit[/]")

        return layout
    
    def _create_progress_bar(self) -> Progress:
        """Creates a rich.progress.Progress instance with our custom columns."""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TextColumn("Cost: [green]${task.fields[cost]:.4f}"),
            console=self.console,
        )

    def __enter__(self):
        self.live.start(refresh=True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.live.stop()

    def get_progress_callback(self):
        """Returns a callback function to be used by the backend."""
        # Create a task for the overall process
        task_id = self.progress.add_task("Initializing...", total=100, cost=0.0)

        def callback(status: str, progress: int, cost: float):
            """Updates the progress bar."""
            self.progress.update(
                task_id,
                description=status,
                completed=progress,
                cost=cost
            )
        return callback
