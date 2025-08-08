"""
app.py - The Textual TUI Application for ClipScribe

This module defines the main Textual application, using a robust,
message-passing architecture for communication between the UI and backend processes.
"""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, RichLog
from textual.containers import Container
from textual import work
from textual.message import Message

from typing import Optional

from ..retrievers import VideoIntelligenceRetriever
from ..config.settings import Settings

class TuiApp(App):
    """A Textual app to manage ClipScribe processing."""

    CSS_PATH = "styles.css"

    class LogMessage(Message):
        """A message containing a log string to be displayed."""
        def __init__(self, log_str: str) -> None:
            self.log_str = log_str
            super().__init__()

    class MetadataMessage(Message):
        """A message containing video metadata to be displayed."""
        def __init__(self, metadata: dict) -> None:
            self.metadata = metadata
            super().__init__()
            
    class ProgressMessage(Message):
        """A message to update the progress display."""
        def __init__(self, update_str: str) -> None:
            self.update_str = update_str
            super().__init__()

    def __init__(self, url: str, use_flash: bool, use_cache: bool, output_dir: str, mode: str, cookies_from_browser: Optional[str], debug: bool):
        super().__init__()
        self.url = url
        self.use_flash = use_flash
        self.use_cache = use_cache
        self.output_dir = output_dir
        self.mode = mode
        self.cookies_from_browser = cookies_from_browser
        self._debug = debug

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        with Container():
            with Container(id="left-pane"):
                yield Static("Initializing...", id="progress-panel")
                yield Static("Waiting for video...", id="metadata-panel")
            yield RichLog(wrap=True, highlight=True, markup=True, id="log")
        yield Footer()

    def on_mount(self) -> None:
        """Called when the app is mounted."""
        self.process_video()

    @work(exclusive=True)
    async def process_video(self) -> None:
        """The main processing logic, run in a worker to avoid blocking the UI."""
        
        def log_callback(message: str):
            self.post_message(self.LogMessage(message))

        def progress_callback(update_str: str):
            self.post_message(self.ProgressMessage(update_str))

        try:
            log_callback("Initializing settings...")
            settings = Settings()
            
            retriever = VideoIntelligenceRetriever(
                use_cache=self.use_cache,
                use_advanced_extraction=True,
                mode=self.mode,
                output_dir=self.output_dir,
                use_flash=self.use_flash,
                cookies_from_browser=self.cookies_from_browser,
                settings=settings,
                on_error=lambda component, error: log_callback(f"[bold red]ERROR[/bold red] [{component}]: {error}"),
                on_phase_log=lambda name, duration: log_callback(f" {name} [dim]({duration:.2f}s)[/dim]"),
                on_phase_start=lambda name, status: progress_callback(f"[bold]{name}[/bold]: {status}")
            )
            
            log_callback(f"Starting video processing for: {self.url}")
            result = await retriever.process_url(self.url)

            if result:
                self.post_message(self.MetadataMessage(result.metadata.dict()))
                log_callback("Saving output files...")
                saved_files = retriever.save_all_formats(result, self.output_dir)
                log_callback(f"Outputs saved to: {saved_files['directory']}")
                self.notify("Processing successful!", title="Status", severity="information")
            else:
                log_callback("[bold red]Processing failed. Please check the log for details.[/bold red]")
                self.notify("Processing failed.", title="Status", severity="error")

        except Exception as e:
            log_callback(f"[bold red]A fatal error occurred: {e}[/bold red]")
            self.notify(f"A fatal error occurred: {e}", title="Status", severity="error")

    def on_log_message(self, message: LogMessage) -> None:
        """Handle a log message from the worker."""
        log = self.query_one(RichLog)
        log.write(message.log_str)

    def on_metadata_message(self, message: MetadataMessage) -> None:
        """Handle a metadata message from the worker."""
        metadata_panel = self.query_one("#metadata-panel", Static)
        metadata_text = f"Title: {message.metadata.get('title', 'N/A')}\nChannel: {message.metadata.get('channel', 'N/A')}"
        metadata_panel.update(metadata_text)
        
    def on_progress_message(self, message: ProgressMessage) -> None:
        """Handle a progress update message from the worker."""
        progress_panel = self.query_one("#progress-panel", Static)
        progress_panel.update(message.update_str)
