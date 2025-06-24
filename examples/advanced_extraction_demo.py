#!/usr/bin/env python3
"""
ClipScribe v2.2 Advanced Intelligence Extraction Demo

This example demonstrates the advanced extraction features:
- REBEL for relationship extraction
- GLiNER for custom entity detection
- Knowledge graph generation
- Domain-specific extraction

Note: First run will download ~3GB of ML models.
Subsequent runs will use cached models.
"""

import asyncio
import json
from pathlib import Path
import sys

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from clipscribe.retrievers.video_retriever import VideoIntelligenceRetriever
from clipscribe.config import Settings
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

console = Console()
settings = Settings()


async def demonstrate_advanced_extraction(video_url: str, domain: str = None):
    """Demonstrate advanced extraction capabilities."""
    
    console.print(f"\n[bold cyan]ClipScribe v2.2 Advanced Extraction Demo[/bold cyan]")
    console.print(f"Video URL: {video_url}")
    if domain:
        console.print(f"Domain: {domain}")
    console.print("-" * 80)
    
    # Create retriever with advanced extraction
    retriever = VideoIntelligenceRetriever(
        use_advanced_extraction=True,
        domain=domain
    )
    
    # Process video
    with console.status("[yellow]Processing video with advanced extraction..."):
        try:
            result = await retriever.process_url(video_url)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            return
    
    if not result:
        console.print("[red]Failed to process video[/red]")
        return
    
    # Display results
    console.print(f"\n[green]✓ Video processed successfully![/green]")
    console.print(f"Title: {result.metadata.title}")
    console.print(f"Duration: {result.metadata.duration:.0f} seconds")
    
    # Show extraction statistics
    if hasattr(result, 'processing_stats') and result.processing_stats:
        stats = result.processing_stats
        
        stats_table = Table(title="Extraction Statistics", show_header=True)
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Count", style="green")
        
        stats_table.add_row("SpaCy Entities", str(stats.get('spacy_entities', 0)))
        stats_table.add_row("GLiNER Entities", str(stats.get('gliner_entities', 0)))
        stats_table.add_row("Total Entities", str(len(result.entities)))
        stats_table.add_row("Relationships", str(stats.get('relationships', 0)))
        stats_table.add_row("Graph Nodes", str(stats.get('graph_nodes', 0)))
        stats_table.add_row("Graph Edges", str(stats.get('graph_edges', 0)))
        
        console.print("\n", stats_table)
    
    # Show top entities by type
    if result.entities:
        entity_types = {}
        for entity in result.entities:
            entity_types[entity.type] = entity_types.get(entity.type, 0) + 1
        
        entity_table = Table(title=f"\nTop Entity Types (Total: {len(result.entities)})")
        entity_table.add_column("Type", style="cyan")
        entity_table.add_column("Count", style="green")
        entity_table.add_column("Examples", style="yellow")
        
        # Sort by count and show top 10
        sorted_types = sorted(entity_types.items(), key=lambda x: x[1], reverse=True)[:10]
        for entity_type, count in sorted_types:
            # Get examples
            examples = [e.name for e in result.entities if e.type == entity_type][:3]
            examples_str = ", ".join(examples)
            if len(examples) > 3:
                examples_str += "..."
            entity_table.add_row(entity_type, str(count), examples_str)
        
        console.print("\n", entity_table)
    
    # Show relationships
    if hasattr(result, 'relationships') and result.relationships:
        rel_table = Table(title=f"\nTop Relationships (Total: {len(result.relationships)})")
        rel_table.add_column("Subject", style="cyan")
        rel_table.add_column("Predicate", style="green")
        rel_table.add_column("Object", style="yellow")
        rel_table.add_column("Confidence", style="magenta")
        
        # Show top 10 relationships by confidence
        sorted_rels = sorted(result.relationships, key=lambda x: x.confidence, reverse=True)[:10]
        for rel in sorted_rels:
            rel_table.add_row(
                rel.subject[:30],
                rel.predicate[:20],
                rel.object[:30],
                f"{rel.confidence:.2f}"
            )
        
        console.print("\n", rel_table)
    
    # Show key facts
    if hasattr(result, 'key_moments') and result.key_moments:
        facts_panel = Panel(
            "\n".join([f"• {fact['fact']}" for fact in result.key_moments[:10]]),
            title=f"Top 10 Key Facts (from {len(result.key_moments)} total)",
            border_style="green"
        )
        console.print("\n", facts_panel)
    
    # Show knowledge graph stats
    if hasattr(result, 'knowledge_graph') and result.knowledge_graph:
        kg = result.knowledge_graph
        kg_info = f"""
[bold]Knowledge Graph Statistics:[/bold]
• Nodes: {kg.get('node_count', 0)}
• Edges: {kg.get('edge_count', 0)}
• Connected Components: {kg.get('connected_components', 0)}
• Graph Density: {kg.get('density', 0):.3f}
"""
        console.print(Panel(kg_info, title="Knowledge Graph", border_style="blue"))
    
    # Save all formats
    console.print("\n[yellow]Saving output files...[/yellow]")
    saved_files = retriever.save_all_formats(result)
    
    console.print(f"\n[green]✓ Files saved to: {saved_files['directory']}[/green]")
    console.print("\nOutput files:")
    for file_type, path in saved_files.items():
        if file_type != 'directory':
            console.print(f"  • {file_type}: {Path(path).name}")
    
    # Show cost
    console.print(f"\n[bold]Total Cost: ${result.processing_cost:.4f}[/bold]")
    

async def main():
    """Run the demo with example videos."""
    
    # Example videos for different domains
    examples = {
        "news": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Replace with news video
        "tech": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Replace with tech video
        "military": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Replace with military video
        "medical": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Replace with medical video
    }
    
    # Get video URL from command line or use default
    if len(sys.argv) > 1:
        video_url = sys.argv[1]
        domain = sys.argv[2] if len(sys.argv) > 2 else None
    else:
        console.print("\n[bold]ClipScribe v2.2 Advanced Extraction Demo[/bold]")
        console.print("\nUsage:")
        console.print("  python advanced_extraction_demo.py <video_url> [domain]")
        console.print("\nDomains: military, tech, finance, medical")
        console.print("\nExample:")
        console.print("  python advanced_extraction_demo.py 'https://youtube.com/watch?v=...' military")
        
        # Use a default example
        console.print("\n[yellow]Using default example video...[/yellow]")
        video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Astley
        domain = None
    
    # Check for API key
    if not settings.google_api_key:
        console.print("\n[red]Error: GOOGLE_API_KEY not set![/red]")
        console.print("Please set your Google API key:")
        console.print("  export GOOGLE_API_KEY='your-key-here'")
        return
    
    # Run extraction
    await demonstrate_advanced_extraction(video_url, domain)
    
    # Show performance note
    console.print("\n[dim]Note: First run downloads ML models (~3GB).[/dim]")
    console.print("[dim]Subsequent runs will be much faster with cached models.[/dim]")
    console.print("\n[bold green]Advanced extraction complete! 🎯[/bold green]")


if __name__ == "__main__":
    asyncio.run(main()) 