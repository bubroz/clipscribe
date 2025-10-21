"""
AnnoMI Dataset Validator

Validates ClipScribe WhisperX + Gemini pipeline against the AnnoMI dataset
(133 expert-annotated motivational interviewing conversations).

Dataset: https://github.com/uccollab/AnnoMI
Format: CSV with YouTube URLs, speaker labels, timestamps, transcripts
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
import json
import asyncio
from datetime import datetime

# ClipScribe imports (will add once we test structure)
# from clipscribe.retrievers import UniversalVideoClient
# from .metrics import calculate_wer, calculate_der, calculate_speaker_accuracy


class AnnoMIValidator:
    """Validator for AnnoMI dataset."""
    
    def __init__(self, dataset_path: Path, output_path: Path):
        """
        Initialize validator.
        
        Args:
            dataset_path: Path to AnnoMI-simple.csv
            output_path: Path to save validation results
        """
        self.dataset_path = dataset_path
        self.output_path = output_path
        self.df = None
        
    def load_dataset(self):
        """Load AnnoMI CSV dataset."""
        print(f"Loading AnnoMI dataset from {self.dataset_path}...")
        self.df = pd.read_csv(self.dataset_path)
        print(f"✓ Loaded {len(self.df)} utterances from {self.df['transcript_id'].nunique()} conversations")
        
    def get_long_conversations(self, min_utterances: int = 100) -> pd.DataFrame:
        """
        Get conversations with sufficient length (likely 30+ minutes).
        
        Args:
            min_utterances: Minimum utterance count (default 100 ≈ 30 min)
            
        Returns:
            DataFrame with conversation metadata
        """
        by_transcript = self.df.groupby('transcript_id').agg({
            'utterance_id': 'count',
            'video_url': 'first',
            'video_title': 'first',
            'topic': 'first',
            'mi_quality': 'first'
        })
        by_transcript.columns = ['utterance_count', 'video_url', 'title', 'topic', 'quality']
        
        long_convos = by_transcript[by_transcript['utterance_count'] >= min_utterances]
        print(f"Found {len(long_convos)} conversations with {min_utterances}+ utterances")
        
        return long_convos.sort_values('utterance_count', ascending=False)
    
    def get_ground_truth_segments(self, transcript_id: int) -> List[Dict]:
        """
        Extract ground truth segments for a conversation.
        
        Args:
            transcript_id: AnnoMI transcript ID
            
        Returns:
            List of segments with speaker, text, timestamp
        """
        conversation = self.df[self.df['transcript_id'] == transcript_id].sort_values('utterance_id')
        
        segments = []
        for idx, row in conversation.iterrows():
            # Parse timestamp HH:MM:SS to seconds
            time_parts = row['timestamp'].split(':')
            start_seconds = int(time_parts[0]) * 3600 + int(time_parts[1]) * 60 + int(time_parts[2])
            
            segment = {
                'start': start_seconds,
                'end': start_seconds + 3,  # Estimate 3s per utterance (no end times in AnnoMI)
                'speaker': row['interlocutor'],  # 'therapist' or 'client'
                'text': row['utterance_text']
            }
            segments.append(segment)
        
        return segments
    
    async def validate_conversation(self, transcript_id: int) -> Dict:
        """
        Validate one conversation.
        
        Args:
            transcript_id: AnnoMI transcript ID
            
        Returns:
            Validation results dict
        """
        print(f"\nValidating conversation #{transcript_id}...")
        
        # Get conversation metadata
        conversation = self.df[self.df['transcript_id'] == transcript_id].iloc[0]
        video_url = conversation['video_url']
        title = conversation['video_title']
        
        print(f"  Title: {title[:60]}")
        print(f"  URL: {video_url}")
        
        # Get ground truth
        gt_segments = self.get_ground_truth_segments(transcript_id)
        print(f"  Ground truth: {len(gt_segments)} segments, 2 speakers")
        
        # TODO: Process with ClipScribe
        # client = UniversalVideoClient()
        # result = await client.process_url(video_url)
        
        # For now, return placeholder
        result = {
            'transcript_id': transcript_id,
            'video_url': video_url,
            'title': title,
            'ground_truth_segments': len(gt_segments),
            'status': 'pending_implementation'
        }
        
        return result
    
    async def validate_batch(self, num_conversations: int = 10) -> List[Dict]:
        """
        Validate multiple conversations.
        
        Args:
            num_conversations: Number to validate
            
        Returns:
            List of validation results
        """
        long_convos = self.get_long_conversations()
        selected = long_convos.head(num_conversations)
        
        print(f"\n{'='*80}")
        print(f"VALIDATING {num_conversations} ANNOMI CONVERSATIONS")
        print(f"{'='*80}\n")
        
        results = []
        for transcript_id in selected.index:
            result = await self.validate_conversation(transcript_id)
            results.append(result)
        
        # Save results
        self.save_results(results)
        
        return results
    
    def save_results(self, results: List[Dict]):
        """Save validation results to JSON."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_path / f"annomi_validation_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✓ Results saved to {output_file}")


async def main():
    """Test the validator."""
    dataset_path = Path("validation_data/samples/annomi/AnnoMI-simple.csv")
    output_path = Path("validation_data/results")
    output_path.mkdir(parents=True, exist_ok=True)
    
    validator = AnnoMIValidator(dataset_path, output_path)
    validator.load_dataset()
    
    # Show available conversations
    long_convos = validator.get_long_conversations()
    print(f"\nTop 10 longest conversations:")
    print(long_convos.head(10)[['utterance_count', 'title', 'quality', 'topic']])
    
    # Test getting ground truth for one conversation
    print(f"\nTesting ground truth extraction for conversation #121...")
    gt_segments = validator.get_ground_truth_segments(121)
    print(f"✓ Extracted {len(gt_segments)} segments")
    print(f"\nFirst 5 segments:")
    for i, seg in enumerate(gt_segments[:5]):
        print(f"  {i+1}. [{seg['start']}s] {seg['speaker']}: {seg['text'][:60]}")
    
    print("\n✅ AnnoMI validator skeleton working!")
    print("Next: Integrate with ClipScribe processing pipeline")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

