"""
CHiME-6 Dataset Validator

Validates ClipScribe WhisperX + Gemini pipeline against CHiME-6 Challenge dataset.
CHiME-6 is the industry benchmark for far-field multi-speaker diarization.

Dataset: http://openslr.org/150/
Format: JSON transcriptions + WAV audio
Benchmark: CHiME-6 Challenge 2020 (winner: 42.7% WER, baseline: 77.9% WER)
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class CHiME6Validator:
    """Validator for CHiME-6 dataset."""
    
    def __init__(self, transcripts_dir: Path, audio_dir: Path, output_path: Path):
        """
        Initialize validator.
        
        Args:
            transcripts_dir: Path to CHiME-6 transcriptions/
            audio_dir: Path to CHiME-6 audio files
            output_path: Path to save validation results
        """
        self.transcripts_dir = transcripts_dir
        self.audio_dir = audio_dir
        self.output_path = output_path
        self.sessions = {}
        
    def load_transcripts(self, split: str = "dev"):
        """
        Load CHiME-6 transcripts for a split.
        
        Args:
            split: 'train', 'dev', or 'eval'
        """
        print(f"Loading CHiME-6 {split} transcripts...")
        
        split_dir = self.transcripts_dir / "transcriptions" / split
        if not split_dir.exists():
            # Try without nested transcriptions/
            split_dir = self.transcripts_dir / split
        
        json_files = list(split_dir.glob("*.json"))
        print(f"✓ Found {len(json_files)} sessions in {split} split")
        
        for json_file in json_files:
            session_id = json_file.stem  # e.g., "S08"
            with open(json_file) as f:
                segments = json.load(f)
            
            self.sessions[session_id] = {
                'file': json_file,
                'segments': segments,
                'split': split
            }
        
        print(f"✓ Loaded {len(self.sessions)} sessions")
        
    def get_ground_truth_segments(self, session_id: str) -> List[Dict]:
        """
        Extract ground truth segments for a session.
        
        CHiME-6 format:
        [
          {
            "start_time": "00:01:10.41",
            "end_time": "00:01:11.00",
            "words": "We are free.",
            "speaker": "P21",
            "session_id": "S08"
          },
          ...
        ]
        
        Args:
            session_id: CHiME-6 session ID (e.g., "S08")
            
        Returns:
            List of segments with start, end, speaker, text in seconds
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not loaded")
        
        raw_segments = self.sessions[session_id]['segments']
        
        # Convert to ClipScribe format (timestamps in seconds)
        segments = []
        for seg in raw_segments:
            # Parse HH:MM:SS.ms to seconds
            start_str = seg['start_time']
            end_str = seg['end_time']
            
            start_sec = self._time_to_seconds(start_str)
            end_sec = self._time_to_seconds(end_str)
            
            segments.append({
                'start': start_sec,
                'end': end_sec,
                'speaker': seg['speaker'],
                'text': seg['words'],
                'session_id': seg['session_id']
            })
        
        return segments
    
    def _time_to_seconds(self, time_str: str) -> float:
        """Convert HH:MM:SS.ms to seconds."""
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        
        return hours * 3600 + minutes * 60 + seconds
    
    async def validate_session(self, session_id: str, use_modal: bool = True) -> Dict:
        """
        Validate one CHiME-6 session.
        
        Args:
            session_id: Session ID (e.g., "S08")
            use_modal: Use Modal GPU processing
            
        Returns:
            Validation results dict
        """
        print(f"\nValidating CHiME-6 session {session_id}...")
        
        # Get ground truth
        gt_segments = self.get_ground_truth_segments(session_id)
        gt_text = ' '.join(seg['text'] for seg in gt_segments)
        
        speakers = set(seg['speaker'] for seg in gt_segments)
        duration = max(seg['end'] for seg in gt_segments)
        
        print(f"  Ground truth: {len(gt_segments)} segments, {len(speakers)} speakers, {duration/60:.1f} min")
        
        # Find audio file
        audio_file = self._find_audio_file(session_id)
        if not audio_file:
            print(f"  ❌ Audio file not found for {session_id}")
            return {'session_id': session_id, 'status': 'no_audio'}
        
        print(f"  Audio: {audio_file}")
        
        if use_modal:
            # Process with Modal GPU
            print(f"  Processing with Modal (WhisperX + Gemini)...")
            clipscribe_result = await self._process_with_modal(audio_file)
        else:
            clipscribe_result = None
        
        if not clipscribe_result:
            return {'session_id': session_id, 'status': 'processing_failed'}
        
        # Calculate metrics
        from .metrics import calculate_wer, calculate_speaker_accuracy, normalize_text
        
        cs_segments = clipscribe_result.get('segments', [])
        cs_text = ' '.join(seg.get('text', '') for seg in cs_segments)
        
        # Calculate WER
        wer_score = calculate_wer(
            normalize_text(cs_text),
            normalize_text(gt_text)
        )
        
        # Map speakers
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
            'session_id': session_id,
            'split': self.sessions[session_id]['split'],
            'ground_truth': {
                'segments': len(gt_segments),
                'speakers': len(speakers),
                'duration_minutes': duration / 60,
                'text_length': len(gt_text)
            },
            'clipscribe': {
                'segments': len(cs_segments),
                'speakers': len(set(seg.get('speaker') for seg in cs_segments)),
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
    
    def _find_audio_file(self, session_id: str) -> Optional[Path]:
        """Find audio file for session."""
        # CHiME-6 audio files are named like: S08_U01.CH1.wav
        # We want the mixed or first channel
        
        if not self.audio_dir or not self.audio_dir.exists():
            print(f"    ❌ Audio dir doesn't exist: {self.audio_dir}")
            return None
        
        # Try to find any file matching session_id
        # Use rglob for recursive search
        patterns = [
            f"**/{session_id}*.wav",
            f"**/{session_id}*.flac",
            f"{session_id}*.wav",  # Also try non-recursive
        ]
        
        for pattern in patterns:
            files = list(self.audio_dir.glob(pattern))
            if files:
                print(f"    Found {len(files)} audio files for {session_id}")
                # Return first file (any channel will work for validation)
                return files[0]
        
        print(f"    ❌ No audio files found matching: {session_id}*.wav")
        print(f"    Searched in: {self.audio_dir}")
        return None
    
    async def _process_with_modal(self, audio_path: Path) -> Optional[Dict]:
        """
        Process audio file with Modal GPU.
        
        For CHiME-6, audio is local. We need to:
        1. Upload to GCS
        2. Process with Modal
        3. Download results
        
        Args:
            audio_path: Local path to audio file
            
        Returns:
            Processing result with segments
        """
        from google.cloud import storage
        import modal
        
        try:
            # Upload to GCS
            print(f"    Uploading to GCS...")
            client = storage.Client()
            bucket = client.bucket("clipscribe-validation")
            
            gcs_path = f"validation/chime6/{audio_path.name}"
            blob = bucket.blob(gcs_path)
            blob.upload_from_filename(str(audio_path))
            
            gcs_url = f"gs://clipscribe-validation/{gcs_path}"
            print(f"    ✓ Uploaded: {gcs_url}")
            
            # Call Modal using correct 1.0+ API
            print(f"    Processing with Modal...")
            Station10Transcriber = modal.Cls.from_name("station10-transcription", "Station10Transcriber")
            
            result_dict = Station10Transcriber().transcribe_from_gcs.remote(
                gcs_input=gcs_url,
                gcs_output="gs://clipscribe-validation/validation/results/"
            )
            
            print(f"    ✓ Modal complete: {result_dict.get('speakers')} speakers, ${result_dict.get('cost', 0):.4f}")
            
            # Download transcript from GCS
            # Modal uploads to the root of gcs_output path with // separator
            # e.g., gs://.../validation/results//transcript.json
            result_path = result_dict.get('gcs_output', '')
            
            if result_path:
                # Remove bucket prefix and find transcript
                blob_path = result_path.replace('gs://clipscribe-validation/', '')
                
                # Try exact path
                transcript_blob = bucket.blob(f"{blob_path}/transcript.json")
                
                if not transcript_blob.exists():
                    # Try with // (Modal's pattern)
                    transcript_blob = bucket.blob(f"{blob_path.rstrip('/')}/transcript.json")
                
                if transcript_blob.exists():
                    print(f"    Downloading transcript from: {transcript_blob.name}")
                    transcript_json = json.loads(transcript_blob.download_as_text())
                    transcript_json['processing_cost'] = result_dict.get('cost', 0)
                    transcript_json['processing_minutes'] = result_dict.get('processing_minutes', 0)
                    return transcript_json
                else:
                    print(f"    ❌ Transcript not found at: {blob_path}/transcript.json")
                    # List what's actually there
                    print(f"    Listing {blob_path}:")
                    blobs = list(bucket.list_blobs(prefix=blob_path[:50]))
                    for b in blobs[:10]:
                        print(f"      - {b.name}")
            
            print(f"    ❌ No transcript found in GCS")
            return None
            
        except Exception as e:
            print(f"    ❌ Modal processing failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _map_speakers(self, cs_segments: List[Dict], gt_segments: List[Dict]) -> Dict[str, str]:
        """Map ClipScribe speakers to CHiME-6 speaker IDs."""
        # Similar logic to AnnoMI but with 4 speakers (P21, P22, P23, P24)
        
        cs_speaker_counts = {}
        for seg in cs_segments:
            spk = seg.get('speaker', 'UNKNOWN')
            cs_speaker_counts[spk] = cs_speaker_counts.get(spk, 0) + 1
        
        gt_speaker_counts = {}
        for seg in gt_segments:
            spk = seg.get('speaker', 'UNKNOWN')
            gt_speaker_counts[spk] = gt_speaker_counts.get(spk, 0) + 1
        
        # Sort by frequency
        cs_sorted = sorted(cs_speaker_counts.items(), key=lambda x: x[1], reverse=True)
        gt_sorted = sorted(gt_speaker_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Map by frequency rank
        mapping = {}
        for i, (cs_spk, _) in enumerate(cs_sorted):
            if i < len(gt_sorted):
                gt_spk, _ = gt_sorted[i]
                mapping[cs_spk] = gt_spk
        
        return mapping
    
    async def validate_dev_set(self) -> List[Dict]:
        """Validate entire dev set (2 sessions)."""
        self.load_transcripts("dev")
        
        print(f"\n{'='*80}")
        print(f"VALIDATING CHiME-6 DEV SET")
        print(f"{'='*80}\n")
        
        results = []
        for session_id in self.sessions.keys():
            result = await self.validate_session(session_id)
            results.append(result)
            
            # Save individual result
            self._save_result(result, f"chime6_{session_id}")
        
        # Save combined results
        self._save_results(results, "chime6_dev_complete")
        
        return results
    
    def _save_result(self, result: Dict, filename: str):
        """Save single result."""
        output_file = self.output_path / f"{filename}_{datetime.now().strftime('%Y%m%d')}.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"    ✓ Saved: {output_file.name}")
    
    def _save_results(self, results: List[Dict], filename: str):
        """Save batch results."""
        output_file = self.output_path / f"{filename}_{datetime.now().strftime('%Y%m%d')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n✓ All results saved to {output_file}")


async def main():
    """Test CHiME-6 validator."""
    
    transcripts_dir = Path("validation_data/samples/chime6/transcriptions")
    audio_dir = Path("validation_data/chime6_audio")  # TODO: download audio
    output_path = Path("validation_data/results")
    output_path.mkdir(parents=True, exist_ok=True)
    
    validator = CHiME6Validator(transcripts_dir, audio_dir, output_path)
    validator.load_transcripts("dev")
    
    # Show what we loaded
    print(f"\nLoaded sessions:")
    for session_id, data in validator.sessions.items():
        segments = data['segments']
        speakers = set(seg['speaker'] for seg in segments)
        duration = validator._time_to_seconds(segments[-1]['end_time'])
        print(f"  {session_id}: {len(segments)} segments, {len(speakers)} speakers, {duration/60:.1f} min")
    
    # Test ground truth extraction
    if validator.sessions:
        test_id = list(validator.sessions.keys())[0]
        print(f"\nTesting ground truth extraction for {test_id}...")
        gt_segments = validator.get_ground_truth_segments(test_id)
        print(f"✓ Extracted {len(gt_segments)} segments")
        print(f"\nFirst 5 segments:")
        for i, seg in enumerate(gt_segments[:5]):
            print(f"  {i+1}. [{seg['start']:.1f}s] {seg['speaker']}: {seg['text']}")
    
    print("\n✅ CHiME-6 validator skeleton working!")
    print("Next: Download CHiME-6 audio, process first session")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

