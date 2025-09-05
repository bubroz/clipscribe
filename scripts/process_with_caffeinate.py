#!/usr/bin/env python3
"""
Process videos while preventing Mac from sleeping.
Uses caffeinate to keep the system awake during processing.
"""

import asyncio
import subprocess
import os
import sys
import signal
import atexit
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

# Global variable to track caffeinate process
caffeinate_process: Optional[subprocess.Popen] = None


def start_caffeinate():
    """Start caffeinate to prevent system sleep."""
    global caffeinate_process
    
    try:
        # -d: Prevent display sleep
        # -i: Prevent system idle sleep
        # -m: Prevent disk idle sleep
        # -s: Keep system awake when on AC power
        caffeinate_process = subprocess.Popen(
            ['caffeinate', '-dims'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("☕ Caffeinate started - system will stay awake")
        return True
    except FileNotFoundError:
        print("⚠️ caffeinate not found - system may sleep during processing")
        return False
    except Exception as e:
        print(f"⚠️ Could not start caffeinate: {e}")
        return False


def stop_caffeinate():
    """Stop caffeinate process."""
    global caffeinate_process
    
    if caffeinate_process:
        try:
            caffeinate_process.terminate()
            caffeinate_process.wait(timeout=5)
            print("☕ Caffeinate stopped - system can sleep normally")
        except:
            try:
                caffeinate_process.kill()
            except:
                pass
        finally:
            caffeinate_process = None


# Register cleanup on exit
atexit.register(stop_caffeinate)


def signal_handler(signum, frame):
    """Handle interrupt signals."""
    print("\n⚠️ Interrupted - cleaning up...")
    stop_caffeinate()
    sys.exit(0)


# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


async def process_video_with_protection(url: str):
    """Process a video while preventing system sleep."""
    
    # Import here to avoid circular imports
    from src.clipscribe.utils.logging import setup_logging
    from src.clipscribe.retrievers.universal_video_client import EnhancedUniversalVideoClient
    from src.clipscribe.processors.hybrid_processor import HybridProcessor
    from datetime import datetime
    import time
    import json
    
    setup_logging(level="INFO")
    
    # Set environment variables
    os.environ["XAI_API_KEY"] = "xai-QlxLU3aSN0EYKt1HnVmOUz3l05v12DkowN2qvAIDsox61KGyMEqV92SMeaQ8PU4voX8WHEBmS7p5T5Fr"
    os.environ["USE_VOXTRAL"] = "true"
    
    print(f"\n📹 Processing: {url}")
    print("="*80)
    
    start_time = time.time()
    
    try:
        # Initialize components
        client = EnhancedUniversalVideoClient()
        processor = HybridProcessor(
            voxtral_model="voxtral-mini-2507",
            grok_model="grok-4-0709"
        )
        
        # Download audio
        print("\n📥 Downloading audio...")
        audio_path, metadata = await client.download_audio(url)
        
        print(f"✅ Downloaded: {metadata.title}")
        print(f"   Duration: {metadata.duration}s ({metadata.duration/60:.1f} min)")
        print(f"   Channel: {metadata.channel}")
        
        # Prepare metadata
        metadata_dict = {
            "video_id": metadata.video_id,
            "title": metadata.title,
            "channel": metadata.channel,
            "channel_id": metadata.channel_id or "unknown",
            "duration": metadata.duration,
            "url": url,
            "description": metadata.description or "",
            "published_at": metadata.published_at
        }
        
        # Process with pipeline
        print("\n🔄 Processing with Voxtral → Grok-4 pipeline...")
        print("   This will keep your Mac awake during processing")
        
        result = await processor.process_video(
            audio_path,
            metadata_dict,
            force_reprocess=True
        )
        
        processing_time = time.time() - start_time
        
        if result and result.entities:
            print(f"\n✅ SUCCESS!")
            print(f"   • Entities: {len(result.entities)}")
            print(f"   • Relationships: {len(result.relationships)}")
            print(f"   • Topics: {len(result.topics)}")
            print(f"   • Processing time: {processing_time:.1f}s ({processing_time/60:.1f} min)")
            print(f"   • Cost: ${result.processing_cost:.4f}")
            
            # Save output
            output_dir = Path(f"output/sensitive_content_tests/{datetime.now().strftime('%Y%m%d')}_{metadata.video_id}")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save summary
            with open(output_dir / "summary.json", "w") as f:
                json.dump({
                    "metadata": metadata_dict,
                    "stats": {
                        "entities": len(result.entities),
                        "relationships": len(result.relationships),
                        "topics": len(result.topics),
                        "processing_time": processing_time,
                        "cost": result.processing_cost
                    },
                    "entities": [{"name": e.name, "type": e.type} for e in result.entities[:20]],
                    "topics": [t.name for t in result.topics[:10]]
                }, f, indent=2, default=str)
            
            print(f"\n💾 Output saved to: {output_dir}")
            
        else:
            print(f"\n⚠️ No entities extracted")
            print(f"   Processing time: {processing_time:.1f}s")
            
    except Exception as e:
        import traceback
        print(f"\n❌ ERROR: {e}")
        print(traceback.format_exc())
        
    finally:
        print(f"\n⏱️ Total time: {(time.time() - start_time)/60:.1f} minutes")


async def main():
    """Main entry point."""
    
    print("="*80)
    print("VIDEO PROCESSING WITH SLEEP PREVENTION")
    print("="*80)
    
    # Start caffeinate
    if not start_caffeinate():
        response = input("\n⚠️ Continue without sleep prevention? (y/n): ")
        if response.lower() != 'y':
            print("Exiting...")
            return
    
    # Get video URL from command line or use default
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        # Use a controversial video from our test set
        url = "https://www.youtube.com/watch?v=Y77AEt-YWr8"  # Whatifalthist - 68 min
        print(f"\nNo URL provided, using default test video")
    
    try:
        await process_video_with_protection(url)
    finally:
        stop_caffeinate()
    
    print("\n✨ Processing complete!")


if __name__ == "__main__":
    asyncio.run(main())
