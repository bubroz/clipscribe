"""
Station10 Intelligence Dashboard v2 - Redesigned with Video Player Concept

Professional TUI for intelligence analysts with:
- Video player area (timeline, topic tracking)
- Chronological topic flow (sorted by time, not relevance)
- Entity browser with type switching
- Details panel for selected items
- Grokipedia integration ready
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, ListView, ListItem, Label
from textual.binding import Binding
from textual.reactive import reactive
from pathlib import Path
import sqlite3
from typing import List, Dict, Optional
import webbrowser


class VideoPlayerArea(Static):
    """
    Video/audio player area showing timeline and current position.
    
    Displays:
    - Video title and duration
    - Progress bar with topic markers
    - Current topic indicator
    - Playback controls (if audio present)
    """
    
    video_title: reactive[str] = reactive("All-In Podcast")
    video_duration: reactive[str] = reactive("88min")
    current_position: reactive[str] = reactive("00:00:00")
    current_topic: reactive[str] = reactive("Israel-Hamas Ceasefire")
    
    def render(self) -> str:
        """Render video player area."""
        # Create timeline bar (simplified for now)
        timeline = "━" * 50
        
        return f"""[bold]{self.video_title}[/bold] ({self.video_duration})
🎧 Position: [cyan]{self.current_position}[/cyan] {timeline}
Currently: [yellow]{self.current_topic}[/yellow]

Controls: [p]lay [space]pause [j/k]topics [c]opy timestamp"""


class TopicsList(ListView):
    """
    Topics list in chronological order (sorted by time range).
    
    Shows:
    - Time range [MM:SS-MM:SS]
    - Topic name
    - Relevance bar (secondary)
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "Topics (Timeline Order - ↑/↓ navigate, Enter select)"
        self.topics_data = []


class EntitiesList(ListView):
    """
    Entities list grouped by type.
    
    Shows:
    - Entity name
    - Confidence score
    - Evidence quote
    - [G] if Grokipedia link exists
    """
    
    current_type: reactive[str] = reactive("PERSON")
    entities_data: reactive[List[Dict]] = reactive([])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "Entities: PERSON (←/→ change type)"
        self.entities_data = []


class DetailsPanel(Static):
    """
    Details panel showing context for selected item.
    
    Shows:
    - Selected topic or entity details
    - Related entities (for topics)
    - Grokipedia links
    - Actions (copy, open link)
    """
    
    selected_item: reactive[Optional[Dict]] = reactive(None)
    selected_type: reactive[str] = reactive("topic")  # "topic" or "entity"
    
    def render(self) -> str:
        """Render details for selected item."""
        if not self.selected_item:
            return "[dim]Select a topic or entity to see details[/dim]"
        
        if self.selected_type == "topic":
            return self._render_topic_details()
        else:
            return self._render_entity_details()
    
    def _render_topic_details(self) -> str:
        """Render topic details."""
        topic = self.selected_item
        name = topic.get('name', 'Unknown')
        time_range = topic.get('time_range', '')
        relevance = topic.get('relevance', 0.0)
        
        lines = [
            f"[bold]Selected Topic:[/bold] {name}",
            "",
            f"Time Range: [cyan]{time_range}[/cyan]",
            f"Relevance: {relevance:.2f} ({'High' if relevance >= 0.9 else 'Medium' if relevance >= 0.8 else 'Low'})",
            f"Type: PoliticalEvent",
            "",
            "[dim]Press 'c' to copy timestamp[/dim]"
        ]
        
        return "\n".join(lines)
    
    def _render_entity_details(self) -> str:
        """Render entity details."""
        entity = self.selected_item
        name = entity.get('name', 'Unknown')
        entity_type = entity.get('type', 'UNKNOWN')
        confidence = entity.get('confidence', 0.0)
        evidence = entity.get('evidence', '')
        
        # Check if Grokipedia link (placeholder for now)
        has_grokipedia = entity_type in ['PERSON', 'ORG', 'GPE']
        grok_indicator = "[green][G][/green]" if has_grokipedia else ""
        
        lines = [
            f"[bold]Selected Entity:[/bold] {name} {grok_indicator}",
            "",
            f"Type: {entity_type}",
            f"Confidence: {confidence:.2f}",
            "",
            f"[bold]Evidence:[/bold]",
            f"[italic]\"{evidence[:200]}...\"[/italic]" if len(evidence) > 200 else f"[italic]\"{evidence}\"[/italic]",
        ]
        
        if has_grokipedia:
            lines.append("")
            lines.append("[dim]Press 'g' to open Grokipedia page[/dim]")
        
        return "\n".join(lines)


class IntelligenceDashboard(App):
    """
    Station10 Intelligence Dashboard - Redesigned for video intelligence analysis.
    
    Layout:
    - Top (20%): Video player area with timeline
    - Middle Left (50%): Topics in chronological order
    - Middle Right (50%): Entities by type
    - Bottom (20%): Details panel for selected item
    
    Keyboard:
    - ↑/↓: Navigate lists
    - ←/→: Switch entity type
    - Tab: Switch panel focus
    - Enter: Select item (show details)
    - j/k: Jump between topics
    - c: Copy timestamp
    - g: Open Grokipedia
    - q: Quit
    """
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #player {
        height: 20%;
        border: solid $primary;
        padding: 1;
    }
    
    #topics {
        width: 1fr;
        height: 60%;
        border: solid $accent;
    }
    
    #entities {
        width: 1fr;
        height: 60%;
        border: solid $secondary;
    }
    
    #details {
        height: 20%;
        border: solid $warning;
        padding: 1;
    }
    
    ListView {
        padding: 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("left", "prev_type", "Prev Type"),
        Binding("right", "next_type", "Next Type"),
        Binding("j", "prev_topic", "Prev Topic"),
        Binding("k", "next_topic", "Next Topic"),
        Binding("c", "copy_timestamp", "Copy"),
        Binding("g", "open_grokipedia", "Grokipedia"),
    ]
    
    current_video_id: reactive[str] = reactive("P-2")
    current_entity_type: reactive[str] = reactive("PERSON")
    selected_topic: reactive[Optional[Dict]] = reactive(None)
    selected_entity: reactive[Optional[Dict]] = reactive(None)
    entity_types: reactive[List[str]] = reactive([])
    
    def compose(self) -> ComposeResult:
        """Create dashboard layout."""
        yield Header(show_clock=True)
        
        # Top: Video player area
        yield VideoPlayerArea(id="player")
        
        # Middle: Topics (left) + Entities (right)
        with Horizontal():
            yield TopicsList(id="topics")
            yield EntitiesList(id="entities")
        
        # Bottom: Details panel
        yield DetailsPanel(id="details")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Load data on startup."""
        self.title = "Station10 Intelligence Dashboard"
        self.sub_title = "Video Intelligence Analysis Platform"
        
        self.load_topics()
        self.load_entity_types()
        self.load_entities()
    
    def load_topics(self):
        """Load topics in CHRONOLOGICAL order (sorted by time_range)."""
        db_path = Path("data/station10.db")
        if not db_path.exists():
            return
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get topics sorted by time_range (chronological)
        cursor.execute("""
            SELECT name, relevance, time_range, schema_type
            FROM topics
            WHERE video_id = ?
            ORDER BY time_range ASC
        """, (self.current_video_id,))
        
        topics_list = self.query_one("#topics", TopicsList)
        topics_list.clear()
        topics_list.topics_data = []
        
        for row in cursor.fetchall():
            name = row[0]
            relevance = row[1]
            time_range = row[2] or "Unknown"
            
            # Create relevance bar (secondary, on right)
            bar_length = 10
            filled = int(relevance * bar_length)
            bar = "█" * filled + "░" * (bar_length - filled)
            
            # Format: [TIME] Name ... relevance bar
            label_text = f"[cyan]{time_range:15}[/cyan] {name:40} [{bar}] {relevance:.2f}"
            
            topics_list.append(ListItem(Label(label_text)))
            topics_list.topics_data.append({
                'name': name,
                'relevance': relevance,
                'time_range': time_range
            })
        
        conn.close()
    
    def load_entity_types(self):
        """Get all entity types for current video."""
        db_path = Path("data/station10.db")
        if not db_path.exists():
            return
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT type
            FROM entities
            WHERE video_id = ?
            ORDER BY type
        """, (self.current_video_id,))
        
        self.entity_types = [row[0] for row in cursor.fetchall()]
        conn.close()
    
    def load_entities(self):
        """Load entities of current type with Grokipedia links."""
        db_path = Path("data/station10.db")
        if not db_path.exists():
            return
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get count for this type
        cursor.execute("""
            SELECT COUNT(*) FROM entities
            WHERE video_id = ? AND type = ?
        """, (self.current_video_id, self.current_entity_type))
        count = cursor.fetchone()[0]
        
        # Get entities with Grokipedia URLs
        cursor.execute("""
            SELECT name, type, confidence, evidence, grokipedia_url
            FROM entities
            WHERE video_id = ? AND type = ?
            ORDER BY confidence DESC
            LIMIT 15
        """, (self.current_video_id, self.current_entity_type))
        
        entities_list = self.query_one("#entities", EntitiesList)
        entities_list.clear()
        entities_list.border_title = f"Entities: {self.current_entity_type} ({count} total) [←/→ change]"
        entities_list.entities_data = []
        
        for row in cursor.fetchall():
            name = row[0]
            entity_type = row[1]
            conf = row[2]
            evidence = row[3] or ""
            grokipedia_url = row[4]
            
            # Truncate evidence
            evidence_short = evidence[:50] + "..." if len(evidence) > 50 else evidence
            
            # Real Grokipedia marker (from database, not guessed)
            grok_marker = "[green][G][/green]" if grokipedia_url else ""
            
            label_text = f"{name} ({conf:.2f}) {grok_marker}\n  [dim italic]\"{evidence_short}\"[/dim italic]"
            entities_list.append(ListItem(Label(label_text)))
            
            # Store entity data for actions (Grokipedia open, details)
            entities_list.entities_data.append({
                'name': name,
                'type': entity_type,
                'confidence': conf,
                'evidence': evidence,
                'grokipedia_url': grokipedia_url
            })
        
        conn.close()
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle item selection in any list."""
        # Determine which list was selected
        if event.list_view.id == "topics":
            # Get selected topic data
            index = event.list_view.index
            topics_list = self.query_one("#topics", TopicsList)
            if index < len(topics_list.topics_data):
                self.selected_topic = topics_list.topics_data[index]
                self.selected_entity = None
                
                # Update details panel
                details = self.query_one("#details", DetailsPanel)
                details.selected_item = self.selected_topic
                details.selected_type = "topic"
                details.refresh()
    
    def action_next_type(self) -> None:
        """Switch to next entity type."""
        if not self.entity_types:
            return
        
        try:
            current_idx = self.entity_types.index(self.current_entity_type)
            next_idx = (current_idx + 1) % len(self.entity_types)
            self.current_entity_type = self.entity_types[next_idx]
        except ValueError:
            self.current_entity_type = self.entity_types[0]
        
        self.load_entities()
    
    def action_prev_type(self) -> None:
        """Switch to previous entity type."""
        if not self.entity_types:
            return
        
        try:
            current_idx = self.entity_types.index(self.current_entity_type)
            prev_idx = (current_idx - 1) % len(self.entity_types)
            self.current_entity_type = self.entity_types[prev_idx]
        except ValueError:
            self.current_entity_type = self.entity_types[-1]
        
        self.load_entities()
    
    def action_copy_timestamp(self) -> None:
        """Copy current timestamp to clipboard."""
        if self.selected_topic and self.selected_topic.get('time_range'):
            time_range = self.selected_topic['time_range']
            # Extract start time
            start_time = time_range.split('-')[0].strip() if '-' in time_range else time_range
            
            # Copy to clipboard (requires pyperclip)
            try:
                import pyperclip
                pyperclip.copy(start_time)
                self.notify(f"Copied timestamp: {start_time}")
            except ImportError:
                self.notify("Install pyperclip for clipboard support: pip install pyperclip")
    
    def action_open_grokipedia(self) -> None:
        """Open Grokipedia page for selected entity."""
        # Get current selected entity from entities list
        entities_list = self.query_one("#entities", EntitiesList)
        
        if not hasattr(entities_list, 'entities_data') or not entities_list.entities_data:
            self.notify("No entity selected")
            return
        
        # Get currently selected index
        if entities_list.index < 0 or entities_list.index >= len(entities_list.entities_data):
            self.notify("No entity selected")
            return
        
        entity = entities_list.entities_data[entities_list.index]
        grokipedia_url = entity.get('grokipedia_url')
        
        if grokipedia_url:
            # Open in browser
            import webbrowser
            webbrowser.open(grokipedia_url)
            self.notify(f"Opening Grokipedia: {entity['name']}")
        else:
            self.notify(f"No Grokipedia page for {entity['name']}")
    
    def action_prev_topic(self) -> None:
        """Jump to previous topic."""
        topics = self.query_one("#topics", TopicsList)
        if topics.index > 0:
            topics.index -= 1
            topics.action_select_cursor()
    
    def action_next_topic(self) -> None:
        """Jump to next topic."""
        topics = self.query_one("#topics", TopicsList)
        topics.index += 1
        topics.action_select_cursor()


def main():
    """Run the redesigned dashboard."""
    app = IntelligenceDashboard()
    app.run()


if __name__ == "__main__":
    main()

