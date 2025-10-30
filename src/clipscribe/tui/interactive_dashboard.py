"""
Station10 Intelligence Dashboard - Interactive TUI (Fixed)

Properly interactive terminal interface with keyboard navigation.
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, ListView, ListItem, Label, Static
from textual.binding import Binding
from textual.reactive import reactive
from pathlib import Path
import sqlite3
from typing import List, Dict


class TopicListView(ListView):
    """Interactive topic list with selection."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "Topics (↑/↓ to navigate)"


class EntityListView(ListView):
    """Interactive entity list grouped by type."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "Entities (←/→ to change type)"
        self.current_type_index = 0
        self.entity_types = []
        self.all_entities = []


class IntelligenceDashboard(App):
    """
    Interactive Intelligence Dashboard.
    
    Keyboard controls:
    - ↑/↓: Navigate topics/entities
    - ←/→: Switch entity type
    - Enter: Select item
    - Tab: Switch focus between panels
    - q: Quit
    """
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    ListView {
        height: 1fr;
        border: solid $primary;
        padding: 1;
    }
    
    .info-panel {
        height: 1fr;
        border: solid $accent;
        padding: 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("left", "prev_type", "Prev Type"),
        Binding("right", "next_type", "Next Type"),
    ]
    
    current_video_id: reactive[str] = reactive("P-2")
    current_type: reactive[str] = reactive("PERSON")
    
    def compose(self) -> ComposeResult:
        """Create dashboard layout."""
        yield Header(show_clock=True)
        
        with Container():
            with Horizontal():
                # Left: Topics
                yield TopicListView(id="topics")
                
                # Middle: Entities  
                yield EntityListView(id="entities")
                
                # Right: Info panel
                with Vertical():
                    yield Static(id="info", classes="info-panel")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Load data when app starts."""
        self.title = "Station10 Intelligence Dashboard"
        self.sub_title = f"Video: All-In Podcast ({self.current_video_id})"
        
        self.load_topics()
        self.load_entities()
    
    def load_topics(self):
        """Load topics from database."""
        db_path = Path("data/station10.db")
        if not db_path.exists():
            return
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, relevance, time_range
            FROM topics
            WHERE video_id = ?
            ORDER BY relevance DESC
        """, (self.current_video_id,))
        
        topic_list = self.query_one("#topics", TopicListView)
        topic_list.clear()
        
        for row in cursor.fetchall():
            name = row[0]
            relevance = row[1]
            time_range = row[2] or ""
            
            # Create visual relevance bar
            bar_length = 20
            filled = int(relevance * bar_length)
            bar = "█" * filled + "░" * (bar_length - filled)
            
            label_text = f"{bar} {relevance:.2f}\n{name}\n{time_range}"
            topic_list.append(ListItem(Label(label_text)))
        
        conn.close()
    
    def load_entities(self):
        """Load entities of current type."""
        db_path = Path("data/station10.db")
        if not db_path.exists():
            return
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all entity types first
        cursor.execute("""
            SELECT DISTINCT type, COUNT(*) as count
            FROM entities
            WHERE video_id = ?
            GROUP BY type
            ORDER BY count DESC
        """, (self.current_video_id,))
        
        types = cursor.fetchall()
        
        # Load entities of current type
        cursor.execute("""
            SELECT name, type, confidence, evidence
            FROM entities
            WHERE video_id = ? AND type = ?
            ORDER BY confidence DESC
            LIMIT 10
        """, (self.current_video_id, self.current_type))
        
        entity_list = self.query_one("#entities", EntityListView)
        entity_list.clear()
        entity_list.border_title = f"Entities: {self.current_type} (←/→ to change)"
        
        for row in cursor.fetchall():
            name = row[0]
            conf = row[2]
            evidence = row[3] or ""
            
            # Truncate evidence
            evidence_short = evidence[:60] + "..." if len(evidence) > 60 else evidence
            
            label_text = f"{name} ({conf:.2f})\n  \"{evidence_short}\""
            entity_list.append(ListItem(Label(label_text)))
        
        conn.close()
    
    def action_next_type(self):
        """Switch to next entity type."""
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
        
        types = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if not types:
            return
        
        try:
            current_idx = types.index(self.current_type)
            next_idx = (current_idx + 1) % len(types)
            self.current_type = types[next_idx]
        except ValueError:
            self.current_type = types[0]
        
        self.load_entities()
    
    def action_prev_type(self):
        """Switch to previous entity type."""
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
        
        types = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if not types:
            return
        
        try:
            current_idx = types.index(self.current_type)
            prev_idx = (current_idx - 1) % len(types)
            self.current_type = types[prev_idx]
        except ValueError:
            self.current_type = types[-1]
        
        self.load_entities()


def main():
    """Run the dashboard."""
    app = IntelligenceDashboard()
    app.run()


if __name__ == "__main__":
    main()
