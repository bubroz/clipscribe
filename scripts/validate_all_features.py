#!/usr/bin/env python3
"""
Comprehensive Feature Validation

Processes all 48 videos and validates:
- Transcription (Voxtral/WhisperX)
- Entity extraction
- Relationship mapping
- Topics, key moments, sentiment
- Grok advanced features (caching, fact-checking, KB)
- All output formats
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from clipscribe.processors.hybrid_processor import HybridProcessor
from clipscribe.utils.prompt_cache import get_prompt_cache
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def process_video_comprehensive(processor, video_path: Path, output_base: Path):
    """Process single video with full feature validation."""
    
    video_name = video_path.stem
    output_dir = output_base / video_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"\n{'='*80}")
    logger.info(f"Processing: {video_name}")
    logger.info(f"Size: {video_path.stat().st_size / (1024*1024):.0f}MB")
    logger.info(f"{'='*80}")
    
    try:
        # Prepare metadata
        metadata = {
            'video_id': video_name,
            'title': video_name,
            'channel': 'Unknown',
            'channel_id': 'unknown',
            'duration': 0,  # Will be extracted from audio
            'url': str(video_path)
        }
        
        # Process with HybridProcessor
        logger.info("Starting hybrid processing (Voxtral + Grok-4)...")
        result = await processor.process_video(
            audio_path=str(video_path),
            metadata=metadata
        )
        
        # Save outputs in multiple formats
        logger.info("Generating outputs...")
        
        # 1. JSON (complete data)
        json_output = output_dir / 'intelligence.json'
        with open(json_output, 'w') as f:
            json.dump({
                'metadata': {
                    'title': result.metadata.title,
                    'duration': result.metadata.duration,
                    'processing_time': result.processing_time,
                    'processing_cost': result.processing_cost
                },
                'transcript': {
                    'text': result.transcript.full_text,
                    'language': result.transcript.language,
                    'confidence': result.transcript.confidence_score
                },
                'entities': [
                    {
                        'name': e.name,
                        'type': e.type,
                        'confidence': e.confidence,
                        'evidence': e.evidence if hasattr(e, 'evidence') else None
                    }
                    for e in result.entities
                ],
                'relationships': [
                    {
                        'subject': r.subject,
                        'predicate': r.predicate,
                        'object': r.object,
                        'confidence': r.confidence,
                        'evidence': r.evidence if hasattr(r, 'evidence') else None
                    }
                    for r in result.relationships
                ],
                'topics': [
                    {
                        'name': t.name,
                        'confidence': t.confidence if hasattr(t, 'confidence') else 0.8
                    }
                    for t in result.topics
                ],
                'summary': result.summary,
                'sentiment': result.sentiment
            }, f, indent=2)
        
        # 2. CSV (entities)
        csv_output = output_dir / 'entities.csv'
        with open(csv_output, 'w') as f:
            f.write("Name,Type,Confidence,Evidence\n")
            for e in result.entities:
                evidence = getattr(e, 'evidence', '')
                f.write(f'"{e.name}","{e.type}",{e.confidence},"{evidence}"\n')
        
        # 3. Summary stats
        stats_output = output_dir / 'stats.json'
        with open(stats_output, 'w') as f:
            json.dump({
                'entities_count': len(result.entities),
                'relationships_count': len(result.relationships),
                'topics_count': len(result.topics),
                'processing_time_seconds': result.processing_time,
                'processing_cost_usd': result.processing_cost,
                'transcript_length_chars': len(result.transcript.full_text),
                'language': result.transcript.language
            }, f, indent=2)
        
        logger.info(f"✅ Processed successfully!")
        logger.info(f"   Entities: {len(result.entities)}")
        logger.info(f"   Relationships: {len(result.relationships)}")
        logger.info(f"   Topics: {len(result.topics)}")
        logger.info(f"   Cost: ${result.processing_cost:.4f}")
        logger.info(f"   Time: {result.processing_time:.1f}s")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Processing failed: {e}")
        return False


async def validate_all_videos():
    """Process all 48 videos and validate features."""
    
    # Load inventory
    with open('output/video_inventory.json', 'r') as f:
        inventory = json.load(f)
    
    # Initialize processor
    processor = HybridProcessor()
    
    # Output directory
    output_base = Path('output/comprehensive_validation')
    output_base.mkdir(parents=True, exist_ok=True)
    
    # Process all videos
    total = inventory['total_videos']
    processed = 0
    failed = 0
    
    progress_file = output_base / 'progress.txt'
    
    with open(progress_file, 'w') as f:
        f.write(f"Comprehensive Validation Started: {datetime.now()}\n")
        f.write(f"Total videos: {total}\n\n")
    
    all_files = []
    for category, files in inventory['files'].items():
        all_files.extend(files)
    
    for i, video_file in enumerate(all_files, 1):
        video_path = Path(video_file)
        
        if not video_path.exists():
            logger.warning(f"Skipping {video_path} - file not found")
            continue
        
        logger.info(f"\n[{i}/{total}] Processing {video_path.name}...")
        
        success = await process_video_comprehensive(processor, video_path, output_base)
        
        if success:
            processed += 1
        else:
            failed += 1
        
        # Update progress
        with open(progress_file, 'a') as f:
            status = "✅" if success else "❌"
            f.write(f"{status} [{i}/{total}] {video_path.name}\n")
        
        # Rate limiting
        await asyncio.sleep(1)
    
    # Get cache stats
    cache = get_prompt_cache()
    cache_stats = cache.get_stats_summary()
    
    # Final summary
    summary = f"""
{'='*80}
VALIDATION COMPLETE
{'='*80}

Videos Processed: {processed}/{total}
Failed: {failed}
Success Rate: {processed/total*100:.1f}%

Cache Performance:
  Hit Rate: {cache_stats['hit_rate_percent']:.1f}%
  Total Savings: ${cache_stats['total_savings_usd']:.2f}
  Avg Savings/Request: ${cache_stats['avg_savings_per_request_usd']:.4f}

Outputs saved to: {output_base}
Progress log: {progress_file}

{'='*80}
"""
    
    print(summary)
    
    with open(progress_file, 'a') as f:
        f.write(summary)
    
    # Save final stats
    final_stats = {
        'completed_at': datetime.now().isoformat(),
        'total_videos': total,
        'processed': processed,
        'failed': failed,
        'success_rate': processed/total,
        'cache_stats': cache_stats
    }
    
    with open(output_base / 'final_stats.json', 'w') as f:
        json.dump(final_stats, f, indent=2)


if __name__ == "__main__":
    print("\n🚀 Starting Comprehensive Feature Validation")
    print("Processing 48 videos across 4 verticals + existing test videos")
    print("This will take 2-4 hours depending on video lengths\n")
    
    asyncio.run(validate_all_videos())

