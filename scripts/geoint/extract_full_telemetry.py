import sys
import json
import logging
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from clipscribe.extractors.metadata_extractor import MetadataExtractor

# Configure logging
logging.basicConfig(level=logging.INFO)

def main():
    file_path = "test_videos/geoint/Day Flight.mpg"
    print(f"Extracting telemetry from: {file_path}")
    
    extractor = MetadataExtractor()
    metadata = extractor.extract_metadata(file_path)
    
    print(f"Extracted {len(metadata)} packets.")
    
    if metadata:
        print("\n--- Sample Packet 1 ---")
        print(json.dumps(metadata[0], indent=2, default=str))
        
        print("\n--- Sample Packet 50 ---")
        if len(metadata) > 50:
            print(json.dumps(metadata[50], indent=2, default=str))
            
        # Save full dump
        output_path = "test_videos/geoint/day_flight_telemetry.json"
        with open(output_path, "w") as f:
            json.dump(metadata, f, indent=2, default=str)
        print(f"\nFull telemetry saved to {output_path}")

if __name__ == "__main__":
    main()

