"""Export ClipScribe intelligence to CSV format."""

import csv
import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


def export_entities_csv(entities: List, output_path: Path):
    """Export entities to CSV."""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'name', 'type', 'confidence', 'mention_count', 'extraction_source'
        ])
        writer.writeheader()
        
        for entity in entities:
            if isinstance(entity, dict):
                writer.writerow({
                    'name': entity.get('name', ''),
                    'type': entity.get('type', ''),
                    'confidence': entity.get('confidence', 0.9),
                    'mention_count': entity.get('mention_count', 0),
                    'extraction_source': ','.join(entity.get('extraction_sources', []))
                })
            else:
                writer.writerow({
                    'name': getattr(entity, 'name', ''),
                    'type': getattr(entity, 'type', ''),
                    'confidence': getattr(entity, 'confidence', 0.9),
                    'mention_count': getattr(entity, 'mention_count', 0),
                    'extraction_source': ','.join(getattr(entity, 'extraction_sources', []))
                })
    
    logger.info(f"Exported {len(entities)} entities to {output_path}")


def export_relationships_csv(relationships: List, output_path: Path):
    """Export relationships to CSV."""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'subject', 'predicate', 'object', 'confidence', 'source'
        ])
        writer.writeheader()
        
        for rel in relationships:
            if isinstance(rel, dict):
                writer.writerow({
                    'subject': rel.get('subject', ''),
                    'predicate': rel.get('predicate', ''),
                    'object': rel.get('object', ''),
                    'confidence': rel.get('confidence', 0.9),
                    'source': rel.get('source', 'grok_analysis')
                })
            else:
                writer.writerow({
                    'subject': getattr(rel, 'subject', ''),
                    'predicate': getattr(rel, 'predicate', ''),
                    'object': getattr(rel, 'object', ''),
                    'confidence': getattr(rel, 'confidence', 0.9) if hasattr(rel, 'confidence') else 0.9,
                    'source': getattr(rel, 'source', 'grok_analysis')
                })
    
    logger.info(f"Exported {len(relationships)} relationships to {output_path}")

