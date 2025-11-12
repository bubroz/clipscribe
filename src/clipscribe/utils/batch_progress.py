"""
Advanced progress indicators for batch processing.
"""

import asyncio
from typing import Dict, Optional

from rich import box
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TaskID, TextColumn, TimeElapsedColumn


class BatchProgress:
    """Manages a live-updating display for concurrent batch processing."""

    def __init__(self):
        self.console = Console()
        self.layout = self._create_layout()
        self.overall_task: Optional[TaskID] = None
        self.video_tasks: Dict[str, TaskID] = {}
        self.overall_progress = Progress(
            TextColumn("[bold blue]Overall Research Progress"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
        )
        self.video_progress = Progress(
            TextColumn("  • {task.description}", justify="left"),
            BarColumn(),
        )

    def _create_layout(self) -> Layout:
        """Creates the layout for the live display."""
        layout = Layout()
        layout.split(
            Layout(name="header", size=3),
            Layout(name="overall", size=3),
            Layout(name="videos"),
        )
        layout["header"].update(
            Panel("[bold cyan]ClipScribe Research Mode[/bold cyan]", box=box.ROUNDED)
        )
        layout["overall"].update(self.overall_progress)
        layout["videos"].update(
            Panel(self.video_progress, title="[bold]Active Videos[/bold]", border_style="green")
        )
        return layout

    def add_overall_task(self, total: int):
        """Adds the main progress bar for the entire batch."""
        self.overall_task = self.overall_progress.add_task("Processing videos...", total=total)

    def add_video_task(self, url: str) -> TaskID:
        """Adds a new task for an individual video."""
        task_id = self.video_progress.add_task(f"Initializing {url[-11:]}...", total=100)
        self.video_tasks[url] = task_id
        return task_id

    def update_video_progress(self, url: str, advance: float, description: str):
        """Updates the progress for a specific video."""
        task_id = self.video_tasks.get(url)
        if task_id is not None:
            # Assuming 4 main steps: download, transcribe, extract, save
            # The hook sends progress from 0-100, so we advance by 1/4th (25)
            # We don't use the 'advance' parameter directly to avoid overshooting
            current_progress = self.video_progress._tasks[task_id].completed
            new_progress = current_progress + 25
            self.video_progress.update(
                task_id, completed=min(new_progress, 99), description=description
            )

    def complete_video_task(self, url: str):
        """Marks a video task as complete and advances the overall progress."""
        task_id = self.video_tasks.get(url)
        if task_id is not None:
            self.video_progress.update(task_id, completed=100, description="[green] Done[/green]")
        if self.overall_task is not None:
            self.overall_progress.update(self.overall_task, advance=1)

    def fail_video_task(self, url: str, reason: str = "Failed"):
        """Marks a video task as failed and advances the overall progress."""
        task_id = self.video_tasks.get(url)
        if task_id is not None:
            # Truncate reason to fit in the console
            short_reason = (reason[:50] + "...") if len(reason) > 50 else reason
            self.video_progress.update(
                task_id, completed=100, description=f"[red] {short_reason}[/red]"
            )
        if self.overall_task is not None:
            self.overall_progress.update(self.overall_task, advance=1)

    async def __aenter__(self):
        """Starts the live display."""
        self.live = Live(self.layout, console=self.console, screen=True, redirect_stderr=False)
        self.live.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Stops the live display."""
        await asyncio.sleep(0.5)  # Give a moment to see completion
        self.live.stop()
