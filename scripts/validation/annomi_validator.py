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
    
    async def validate_conversation(self, transcript_id: int, use_modal: bool = True) -> Dict:
        """
        Validate one conversation.
        
        Args:
            transcript_id: AnnoMI transcript ID
            use_modal: Use Modal GPU transcription (WhisperX + Gemini)
            
        Returns:
            Validation results dict with WER, speaker accuracy, etc.
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
        gt_text = ' '.join(seg['text'] for seg in gt_segments)
        print(f"  Ground truth: {len(gt_segments)} segments, 2 speakers")
        
        if use_modal:
            # Process with Modal GPU (WhisperX + Gemini)
            print(f"  Processing with Modal (WhisperX + Gemini)...")
            clipscribe_result = await self._process_with_modal(video_url)
        else:
            # Process with local ClipScribe (future)
            print(f"  Processing with local ClipScribe...")
            clipscribe_result = None  # TODO: implement local processing
        
        if not clipscribe_result:
            return {
                'transcript_id': transcript_id,
                'status': 'processing_failed'
            }
        
        # Calculate metrics
        from .metrics import calculate_wer, calculate_speaker_accuracy, normalize_text
        
        # Extract ClipScribe segments and transcript
        cs_segments = clipscribe_result.get('segments', [])
        cs_text = ' '.join(seg.get('text', '') for seg in cs_segments)
        
        # Calculate WER
        wer_score = calculate_wer(
            normalize_text(cs_text),
            normalize_text(gt_text)
        )
        
        # Map ClipScribe speakers to ground truth
        # AnnoMI has 2 speakers: 'therapist' and 'client'
        # ClipScribe has: 'SPEAKER_01', 'SPEAKER_02', etc.
        speaker_mapping = self._map_speakers(cs_segments, gt_segments)
        
        # Calculate speaker accuracy
        speaker_acc, speaker_stats = calculate_speaker_accuracy(
            cs_segments,
            gt_segments,
            speaker_mapping
        )
        
        # Count Gemini corrections
        gemini_corrections = sum(1 for seg in cs_segments if seg.get('gemini_corrected'))
        
        result = {
            'transcript_id': transcript_id,
            'video_url': video_url,
            'title': title,
            'ground_truth': {
                'segments': len(gt_segments),
                'speakers': 2,
                'text_length': len(gt_text)
            },
            'clipscribe': {
                'segments': len(cs_segments),
                'speakers': len(set(seg.get('speaker') for seg in cs_segments)),
                'text_length': len(cs_text),
                'processing_time': clipscribe_result.get('processing_minutes', 0),
                'cost': clipscribe_result.get('cost', 0)
            },
            'metrics': {
                'wer': wer_score,
                'speaker_accuracy': speaker_acc,
                'gemini_corrections': gemini_corrections
            },
            'speaker_mapping': speaker_mapping,
            'speaker_stats': speaker_stats,
            'status': 'success'
        }
        
        print(f"  ✓ WER: {wer_score:.1%}")
        print(f"  ✓ Speaker accuracy: {speaker_acc:.1%}")
        print(f"  ✓ Gemini corrections: {gemini_corrections}")
        
        return result
    
    async def _process_with_modal(self, video_url: str) -> Optional[Dict]:
        """
        Process video with Modal GPU (WhisperX + Gemini).
        
        Args:
            video_url: YouTube URL
            
        Returns:
            Processing result with segments
        """
        import modal
        
        try:
            # Lookup Modal function
            transcribe_fn = modal.Function.lookup("station10-transcription", "test_gcs_transcription")
            
            # For YouTube videos, we need to:
            # 1. Download audio with yt-dlp
            # 2. Upload to GCS
            # 3. Call Modal with GCS path
            
            # TODO: Implement YouTube → GCS → Modal pipeline
            # For now, return None to indicate not yet implemented
            
            print(f"    ⚠️  Modal integration TODO: YouTube → GCS → Modal")
            return None
            
        except Exception as e:
            print(f"    ❌ Modal processing failed: {e}")
            return None
    
    def _map_speakers(self, cs_segments: List[Dict], gt_segments: List[Dict]) -> Dict[str, str]:
        """
        Map ClipScribe speaker IDs to ground truth speaker labels.
        
        For AnnoMI: Map SPEAKER_01/02 → therapist/client based on who speaks more.
        
        Args:
            cs_segments: ClipScribe segments
            gt_segments: Ground truth segments
            
        Returns:
            Mapping dict {CS_ID: GT_LABEL}
        """
        # Count segments per ClipScribe speaker
        cs_speaker_counts = {}
        for seg in cs_segments:
            spk = seg.get('speaker', 'UNKNOWN')
            cs_speaker_counts[spk] = cs_speaker_counts.get(spk, 0) + 1
        
        # Count segments per ground truth speaker
        gt_speaker_counts = {}
        for seg in gt_segments:
            spk = seg.get('speaker', 'UNKNOWN')
            gt_speaker_counts[spk] = gt_speaker_counts.get(spk, 0) + 1
        
        # Sort both by frequency
        cs_sorted = sorted(cs_speaker_counts.items(), key=lambda x: x[1], reverse=True)
        gt_sorted = sorted(gt_speaker_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Map most frequent → most frequent, second → second, etc.
        mapping = {}
        for i, (cs_spk, _) in enumerate(cs_sorted):
            if i < len(gt_sorted):
                gt_spk, _ = gt_sorted[i]
                mapping[cs_spk] = gt_spk
        
        return mapping
    
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

