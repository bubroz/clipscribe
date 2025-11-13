"""Markdown report generator for ClipScribe intelligence extraction.

Generates GitHub-flavored markdown that's:
- Searchable in any text editor
- Readable in VS Code, Obsidian, Notion
- Renderable on GitHub
- Copy-paste friendly
"""

from pathlib import Path
from datetime import datetime


def generate_markdown_report(
    transcript_result,
    intelligence_result,
    output_path: Path,
    filename: str = "report.md"
):
    """Generate markdown report from ClipScribe results.
    
    Args:
        transcript_result: TranscriptResult from provider
        intelligence_result: IntelligenceResult from provider
        output_path: Directory to save report
        filename: Output filename (default: report.md)
        
    Returns:
        Path to generated markdown file
    """
    output_path = Path(output_path)
    
    # Build markdown content
    md_content = []
    
    # Header
    md_content.append("# ClipScribe Intelligence Extraction Report")
    md_content.append(f"\n**Generated:** {datetime.now().strftime('%B %d, %Y')}")
    md_content.append(f"**Duration:** {transcript_result.duration/60:.1f} minutes")
    md_content.append(f"**Provider:** {transcript_result.provider} + {intelligence_result.provider}")
    md_content.append(f"**Cost:** ${transcript_result.cost + intelligence_result.cost:.4f}\n")
    md_content.append("---\n")
    
    # Executive Summary
    md_content.append("## Executive Summary\n")
    md_content.append(f"- **{len(intelligence_result.entities)}** entities extracted")
    md_content.append(f"- **{len(intelligence_result.relationships)}** relationships mapped")
    md_content.append(f"- **{transcript_result.speakers}** speakers identified")
    md_content.append(f"- **{len(intelligence_result.topics)}** main topics")
    md_content.append(f"- **{len(intelligence_result.key_moments)}** key moments\n")
    
    # Entities
    md_content.append("## Entities\n")
    md_content.append(f"Total: {len(intelligence_result.entities)} entities with evidence\n")
    
    if intelligence_result.entities:
        md_content.append("| Name | Type | Confidence | Evidence |")
        md_content.append("|------|------|------------|----------|")
        
        for entity in intelligence_result.entities[:20]:
            name = entity.get('name', 'Unknown').replace('|', '\\|')
            type_val = entity.get('type', 'UNKNOWN')
            conf = f"{entity.get('confidence', 0):.2f}"
            evidence = entity.get('evidence', '')[:100].replace('|', '\\|').replace('\n', ' ')
            md_content.append(f"| {name} | {type_val} | {conf} | {evidence}... |")
        
        if len(intelligence_result.entities) > 20:
            md_content.append(f"\n*Showing top 20 of {len(intelligence_result.entities)} entities*\n")
    
    # Relationships  
    md_content.append("\n## Relationships\n")
    md_content.append(f"Total: {len(intelligence_result.relationships)} relationships with evidence\n")
    
    if intelligence_result.relationships:
        for idx, rel in enumerate(intelligence_result.relationships[:15], 1):
            subject = rel.get('subject', 'Unknown')
            predicate = rel.get('predicate', 'related_to')
            obj = rel.get('object', 'Unknown')
            evidence = rel.get('evidence', 'No evidence')
            conf = rel.get('confidence', 0)
            
            md_content.append(f"### {idx}. {subject} → {predicate} → {obj}")
            md_content.append(f"**Confidence:** {conf:.2f}")
            md_content.append(f"> {evidence}\n")
        
        if len(intelligence_result.relationships) > 15:
            md_content.append(f"*Showing top 15 of {len(intelligence_result.relationships)} relationships*\n")
    
    # Topics
    md_content.append("\n## Topics\n")
    md_content.append(f"Total: {len(intelligence_result.topics)} main topics\n")
    
    if intelligence_result.topics:
        md_content.append("| Topic | Relevance | Time Range |")
        md_content.append("|-------|-----------|------------|")
        
        for topic in intelligence_result.topics:
            name = topic.get('name', 'Unknown').replace('|', '\\|')
            relevance = f"{topic.get('relevance', 0):.2f}"
            time_range = topic.get('time_range', 'N/A')
            md_content.append(f"| {name} | {relevance} | {time_range} |")
    
    # Key Moments
    md_content.append("\n## Key Moments\n")
    md_content.append(f"Total: {len(intelligence_result.key_moments)} significant moments\n")
    
    if intelligence_result.key_moments:
        for moment in intelligence_result.key_moments:
            timestamp = moment.get('timestamp', '00:00')
            desc = moment.get('description', 'No description')
            sig = moment.get('significance', 0)
            quote = moment.get('quote', 'No quote')
            
            md_content.append(f"### ⏰ {timestamp} - {desc}")
            md_content.append(f"**Significance:** {sig:.2f}")
            md_content.append(f"> {quote}\n")
    
    # Sentiment
    md_content.append("\n## Sentiment Analysis\n")
    sentiment = intelligence_result.sentiment
    overall = sentiment.get('overall', 'unknown')
    confidence = sentiment.get('confidence', 0)
    
    md_content.append(f"**Overall Sentiment:** {overall.upper()} (confidence: {confidence:.2f})\n")
    
    if sentiment.get('per_topic'):
        md_content.append("**Per-Topic Sentiment:**\n")
        for topic, topic_sentiment in sentiment.get('per_topic', {}).items():
            md_content.append(f"- **{topic}:** {topic_sentiment}")
    
    # Footer
    md_content.append("\n---\n")
    md_content.append("*Powered by ClipScribe Intelligence Extraction*")
    md_content.append("\n[clipscribe.ai](https://clipscribe.ai) • [GitHub](https://github.com/bubroz/clipscribe)")
    
    # Write file
    md_path = output_path / filename
    md_path.write_text('\n'.join(md_content), encoding='utf-8')
    csv_files['markdown'] = md_path
    
    return csv_files

