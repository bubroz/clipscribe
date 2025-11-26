"""
Benchmark KLV Parser.

Measures the performance of the MetadataExtractor on the reference file.
Target: >10x realtime speed.
"""

import time
import logging
from pathlib import Path
import sys

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from clipscribe.extractors.metadata_extractor import MetadataExtractor

# Configure logging - reduce noise for benchmark
logging.basicConfig(level=logging.WARNING)

def benchmark():
    video_path = "test_videos/geoint/Day Flight.mpg"
    
    print(f"Benchmarking KLV extraction on: {video_path}")
    
    start_time = time.time()
    
    extractor = MetadataExtractor()
    telemetry = extractor.extract_metadata(video_path)
    
    end_time = time.time()
    duration = end_time - start_time
    
    packet_count = len(telemetry)
    
    # "Day Flight.mpg" is approx 195 seconds (3m 15s)
    video_duration = 195.0 
    speed_factor = video_duration / duration if duration > 0 else 0
    
    print("\n--- Results ---")
    print(f"Time taken: {duration:.4f} seconds")
    print(f"Packets extracted: {packet_count}")
    print(f"Packets/sec: {packet_count / duration:.2f}")
    print(f"Speed factor: {speed_factor:.2f}x realtime")
    
    if speed_factor < 10:
        print("\n⚠️  PERFORMANCE WARNING: Parsing is slow (<10x realtime)")
    else:
        print("\n✅ Performance PASS (>10x realtime)")

if __name__ == "__main__":
    benchmark()

