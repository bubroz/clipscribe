"""Export ClipScribe intelligence to PDF format."""

import logging
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

logger = logging.getLogger(__name__)


def export_to_pdf(
    title: str,
    url: str,
    channel: str,
    entities: list,
    relationships: list,
    transcript: str,
    output_path: Path,
    metadata: dict = None
):
    """
    Export video intelligence to professional PDF report.
    
    Args:
        title: Video title
        url: Video URL
        channel: Channel name
        entities: List of entities
        relationships: List of relationships
        transcript: Full transcript
        output_path: Where to save PDF
        metadata: Optional processing metadata
    """
    doc = SimpleDocTemplate(str(output_path), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=12
    )
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Metadata section
    story.append(Paragraph(f"<b>Channel:</b> {channel}", styles['Normal']))
    story.append(Paragraph(f"<b>URL:</b> {url}", styles['Normal']))
    if metadata:
        if 'cost' in metadata:
            story.append(Paragraph(f"<b>Processing Cost:</b> ${metadata['cost']:.4f}", styles['Normal']))
        story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Entities section
    story.append(Paragraph(f"<b>Key Entities ({len(entities)})</b>", styles['Heading2']))
    story.append(Spacer(1, 0.1*inch))
    
    # Entities table
    entity_data = [['Name', 'Type', 'Mentions']]
    for entity in entities[:20]:  # Top 20
        name = entity.get('name') if isinstance(entity, dict) else getattr(entity, 'name', '')
        etype = entity.get('type') if isinstance(entity, dict) else getattr(entity, 'type', '')
        mentions = entity.get('mention_count', 0) if isinstance(entity, dict) else getattr(entity, 'mention_count', 0)
        entity_data.append([name[:40], etype, str(mentions)])
    
    entity_table = Table(entity_data, colWidths=[3*inch, 1.5*inch, 0.8*inch])
    entity_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(entity_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Relationships section
    story.append(Paragraph(f"<b>Key Relationships ({len(relationships)})</b>", styles['Heading2']))
    story.append(Spacer(1, 0.1*inch))
    
    for rel in relationships[:15]:  # Top 15
        if isinstance(rel, dict):
            subj = rel.get('subject', '')
            pred = rel.get('predicate', '')
            obj = rel.get('object', '')
        else:
            subj = getattr(rel, 'subject', '')
            pred = getattr(rel, 'predicate', '')
            obj = getattr(rel, 'object', '')
        
        if subj and pred and obj:
            story.append(Paragraph(f"• {subj} <i>{pred}</i> {obj}", styles['Normal']))
    
    story.append(Spacer(1, 0.3*inch))
    
    # Transcript section
    story.append(Paragraph("<b>Transcript</b>", styles['Heading2']))
    story.append(Spacer(1, 0.1*inch))
    transcript_preview = transcript[:2000] + "..." if len(transcript) > 2000 else transcript
    story.append(Paragraph(transcript_preview, styles['Normal']))
    
    # Build PDF
    doc.build(story)
    logger.info(f"Exported PDF to {output_path}")

