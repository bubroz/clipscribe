"""
Station10 Intelligence Dashboard - Terminal User Interface

Rich, interactive TUI for intelligence analysts using Textual framework.
Keyboard-driven, efficient, beautiful terminal experience.
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, DataTable, Button, Input, Select, Label
from textual.binding import Binding
from textual.reactive import reactive
from pathlib import Path
import sqlite3
from typing import List, Dict, Any
import json


class TopicBrowser(Static):
    """
    Topic browser panel showing topics with relevance scores.
    
    Displays:
    - Topic name
    - Relevance bar (visual 0-1.0)
    - Time range
    - Schema.org type
    """
    
    topics: reactive[List[Dict]] = reactive(list)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "Topics"
        self.topics = []
    
    def render(self) -> str:
        """Render topics list with relevance bars."""
        if not self.topics:
            return "[dim]No topics loaded[/dim]"
        
        lines = []
        for i, topic in enumerate(self.topics, 1):
            name = topic.get('name', 'Unknown')
            relevance = topic.get('relevance', 0.0)
            time_range = topic.get('time_range', '')
            
            # Create relevance bar (visual)
            bar_length = 20
            filled = int(relevance * bar_length)
            bar = "█" * filled + "░" * (bar_length - filled)
            
            # Color code by relevance
            if relevance >= 0.9:
                color = "green"
            elif relevance >= 0.8:
                color = "yellow"
            else:
                color = "blue"
            
            lines.append(f"{i}. [{color}]{bar}[/{color}] {relevance:.2f}")
            lines.append(f"   {name}")
            if time_range:
                lines.append(f"   [dim]{time_range}[/dim]")
            lines.append("")
        
        return "\n".join(lines)
    
    def load_topics(self, video_id: str):
        """Load topics for a video from database."""
        db_path = Path("data/station10.db")
        if not db_path.exists():
            return
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, relevance, time_range, schema_type
            FROM topics
            WHERE video_id = ?
            ORDER BY relevance DESC
        """, (video_id,))
        
        self.topics = []
        for row in cursor.fetchall():
            self.topics.append({
                'name': row[0],
                'relevance': row[1],
                'time_range': row[2],
                'schema_type': row[3]
            })
        
        conn.close()
        self.refresh()


class EntityBrowser(Static):
    """
    Entity browser showing entities grouped by type.
    
    Displays:
    - Entity type (PERSON, ORG, etc.)
    - Count per type
    - Top entities with evidence quotes
    """
    
    entities: reactive[List[Dict]] = reactive(list)
    selected_type: reactive[str] = reactive("PERSON")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "Entities"
        self.entities = []
    
    def render(self) -> str:
        """Render entities grouped by type."""
        if not self.entities:
            return "[dim]No entities loaded[/dim]"
        
        # Group by type
        by_type = {}
        for entity in self.entities:
            entity_type = entity.get('type', 'UNKNOWN')
            if entity_type not in by_type:
                by_type[entity_type] = []
            by_type[entity_type].append(entity)
        
        lines = []
        
        # Show type summary
        lines.append("[bold]Entity Types:[/bold]")
        for entity_type, entities in sorted(by_type.items(), key=lambda x: len(x[1]), reverse=True):
            count = len(entities)
            is_selected = entity_type == self.selected_type
            marker = "▶" if is_selected else " "
            lines.append(f"{marker} {entity_type}: {count}")
        
        lines.append("")
        lines.append(f"[bold]Selected: {self.selected_type}[/bold]")
        lines.append("")
        
        # Show entities of selected type
        selected_entities = by_type.get(self.selected_type, [])
        for i, entity in enumerate(selected_entities[:10], 1):  # Top 10
            name = entity.get('name', 'Unknown')
            conf = entity.get('confidence', 0.0)
            evidence = entity.get('evidence', '')
            
            # Entity with confidence
            conf_color = "green" if conf >= 0.9 else "yellow" if conf >= 0.8 else "white"
            lines.append(f"{i}. [{conf_color}]{name}[/{conf_color}] ({conf:.2f})")
            
            # Evidence quote (truncated)
            if evidence:
                evidence_short = evidence[:60] + "..." if len(evidence) > 60 else evidence
                lines.append(f"   [dim italic]\"{evidence_short}\"[/dim italic]")
            
            lines.append("")
        
        if len(selected_entities) > 10:
            lines.append(f"[dim]... and {len(selected_entities) - 10} more[/dim]")
        
        return "\n".join(lines)
    
    def load_entities(self, video_id: str):
        """Load entities for a video from database."""
        db_path = Path("data/station10.db")
        if not db_path.exists():
            return
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, type, confidence, evidence
            FROM entities
            WHERE video_id = ?
            ORDER BY confidence DESC
        """, (video_id,))
        
        self.entities = []
        for row in cursor.fetchall():
            self.entities.append({
                'name': row[0],
                'type': row[1],
                'confidence': row[2],
                'evidence': row[3]
            })
        
        conn.close()
        self.refresh()


class KeyMomentsList(Static):
    """
    Key moments list with timestamps and significance.
    
    Displays:
    - Timestamp
    - Description
    - Significance bar
    - Quote preview
    """
    
    moments: reactive[List[Dict]] = reactive(list)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "Key Moments"
        self.moments = []
    
    def render(self) -> str:
        """Render key moments list."""
        if not self.moments:
            return "[dim]No key moments loaded[/dim]"
        
        lines = []
        for i, moment in enumerate(self.moments, 1):
            timestamp = moment.get('timestamp', '00:00:00')
            description = moment.get('description', 'No description')
            significance = moment.get('significance', 0.0)
            quote = moment.get('quote', '')
            
            # Significance bar
            bar_length = 20
            filled = int(significance * bar_length)
            bar = "█" * filled + "░" * (bar_length - filled)
            
            # Color by significance
            if significance >= 0.9:
                color = "green"
            elif significance >= 0.85:
                color = "yellow"
            else:
                color = "blue"
            
            lines.append(f"{i}. [{timestamp}]")
            lines.append(f"   [{color}]{bar}[/{color}] {significance:.2f}")
            lines.append(f"   {description}")
            
            if quote:
                quote_short = quote[:60] + "..." if len(quote) > 60 else quote
                lines.append(f"   [dim italic]\"{quote_short}\"[/dim italic]")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def load_moments(self, video_id: str):
        """Load key moments from GCS (would be from database in production)."""
        # TODO: Implement key_moments database table
        # For now, placeholder
        self.moments = []
        self.refresh()


class SentimentIndicator(Static):
    """
    Sentiment display with overall and per-topic breakdown.
    """
    
    sentiment: reactive[Dict] = reactive({})
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "Sentiment"
        self.sentiment = {}
    
    def render(self) -> str:
        """Render sentiment analysis."""
        if not self.sentiment:
            return "[dim]No sentiment data[/dim]"
        
        overall = self.sentiment.get('overall', 'neutral')
        confidence = self.sentiment.get('confidence', 0.0)
        per_topic = self.sentiment.get('per_topic', {})
        
        # Color code sentiment
        if overall == 'positive':
            color = "green"
            icon = "↑"
        elif overall == 'negative':
            color = "red"
            icon = "↓"
        else:
            color = "white"
            icon = "→"
        
        lines = [
            f"[bold]Overall:[/bold] [{color}]{icon} {overall.upper()}[/{color}]",
            f"Confidence: {confidence:.0%}",
            ""
        ]
        
        if per_topic:
            lines.append("[bold]Per-Topic:[/bold]")
            for topic, sent in list(per_topic.items())[:3]:
                sent_icon = "↑" if sent == "positive" else "↓" if sent == "negative" else "→"
                lines.append(f"{sent_icon} {topic}: {sent}")
        
        return "\n".join(lines)


class IntelligenceDashboard(App):
    """
    Main Station10 Intelligence Dashboard TUI.
    
    Terminal-based interface for viewing video intelligence:
    - Topics with relevance scores
    - Entities by type with evidence
    - Key moments with timestamps
    - Sentiment analysis
    
    Keyboard shortcuts:
    - t: Focus topics
    - e: Focus entities
    - m: Focus moments
    - s: Search
    - q: Quit
    """
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #topics {
        width: 1fr;
        height: 1fr;
        border: solid $primary;
        padding: 1;
    }
    
    #entities {
        width: 1fr;
        height: 1fr;
        border: solid $secondary;
        padding: 1;
    }
    
    #moments {
        width: 1fr;
        height: 1fr;
        border: solid $accent;
        padding: 1;
    }
    
    #sentiment {
        width: 1fr;
        height: 8;
        border: solid $warning;
        padding: 1;
    }
    
    .panel {
        margin: 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("t", "focus_topics", "Topics"),
        Binding("e", "focus_entities", "Entities"),
        Binding("m", "focus_moments", "Moments"),
        Binding("s", "search", "Search"),
    ]
    
    def compose(self) -> ComposeResult:
        """Create dashboard layout."""
        yield Header(show_clock=True)
        
        with Container():
            with Horizontal():
                # Left column: Topics and Entities
                with Vertical():
                    yield TopicBrowser(id="topics", classes="panel")
                    yield EntityBrowser(id="entities", classes="panel")
                
                # Right column: Moments and Sentiment
                with Vertical():
                    yield KeyMomentsList(id="moments", classes="panel")
                    yield SentimentIndicator(id="sentiment", classes="panel")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize dashboard with test data."""
        self.title = "Station10 Intelligence Dashboard"
        self.sub_title = "Video Intelligence Analysis"
        
        # Load data for test video (All-In Podcast)
        self.load_video("P-2")
    
    def load_video(self, video_id: str):
        """Load all intelligence for a video."""
        # Load topics
        topic_browser = self.query_one("#topics", TopicBrowser)
        topic_browser.load_topics(video_id)
        
        # Load entities
        entity_browser = self.query_one("#entities", EntityBrowser)
        entity_browser.load_entities(video_id)
        
        # Load moments (TODO: implement)
        # moments_list = self.query_one("#moments", KeyMomentsList)
        # moments_list.load_moments(video_id)
        
        # Set sentiment (TODO: load from database)
        # sentiment = self.query_one("#sentiment", SentimentIndicator)
        # sentiment.sentiment = {...}
    
    def action_focus_topics(self) -> None:
        """Focus topics panel."""
        self.query_one("#topics").focus()
    
    def action_focus_entities(self) -> None:
        """Focus entities panel."""
        self.query_one("#entities").focus()
    
    def action_focus_moments(self) -> None:
        """Focus moments panel."""
        self.query_one("#moments").focus()
    
    def action_search(self) -> None:
        """Open search dialog."""
        # TODO: Implement search modal
        pass


def main():
    """Run the Intelligence Dashboard."""
    app = IntelligenceDashboard()
    app.run()


if __name__ == "__main__":
    main()

