#!/usr/bin/env python3
"""Generate professional export samples (DOCX, CSV, PPTX, Markdown) from JSON outputs.

This script takes the existing JSON sample outputs and generates all export formats
for clipscribe.ai/samples/ hosting.
"""

import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from clipscribe.providers.base import TranscriptResult, IntelligenceResult, TranscriptSegment
from clipscribe.exporters.docx_report import generate_docx_report
from clipscribe.exporters.csv_exporter import export_to_csv
from clipscribe.exporters.pptx_report import generate_pptx_report
from clipscribe.exporters.markdown_report import generate_markdown_report


def load_json_sample(json_path: Path) -> tuple[TranscriptResult, IntelligenceResult]:
    """Load JSON sample and convert to result objects.
    
    Args:
        json_path: Path to JSON sample file
        
    Returns:
        Tuple of (TranscriptResult, IntelligenceResult)
    """
    with open(json_path) as f:
        data = json.load(f)
    
    # Extract transcript data
    transcript_data = data['transcript']
    
    # Convert segments to TranscriptSegment objects
    segments = [
        TranscriptSegment(**seg) for seg in transcript_data['segments']
    ]
    
    # Create TranscriptResult
    transcript_result = TranscriptResult(
        segments=segments,
        language=transcript_data['language'],
        duration=transcript_data['duration'],
        speakers=transcript_data['speakers'],
        word_level=True,  # All samples have word-level timing
        provider=transcript_data['provider'],
        model=transcript_data['model'],
        cost=transcript_data['cost'],
        metadata=transcript_data.get('metadata', {})
    )
    
    # Create IntelligenceResult
    intelligence_data = data['intelligence']
    intelligence_result = IntelligenceResult(
        entities=intelligence_data['entities'],
        relationships=intelligence_data['relationships'],
        topics=intelligence_data['topics'],
        key_moments=intelligence_data['key_moments'],
        sentiment=intelligence_data['sentiment'],
        provider=intelligence_data['provider'],
        model=intelligence_data['model'],
        cost=intelligence_data['cost'],
        cost_breakdown=intelligence_data.get('cost_breakdown', {}),
        cache_stats=intelligence_data.get('cache_stats', {}),
        metadata=intelligence_data.get('metadata', {})
    )
    
    return transcript_result, intelligence_result


def generate_all_formats(
    sample_name: str,
    transcript_result: TranscriptResult,
    intelligence_result: IntelligenceResult,
    output_base: Path
):
    """Generate all export formats for a sample.
    
    Args:
        sample_name: Base name for the sample (without .json)
        transcript_result: Transcript data
        intelligence_result: Intelligence data
        output_base: Base output directory
    """
    print(f"\n=== {sample_name} ===")
    
    # 1. Generate DOCX report
    print("  → Generating DOCX report...")
    docx_path = generate_docx_report(
        transcript_result=transcript_result,
        intelligence_result=intelligence_result,
        output_path=output_base,
        filename=f"{sample_name}.docx"
    )
    print(f"    ✓ {docx_path.name}")
    
    # 2. Generate CSV exports (5 files in subdirectory)
    print("  → Generating CSV exports...")
    csv_dir = output_base / f"{sample_name}_csv"
    csv_files = export_to_csv(
        intelligence_result=intelligence_result,
        transcript_result=transcript_result,
        output_path=csv_dir
    )
    for csv_type, csv_path in csv_files.items():
        print(f"    ✓ {csv_type}.csv")
    
    # 3. Generate PPTX presentation
    print("  → Generating PPTX presentation...")
    pptx_path = generate_pptx_report(
        transcript_result=transcript_result,
        intelligence_result=intelligence_result,
        output_path=output_base,
        filename=f"{sample_name}.pptx"
    )
    print(f"    ✓ {pptx_path.name}")
    
    # 4. Generate Markdown report
    print("  → Generating Markdown report...")
    md_path = generate_markdown_report(
        transcript_result=transcript_result,
        intelligence_result=intelligence_result,
        output_path=output_base,
        filename=f"{sample_name}.md"
    )
    print(f"    ✓ {md_path.name}")


def main():
    """Generate all export samples."""
    # Define samples directory
    samples_dir = Path(__file__).parent.parent.parent / "examples" / "sample_outputs"
    
    # Sample files to process
    samples = [
        "multispeaker_panel_36min",
        "business_interview_30min",
        "technical_single_speaker_16min"
    ]
    
    print("ClipScribe Export Sample Generator")
    print("=" * 50)
    print(f"Source: {samples_dir}")
    print(f"Formats: DOCX, CSV (5 files), PPTX, Markdown")
    print("=" * 50)
    
    for sample_name in samples:
        json_path = samples_dir / f"{sample_name}.json"
        
        if not json_path.exists():
            print(f"⚠️  Skipping {sample_name} (file not found)")
            continue
        
        # Load JSON and convert to result objects
        transcript_result, intelligence_result = load_json_sample(json_path)
        
        # Generate all formats
        generate_all_formats(
            sample_name=sample_name,
            transcript_result=transcript_result,
            intelligence_result=intelligence_result,
            output_base=samples_dir
        )
    
    print("\n" + "=" * 50)
    print("✓ Export generation complete!")
    print("=" * 50)
    print(f"\nGenerated files in: {samples_dir}")
    print("\nFormats created:")
    print("  • 3 DOCX reports (Word/Google Docs/Pages)")
    print("  • 3 PPTX presentations (PowerPoint/Google Slides/Keynote)")
    print("  • 3 Markdown reports (GitHub/VS Code/Obsidian)")
    print("  • 15 CSV files (5 per sample: entities, relationships, topics, key_moments, segments)")
    print("\nTotal: 24 files ready for clipscribe.ai hosting")


if __name__ == "__main__":
    main()

