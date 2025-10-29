#!/usr/bin/env python3
"""
Comprehensive analysis of validation results with duplicate detection.
"""
import json
from pathlib import Path
from google.cloud import storage
from collections import Counter

def analyze_video_results(video_name: str, gcs_path: str, expected_entities_range: tuple):
    """Analyze a single video's results."""
    client = storage.Client()
    bucket = client.bucket('clipscribe-validation')
    transcript_blob = bucket.blob(gcs_path)
    
    if not transcript_blob.exists():
        return {"error": "Transcript not found", "video": video_name}
    
    transcript_data = json.loads(transcript_blob.download_as_text())
    
    segments = transcript_data.get('segments', [])
    entities = transcript_data.get('entities', [])
    relationships = transcript_data.get('relationships', [])
    
    # Check for duplicates
    entity_names = [e.get('name', '').lower() for e in entities]
    name_counts = Counter(entity_names)
    duplicates = {name: count for name, count in name_counts.items() if count > 1}
    
    # Confidence analysis (handle both float and string values)
    confidences = []
    for e in entities:
        conf = e.get('confidence', 0)
        if isinstance(conf, str):
            try:
                conf = float(conf)
            except ValueError:
                conf = 0
        confidences.append(conf)
    
    avg_conf = sum(confidences) / len(confidences) if confidences else 0
    low_conf_count = sum(1 for c in confidences if c < 0.7)
    
    # Entity type distribution
    entity_types = Counter(e.get('type', 'UNKNOWN') for e in entities)
    
    # Transcript length
    full_text = ' '.join(s.get('text', '') for s in segments)
    
    min_expected, max_expected = expected_entities_range
    entity_count_status = "✅ PASS"
    if len(entities) < min_expected:
        entity_count_status = "⚠️ LOW"
    elif len(entities) > max_expected:
        entity_count_status = "⚠️ HIGH"
    
    return {
        "video": video_name,
        "status": "success",
        "segments": len(segments),
        "transcript_length": len(full_text),
        "entities": len(entities),
        "entity_count_status": entity_count_status,
        "expected_range": f"{min_expected}-{max_expected}",
        "relationships": len(relationships),
        "entity_types": len(entity_types),
        "avg_confidence": round(avg_conf, 2),
        "low_confidence_entities": low_conf_count,
        "duplicate_names": len(duplicates),
        "top_duplicates": dict(name_counts.most_common(5)),
        "entity_type_distribution": dict(entity_types),
        "sample_entities": [
            f"{e.get('name')} ({e.get('type')}, {e.get('confidence', 0):.2f})"
            for e in entities[:5]
        ]
    }

def main():
    print("=" * 80)
    print("COMPREHENSIVE VALIDATION ANALYSIS")
    print("=" * 80)
    print()
    
    # Define videos with expected entity ranges based on content
    videos = [
        {
            "name": "All-In Podcast",
            "gcs_path": "validation/results/P-2//transcript.json",
            "expected_range": (80, 150),  # Long, dense content
            "actual_previous": 499  # From validation run
        },
        {
            "name": "The View Oct 14",
            "gcs_path": "validation/results/View-1//transcript.json",
            "expected_range": (60, 120),  # Medium content
            "actual_previous": 113  # From validation run
        },
        {
            "name": "MTG Interview",
            "gcs_path": "validation/results/P-1//transcript.json",
            "expected_range": (70, 140),  # Medium-long content
            "actual_previous": 197  # From validation run
        }
    ]
    
    results = []
    for video in videos:
        print(f"Analyzing: {video['name']}")
        print("-" * 80)
        
        result = analyze_video_results(
            video['name'],
            video['gcs_path'],
            video['expected_range']
        )
        
        results.append(result)
        
        # Print analysis
        print(f"  Segments: {result['segments']}")
        print(f"  Transcript length: {result['transcript_length']:,} chars")
        print(f"  Entities: {result['entities']} {result['entity_count_status']}")
        print(f"  Expected range: {result['expected_range']}")
        print(f"  Actual (previous run): {video['actual_previous']}")
        print(f"  Relationships: {result['relationships']}")
        print(f"  Entity types: {result['entity_types']}")
        print(f"  Avg confidence: {result['avg_confidence']}")
        print(f"  Low confidence (<0.7): {result['low_confidence_entities']}")
        print(f"  Duplicate names: {result['duplicate_names']}")
        
        if result['duplicate_names'] > 0:
            print(f"  Top duplicates:")
            for name, count in list(result['top_duplicates'].items())[:3]:
                if count > 1:
                    print(f"    - {name}: {count}x")
        
        print(f"  Sample entities:")
        for sample in result['sample_entities']:
            print(f"    - {sample}")
        
        print()
    
    # Summary analysis
    print("=" * 80)
    print("SUMMARY ANALYSIS")
    print("=" * 80)
    
    total_entities = sum(r['entities'] for r in results)
    total_duplicates = sum(r['duplicate_names'] for r in results)
    
    print(f"Total videos: {len(results)}")
    print(f"Total entities extracted: {total_entities}")
    print(f"Total duplicate names: {total_duplicates}")
    print(f"Avg entities per video: {total_entities / len(results):.0f}")
    
    # Check for excessive entities (potential over-extraction from chunking)
    excessive_videos = [r for r in results if r['entity_count_status'] == "⚠️ HIGH"]
    if excessive_videos:
        print(f"\n⚠️  EXCESSIVE ENTITY EXTRACTION DETECTED:")
        for vid in excessive_videos:
            print(f"  - {vid['video']}: {vid['entities']} entities (expected {vid['expected_range']})")
            print(f"    Likely cause: Chunking without proper deduplication")
            print(f"    Duplicate names: {vid['duplicate_names']}")
    else:
        print(f"\n✅ All videos within expected entity ranges")
    
    # Quality metrics
    avg_confidence = sum(r['avg_confidence'] for r in results) / len(results)
    print(f"\nQuality Metrics:")
    print(f"  Avg confidence across all videos: {avg_confidence:.2f}")
    print(f"  Videos with duplicates: {sum(1 for r in results if r['duplicate_names'] > 0)}/{len(results)}")
    
    # Recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    if excessive_videos or total_duplicates > 20:
        print("⚠️  ACTION REQUIRED:")
        print("  1. Deduplication is needed for chunked extraction")
        print("  2. Add entity deduplication by (name, type) with confidence threshold")
        print("  3. Consider relationship deduplication as well")
        print("  4. Re-run validation after fixes")
    else:
        print("✅ Entity extraction quality is good")
        print("✅ Ready to proceed with Week 5-8 features")
    
    # Save results
    output_file = Path('validation_data/detailed_analysis.json')
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n📄 Detailed results saved: {output_file}")

if __name__ == "__main__":
    main()

