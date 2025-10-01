"""
Export ClipScribe intelligence to Obsidian vault format.

Creates a knowledge base with:
- Wikilinks between entities
- Individual entity notes
- Video summary notes
- Automatic graph view integration
"""

import logging
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class ObsidianExporter:
    """
    Export video intelligence to Obsidian vault.
    
    Structure:
    vault/
      entities/
        Person Name.md
        Organization Name.md
      videos/
        2025-09-30 Video Title.md
      relationships/
        (optional: relationship type notes)
    
    Features:
    - Wikilinks: [[Entity Name]] syntax
    - Frontmatter: YAML metadata
    - Backlinks: Automatic bidirectional linking
    - Graph view: Native Obsidian visualization
    """
    
    def __init__(self, vault_path: Path):
        """
        Initialize Obsidian exporter.
        
        Args:
            vault_path: Path to Obsidian vault root
        """
        self.vault_path = Path(vault_path)
        
        # Create vault structure
        self.entities_dir = self.vault_path / "entities"
        self.videos_dir = self.vault_path / "videos"
        
        self.entities_dir.mkdir(parents=True, exist_ok=True)
        self.videos_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"ObsidianExporter initialized: {vault_path}")
    
    def export_video(
        self,
        title: str,
        url: str,
        channel: str,
        duration: int,
        entities: List,
        relationships: List,
        transcript: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        Export video intelligence to Obsidian vault.
        
        Args:
            title: Video title
            url: Video URL
            channel: Channel name
            duration: Duration in seconds
            entities: List of entities (dicts or objects)
            relationships: List of relationships
            transcript: Full transcript text
            metadata: Optional additional metadata
            
        Returns:
            Dict with paths to created files
        """
        created_files = {}
        
        # Create video note
        video_file = self._create_video_note(
            title, url, channel, duration, entities, relationships, transcript, metadata
        )
        created_files['video_note'] = str(video_file)
        
        # Create entity notes
        entity_files = self._create_entity_notes(entities, title)
        created_files['entity_notes'] = [str(f) for f in entity_files]
        
        logger.info(f"Exported to Obsidian: {len(entity_files)} entity notes + 1 video note")
        return created_files
    
    def _create_video_note(
        self,
        title: str,
        url: str,
        channel: str,
        duration: int,
        entities: List,
        relationships: List,
        transcript: str,
        metadata: Optional[Dict]
    ) -> Path:
        """Create video summary note with wikilinks."""
        
        # Sanitize filename
        safe_title = self._sanitize_filename(title)
        date_prefix = datetime.now().strftime("%Y-%m-%d")
        filename = f"{date_prefix} {safe_title}.md"
        
        video_file = self.videos_dir / filename
        
        # Build frontmatter
        frontmatter = f"""---
title: "{title}"
channel: "{channel}"
url: {url}
duration: {duration}s
date: {datetime.now().strftime("%Y-%m-%d")}
entities: {len(entities)}
relationships: {len(relationships)}
"""
        
        if metadata:
            if 'cost' in metadata:
                frontmatter += f"cost: ${metadata['cost']:.4f}\n"
            if 'entity_count' in metadata:
                frontmatter += f"entity_count: {metadata['entity_count']}\n"
        
        frontmatter += "---\n\n"
        
        # Build content
        content = f"# {title}\n\n"
        content += f"**Channel**: [[{channel}]]\n"
        content += f"**URL**: {url}\n"
        content += f"**Duration**: {duration}s ({duration // 60}m {duration % 60}s)\n\n"
        
        # Entities section with wikilinks
        if entities:
            content += "## Key Entities\n\n"
            for entity in entities:
                name = entity.get('name') if isinstance(entity, dict) else getattr(entity, 'name', str(entity))
                entity_type = entity.get('type') if isinstance(entity, dict) else getattr(entity, 'type', 'UNKNOWN')
                mentions = entity.get('mention_count', 0) if isinstance(entity, dict) else getattr(entity, 'mention_count', 0)
                
                content += f"- [[{name}]] ({entity_type})"
                if mentions > 0:
                    content += f": {mentions} mentions"
                content += "\n"
            content += "\n"
        
        # Relationships section with wikilinks
        if relationships:
            content += "## Key Relationships\n\n"
            for rel in relationships:
                if isinstance(rel, dict):
                    subj = rel.get('subject', '')
                    pred = rel.get('predicate', '')
                    obj = rel.get('object', '')
                else:
                    subj = getattr(rel, 'subject', '')
                    pred = getattr(rel, 'predicate', '')
                    obj = getattr(rel, 'object', '')
                
                if subj and pred and obj:
                    content += f"- [[{subj}]] {pred} [[{obj}]]\n"
            content += "\n"
        
        # Transcript section
        content += "## Transcript\n\n"
        content += f"```\n{transcript}\n```\n"
        
        # Write file
        video_file.write_text(frontmatter + content)
        logger.debug(f"Created video note: {video_file}")
        
        return video_file
    
    def _create_entity_notes(self, entities: List, source_video: str) -> List[Path]:
        """Create or update individual entity notes."""
        created_files = []
        
        for entity in entities:
            name = entity.get('name') if isinstance(entity, dict) else getattr(entity, 'name', str(entity))
            entity_type = entity.get('type') if isinstance(entity, dict) else getattr(entity, 'type', 'UNKNOWN')
            
            safe_name = self._sanitize_filename(name)
            entity_file = self.entities_dir / f"{safe_name}.md"
            
            # Check if entity note already exists
            if entity_file.exists():
                # Append to existing note
                content = entity_file.read_text()
                
                # Add video reference if not already there
                video_link = f"- [[{source_video}]]"
                if video_link not in content:
                    # Find "## Mentioned In" section or add it
                    if "## Mentioned In" in content:
                        content = content.replace("## Mentioned In\n", f"## Mentioned In\n{video_link}\n")
                    else:
                        content += f"\n## Mentioned In\n{video_link}\n"
                    
                    entity_file.write_text(content)
                    logger.debug(f"Updated entity note: {entity_file}")
            else:
                # Create new entity note
                frontmatter = f"""---
type: {entity_type.lower()}
created: {datetime.now().strftime("%Y-%m-%d")}
---

"""
                
                content = f"# {name}\n\n"
                content += f"**Type**: {entity_type}\n\n"
                content += f"## Mentioned In\n"
                content += f"- [[{source_video}]]\n\n"
                content += f"## Notes\n\n"
                content += f"(Add your notes about {name} here)\n"
                
                entity_file.write_text(frontmatter + content)
                logger.debug(f"Created entity note: {entity_file}")
            
            created_files.append(entity_file)
        
        return created_files
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitize name for filename (remove invalid characters)."""
        # Replace invalid characters
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '#']
        safe_name = name
        for char in invalid_chars:
            safe_name = safe_name.replace(char, '-')
        
        # Remove leading/trailing spaces and dots
        safe_name = safe_name.strip('. ')
        
        return safe_name


def export_to_obsidian(
    result,
    vault_path: Path
) -> Dict[str, str]:
    """
    Convenience function to export VideoIntelligence to Obsidian.
    
    Args:
        result: VideoIntelligence object
        vault_path: Path to Obsidian vault
        
    Returns:
        Dict with created file paths
    """
    exporter = ObsidianExporter(vault_path)
    
    return exporter.export_video(
        title=result.metadata.title,
        url=result.metadata.url,
        channel=result.metadata.channel,
        duration=result.metadata.duration,
        entities=result.entities,
        relationships=result.relationships,
        transcript=result.transcript.full_text,
        metadata={
            'cost': result.processing_cost,
            'entity_count': len(result.entities),
            'relationship_count': len(result.relationships)
        }
    )

